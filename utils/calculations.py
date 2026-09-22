"""
일반병동차등제 등급별 병실료(명칭 기준) + 야간간호료/야간전담간호료(등급 무관, 항목 선택형)
수익 계산 엔진. 모든 금액 연산은 Decimal로 처리하여 부동소수점 오차를 방지합니다.
"""
from decimal import Decimal, ROUND_HALF_UP


def _find_room_fee_row(fee_db: dict, grade: str, name: str):
    for row in fee_db.get("room_fee", []):
        if row["등급"] == str(grade) and row["명칭"] == name:
            return row
    return None


def _find_night_item(fee_db: dict, night_key: str):
    for item in fee_db.get("night_items", []):
        if item["key"] == night_key:
            return item
    return None


def calc_room_revenue(fee_db: dict, grade: str, census: list) -> dict:
    """
    census: [{"명칭": "병원 2등급간호관리료적용 2인실입원료", "구간": "1~15일", "환자일수": 120}, ...]
    반환: {"lines": [...], "subtotal": Decimal, "total_patient_days": int}
    """
    lines = []
    subtotal = Decimal("0")
    total_patient_days = 0

    for item in census:
        name = item["명칭"]
        tier = item["구간"]
        days = int(item.get("환자일수", 0) or 0)
        if days <= 0:
            continue

        row = _find_room_fee_row(fee_db, grade, name)
        if row is None:
            lines.append({
                "명칭": name, "구간": tier, "환자일수": days,
                "단가": Decimal("0"), "수가코드": "(DB 없음)", "금액": Decimal("0"),
                "warning": True,
            })
            continue

        tier_info = row["tiers"].get(tier)
        unit_price = tier_info["금액"] if tier_info else Decimal("0")
        code = tier_info["수가코드"] if tier_info else ""
        amount = (unit_price * Decimal(days)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        lines.append({
            "명칭": name, "구간": tier, "환자일수": days,
            "단가": unit_price, "수가코드": code, "금액": amount,
            "warning": unit_price == 0,
        })
        subtotal += amount
        total_patient_days += days

    return {"lines": lines, "subtotal": subtotal, "total_patient_days": total_patient_days}


def calc_night_revenue(fee_db: dict, night_key: str, total_patient_days: int) -> dict:
    item = _find_night_item(fee_db, night_key)
    if item is None:
        return {"구분": "-", "명칭": "(선택 안 됨)", "단가": Decimal("0"),
                "환자일수": total_patient_days, "금액": Decimal("0")}
    unit_price = item["금액"]
    amount = (unit_price * Decimal(total_patient_days)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return {
        "구분": item["구분"],
        "명칭": item["명칭"],
        "단가": unit_price,
        "환자일수": total_patient_days,
        "금액": amount,
    }


def calc_total_revenue(fee_db: dict, grade: str, census: list, night_key: str) -> dict:
    room_result = calc_room_revenue(fee_db, grade, census)
    night_result = calc_night_revenue(fee_db, night_key, room_result["total_patient_days"])
    total = room_result["subtotal"] + night_result["금액"]
    return {
        "grade": grade,
        "room": room_result,
        "night": night_result,
        "total_revenue": total,
    }


def compare_grades(fee_db: dict, base_grade: str, grades: list, census: list, night_key: str) -> list:
    """
    base_grade에서 입력한 census(명칭 기준)를, 명칭에서 추출한 '병실크기'를 매개로
    다른 등급의 동일 병실크기 수가에 대입하여 수익을 비교합니다.
    (예: 2등급의 '2인실' 재원일수를 1등급/3등급의 '2인실' 단가에 그대로 적용)
    """
    base_rows = {r["명칭"]: r for r in fee_db.get("room_fee", []) if r["등급"] == str(base_grade)}

    # (병실크기 또는 명칭, 구간) -> 총 환자일수 로 집계
    size_days = {}
    for item in census:
        days = int(item.get("환자일수", 0) or 0)
        if days <= 0:
            continue
        row = base_rows.get(item["명칭"])
        size_key = (row.get("병실크기") or item["명칭"]) if row else item["명칭"]
        key = (size_key, item["구간"])
        size_days[key] = size_days.get(key, 0) + days

    results = []
    for g in grades:
        grade_rows_by_size = {}
        for r in fee_db.get("room_fee", []):
            if r["등급"] != str(g):
                continue
            size_key = r.get("병실크기") or r["명칭"]
            grade_rows_by_size[size_key] = r

        subtotal = Decimal("0")
        total_days = 0
        unmatched = False
        for (size_key, tier), days in size_days.items():
            row = grade_rows_by_size.get(size_key)
            if row is None:
                unmatched = True
                continue
            tier_info = row["tiers"].get(tier)
            price = tier_info["금액"] if tier_info else Decimal("0")
            subtotal += (price * Decimal(days)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            total_days += days

        night_result = calc_night_revenue(fee_db, night_key, total_days)
        total = subtotal + night_result["금액"]
        results.append({
            "grade": g,
            "room_subtotal": subtotal,
            "night_amount": night_result["금액"],
            "total_revenue": total,
            "unmatched": unmatched,
        })
    return results


def format_krw(amount: Decimal) -> str:
    return f"{int(amount):,}원"
