import streamlit as st
import feedparser
import google.generativeai as genai
from github import Github
import json
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import time

# --- 환경 변수 로드 ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# Gemini & GitHub 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

# --- GitHub JSON 조작 함수 ---
def load_json(file_path, default):
    try:
        content = repo.get_contents(file_path)
        return json.loads(content.decoded_content.decode('utf-8'))
    except: return default

def save_json(file_path, data, msg):
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    try:
        file = repo.get_contents(file_path)
        repo.update_file(file_path, msg, json_str, file.sha)
    except: repo.create_file(file_path, msg, json_str)

# --- 데이터 로드 ---
FEEDS_FILE = "feeds.json"
REPORTS_FILE = "daily_reports.json" # 날짜별 통합 보고서 저장

feeds = load_json(FEEDS_FILE, [])
reports = load_json(REPORTS_FILE, {})

# --- UI 설정 ---
st.set_page_config(page_title="AI 가전 뉴스룸", page_icon="📑", layout="wide")

# 사이드바 메뉴
menu = st.sidebar.selectbox("메뉴", ["🏠 뉴스룸 홈", "🛠️ 관리자 대시보드"])

# ==========================================
# 1. 뉴스룸 홈 (메인 화면)
# ==========================================
if menu == "🏠 뉴스룸 홈":
    st.title("📑 가전업계 AI 데일리 리포트")
    
    if not reports:
        st.info("아직 생성된 보고서가 없습니다. 관리자 페이지에서 수집을 시작해주세요.")
    else:
        # 최신 날짜순 정렬
        report_dates = sorted(reports.keys(), reverse=True)
        
        # 상단 네비게이션 바 (날짜 선택)
        selected_date = st.select_slider("조회할 날짜를 선택하세요", options=report_dates, value=report_dates[0])
        
        st.divider()
        st.subheader(f"📅 {selected_date} 핵심 요약 보고서")
        
        # Gemini가 생성한 마크다운 보고서 출력
        st.markdown(reports[selected_date])

# ==========================================
# 2. 관리자 대시보드
# ==========================================
else:
    st.title("🛠️ 관리자 대시보드")
    pw = st.text_input("비밀번호", type="password")
    
    if pw == ADMIN_PASSWORD:
        tab1, tab2 = st.tabs(["RSS 피드 관리", "수집 및 분석 실행"])
        
        with tab1:
            st.subheader("📡 RSS 등록")
            new_url = st.text_input("RSS URL 입력")
            if st.button("추가"):
                if new_url and new_url not in feeds:
                    feeds.append(new_url)
                    save_json(FEEDS_FILE, feeds, "Add feed")
                    st.success("추가됨"); st.rerun()
            
            for f in feeds:
                c1, c2 = st.columns([8, 1])
                c1.write(f)
                if c2.button("X", key=f):
                    feeds.remove(f)
                    save_json(FEEDS_FILE, feeds, "Remove feed")
                    st.rerun()

        with tab2:
            st.subheader("🚀 최근 3일치 뉴스 분석")
            if st.button("분석 시작"):
                all_articles = []
                three_days_ago = datetime.now() - timedelta(days=3)
                
                with st.spinner("최근 3일 뉴스를 긁어오는 중..."):
                    for url in feeds:
                        feed = feedparser.parse(url)
                        for entry in feed.entries:
                            # 발행일 파싱 및 3일 이내 체크
                            try:
                                pub_date = date_parser.parse(entry.published).replace(tzinfo=None)
                                if pub_date > three_days_ago:
                                    all_articles.append({
                                        "title": entry.title,
                                        "link": entry.link,
                                        "summary": entry.get("summary", "")[:500] # 분석을 위해 일부만
                                    })
                            except: continue
                
                if not all_articles:
                    st.warning("최근 3일 내 새로운 기사가 없습니다.")
                else:
                    st.write(f"총 {len(all_articles)}개의 기사를 발견했습니다. 토픽별 그룹화 중...")
                    
                    # Gemini에게 전달할 텍스트 구성
                    articles_text = "\n".join([f"- [{a['title']}]({a['link']})" for a in all_articles])
                    
                    prompt = f"""
                    당신은 가전업계 전문 시장 분석가입니다. 아래 뉴스 목록은 최근 3일간의 국내 가전(정수기, 청정기, 안마의자, 로봇청소기, 삼성/LG/코웨이 등) 소식입니다.
                    
                    [지침]
                    1. 모든 뉴스를 읽고 유사한 주제(예: 신제품 출시, 실적 발표, 렌탈 시장 동향 등)끼리 **토픽별로 묶어서** 리포트를 작성하세요.
                    2. 각 토픽은 제목, 핵심 내용 요약(3-5문장), 그리고 관련된 기사들의 제목과 링크를 포함해야 합니다.
                    3. 마지막에는 '오늘의 한 줄 인사이트'를 추가하세요.
                    4. 전체 보고서는 1장 분량의 깔끔한 마크다운(Markdown) 형식을 유지하세요.
                    
                    [기사 목록]
                    {articles_text}
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        report_md = response.text
                        
                        # 결과 저장
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        reports[today_str] = report_md
                        save_json(REPORTS_FILE, reports, f"Create report for {today_str}")
                        
                        st.success("보고서 생성이 완료되었습니다! 홈 화면에서 확인하세요.")
                    except Exception as e:
                        st.error(f"Gemini 분석 중 오류: {e}")

    elif pw:
        st.error("인증 실패")
