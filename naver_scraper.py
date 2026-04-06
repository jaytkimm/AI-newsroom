import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

def fetch_naver_news(queries, hours=72):
    """
    네이버 뉴스 검색을 스크래핑합니다. (최신순 필터링은 하지 않고 검색결과 1페이지 위주 수집)
    """
    import urllib.parse
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    articles = []
    
    for query in queries:
        try:
            url = f"https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(query)}"
            req = requests.get(url, headers=headers)
            soup = BeautifulSoup(req.text, 'html.parser')
            
            news_items = soup.select('.news_area')
            for item in news_items:
                tit_tag = item.select_one('.news_tit')
                dsc_tag = item.select_one('.dsc_wrap')
                
                if tit_tag:
                    title = tit_tag.get('title') or tit_tag.text
                    link = tit_tag.get('href')
                    summary = dsc_tag.text if dsc_tag else "내용 없음"
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'summary': summary.strip(),
                        'published': datetime.now(timezone.utc).isoformat(),
                        'feed_source': f"네이버 뉴스 ({query})"
                    })
        except Exception as e:
            print(f"Error fetching Naver news for {query}: {e}")
            
    return articles
