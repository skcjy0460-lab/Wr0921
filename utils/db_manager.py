"""
일반병동차등제 병실료 / 야간간호료 / 야간전담간호료 수가 DB 관리.

엑셀 구조 (실제 건강보험 수가 체계 기준, 3개 시트):

1) 병실료
   명칭 | 등급 | 수가코드_1~15일 | 금액_1~15일 | 수가코드_16~30일 | 금액_16~30일 | 수가코드_31일이상 | 금액_31일이상
   - 명칭: 실제 청구 항목명 (예: "병원 2등급간호관리료적용 2인실입원료")
   - 등급: 병원이 적용 중인 간호관리료 차등등급 (숫자 등급 또는 'A' 등 특수 등급 모두 허용, 문자열로 취급)
   - 병실 크기(1인실~6인실)는 명칭에서 자동으로 추출하여 등급 간 비교에 사용합니다.

2) 야간간호료 / 야간전담간호료
   명칭 | 수가코드 | 1일당_금액
   - 등급과 무관하게 병원이 실제 운영 중인 항목(예: 야간전담간호사 운영비율 구간별)을 그대로 나열
   - 리포트 작성 시 이 중 실제 적용 중인 항목 1개를 선택해서 사용합니다.

업로드된 파일은 세션에 보관되며, '기본 DB로 저장' 시 로컬 JSON(data/fee_schedule.json)에
영구 저장되어 다음 실행 시 자동으로 불러옵니다.
"""
import io
import json
import re
from pathlib import Path
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "fee_schedule.json"

TIER_NAMES = ["1~15일", "16~30일", "31일이상"]

ROOM_FEE_COLUMNS = [
    "명칭", "등급",
    "수가코드_1~15일", "금액_1~15일",
    "수가코드_16~30일", "금액_16~30일",
    "수가코드_31일이상", "금액_31일이상",
]
NIGHT_FEE_COLUMNS = ["명칭", "수가코드", "1일당_금액"]

_ROOM_SIZE_RE = re.compile(r"([1-6])\s*인실")


def extract_room_size(name: str):
    """명칭 문자열에서 '2인실'과 같은 병실 크기를 추출 (등급 간 비교용 매칭 키)."""
    m = _ROOM_SIZE_RE.search(name or "")
    return f"{m.group(1)}인실" if m else None


def generate_template_excel() -> bytes:
    """실제 데이터 형식에 맞춘 예시 템플릿 엑셀 바이트를 생성."""
    room_rows = [
        {"명칭": "병원 1인실입원료[비급여]", "등급": "1",
         "수가코드_1~15일": "", "금액_1~15일": 0,
         "수가코드_16~30일": "", "금액_16~30일": 0,
         "수가코드_31일이상": "", "금액_31일이상": 0},
        {"명칭": "병원 1등급간호관리료적용 2인실입원료", "등급": "1",
         "수가코드_1~15일": "", "금액_1~15일": 0,
         "수가코드_16~30일": "", "금액_16~30일": 0,
         "수가코드_31일이상": "", "금액_31일이상": 0},
        {"명칭": "병원 2등급간호관리료적용 2인실입원료", "등급": "2",
         "수가코드_1~15일": "", "금액_1~15일": 0,
         "수가코드_16~30일": "", "금액_16~30일": 0,
         "수가코드_31일이상": "", "금액_31일이상": 0},
    ]
    room_df = pd.DataFrame(room_rows, columns=ROOM_FEE_COLUMNS)

    night_df = pd.DataFrame(
        [{"명칭": "야간간호료-병원", "수가코드": "", "1일당_금액": 0}],
        columns=NIGHT_FEE_COLUMNS,
    )
    night_dedicated_df = pd.DataFrame(
        [
            {"명칭": "야간전담간호사 관리료-병원 야간전담간호사 운영비율 10% 미만", "수가코드": "", "1일당_금액": 0},
            {"명칭": "야간전담간호사 관리료-병원 야간전담간호사 운영비율 10% 이상 ~ 15% 미만", "수가코드": "", "1일당_금액": 0},
        ],
        columns=NIGHT_FEE_COLUMNS,
    )

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        room_df.to_excel(writer, sheet_name="병실료", index=False)
        night_df.to_excel(writer, sheet_name="야간간호료", index=False)
        night_dedicated_df.to_excel(writer, sheet_name="야간전담간호료", index=False)

        guide = pd.DataFrame({
            "작성 안내": [
                "1) 병실료 시트: 명칭(실제 청구 항목명)과 등급별로 재원일수 구간(1~15일/16~30일/31일이상)에 해당하는 수가코드와 금액을 입력하세요.",
                "2) 명칭에 'N인실'이 포함되어 있으면 등급 간 비교 시 동일 병실 크기로 자동 매칭됩니다.",
                "3) 등급은 숫자 등급(1~6 등) 또는 'A' 등 병원에서 사용하는 표기를 그대로 입력하세요.",
                "4) 야간간호료 / 야간전담간호료 시트에는 등급 없이, 병원이 실제 운영 중인 항목을 명칭별로 나열하세요.",
                "   (예: 야간전담간호사 운영비율 구간별로 여러 행을 추가)",
                "5) 금액은 숫자만 입력하세요 (원 단위, 콤마 없이).",
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
    result = {"room_fee": [], "night_items": []}

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
                name = str(row["명칭"]).strip() if pd.notna(row["명칭"]) else ""
                grade = str(row["등급"]).strip() if pd.notna(row["등급"]) else ""
                if not name or not grade:
                    continue
                result["room_fee"].append({
                    "명칭": name,
                    "등급": grade,
                    "병실크기": extract_room_size(name),
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

    # 야간간호료 / 야간전담간호료 (등급 없이 명칭 기준 항목 나열)
    for sheet_key, group_label in [("야간간호료", "야간간호료"), ("야간전담간호료", "야간전담간호료")]:
        if sheet_key not in xls.sheet_names:
            errors.append(f"'{sheet_key}' 시트를 찾을 수 없습니다.")
            continue
        df = pd.read_excel(xls, sheet_name=sheet_key)
        missing_cols = [c for c in NIGHT_FEE_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"'{sheet_key}' 시트에 컬럼 누락: {missing_cols}")
            continue
        for i, row in df.iterrows():
            name = str(row["명칭"]).strip() if pd.notna(row["명칭"]) else ""
            if not name:
                continue
            code = str(row["수가코드"]) if pd.notna(row["수가코드"]) else ""
            item_key = f"{group_label}::{code or name}"
            result["night_items"].append({
                "구분": group_label,
                "명칭": name,
                "수가코드": code,
                "금액": _to_decimal(row["1일당_금액"]),
                "key": item_key,
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

    for row in raw.get("room_fee", []):
        for tier in row["tiers"].values():
            tier["금액"] = _to_decimal(tier["금액"])
    for row in raw.get("night_items", []):
        row["금액"] = _to_decimal(row["금액"])
    return raw


def get_available_grades(fee_db: dict) -> list:
    grades = {row["등급"] for row in fee_db.get("room_fee", [])}

    def sort_key(g):
        return (0, int(g)) if g.isdigit() else (1, g)

    return sorted(grades, key=sort_key)


def get_grade_room_rows(fee_db: dict, grade: str) -> list:
    return [r for r in fee_db.get("room_fee", []) if r["등급"] == str(grade)]


def get_room_size_map(fee_db: dict, grade: str) -> dict:
    """선택 등급에서 '1인실'~'6인실' 등 병실 크기 -> 해당 명칭 목록 매핑. (병상수 자동입력용)"""
    mapping = {}
    for r in get_grade_room_rows(fee_db, grade):
        size = r.get("병실크기")
        if size:
            mapping.setdefault(size, []).append(r["명칭"])
    return mapping


def sorted_room_sizes(sizes) -> list:
    return sorted(sizes, key=lambda s: int(s[0]) if s and s[0].isdigit() else 99)


def build_census_rows(fee_db: dict, grade: str) -> list:
    """선택된 등급의 병실료 명칭별 × 재원구간별 입력 행(환자일수=0)을 생성."""
    rows = []
    for r in get_grade_room_rows(fee_db, grade):
        for tier in TIER_NAMES:
            rows.append({"명칭": r["명칭"], "구간": tier, "환자일수": 0})
    return rows


def get_night_items(fee_db: dict) -> list:
    return fee_db.get("night_items", [])


def get_db_from_session_or_disk():
    if "fee_db" in st.session_state:
        return st.session_state["fee_db"]
    disk_db = load_db_from_disk()
    if disk_db:
        st.session_state["fee_db"] = disk_db
    return disk_db
