import os
import tomllib
import holidays
from datetime import datetime
import pytz

# Try loading secrets in local dev env
try:
    with open('.streamlit/secrets.toml', 'rb') as f:
        secrets = tomllib.load(f)
        for k, v in secrets.items():
            if type(v) == str: os.environ[k] = v
except: pass

from github_storage import get_feeds, get_daily_reports, save_daily_report
from rss_parser import fetch_and_filter_articles
from naver_scraper import fetch_naver_news
from youtube_scraper import fetch_youtube_videos
from ai_reporter import generate_daily_briefing
from email_sender import send_email

def main():
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    today_str = now.strftime('%Y-%m-%d')
    kr_holidays = holidays.KR()
    
    # 주말 및 공휴일 체크 로직
    if now.weekday() >= 5 or now.date() in kr_holidays:
        print(f"[{today_str}] 주말이거나 공휴일입니다. 수집을 건너뛰고 누적합니다.")
        return

    # 이전 리포트와의 시간차 計算을 통해 공휴일/주말이 낀 만큼 자동 시간 보정
    reports = get_daily_reports()
    if not reports:
        hours_to_fetch = 72
    else:
        last_date_str = sorted(reports.keys())[-1]
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d').replace(tzinfo=kst)
        hours_diff = (now - last_date).total_seconds() / 3600.0
        # 최소 24시간, 최대 120시간(약 5일 휴무 대비) 보정
        hours_to_fetch = max(24, min(int(hours_diff), 120))
        
    print(f"[{today_str}] 스케줄러 수집 실행 (최근 {hours_to_fetch}시간 역추적)...")
    
    feeds = get_feeds()
    articles = []
    
    if feeds:
        articles += fetch_and_filter_articles(feeds, hours=hours_to_fetch)
        
    naver_queries = ["가전", "로봇청소기", "스마트홈", "AI가전"]
    articles += fetch_naver_news(naver_queries, hours=hours_to_fetch)
    
    youtube_channels = ["UChbDEJUckWuoEBSOFTwMtbQ", "UCHs0X-ZqA8k_T-tVq0zM6fA"]
    articles += fetch_youtube_videos(youtube_channels, hours=hours_to_fetch)
    
    if articles:
        report_md = generate_daily_briefing(articles)
        
        # 깃허브 저장소에 저장
        save_daily_report(today_str, report_md)
        print(f"리포트 생성 및 저장 완료: {today_str}")
        
        # 지정된 이메일로 전송
        send_email(today_str, report_md)
    else:
        print("수집된 기사가 없어 리포트를 생성하지 않습니다.")

if __name__ == "__main__":
    main()
