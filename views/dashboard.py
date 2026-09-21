import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
import pandas as pd
import streamlit as st

from utils import db_manager as dbm
from utils import calculations as calc

st.title("📊 일반병동 수익 계산 대시보드")

fee_db = dbm.get_db_from_session_or_disk()
if not fee_db:
    st.warning("먼저 **수가 데이터(DB) 관리** 메뉴에서 수가 DB를 업로드해 주세요.")
    st.stop()

grades = dbm.get_available_grades(fee_db)

# ---------- 입력 영역 ----------
st.markdown("#### 1. 기본 조건 설정")
c1, c2, c3 = st.columns(3)
with c1:
    hospital_name = st.text_input("병원명", value=st.session_state.get("hospital_name", ""), placeholder="예: OO병원")
with c2:
    grade = st.selectbox("적용 간호관리료 등급", grades, index=0)
with c3:
    night_type = st.radio("야간 가산 유형", ["야간간호료", "야간전담간호료"], horizontal=True)

st.markdown("#### 2. 분석 기간")
period_options = ["1일", "3일", "7일", "14일", "21일", "30일", "직접 입력"]
period_choice = st.radio("기간 선택", period_options, horizontal=True, index=2)
if period_choice == "직접 입력":
    custom_days = st.number_input("기간(일)", min_value=1, max_value=366, value=7)
    period_days = int(custom_days)
    period_label = f"최근 {period_days}일"
else:
    period_days = int(period_choice.replace("일", ""))
    period_label = f"최근 {period_days}일"

st.markdown("#### 3. 병실구분별 재원일수(연인원) 입력")
st.caption("선택한 분석 기간 동안 병실구분 × 재원일수구간별 **총 환자일수(연인원)** 를 입력하세요. "
           "예: 2인실에서 1~15일 구간 환자가 평균 4명씩 7일간 입원했다면 28일을 입력합니다.")

if "census_editor" not in st.session_state:
    rows = []
    for room in dbm.ROOM_TYPES:
        for tier in ["1~15일", "16~30일", "31일이상"]:
            rows.append({"병실구분": room, "구간": tier, "환자일수": 0})
    st.session_state["census_editor"] = pd.DataFrame(rows)

edited_df = st.data_editor(
    st.session_state["census_editor"],
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "병실구분": st.column_config.TextColumn(disabled=True),
        "구간": st.column_config.TextColumn(disabled=True),
        "환자일수": st.column_config.NumberColumn(min_value=0, step=1),
    },
    key="census_data_editor",
)
st.session_state["census_editor"] = edited_df

st.divider()

if st.button("🧮 수익 계산하기", type="primary", use_container_width=True):
    census = edited_df.to_dict("records")
    census = [c for c in census if int(c.get("환자일수", 0) or 0) > 0]

    if not census:
        st.error("환자일수를 1건 이상 입력해 주세요.")
        st.stop()

    result = calc.calc_total_revenue(fee_db, grade, census, night_type)
    comparison = calc.compare_grades(fee_db, grades, census, night_type)
    for r in comparison:
        r["is_current"] = (r["grade"] == grade)

    st.session_state["last_calc"] = {
        "hospital_name": hospital_name or "미입력 병원",
        "period_label": period_label,
        "period_days": period_days,
        "grade": grade,
        "night_type": night_type,
        "census": census,
        "result": result,
        "comparison": comparison,
    }
    st.success("계산이 완료되었습니다. 아래에서 결과를 확인하거나 'AI 보고서 생성' 메뉴로 이동하세요.")

# ---------- 결과 표시 ----------
if "last_calc" in st.session_state:
    data = st.session_state["last_calc"]
    result = data["result"]

    st.markdown("#### 계산 결과")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 수익", calc.format_krw(result["total_revenue"]))
    m2.metric("병실료 소계", calc.format_krw(result["room"]["subtotal"]))
    m3.metric(f"{data['night_type']}", calc.format_krw(result["night"]["금액"]))
    m4.metric("총 환자일수(연인원)", f"{result['room']['total_patient_days']:,}일")

    with st.expander("병실구분별 상세 내역 보기", expanded=True):
        rows = []
        for line in result["room"]["lines"]:
            rows.append({
                "병실구분": line["병실구분"], "구간": line["구간"],
                "환자일수": line["환자일수"], "단가(원)": int(line["단가"]),
                "수가코드": line["수가코드"], "금액(원)": int(line["금액"]),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("간호관리료 등급별 수익 비교", expanded=True):
        comp_rows = [{"등급": r["grade"], "총 수익(원)": int(r["total_revenue"]),
                       "현재 적용": "✅" if r.get("is_current") else ""} for r in data["comparison"]]
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

    st.info("👉 상단 메뉴의 **AI 보고서 생성**에서 이 계산 결과로 프리미엄 A4 보고서를 만들 수 있습니다.")
