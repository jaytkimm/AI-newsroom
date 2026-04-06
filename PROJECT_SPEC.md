# 📺 AI 가전 뉴스룸 (AI Home Appliance Newsroom)

## 1. 프로젝트 개요
본 프로젝트는 국내 주요 가전제품(정수기, 청정기, 로봇청소기 등) 및 관련 제조사(삼성, LG, 코웨이 등)의 최신 뉴스 기사를 자동으로 수집하고, AI를 통해 1장짜리 데일리 브리핑 보고서로 요약해 주는 자동화 대시보드입니다. 별도의 백엔드 데이터베이스 없이 GitHub 저장소를 JSON 데이터 스토리지로 활용하여 완전한 서버리스(Serverless) 형태로 운영됩니다.

## 2. 기술 스택 (Tech Stack)
* **Language:** Python 3.x
* **Frontend & Web Framework:** Streamlit
* **AI / LLM:** Google Gemini API (`gemini-pro` 모델)
* **Data Storage:** GitHub Repository (JSON 파일 기반 데이터베이스 활용, `PyGithub` 라이브러리)
* **Data Parsing:** `feedparser` (RSS 피드 파싱), `python-dateutil` (날짜 데이터 전처리)
* **Deployment:** Streamlit Community Cloud

## 3. 핵심 기능 명세

### 3.1. 메인 화면 (뉴스룸 홈)
* **날짜별 리포트 조회:** GitHub 스토리지에 저장된 일일 생성 리포트를 불러옵니다.
* **타임라인 네비게이션:** 상단 슬라이더(`st.select_slider`)를 통해 과거 날짜의 리포트를 선택하여 조회할 수 있으며, 최신 리포트가 기본 화면으로 노출됩니다.
* **마크다운 렌더링:** Gemini가 생성한 가독성 높은 마크다운 형식의 리포트를 화면에 출력합니다.

### 3.2. 관리자 대시보드
* **보안 인증:** `.streamlit/secrets.toml` 또는 Streamlit Cloud 환경 변수에 등록된 관리자 비밀번호를 통해 접근을 제어합니다.
* **RSS 피드 관리 (CRUD):** * 새로운 타겟 RSS URL을 등록하거나 삭제할 수 있습니다.
    * 변경 사항은 즉시 GitHub의 `feeds.json`에 동기화됩니다.
* **수집 및 AI 분석 파이프라인 트리거:**
    1.  **데이터 수집:** 등록된 RSS 피드를 순회하며 **최근 72시간(3일)** 이내의 기사만 필터링하여 스크랩합니다.
    2.  **데이터 전처리:** 뉴스 제목, 원문 링크, 본문 요약 데이터를 추출하여 리스트업합니다.
    3.  **AI 토픽 그룹화 및 리포팅:** 추출된 기사 목록 전체를 Gemini 프롬프트에 주입하여, 연관된 주제(신제품, 실적 등)별로 그룹화하고 인사이트를 도출하는 1장 분량의 브리핑 문서를 생성합니다.
    4.  **저장 동기화:** 생성된 텍스트는 당일 날짜를 Key값으로 하여 `daily_reports.json`에 저장(Commit)됩니다.

## 4. 데이터 스키마 (Data Schema)
모든 데이터는 GitHub Repository의 루트 경로에 JSON 형태로 관리됩니다.

### 4.1. `feeds.json` (구독 리스트)
```json
[
  "[https://news.google.com/rss/search?q=(가전](https://news.google.com/rss/search?q=(가전))...",
  "[https://news.google.com/rss/search?q=(로봇청소기](https://news.google.com/rss/search?q=(로봇청소기))..."
]