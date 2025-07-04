import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict

RSS_FILE = "data/rss_articles.json"
NEWSAPI_FILE = "data/newsapi_ai_articles.json"
OUTPUT_FILE = "data/recent_articles.json"


def load_json(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {path}")


def parse_date(ts: str):
    if not ts:
        return None
    ts = ts.strip()
    try:
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
        return datetime.fromisoformat(ts).date()
    except ValueError:
        try:
            return datetime.strptime(ts, "%Y-%m-%d").date()
        except ValueError:
            return None


def filter_recent(articles: List[Dict]) -> List[Dict]:
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    recent_dates = {today, yesterday}

    filtered: List[Dict] = []
    for art in articles:
        date_str = art.get("publishedAt")
        date = parse_date(date_str) if date_str else None
        if date and date in recent_dates:
            filtered.append(art)
    return filtered


def main() -> None:
    rss_articles = load_json(RSS_FILE)
    newsapi_articles = load_json(NEWSAPI_FILE)
    combined = rss_articles + newsapi_articles
    recent = filter_recent(combined)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(recent, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(recent)} articles to {OUTPUT_FILE}")
    filtered = recent
    print(f"\U0001F4C5 \u4FDD\u7559\u7684\u6700\u65B0\u6587\u7AE0\u6578\u91CF: {len(filtered)}")


if __name__ == "__main__":
    main()
