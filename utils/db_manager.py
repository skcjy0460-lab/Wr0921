"""
일반병동차등제 병실료 / 야간간호료 / 야간전담간호료 수가 DB 관리.

엑셀 템플릿 구조 (3개 시트):

1) 병실료
   등급 | 병실구분 | 수가코드_1~15일 | 금액_1~15일 | 수가코드_16~30일 | 금액_16~30일 | 수가코드_31일이상 | 금액_31일이상
   - 병실구분: 1인실, 2인실, 3인실, 4인실, 5인실, 6인실

2) 야간간호료
   등급 | 수가코드 | 1일당_금액

3) 야간전담간호료
   등급 | 수가코드 | 1일당_금액

업로드된 파일은 세션에 보관되며, '기본 DB로 저장' 시 로컬 JSON(data/fee_schedule.json)에
영구 저장되어 다음 실행 시 자동으로 불러옵니다.
"""
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "fee_schedule.json"

ROOM_TYPES = ["1인실", "2인실", "3인실", "4인실", "5인실", "6인실"]

ROOM_FEE_COLUMNS = [
    "등급", "병실구분",
    "수가코드_1~15일", "금액_1~15일",
    "수가코드_16~30일", "금액_16~30일",
    "수가코드_31일이상", "금액_31일이상",
]
NIGHT_FEE_COLUMNS = ["등급", "수가코드", "1일당_금액"]


def generate_template_excel() -> bytes:
    """빈 템플릿(예시 1개 등급 포함) 엑셀 바이트를 생성."""
    room_rows = []
    for room in ROOM_TYPES:
        room_rows.append({
            "등급": 1, "병실구분": room,
            "수가코드_1~15일": "", "금액_1~15일": 0,
            "수가코드_16~30일": "", "금액_16~30일": 0,
            "수가코드_31일이상": "", "금액_31일이상": 0,
        })
    room_df = pd.DataFrame(room_rows, columns=ROOM_FEE_COLUMNS)

    night_df = pd.DataFrame(
        [{"등급": 1, "수가코드": "", "1일당_금액": 0}],
        columns=NIGHT_FEE_COLUMNS,
    )
    night_dedicated_df = pd.DataFrame(
        [{"등급": 1, "수가코드": "", "1일당_금액": 0}],
        columns=NIGHT_FEE_COLUMNS,
    )

    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        room_df.to_excel(writer, sheet_name="병실료", index=False)
        night_df.to_excel(writer, sheet_name="야간간호료", index=False)
        night_dedicated_df.to_excel(writer, sheet_name="야간전담간호료", index=False)

        guide = pd.DataFrame({
            "작성 안내": [
                "1) 병실료 시트: 등급 × 병실구분(1인실~6인실)별로 재원일수 구간(1~15일/16~30일/31일이상)에 해당하는 수가코드와 금액을 입력하세요.",
                "2) 야간간호료 / 야간전담간호료 시트: 등급별 1일당 가산 금액을 입력하세요. (두 항목은 상호 배타적으로 적용됩니다)",
                "3) 등급은 병원에서 적용 중인 간호관리료 차등등급 번호를 그대로 입력하세요. (예: 1~7)",
                "4) 금액은 숫자만 입력하세요 (원 단위, 콤마 없이).",
                "5) 행을 추가/복사하여 필요한 만큼 등급을 늘려서 작성할 수 있습니다.",
            ]
        })
        guide.to_excel(writer, sheet_name="작성안내", index=False)

    return buf.getvalue()


def _to_decimal(value) -> Decimal:
    try:
        if value is None or value == "":
            return Decimal("0")
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def parse_uploaded_excel(uploaded_file) -> dict:
    """업로드된 엑셀을 파싱하고 검증. 오류 목록과 함께 결과를 반환."""
    errors = []
    result = {"room_fee": [], "night_fee": [], "night_dedicated_fee": []}

    try:
        xls = pd.ExcelFile(uploaded_file)
    except Exception as e:
        return {"errors": [f"엑셀 파일을 읽을 수 없습니다: {e}"], "data": None}

    # 병실료
    if "병실료" not in xls.sheet_names:
        errors.append("'병실료' 시트를 찾을 수 없습니다.")
    else:
        df = pd.read_excel(xls, sheet_name="병실료")
        missing_cols = [c for c in ROOM_FEE_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"'병실료' 시트에 컬럼 누락: {missing_cols}")
        else:
            for i, row in df.iterrows():
                room = str(row["병실구분"]).strip()
                if pd.isna(row["등급"]) or room in ("", "nan"):
                    continue
                if room not in ROOM_TYPES:
                    errors.append(f"'병실료' {i+2}행: 알 수 없는 병실구분 '{room}' (허용값: {ROOM_TYPES})")
                    continue
                result["room_fee"].append({
                    "등급": int(row["등급"]),
                    "병실구분": room,
                    "tiers": {
                        "1~15일": {
                            "수가코드": str(row["수가코드_1~15일"]) if pd.notna(row["수가코드_1~15일"]) else "",
                            "금액": _to_decimal(row["금액_1~15일"]),
                        },
                        "16~30일": {
                            "수가코드": str(row["수가코드_16~30일"]) if pd.notna(row["수가코드_16~30일"]) else "",
                            "금액": _to_decimal(row["금액_16~30일"]),
                        },
                        "31일이상": {
                            "수가코드": str(row["수가코드_31일이상"]) if pd.notna(row["수가코드_31일이상"]) else "",
                            "금액": _to_decimal(row["금액_31일이상"]),
                        },
                    },
                })

    # 야간간호료 / 야간전담간호료
    for sheet_key, result_key in [("야간간호료", "night_fee"), ("야간전담간호료", "night_dedicated_fee")]:
        if sheet_key not in xls.sheet_names:
            errors.append(f"'{sheet_key}' 시트를 찾을 수 없습니다.")
            continue
        df = pd.read_excel(xls, sheet_name=sheet_key)
        missing_cols = [c for c in NIGHT_FEE_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"'{sheet_key}' 시트에 컬럼 누락: {missing_cols}")
            continue
        for i, row in df.iterrows():
            if pd.isna(row["등급"]):
                continue
            result[result_key].append({
                "등급": int(row["등급"]),
                "수가코드": str(row["수가코드"]) if pd.notna(row["수가코드"]) else "",
                "금액": _to_decimal(row["1일당_금액"]),
            })

    if not errors and not result["room_fee"]:
        errors.append("'병실료' 시트에 유효한 데이터가 없습니다.")

    return {"errors": errors, "data": result if not errors else None}


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError


def save_db_to_disk(data: dict):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=_decimal_default)


def load_db_from_disk() -> dict | None:
    if not DB_PATH.exists():
        return None
    with open(DB_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    def restore(d):
        if isinstance(d, dict):
            return {k: restore(v) for k, v in d.items()}
        if isinstance(d, list):
            return [restore(v) for v in d]
        return d

    raw = restore(raw)
    # 금액 필드를 다시 Decimal로 변환
    for row in raw.get("room_fee", []):
        for tier in row["tiers"].values():
            tier["금액"] = _to_decimal(tier["금액"])
    for key in ("night_fee", "night_dedicated_fee"):
        for row in raw.get(key, []):
            row["금액"] = _to_decimal(row["금액"])
    return raw


def get_available_grades(fee_db: dict) -> list:
    grades = {row["등급"] for row in fee_db.get("room_fee", [])}
    return sorted(grades)


def get_db_from_session_or_disk():
    if "fee_db" in st.session_state:
        return st.session_state["fee_db"]
    disk_db = load_db_from_disk()
    if disk_db:
        st.session_state["fee_db"] = disk_db
    return disk_db
