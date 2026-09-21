"""
Gemini API 클라이언트. 모델 폴백 체인을 적용해 특정 모델이 사용 불가/쿼터 초과일 때
자동으로 다음 모델로 재시도합니다.

secrets.toml 필요 항목:
    GEMINI_API_KEY = "..."
"""
import streamlit as st

FALLBACK_CHAIN = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


@st.cache_resource(show_spinner=False)
def _build_client(api_key: str):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    return genai


def get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        return None


def generate_report_narrative(prompt: str) -> dict:
    """
    반환: {"text": str, "model_used": str} 또는 오류 시 {"text": None, "error": str}
    """
    api_key = get_api_key()
    if not api_key:
        return {"text": None, "error": "GEMINI_API_KEY가 설정되어 있지 않습니다. (.streamlit/secrets.toml 확인)"}

    genai = _build_client(api_key)

    last_error = None
    for model_name in FALLBACK_CHAIN:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = (response.text or "").strip()
            if text:
                return {"text": text, "model_used": model_name}
        except Exception as e:
            last_error = f"{model_name}: {e}"
            continue

    return {"text": None, "error": f"모든 모델 호출에 실패했습니다. 마지막 오류: {last_error}"}


def build_report_prompt(context: dict) -> str:
    """계산 결과를 바탕으로 AI 해설 프롬프트를 구성."""
    return f"""
당신은 한국 병원 경영 컨설턴트입니다. 아래 일반병동 수익 데이터를 바탕으로
병원 경영진이 읽을 전문적인 보고서 해설 문단을 작성하세요.

[조건]
- 병원명: {context.get('hospital_name', '해당 병원')}
- 분석 기간: {context.get('period_label')}
- 적용 간호관리료 등급: {context.get('grade')}등급
- 병실료 소계: {context.get('room_subtotal')}원
- 야간(전담)간호료: {context.get('night_amount')}원 ({context.get('night_type')})
- 총 수익: {context.get('total_revenue')}원
- 총 환자일수(연인원): {context.get('total_patient_days')}일
- 등급별 비교 데이터: {context.get('grade_comparison')}

[작성 지침]
1. 3~4개 문단, 총 400~600자 내외의 한국어 경영 보고서 톤으로 작성
2. 첫 문단: 기간 내 수익 현황 총평
3. 둘째 문단: 병실 구성 및 재원일수 구간별 특이사항(가장 기여도가 큰 병실 유형 언급)
4. 셋째 문단: 간호관리료 등급 변동 시 예상되는 수익 영향(등급별 비교 데이터 활용)
5. 마지막 문단: 실무진에게 제안할 개선 방향 1~2가지
6. 마크다운 기호(#, *, -) 사용하지 말고 순수 텍스트 문단으로만 작성
7. 과장된 표현 대신 데이터에 근거한 담백하고 신뢰감 있는 문체 사용
""".strip()
