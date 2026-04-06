import streamlit as st
from datetime import datetime, timezone

from github_storage import get_feeds, save_feeds, get_daily_reports, save_daily_report
from rss_parser import fetch_and_filter_articles
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
    
    # Render Report
    if selected_date in reports:
        st.markdown(reports[selected_date])
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
    
    if st.button("🚀 데이터 수집 및 AI 리포트 생성 시작", type="primary"):
        with st.spinner("파이프라인 실행 중... (시간이 소요될 수 있습니다)"):
            try:
                # 1. Fetch
                st.toast("1. 뉴스 기사 수집 중...")
                articles = fetch_and_filter_articles(feeds, hours=72)
                st.info(f"총 {len(articles)}개의 기사가 수집되었습니다.")
                
                # 2. Add AI Briefing
                st.toast("2. Gemini AI 리포트 생성 중...")
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
