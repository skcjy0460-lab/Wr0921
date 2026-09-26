import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from utils import db_manager as dbm
from utils import calculations as calc
from utils import ai_client
from utils import report_generator as rg

st.title("⚖️ 비교 AI 보고서 생성")
st.caption("두 가지 운영 시나리오(A안/B안)를 병상가동률·야간 가산 항목 기준으로 비교하고, Wivo AI가 최종 진단합니다.")

fee_db = dbm.get_db_from_session_or_disk()
if not fee_db:
    st.warning("먼저 **수가 데이터(DB) 관리** 메뉴에서 수가 DB를 업로드해 주세요.")
    st.stop()

grades = dbm.get_available_grades(fee_db)
night_items = dbm.get_night_items(fee_db)

# ---------- 1. 공통 조건 ----------
st.markdown("#### 1. 공통 조건")
c1, c2 = st.columns(2)
with c1:
    hospital_name = st.text_input("병원명", key="cmp_hospital", placeholder="예: OO병원")
with c2:
    grade = st.selectbox("적용 간호관리료 등급", grades, index=0, key="cmp_grade")

period_options = ["1일", "3일", "7일", "14일", "21일", "30일", "직접 입력"]
period_choice = st.radio("분석 기간", period_options, horizontal=True, index=2, key="cmp_period")
if period_choice == "직접 입력":
    period_days = int(st.number_input("기간(일)", min_value=1, max_value=366, value=7, key="cmp_period_days"))
else:
    period_days = int(period_choice.replace("일", ""))
period_label = f"최근 {period_days}일"

size_map = dbm.get_room_size_map(fee_db, grade)
room_sizes = dbm.sorted_room_sizes(size_map.keys())

if not room_sizes:
    st.error("선택한 등급의 병실료 명칭에서 'N인실' 표기를 찾을 수 없어 비교 기능을 사용할 수 없습니다.")
    st.stop()

st.caption("병실 크기별 병상수 (두 시나리오에 공통 적용 — 병상가동률만 다르게 비교합니다)")
bed_counts = {}
bed_cols = st.columns(len(room_sizes))
for col, size in zip(bed_cols, room_sizes):
    with col:
        bed_counts[size] = st.number_input(f"{size} 병상수", min_value=0, step=1, key=f"cmp_beds_{grade}_{size}")

st.divider()

# ---------- 2. 시나리오 설정 ----------
st.markdown("#### 2. 시나리오 설정 (A안 / B안)")

NONE_OPTION = "(선택 안 함)"


def _night_select(category_label: str, key_prefix: str):
    items = [i for i in night_items if i["구분"] == category_label]
    if not items:
        return None
    labels = {NONE_OPTION: NONE_OPTION}
    labels.update({it["key"]: f"{it['명칭']} — {int(it['금액']):,}원/일" for it in items})
    options = [NONE_OPTION] + [it["key"] for it in items]
    sel = st.selectbox(category_label, options=options, format_func=lambda k: labels[k],
                        key=f"{key_prefix}_{category_label}")
    return None if sel == NONE_OPTION else sel


colA, colB = st.columns(2)
with colA:
    st.markdown("##### 🅰️ A안")
    label_a = st.text_input("A안 이름", value="A안", key="cmp_label_a")
    occ_a = st.slider("병상가동률(%)", 0, 100, 20, key="cmp_occ_a")
    ng_a = _night_select("야간간호료", "cmp_night_a")
    nd_a = _night_select("야간전담간호료", "cmp_night_a")
    night_keys_a = [k for k in [ng_a, nd_a] if k]

with colB:
    st.markdown("##### 🅱️ B안")
    label_b = st.text_input("B안 이름", value="B안", key="cmp_label_b")
    occ_b = st.slider("병상가동률(%)", 0, 100, 50, key="cmp_occ_b")
    ng_b = _night_select("야간간호료", "cmp_night_b")
    nd_b = _night_select("야간전담간호료", "cmp_night_b")
    night_keys_b = [k for k in [ng_b, nd_b] if k]

st.divider()


def _build_census(occupancy: int):
    census = []
    for size, beds in bed_counts.items():
        if beds <= 0:
            continue
        days = round(beds * occupancy / 100 * period_days)
        for name in size_map.get(size, []):
            census.append({"명칭": name, "구간": "1~15일", "환자일수": days})
    return census


if st.button("⚖️ 두 안 비교 계산하기", type="primary", use_container_width=True):
    census_a = _build_census(occ_a)
    census_b = _build_census(occ_b)

    if not census_a and not census_b:
        st.error("병상수를 1개 이상 입력해 주세요.")
        st.stop()

    result_a = calc.calc_total_revenue(fee_db, grade, census_a, night_keys_a)
    result_b = calc.calc_total_revenue(fee_db, grade, census_b, night_keys_b)

    st.session_state["last_compare"] = {
        "hospital_name": hospital_name or "미입력 병원",
        "period_label": period_label,
        "grade": grade,
        "label_a": label_a, "occupancy_a": occ_a, "night_keys_a": night_keys_a, "result_a": result_a,
        "label_b": label_b, "occupancy_b": occ_b, "night_keys_b": night_keys_b, "result_b": result_b,
        "bed_counts": bed_counts,
    }
    st.success("비교 계산이 완료되었습니다. 아래에서 결과를 확인하고 비교 보고서를 생성하세요.")

# ---------- 결과 ----------
if "last_compare" in st.session_state:
    data = st.session_state["last_compare"]
    ra, rb = data["result_a"], data["result_b"]

    st.markdown("#### 계산 결과 비교")
    cA, cB = st.columns(2)
    with cA:
        st.markdown(f"**{data['label_a']}** · 가동률 {data['occupancy_a']}%")
        st.metric("총 수익", calc.format_krw(ra["total_revenue"]))
        st.caption(f"병실료 {calc.format_krw(ra['room']['subtotal'])} · 야간가산 {calc.format_krw(ra['night']['금액'])}")
    with cB:
        st.markdown(f"**{data['label_b']}** · 가동률 {data['occupancy_b']}%")
        st.metric("총 수익", calc.format_krw(rb["total_revenue"]))
        st.caption(f"병실료 {calc.format_krw(rb['room']['subtotal'])} · 야간가산 {calc.format_krw(rb['night']['금액'])}")

    diff = rb["total_revenue"] - ra["total_revenue"]
    if diff > 0:
        better = data["label_b"]
    elif diff < 0:
        better = data["label_a"]
    else:
        better = "동일"

    if diff != 0:
        st.info(f"**{better}**이(가) 총수익 기준 {calc.format_krw(abs(diff))} 더 높습니다.")
    else:
        st.info("두 안의 총수익이 동일합니다.")

    st.divider()
    use_ai = st.toggle("Wivo AI 비교 진단 포함", value=True, key="cmp_use_ai")

    if st.button("📄 비교 보고서 생성", type="primary", use_container_width=True):
        ai_narrative = None

        def _night_summary(keys):
            if not keys:
                return "선택 안 함"
            return " + ".join(
                next((it["구분"] for it in night_items if it["key"] == k), k) for k in keys
            )

        if use_ai:
            with st.spinner("Wivo AI가 두 안을 비교 진단하는 중입니다..."):
                prompt = ai_client.build_comparison_prompt({
                    "hospital_name": data["hospital_name"],
                    "period_label": data["period_label"],
                    "grade": data["grade"],
                    "label_a": data["label_a"], "occupancy_a": data["occupancy_a"],
                    "night_summary_a": _night_summary(data["night_keys_a"]),
                    "room_subtotal_a": int(ra["room"]["subtotal"]), "night_amount_a": int(ra["night"]["금액"]),
                    "total_revenue_a": int(ra["total_revenue"]),
                    "label_b": data["label_b"], "occupancy_b": data["occupancy_b"],
                    "night_summary_b": _night_summary(data["night_keys_b"]),
                    "room_subtotal_b": int(rb["room"]["subtotal"]), "night_amount_b": int(rb["night"]["금액"]),
                    "total_revenue_b": int(rb["total_revenue"]),
                    "diff_amount": int(abs(diff)),
                    "better_label": better,
                })
                ai_result = ai_client.generate_comparison_verdict(prompt)
                if ai_result.get("text"):
                    ai_narrative = ai_result["text"]
                    st.toast("Wivo AI 비교 진단 생성 완료", icon="✨")
                else:
                    st.warning(f"{ai_result.get('error')} — 진단 없이 보고서를 생성합니다.")

        html = rg.build_comparison_html_report({
            "hospital_name": data["hospital_name"],
            "period_label": data["period_label"],
            "grade": data["grade"],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "label_a": data["label_a"], "occupancy_a": data["occupancy_a"], "result_a": ra,
            "night_items_a": ra["night"]["items"],
            "label_b": data["label_b"], "occupancy_b": data["occupancy_b"], "result_b": rb,
            "night_items_b": rb["night"]["items"],
            "diff_amount": diff, "better_label": better,
            "ai_narrative": ai_narrative,
        })
        st.session_state["compare_report_html"] = html
        st.success("비교 보고서가 생성되었습니다.")

if "compare_report_html" in st.session_state:
    html = st.session_state["compare_report_html"]
    data = st.session_state.get("last_compare", {})

    st.download_button(
        "⬇️ 비교 보고서 다운로드 (A4 인쇄용)",
        data=html.encode("utf-8"),
        file_name=f"{data.get('hospital_name','비교')}_시나리오비교보고서_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True,
    )
    st.caption("다운로드한 HTML 파일을 브라우저로 열고 인쇄(Ctrl/Cmd+P) → 'PDF로 저장'을 선택하면 A4 PDF로 저장할 수 있습니다.")

    st.markdown("#### 미리보기")
    components.html(html, height=900, scrolling=True)
