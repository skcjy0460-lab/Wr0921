"""
일반병동 수익 보고서 생성기 (Ward Revenue Report Generator)
- Wivo Company / 메디엄
- Streamlit 기반, Gemini AI 리포트 해설, 프리미엄 A4 HTML 리포트 출력
"""
import streamlit as st
from pathlib import Path

from utils.license import check_license_gate

BASE_DIR = Path(__file__).parent

st.set_page_config(
    page_title="일반병동 수익 보고서 | Wivo",
    page_icon=str(BASE_DIR / "assets" / "logo.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_global_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=Playfair+Display:wght@600;700;800&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Noto Sans KR', sans-serif;
        }

        :root {
            --navy-950: #050B18;
            --navy-900: #0A1428;
            --navy-800: #0F1E3A;
            --navy-700: #16294f;
            --teal-400: #2FE6C6;
            --teal-500: #17C9B2;
            --blue-500: #1257E0;
            --blue-400: #2E7CF6;
            --gold-400: #D4AF63;
            --gold-500: #C6992F;
            --ink-100: #EAF0FF;
            --ink-300: #B7C3DE;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--navy-950) 0%, var(--navy-900) 100%);
            border-right: 1px solid rgba(47, 230, 198, 0.15);
        }
        section[data-testid="stSidebar"] * { color: var(--ink-100) !important; }

        .wivo-brand-row {
            display: flex; align-items: center; gap: 10px;
            padding: 18px 4px 22px 4px;
            border-bottom: 1px solid rgba(47,230,198,0.18);
            margin-bottom: 14px;
        }
        .wivo-brand-title {
            font-family: 'Playfair Display', serif;
            font-weight: 700; font-size: 1.05rem;
            letter-spacing: 0.02em;
            color: var(--ink-100);
            line-height: 1.15;
        }
        .wivo-brand-sub {
            font-size: 0.72rem; color: var(--gold-400);
            letter-spacing: 0.12em;
        }

        div.block-container { padding-top: 2rem; }

        .metric-card {
            background: linear-gradient(155deg, var(--navy-900) 0%, var(--navy-800) 100%);
            border: 1px solid rgba(212,175,99,0.25);
            border-radius: 10px;
            padding: 18px 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


load_global_css()

with st.sidebar:
    st.markdown(
        f"""
        <div class="wivo-brand-row">
            <div>
                <div class="wivo-brand-title">일반병동 수익 보고서</div>
                <div class="wivo-brand-sub">WIVO COMPANY · MEDIEM</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.image(str(BASE_DIR / "assets" / "logo.png"), use_container_width=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# 라이선스 게이트 (secrets에 LICENSE_KEYS가 설정된 경우에만 활성화)
check_license_gate()

pages = {
    "분석": [
        st.Page("views/dashboard.py", title="수익 계산 대시보드", icon="📊", default=True),
        st.Page("views/report.py", title="AI 보고서 생성", icon="🧾"),
    ],
    "관리": [
        st.Page("views/data_management.py", title="수가 데이터(DB) 관리", icon="🗂️"),
    ],
}

nav = st.navigation(pages)
nav.run()
