import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

import asyncio
import aiohttp

import feedparser
from bs4 import BeautifulSoup
from utils import load_keywords, keyword_score

CONFIG_FILE = "config/sources.json"
OUTPUT_FILE = "data/rss_articles.json"

# Limit how many articles to fetch from each RSS feed to avoid long runtimes
MAX_ARTICLES_PER_SOURCE = 3


def load_sources() -> List[Dict]:
    """Return list of all RSS sources from configuration."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Missing {CONFIG_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {CONFIG_FILE}")
        return []
    
    # ✅ 改成讀 "rss_sources"
    rss_sources = [s for s in data.get("rss_sources", []) if s.get("source_type") == "rss"]
    rsshub_sources = [s for s in data.get("rsshub_sources", []) if s.get("source_type") == "rsshub"]
    return rss_sources + rsshub_sources



def parse_timestamp(entry: dict) -> str:
    """Convert feedparser timestamp to ISO 8601."""
    ts = entry.get("published_parsed") or entry.get("updated_parsed")
    if not ts:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    dt = datetime.fromtimestamp(
        getattr(__import__("calendar"), "timegm")(ts), tz=timezone.utc
    )
    return dt.isoformat().replace("+00:00", "Z")


async def fetch_full_text_async(
    url: str, session: aiohttp.ClientSession
) -> Optional[str]:
    """Fetch full text using Jina AI reader or fallback to raw HTML."""
    candidates = [f"https://r.jina.ai/{url}", url]
    for link in candidates:
        try:
            async with session.get(link, timeout=10) as resp:
                resp.raise_for_status()
                html = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            continue
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article")
        if article:
            text = "\n".join(p.get_text(strip=True) for p in article.find_all("p"))
        else:
            text = "\n".join(p.get_text(strip=True) for p in soup.find_all("p"))
        if text:
            return text
    return None


async def process_feed_async(src: Dict, session: aiohttp.ClientSession) -> List[Dict]:
    """Fetch a single RSS feed and return processed articles."""
    name = src.get("name", "")
    url = src.get("rss_url")
    if not url:
        return []
    try:
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            feed_data = await resp.text()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        print(f"\u26a0\ufe0f Failed to fetch feed {url}")
        return []
    feed = feedparser.parse(feed_data)
    tasks = []
    entries: List[dict] = []
    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        title = entry.get("title")
        link = entry.get("link")
        if not title or not link:
            continue
        entries.append(entry)
        tasks.append(fetch_full_text_async(link, session))
    if not tasks:
        return []
    contents = await asyncio.gather(*tasks)
    articles: List[Dict] = []
    for entry, content in zip(entries, contents):
        if not content:
            continue
        articles.append(
            {
                "title": entry.get("title"),
                "content": content,
                "url": entry.get("link"),
                "source": {"name": name},
                "publishedAt": parse_timestamp(entry),
            }
        )
    return articles


async def fetch_rss_articles_async() -> List[Dict]:
    sources = load_sources()
    keywords_cfg = load_keywords()
    all_keywords = [kw for group in keywords_cfg.values() for kw in group]
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *(process_feed_async(src, session) for src in sources)
        )
    articles: List[Dict] = []
    for batch in results:
        for art in batch:
            text = f"{art.get('title', '')} {art.get('content', '')}"
            if keyword_score(text, all_keywords) > 0:
                articles.append(art)
    return articles


async def main_async() -> None:
    os.makedirs("data", exist_ok=True)
    articles = await fetch_rss_articles_async()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(articles)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main_async())
