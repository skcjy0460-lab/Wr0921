import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
night_items = dbm.get_night_items(fee_db)

if not night_items:
    st.warning("야간간호료/야간전담간호료 항목이 DB에 없습니다. 수가 데이터 관리 메뉴에서 업로드해 주세요.")
    st.stop()

# ---------- 입력 영역 ----------
st.markdown("#### 1. 기본 조건 설정")
c1, c2 = st.columns(2)
with c1:
    hospital_name = st.text_input("병원명", value=st.session_state.get("hospital_name", ""), placeholder="예: OO병원")
with c2:
    grade = st.selectbox("적용 간호관리료 등급", grades, index=0)

night_labels = {
    item["key"]: f"[{item['구분']}] {item['명칭']} — {int(item['금액']):,}원/일"
    for item in night_items
}
night_key = st.selectbox(
    "야간간호료 / 야간전담간호료 적용 항목",
    options=list(night_labels.keys()),
    format_func=lambda k: night_labels[k],
)

st.markdown("#### 2. 분석 기간")
period_options = ["1일", "3일", "7일", "14일", "21일", "30일", "직접 입력"]
period_choice = st.radio("기간 선택", period_options, horizontal=True, index=2)
if period_choice == "직접 입력":
    custom_days = st.number_input("기간(일)", min_value=1, max_value=366, value=7)
    period_days = int(custom_days)
else:
    period_days = int(period_choice.replace("일", ""))
period_label = f"최근 {period_days}일"

st.markdown("#### 3. 병실 항목별 재원일수(연인원) 입력")
st.caption("선택한 등급에 등록된 병실료 명칭 × 재원일수구간별 **총 환자일수(연인원)** 를 입력하세요. "
           "예: 2인실에서 1~15일 구간 환자가 평균 4명씩 7일간 입원했다면 28일을 입력합니다.")

editor_state_key = f"census_editor_{grade}"
if editor_state_key not in st.session_state:
    rows = dbm.build_census_rows(fee_db, grade)
    if not rows:
        st.warning(f"'{grade}' 등급에 등록된 병실료 명칭이 없습니다. 수가 데이터를 확인해 주세요.")
        st.stop()
    st.session_state[editor_state_key] = pd.DataFrame(rows)

edited_df = st.data_editor(
    st.session_state[editor_state_key],
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "명칭": st.column_config.TextColumn(disabled=True, width="large"),
        "구간": st.column_config.TextColumn(disabled=True),
        "환자일수": st.column_config.NumberColumn(min_value=0, step=1),
    },
    key=f"census_data_editor_{grade}",
)
st.session_state[editor_state_key] = edited_df

st.divider()

if st.button("🧮 수익 계산하기", type="primary", use_container_width=True):
    census = edited_df.to_dict("records")
    census = [c for c in census if int(c.get("환자일수", 0) or 0) > 0]

    if not census:
        st.error("환자일수를 1건 이상 입력해 주세요.")
        st.stop()

    result = calc.calc_total_revenue(fee_db, grade, census, night_key)
    comparison = calc.compare_grades(fee_db, grade, grades, census, night_key)
    for r in comparison:
        r["is_current"] = (r["grade"] == grade)

    st.session_state["last_calc"] = {
        "hospital_name": hospital_name or "미입력 병원",
        "period_label": period_label,
        "period_days": period_days,
        "grade": grade,
        "night_label": night_labels[night_key],
        "night_key": night_key,
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
    m3.metric("야간 가산", calc.format_krw(result["night"]["금액"]))
    m4.metric("총 환자일수(연인원)", f"{result['room']['total_patient_days']:,}일")
    st.caption(f"적용 야간 항목: {data['night_label']}")

    with st.expander("병실 항목별 상세 내역 보기", expanded=True):
        rows = []
        for line in result["room"]["lines"]:
            rows.append({
                "명칭": line["명칭"], "구간": line["구간"],
                "환자일수": line["환자일수"], "단가(원)": int(line["단가"]),
                "수가코드": line["수가코드"], "금액(원)": int(line["금액"]),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("간호관리료 등급별 수익 비교", expanded=True):
        st.caption("※ 입력한 재원일수를 병실 크기(N인실) 기준으로 각 등급의 수가에 대입한 예상 수익입니다.")
        comp_rows = [{
            "등급": r["grade"], "병실료(원)": int(r["room_subtotal"]),
            "야간가산(원)": int(r["night_amount"]), "총 수익(원)": int(r["total_revenue"]),
            "현재 적용": "✅" if r.get("is_current") else "",
            "매칭 불가 항목 있음": "⚠️" if r.get("unmatched") else "",
        } for r in data["comparison"]]
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

    st.info("👉 상단 메뉴의 **AI 보고서 생성**에서 이 계산 결과로 프리미엄 A4 보고서를 만들 수 있습니다.")
