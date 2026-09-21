import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from utils import db_manager as dbm

st.title("🗂️ 수가 데이터(DB) 관리")
st.caption("일반병동차등제 병실료 · 야간간호료 · 야간전담간호료 수가를 엑셀로 업로드하여 계산 기준 DB를 구성합니다.")

st.divider()

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("#### 1. 템플릿 다운로드")
    st.write("아래 템플릿을 다운로드하여 병원의 실제 수가 코드/금액을 입력한 뒤 다시 업로드하세요.")
    st.download_button(
        "📥 엑셀 템플릿 다운로드",
        data=dbm.generate_template_excel(),
        file_name="일반병동_수가_DB_템플릿.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with col2:
    st.markdown("#### 2. 작성된 엑셀 업로드")
    uploaded = st.file_uploader("수가 DB 엑셀 파일(.xlsx)", type=["xlsx"], label_visibility="collapsed")
    if uploaded:
        parsed = dbm.parse_uploaded_excel(uploaded)
        if parsed["errors"]:
            st.error("업로드한 파일에 문제가 있습니다:")
            for e in parsed["errors"]:
                st.write(f"- {e}")
        else:
            st.session_state["fee_db"] = parsed["data"]
            st.success(f"업로드 완료! 등급 {dbm.get_available_grades(parsed['data'])}개 확인됨.")
            if st.button("💾 이 DB를 기본값으로 저장 (다음 실행에도 유지)", use_container_width=True):
                dbm.save_db_to_disk(parsed["data"])
                st.toast("기본 DB로 저장되었습니다.", icon="✅")

st.divider()

fee_db = dbm.get_db_from_session_or_disk()

if not fee_db:
    st.info("아직 업로드된 수가 DB가 없습니다. 위에서 템플릿을 다운로드하고 작성 후 업로드해 주세요.")
    st.stop()

st.markdown("#### 3. 현재 등록된 DB 확인")
grades = dbm.get_available_grades(fee_db)
st.write(f"등록된 등급: **{grades}**")

tab1, tab2, tab3 = st.tabs(["병실료", "야간간호료", "야간전담간호료"])

with tab1:
    rows = []
    for r in fee_db["room_fee"]:
        for tier_name, tier in r["tiers"].items():
            rows.append({
                "등급": r["등급"], "병실구분": r["병실구분"], "구간": tier_name,
                "수가코드": tier["수가코드"], "금액": int(tier["금액"]),
            })
    if rows:
        df = pd.DataFrame(rows).sort_values(["등급", "병실구분", "구간"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("데이터 없음")

with tab2:
    if fee_db["night_fee"]:
        df = pd.DataFrame(fee_db["night_fee"])
        df["금액"] = df["금액"].astype(int)
        st.dataframe(df.sort_values("등급"), use_container_width=True, hide_index=True)
    else:
        st.caption("데이터 없음")

with tab3:
    if fee_db["night_dedicated_fee"]:
        df = pd.DataFrame(fee_db["night_dedicated_fee"])
        df["금액"] = df["금액"].astype(int)
        st.dataframe(df.sort_values("등급"), use_container_width=True, hide_index=True)
    else:
        st.caption("데이터 없음")

st.divider()
if st.button("🗑️ 현재 세션 DB 초기화"):
    st.session_state.pop("fee_db", None)
    st.rerun()
