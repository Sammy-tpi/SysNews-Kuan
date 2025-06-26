import json
import feedparser

CONFIG_FILE = "config/sources.json"

def is_valid_rss(url):
    """Returns True if url returns at least one feed entry, otherwise False."""
    try:
        feed = feedparser.parse(url)
        return bool(feed.entries)
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return False

def check_feeds(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_sources = []
    # 合併 rss_sources 和 rsshub_sources
    for key in ("rss_sources", "rsshub_sources"):
        all_sources += data.get(key, [])

    for src in all_sources:
        name = src.get("name", "No Name")
        url = src.get("rss_url", "")
        if not url:
            print(f"❌ {name} : No url")
            continue
        valid = is_valid_rss(url.strip())
        if valid:
            print(f"✅ {name} : {url}")
        else:
            print(f"❌ {name} : {url}")

if __name__ == "__main__":
    check_feeds(CONFIG_FILE)
