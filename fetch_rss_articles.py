import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

import feedparser
import requests
from bs4 import BeautifulSoup

CONFIG_FILE = "config/sources.json"
OUTPUT_FILE = "data/rss_articles.json"


def load_sources() -> List[Dict]:
    """Return list of RSS sources from configuration."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"\u274c Missing {CONFIG_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"\u274c Invalid JSON in {CONFIG_FILE}")
        return []
    return [s for s in data.get("sources", []) if s.get("type") == "rss"]


def parse_timestamp(entry: dict) -> str:
    """Convert feedparser timestamp to ISO 8601."""
    ts = entry.get("published_parsed") or entry.get("updated_parsed")
    if not ts:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    dt = datetime.fromtimestamp(
        getattr(__import__("calendar"), "timegm")(ts), tz=timezone.utc
    )
    return dt.isoformat().replace("+00:00", "Z")


def fetch_full_text(url: str) -> Optional[str]:
    """Fetch full text using Jina AI reader or fallback to raw HTML."""
    candidates = [f"https://r.jina.ai/{url}", url]
    for link in candidates:
        try:
            resp = requests.get(link, timeout=10)
            resp.raise_for_status()
        except requests.RequestException:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        article = soup.find("article")
        if article:
            text = "\n".join(p.get_text(strip=True) for p in article.find_all("p"))
        else:
            text = "\n".join(p.get_text(strip=True) for p in soup.find_all("p"))
        if text:
            return text
    return None


def fetch_rss_articles() -> List[Dict]:
    sources = load_sources()
    articles: List[Dict] = []
    for src in sources:
        name = src.get("name", "")
        url = src.get("rss_url")
        if not url:
            continue
        try:
            feed = feedparser.parse(url)
        except Exception:
            print(f"\u26a0\ufe0f Failed to parse feed {url}")
            continue
        for entry in feed.entries:
            title = entry.get("title")
            link = entry.get("link")
            if not title or not link:
                continue
            content = fetch_full_text(link)
            if not content:
                continue
            articles.append(
                {
                    "title": title,
                    "content": content,
                    "url": link,
                    "source": {"name": name},
                    "publishedAt": parse_timestamp(entry),
                }
            )
    return articles


def main() -> None:
    os.makedirs("data", exist_ok=True)
    articles = fetch_rss_articles()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(articles)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
