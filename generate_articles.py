import json
import os
from typing import List, Dict

from dotenv import load_dotenv
import requests

load_dotenv()

NEWSAPI_AI_KEY = os.getenv("NEWSAPI_AI_KEY")
if not NEWSAPI_AI_KEY:
    raise RuntimeError(
        "NEWSAPI_AI_KEY environment variable is required to fetch articles"
    )
NEWSAPI_AI_URL = "https://eventregistry.org/api/v1/article/getArticles"

NUM_ARTICLES = 10
OUTPUT_FILE = "news_data.json"


def fetch_newsapi_ai_articles() -> List[Dict]:
    params = {
        "keyword": "AI Fintech",
        "articlesPage": 1,
        "articlesCount": NUM_ARTICLES,
        "resultType": "articles",
        "lang": "eng",
        "apiKey": NEWSAPI_AI_KEY,
    }
    try:
        resp = requests.get(NEWSAPI_AI_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch articles: {exc}") from exc
    data = resp.json()
    articles = []
    for item in data.get("articles", {}).get("results", []):
        articles.append({
            "title": item.get("title"),
            "content": item.get("body"),
            "url": item.get("url"),
            "source": {"name": item.get("source", {}).get("title")},
            "publishedAt": item.get("date"),
        })
    return articles


def simple_summary(text: str, limit: int = 2) -> str:
    if not text:
        return ""
    sentences = text.split(". ")
    return ". ".join(sentences[:limit]).strip()


def generate_dataset() -> List[Dict]:
    raw_articles = fetch_newsapi_ai_articles()
    summarized = []
    for art in raw_articles:
        summary = simple_summary(art.get("content", ""))
        summarized.append({
            "region": "Global",
            "category": "General Tech & Startups",
            "title": art.get("title"),
            "summary": summary,
            "source": art.get("source", {}).get("name"),
            "read_time": "1 min read",
            "url": art.get("url"),
            "tags": [],
        })
    return summarized


def main() -> None:
    articles = generate_dataset()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
