import streamlit as st
from datetime import datetime, timezone

from github_storage import get_feeds, save_feeds, get_daily_reports, save_daily_report
from rss_parser import fetch_and_filter_articles
from naver_scraper import fetch_naver_news
from youtube_scraper import fetch_youtube_videos
from ai_reporter import generate_daily_briefing

st.set_page_config(
    page_title="AI 가전 뉴스룸",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_password():
    """Returns True if user entered the correct password."""
    if st.session_state.get('authenticated'):
        return True

    def password_entered():
        if st.session_state["password"] == st.secrets.get("ADMIN_PASSWORD", "admin"):
            st.session_state["authenticated"] = True
            del st.session_state["password"]
        else:
            st.error("비밀번호가 일치하지 않습니다.")

    st.text_input("🔑 관리자 패스워드를 입력하세요", type="password", on_change=password_entered, key="password")
    return False

def show_main_screen():
    st.title("📺 AI 가전 뉴스룸 (Home Appliance Newsroom)")
    st.markdown("최신 가전 트렌드를 AI가 매일 요약해 드립니다.")
    
    reports = get_daily_reports()
    
    if not reports:
        st.info("아직 생성된 리포트가 없습니다. 관리자 대시보드에서 파이프라인을 실행해주세요.")
        return
        
    dates = sorted(list(reports.keys()), reverse=False) # older first for slider
    latest_date = dates[-1]
    
    # Timeline navigation
    if len(dates) == 1:
        st.info(f"📅 현재 1개의 리포트만 존재합니다. ({latest_date})")
        selected_date = latest_date
    else:
        selected_date = st.select_slider(
            "📅 지난 리포트 보기 (타임라인)",
            options=dates,
            value=latest_date
        )
    
    st.divider()
    
    # Render Report & Infographics
    if selected_date in reports:
        report_str = reports[selected_date]
        
        # Check if html code is attached
        if "```html" in report_str:
            parts = report_str.split("```html")
            text_content = parts[0]
            html_code = parts[1].split("```")[0]
            
            # Print main text first
            st.markdown(text_content)
            
            # Render HTML Infographic Dashboard
            import streamlit.components.v1 as components
            # Wrap the generated html in a nice container if needed, but the model should provide full styling
            components.html(html_code, height=750, scrolling=True)
            
            # Print any remaining trailing text after code block
            remaining = parts[1].split("```", 1)
            if len(remaining) > 1:
                st.markdown(remaining[1])
        else:
            st.markdown(report_str)
    else:
        st.warning("선택한 날짜의 리포트를 불러올 수 없습니다.")

def show_admin_dashboard():
    st.title("🛠️ 관리자 대시보드")
    
    st.header("1. RSS 피드 관리")
    feeds = get_feeds()
    
    # Add new feed
    new_feed = st.text_input("새로운 RSS 피드 URL 추가")
    if st.button("➕ 피드 추가"):
        if new_feed and new_feed not in feeds:
            feeds.append(new_feed)
            try:
                save_feeds(feeds)
                st.success("피드가 성공적으로 추가되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"피드 추가 실패: {str(e)}")
                
    st.subheader("등록된 구독 리스트")
    if not feeds:
        st.info("등록된 RSS 피드가 없습니다.")
    else:
        for i, feed in enumerate(feeds):
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f"- {feed}")
            with col2:
                if st.button("❌ 삭제", key=f"del_{i}"):
                    feeds.remove(feed)
                    try:
                        save_feeds(feeds)
                        st.success("피드가 삭제되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"피드 삭제 실패: {str(e)}")

    st.divider()
    st.header("2. AI 분석 파이프라인 트리거")
    st.markdown("등록된 RSS 피드를 스크랩하여 최근 72시간 이내의 뉴스를 AI가 수집 및 분석합니다.")
    
    if st.button("🚀 전체 데이터 수집 및 AI 리포트 생성 (가전, 네이버, 유튜브 포함)", type="primary", use_container_width=True):
        with st.spinner("파이프라인 실행 중... (시간이 소요될 수 있습니다)"):
            try:
                articles = []
                
                # 1. Fetch Google RSS
                if feeds:
                    st.toast("1. 구글 뉴스 기사 수집 중...")
                    articles += fetch_and_filter_articles(feeds, hours=72)
                
                # 2. Fetch Naver Scraper
                st.toast("2. 네이버 뉴스 스크래핑 수집 중...")
                naver_queries = ["가전", "로봇청소기", "스마트홈", "AI가전"] # 기본 검색어
                articles += fetch_naver_news(naver_queries, hours=72)
                
                # 3. Fetch YouTube
                st.toast("3. 유튜브 테크/가전 관련 최근 영상 분석 중...")
                youtube_channels = ["UChbDEJUckWuoEBSOFTwMtbQ", "UCHs0X-ZqA8k_T-tVq0zM6fA"] # 대표 테크채널 예시
                articles += fetch_youtube_videos(youtube_channels, hours=72)
                
                st.info(f"총 {len(articles)}개의 기사 및 영상이 수집되었습니다.")
                
                # 4. Generate AI Briefing + Infographic
                st.toast("4. Nano-Banana 인포그래픽 및 AI 리포트 작성 중...")
                report_md = generate_daily_briefing(articles)
                
                # 3. Save
                st.toast("3. GitHub Storage 저장 중...")
                today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                save_daily_report(today_str, report_md)
                
                st.success(f"[{today_str}] 데일리 브리핑이 성공적으로 생성 및 저장되었습니다!")
                st.balloons()
            except Exception as e:
                st.error(f"파이프라인 실행 중 오류 발생: {str(e)}")

# Main Routing
tab1, tab2 = st.tabs(["🏡 뉴스룸 홈", "⚙️ 관리자 대시보드"])

with tab1:
    show_main_screen()

with tab2:
    if check_password():
        show_admin_dashboard()
