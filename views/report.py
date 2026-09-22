import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from utils import ai_client
from utils import report_generator as rg

st.title("🧾 AI 보고서 생성")

if "last_calc" not in st.session_state:
    st.warning("먼저 **수익 계산 대시보드**에서 수익 계산을 완료해 주세요.")
    st.stop()

data = st.session_state["last_calc"]
result = data["result"]

st.caption(f"{data['hospital_name']} · {data['period_label']} · {data['grade']}등급 기준 계산 결과로 보고서를 생성합니다.")

use_ai = st.toggle("Gemini AI 경영 분석 해설 포함", value=True,
                    help="병실 구성, 등급별 영향, 개선 방향 등을 AI가 자동 작성합니다.")

if st.button("📄 보고서 생성", type="primary", use_container_width=True):
    ai_narrative = None

    if use_ai:
        with st.spinner("AI가 경영 분석 해설을 작성하는 중입니다..."):
            prompt = ai_client.build_report_prompt({
                "hospital_name": data["hospital_name"],
                "period_label": data["period_label"],
                "grade": data["grade"],
                "room_subtotal": int(result["room"]["subtotal"]),
                "night_amount": int(result["night"]["금액"]),
                "night_type": data["night_label"],
                "total_revenue": int(result["total_revenue"]),
                "total_patient_days": result["room"]["total_patient_days"],
                "total_beds": data.get("total_beds", 0),
                "occupancy": data.get("occupancy"),
                "grade_comparison": [
                    {"등급": r["grade"], "총수익": int(r["total_revenue"])} for r in data["comparison"]
                ],
            })
            ai_result = ai_client.generate_report_narrative(prompt)
            if ai_result.get("text"):
                ai_narrative = ai_result["text"]
                st.toast(f"AI 해설 생성 완료 ({ai_result.get('model_used')})", icon="✨")
            else:
                st.warning(f"AI 해설 생성에 실패했습니다: {ai_result.get('error')} — 해설 없이 보고서를 생성합니다.")

    html = rg.build_html_report({
        "hospital_name": data["hospital_name"],
        "period_label": data["period_label"],
        "generated_at": datetime.now().strftime("%Y년 %m월 %d일 %H:%M"),
        "grade": data["grade"],
        "night_type": result["night"]["구분"],
        "night_detail": result["night"]["명칭"],
        "total_beds": data.get("total_beds", 0),
        "bed_counts": data.get("bed_counts", {}),
        "occupancy": data.get("occupancy"),
        "room_lines": result["room"]["lines"],
        "room_subtotal": result["room"]["subtotal"],
        "night_amount": result["night"]["금액"],
        "night_unit_price": result["night"]["단가"],
        "night_patient_days": result["night"]["환자일수"],
        "total_revenue": result["total_revenue"],
        "total_patient_days": result["room"]["total_patient_days"],
        "grade_comparison": data["comparison"],
        "ai_narrative": ai_narrative,
    })

    st.session_state["generated_report_html"] = html
    st.success("보고서가 생성되었습니다.")

if "generated_report_html" in st.session_state:
    html = st.session_state["generated_report_html"]

    st.download_button(
        "⬇️ HTML 보고서 다운로드 (A4 인쇄용)",
        data=html.encode("utf-8"),
        file_name=f"{data['hospital_name']}_일반병동수익보고서_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True,
    )
    st.caption("다운로드한 HTML 파일을 브라우저로 열고 인쇄(Ctrl/Cmd+P) → 'PDF로 저장'을 선택하면 A4 PDF로 저장할 수 있습니다.")

    st.markdown("#### 미리보기")
    components.html(html, height=900, scrolling=True)
