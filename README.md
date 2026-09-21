# 일반병동 수익 보고서 생성기 (Ward Revenue Report Generator)

Wivo Company · 메디엄 — 일반병동차등제 등급에 따른 병실료 / 야간간호료 / 야간전담간호료
기반 수익을 계산하고, Gemini AI 해설이 포함된 프리미엄 A4 HTML 보고서를 생성하는 Streamlit 앱입니다.

## 주요 기능

1. **수가 DB 관리** — 병실료(1인실~6인실 × 1~15일/16~30일/31일이상)와 야간간호료/야간전담간호료를
   엑셀 템플릿으로 업로드하여 자체 DB로 구성. `data/fee_schedule.json`에 영구 저장 가능.
2. **수익 계산 대시보드** — 기간(1/3/7/14/21/30일 또는 직접 입력) × 병실구분 × 재원일수구간별
   환자일수(연인원)를 입력하면 Decimal 정밀도로 정확한 수익을 계산. 동일 데이터를 등록된
   모든 등급에 적용해 등급 변동 영향을 비교.
3. **AI 보고서 생성** — Gemini(3.6-flash → 3.5-flash-lite → 2.5-flash → 2.0-flash 자동 폴백)가
   계산 결과를 바탕으로 경영 분석 해설을 작성하고, 프리미엄 디자인의 A4 HTML 보고서로 출력.
   브라우저에서 인쇄(Ctrl/Cmd+P) → PDF 저장으로 바로 PDF 산출 가능.
4. **라이선스 키 게이트(선택)** — `secrets.toml`에 `LICENSE_KEYS`를 등록하면 유료 접근 통제 활성화.
   미등록 시 자동으로 게이트 없이 동작(개발/테스트 모드).

## 설치 및 실행

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml에 GEMINI_API_KEY 입력 (Google AI Studio에서 발급)
streamlit run app.py
```

## Streamlit Cloud 배포 시

1. 이 폴더 전체를 GitHub 저장소에 업로드
2. Streamlit Cloud에서 `app.py`를 메인 파일로 지정해 배포
3. App Settings → Secrets 에 `.streamlit/secrets.toml.example` 내용을 참고해
   `GEMINI_API_KEY`(및 필요 시 `LICENSE_KEYS`)를 등록

## 수가 DB 엑셀 형식

- **병실료** 시트: `등급 | 병실구분 | 수가코드_1~15일 | 금액_1~15일 | 수가코드_16~30일 | 금액_16~30일 | 수가코드_31일이상 | 금액_31일이상`
- **야간간호료** / **야간전담간호료** 시트: `등급 | 수가코드 | 1일당_금액`
- '수가 데이터(DB) 관리' 메뉴에서 템플릿을 바로 다운로드할 수 있습니다.
- ⚠️ 실제 수가 금액은 병원마다 적용 기준이 다를 수 있으므로, 반드시 병원 자체 수가표를 기준으로
  엑셀을 작성해 업로드해 주세요(본 프로그램은 금액을 자동으로 추정하지 않습니다).

## 폴더 구조

```
ward_revenue_app/
├── app.py                      # 메인 진입점 (st.navigation)
├── requirements.txt
├── .streamlit/secrets.toml.example
├── assets/logo.png             # Wivo Company 로고
├── data/                       # 저장된 수가 DB(fee_schedule.json)가 위치
├── utils/
│   ├── license.py              # 라이선스 키 게이트
│   ├── db_manager.py           # 수가 DB 업로드/템플릿/영속화
│   ├── calculations.py         # Decimal 정밀도 수익 계산 엔진
│   ├── ai_client.py            # Gemini 폴백 체인 클라이언트
│   └── report_generator.py     # 프리미엄 A4 HTML 보고서 생성
└── views/
    ├── dashboard.py            # 수익 계산 대시보드
    ├── data_management.py      # 수가 DB 관리
    └── report.py                # AI 보고서 생성
```

## 다음 확장 아이디어

- 야간간호료/야간전담간호료를 월별·분기별로 추이 그래프화
- 엑셀(.xlsx) 형태의 원본 데이터 보고서 동시 출력
- 다중 병동(중환자실 등) 확장 대응
- 유료 결제 연동(라이선스 키 자동 발급)
