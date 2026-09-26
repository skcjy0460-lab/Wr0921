"""
Wivo AI 클라이언트 (내부적으로 Gemini API 사용, 모델 폴백 체인 적용).
UI/보고서에는 항상 "Wivo AI"라는 이름으로만 노출되며, 실제 모델명이나
공급사명은 화면·오류 메시지 어디에도 표시되지 않습니다.

secrets.toml 필요 항목:
    GEMINI_API_KEY = "..."
"""
import streamlit as st

# 내부 폴백 체인 (사용자에게는 절대 노출되지 않음)
_FALLBACK_CHAIN = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

AI_DISPLAY_NAME = "Wivo AI"


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


def _generate_with_fallback(prompt: str) -> dict:
    """
    반환: {"text": str} 또는 오류 시 {"text": None, "error": str}
    내부 모델명은 반환값에 절대 포함하지 않는다 (UI 노출 방지).
    """
    api_key = get_api_key()
    if not api_key:
        return {"text": None, "error": f"{AI_DISPLAY_NAME} 사용을 위한 API 키가 설정되어 있지 않습니다. (.streamlit/secrets.toml 확인)"}

    genai = _build_client(api_key)

    had_error = False
    for model_name in _FALLBACK_CHAIN:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = (response.text or "").strip()
            if text:
                return {"text": text}
        except Exception:
            had_error = True
            continue

    detail = " (일시적인 응답 오류)" if had_error else ""
    return {"text": None, "error": f"{AI_DISPLAY_NAME} 응답 생성에 실패했습니다{detail}. 잠시 후 다시 시도해 주세요."}


def generate_report_narrative(prompt: str) -> dict:
    return _generate_with_fallback(prompt)


def generate_comparison_verdict(prompt: str) -> dict:
    return _generate_with_fallback(prompt)


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
- 병상 현황: 총 {context.get('total_beds', 0)}병상, 병상가동률 {context.get('occupancy', '입력 안 됨')}%
- 등급별 비교 데이터: {context.get('grade_comparison')}

[작성 지침]
1. 3~4개 문단, 총 400~600자 내외의 한국어 경영 보고서 톤으로 작성
2. 첫 문단: 기간 내 수익 현황 총평
3. 둘째 문단: 병실 구성 및 재원일수 구간별 특이사항(가장 기여도가 큰 병실 유형 언급)
4. 셋째 문단: 간호관리료 등급 변동 시 예상되는 수익 영향(등급별 비교 데이터 활용)
5. 마지막 문단: 실무진에게 제안할 개선 방향 1~2가지
6. 마크다운 기호(#, *, -) 사용하지 말고 순수 텍스트 문단으로만 작성
7. 과장된 표현 대신 데이터에 근거한 담백하고 신뢰감 있는 문체 사용
8. 어떤 AI 모델이나 외부 서비스명(예: Gemini 등)도 절대 언급하지 말 것
""".strip()


def build_comparison_prompt(context: dict) -> str:
    """A안/B안 두 시나리오를 비교하는 AI 진단 프롬프트를 구성."""
    return f"""
당신은 한국 병원 경영 컨설턴트입니다. 아래 두 가지 운영 시나리오(A안/B안)의
일반병동 수익 계산 결과를 비교하여, 병원 경영진에게 어느 안이 더 유리한지
데이터에 근거해 진단하는 보고서 문단을 작성하세요.

[공통 조건]
- 병원명: {context.get('hospital_name', '해당 병원')}
- 분석 기간: {context.get('period_label')}
- 적용 간호관리료 등급: {context.get('grade')}등급

[A안: {context.get('label_a')}]
- 병상가동률: {context.get('occupancy_a')}%
- 적용 야간 항목: {context.get('night_summary_a')}
- 병실료 소계: {context.get('room_subtotal_a')}원
- 야간 가산 합계: {context.get('night_amount_a')}원
- 총 수익: {context.get('total_revenue_a')}원

[B안: {context.get('label_b')}]
- 병상가동률: {context.get('occupancy_b')}%
- 적용 야간 항목: {context.get('night_summary_b')}
- 병실료 소계: {context.get('room_subtotal_b')}원
- 야간 가산 합계: {context.get('night_amount_b')}원
- 총 수익: {context.get('total_revenue_b')}원

- 총수익 차이: {context.get('diff_amount')}원 ({context.get('better_label')}이 더 높음)

[작성 지침]
1. 3~4개 문단, 총 400~600자 내외의 한국어 경영 보고서 톤으로 작성
2. 첫 문단: 두 시나리오의 수익 차이를 금액과 비율로 총평
3. 둘째 문단: 그 차이가 어디서 발생하는지(병상가동률/야간 가산 항목 차이 등) 구체적으로 설명
4. 셋째 문단: 단순 수익 외에 고려할 요소가 있다면 언급 (예: 야간전담간호사 인건비·인력 확보 부담, 가동률 목표 달성 가능성 등 데이터에 근거해 유추 가능한 범위 내에서만)
5. 마지막 문단: 두 안 중 어느 쪽을 권장하는지 명확히 결론짓고, 실행 시 확인할 점 1~2가지 제안
6. 마크다운 기호(#, *, -) 사용하지 말고 순수 텍스트 문단으로만 작성
7. 어떤 AI 모델이나 외부 서비스명(예: Gemini 등)도 절대 언급하지 말 것
""".strip()
