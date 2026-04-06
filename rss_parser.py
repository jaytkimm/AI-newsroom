import feedparser
from dateutil import parser as date_parser
from datetime import datetime, timedelta, timezone

def fetch_and_filter_articles(feeds_list, hours=72):
    """
    Fetch articles from RSS feeds and format them.
    Filters articles newer than `hours`.
    """
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=hours)
    
    articles = []
    
    for feed_url in feeds_list:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                try:
                    # try parsing published date
                    published_str = entry.get('published', entry.get('updated', ''))
                    if published_str:
                        pub_time = date_parser.parse(published_str)
                        if pub_time.tzinfo is None:
                            pub_time = pub_time.replace(tzinfo=timezone.utc)
                        
                        if pub_time >= cutoff_time:
                            articles.append({
                                'title': entry.get('title', 'No Title'),
                                'link': entry.get('link', ''),
                                'summary': entry.get('summary', 'No Summary'),
                                'published': pub_time.isoformat(),
                                'feed_source': feed.feed.get('title', feed_url)
                            })
                except Exception as e:
                    # skip entry if date parsing fails
                    continue
        except Exception as e:
            # log or skip
            continue
            
    return articles
