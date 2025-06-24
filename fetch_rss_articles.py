import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

import asyncio
import aiohttp

import feedparser
from bs4 import BeautifulSoup
from utils import load_keywords, keyword_score

ALLOWED_CATEGORIES = {
    "tech",
    "technology",
    "ai",
    "artificial intelligence",
    "fintech",
    "finance",
    "startup",
    "crypto",
    "blockchain",
    "business",
}


def has_allowed_category(entry) -> bool:
    tags = entry.get("tags", [])
    return any(
        any(allowed in tag.get("term", "").lower() for allowed in ALLOWED_CATEGORIES)
        for tag in tags
    )


def should_keep_entry(entry, keywords) -> bool:
    # 🚧 [Polaris Dev] Disabled keyword/category filtering for GPT/ML classification
    return True


CONFIG_FILE = "config/sources.json"
OUTPUT_FILE = "data/rss_articles.json"
FETCH_COUNTS_FILE = "logs/fetch_counts.json"

# Limit how many articles to fetch from each RSS feed to avoid long runtimes
MAX_ARTICLES_PER_SOURCE = 250


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

    rss_sources = [s for s in data.get("rss_sources", []) if s.get("source_type") == "rss"]
    return rss_sources


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


async def process_feed_async(
    src: Dict,
    session: aiohttp.ClientSession,
    keywords: List[str],
) -> List[Dict]:
    """Fetch a single RSS feed and return processed articles."""
    name = src.get("name", "")
    url = src.get("rss_url")
    if not url:
        print(f"\u26a0\ufe0f {name} is missing rss_url")
        return []
    try:
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            feed_data = await resp.text()
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        print(f"\u26a0\ufe0f Failed to fetch feed for {name}: {exc}")
        return []
    feed = feedparser.parse(feed_data)
    # 🚧 [Polaris Dev] Disabled keyword/category filtering for GPT/ML classification
    filtered_entries: List[dict] = feed.entries[:MAX_ARTICLES_PER_SOURCE]

    tasks = [fetch_full_text_async(e.get("link"), session) for e in filtered_entries]
    if not tasks:
        return []
    contents = await asyncio.gather(*tasks)
    articles: List[Dict] = []
    for entry, content in zip(filtered_entries, contents):
        if not content:
            continue
        article = {
            "title": entry.get("title"),
            "content": content,
            "url": entry.get("link"),
            "source": {"name": name},
            "publishedAt": parse_timestamp(entry),
        }
        # 🚧 [Polaris Dev] Skip keyword_score filtering
        articles.append(article)
    return articles


async def fetch_rss_articles_async() -> List[Dict]:
    sources = load_sources()
    keywords = load_keywords()
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *(process_feed_async(src, session, keywords) for src in sources)
        )
    articles: List[Dict] = []
    fetch_counts: Dict[str, int] = {}
    for src, batch in zip(sources, results):
        name = src.get("name", "")
        count = len(batch)
        fetch_counts[name] = count
        print(f"\u2705 Fetched {count} articles from {name}")
        for art in batch:
            # 🚧 [Polaris Dev] Skip keyword_score filtering
            articles.append(art)
    os.makedirs("logs", exist_ok=True)
    with open(FETCH_COUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(fetch_counts, f, ensure_ascii=False, indent=2)
    return articles


async def main_async() -> None:
    os.makedirs("data", exist_ok=True)
    articles = await fetch_rss_articles_async()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(articles)} articles to {OUTPUT_FILE}")
    print(f"\U0001F4E5 RSS \u6587\u7AE0\u6578\u91CF: {len(articles)}")


if __name__ == "__main__":
    asyncio.run(main_async())
