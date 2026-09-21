"""
일반병동차등제 등급별 병실료 + 야간간호료/야간전담간호료 수익 계산 엔진.
모든 금액 연산은 Decimal로 처리하여 부동소수점 오차를 방지합니다.
"""
from decimal import Decimal, ROUND_HALF_UP


def _find_room_fee_row(fee_db: dict, grade: int, room_type: str):
    for row in fee_db.get("room_fee", []):
        if row["등급"] == grade and row["병실구분"] == room_type:
            return row
    return None


def _find_night_fee(fee_db: dict, grade: int, key: str) -> Decimal:
    for row in fee_db.get(key, []):
        if row["등급"] == grade:
            return row["금액"]
    return Decimal("0")


def calc_room_revenue(fee_db: dict, grade: int, census: list) -> dict:
    """
    census: [{"병실구분": "2인실", "구간": "1~15일", "환자일수": 120}, ...]
    반환: {"lines": [...], "subtotal": Decimal, "total_patient_days": int}
    """
    lines = []
    subtotal = Decimal("0")
    total_patient_days = 0

    for item in census:
        room = item["병실구분"]
        tier = item["구간"]
        days = int(item.get("환자일수", 0) or 0)
        if days <= 0:
            continue

        row = _find_room_fee_row(fee_db, grade, room)
        if row is None:
            lines.append({
                "병실구분": room, "구간": tier, "환자일수": days,
                "단가": Decimal("0"), "수가코드": "(DB 없음)", "금액": Decimal("0"),
                "warning": True,
            })
            continue

        tier_info = row["tiers"].get(tier)
        unit_price = tier_info["금액"] if tier_info else Decimal("0")
        code = tier_info["수가코드"] if tier_info else ""
        amount = (unit_price * Decimal(days)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        lines.append({
            "병실구분": room, "구간": tier, "환자일수": days,
            "단가": unit_price, "수가코드": code, "금액": amount,
            "warning": unit_price == 0,
        })
        subtotal += amount
        total_patient_days += days

    return {"lines": lines, "subtotal": subtotal, "total_patient_days": total_patient_days}


def calc_night_revenue(fee_db: dict, grade: int, total_patient_days: int, night_type: str) -> dict:
    """
    night_type: "야간간호료" 또는 "야간전담간호료" (상호 배타적)
    """
    key = "night_fee" if night_type == "야간간호료" else "night_dedicated_fee"
    unit_price = _find_night_fee(fee_db, grade, key)
    amount = (unit_price * Decimal(total_patient_days)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return {
        "유형": night_type,
        "단가": unit_price,
        "환자일수": total_patient_days,
        "금액": amount,
    }


def calc_total_revenue(fee_db: dict, grade: int, census: list, night_type: str) -> dict:
    room_result = calc_room_revenue(fee_db, grade, census)
    night_result = calc_night_revenue(fee_db, grade, room_result["total_patient_days"], night_type)
    total = room_result["subtotal"] + night_result["금액"]
    return {
        "grade": grade,
        "room": room_result,
        "night": night_result,
        "total_revenue": total,
    }


def compare_grades(fee_db: dict, grades: list, census: list, night_type: str) -> list:
    """동일한 재원일수 데이터를 여러 등급에 적용했을 때의 수익 비교."""
    results = []
    for g in grades:
        r = calc_total_revenue(fee_db, g, census, night_type)
        results.append(r)
    return results


def project_period(daily_avg_patient_days_per_room: dict, days_in_period: int) -> list:
    """
    daily_avg_patient_days_per_room: {"1인실_1~15일": 3.2, ...} 형태의 1일 평균 환자수를
    기간(days_in_period)에 대해 투영하여 census 리스트로 변환.
    key 형식: "{병실구분}_{구간}"
    """
    census = []
    for key, avg in daily_avg_patient_days_per_room.items():
        if avg <= 0:
            continue
        room, tier = key.split("_", 1)
        projected_days = int(round(avg * days_in_period))
        census.append({"병실구분": room, "구간": tier, "환자일수": projected_days})
    return census


def format_krw(amount: Decimal) -> str:
    return f"{int(amount):,}원"
