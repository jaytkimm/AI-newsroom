import feedparser
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser

def fetch_youtube_videos(channel_ids, hours=72):
    """
    유튜브 채널 ID 기반으로 최신 영상 목록을 스크래핑(RSS) 합니다.
    """
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=hours)
    articles = []
    
    for channel_id in channel_ids:
        # 유튜브 채널 고유 RSS URL
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                try:
                    pub_time = date_parser.parse(entry.published)
                    if pub_time.tzinfo is None:
                        pub_time = pub_time.replace(tzinfo=timezone.utc)
                        
                    if pub_time >= cutoff_time:
                        articles.append({
                            'title': f"[유튜브 영상] {entry.get('title', 'No Title')}",
                            'link': entry.get('link', ''),
                            'summary': entry.get('summary', '')[:200] + '...',
                            'published': pub_time.isoformat(),
                            'feed_source': f"YouTube ({feed.feed.get('title', channel_id)})"
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Error fetching YouTube feed for {channel_id}: {e}")
            
    return articles
