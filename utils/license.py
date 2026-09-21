"""
라이선스 키 게이트.
- st.secrets["LICENSE_KEYS"]에 유효 키 목록을 등록해두면 유료 접근 통제가 활성화됩니다.
- secrets가 설정되어 있지 않으면(개발/테스트 단계) 게이트를 건너뜁니다.
- 향후 유료 전환 시 Streamlit Cloud > Settings > Secrets 에
  LICENSE_KEYS = ["WIVO-XXXX-XXXX", "WIVO-YYYY-YYYY"] 형태로 추가하면 됩니다.
"""
import streamlit as st


def _get_valid_keys():
    try:
        keys = st.secrets.get("LICENSE_KEYS", None)
    except Exception:
        keys = None
    if not keys:
        return None
    if isinstance(keys, str):
        return {keys.strip()}
    return {str(k).strip() for k in keys}


def check_license_gate():
    valid_keys = _get_valid_keys()

    # secrets 미설정 = 게이트 비활성 (개발 모드)
    if valid_keys is None:
        return

    if st.session_state.get("license_ok"):
        return

    st.markdown(
        """
        <style>
        .license-wrap { max-width: 420px; margin: 80px auto 0 auto; text-align:center; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='license-wrap'>", unsafe_allow_html=True)
    st.markdown("### 🔐 라이선스 인증")
    st.caption("유료 라이선스 키를 입력해 주세요.")
    key_input = st.text_input("License Key", type="password", label_visibility="collapsed",
                               placeholder="WIVO-XXXX-XXXX-XXXX")
    if st.button("인증하기", use_container_width=True, type="primary"):
        if key_input.strip() in valid_keys:
            st.session_state["license_ok"] = True
            st.rerun()
        else:
            st.error("유효하지 않은 라이선스 키입니다.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
