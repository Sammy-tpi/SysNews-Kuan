import json
import os
from typing import List, Dict

import requests
from dotenv import load_dotenv
from utils import load_keywords, keyword_score, source_weight

load_dotenv()
NEWSAPI_AI_KEY = os.getenv("NEWSAPI_AI_KEY")
if not NEWSAPI_AI_KEY:
    raise RuntimeError("Missing NEWSAPI_AI_KEY in environment")
NEWSAPI_AI_URL = "https://eventregistry.org/api/v1/article/getArticles"

# Fetch only one article per run to keep testing inexpensive
NUM_AI_ARTICLES = 1

# Persist the results inside the ``data`` directory
OUTPUT_FILE = "data/newsapi_ai_articles.json"


def fetch_newsapi_ai_articles() -> List[Dict]:
    params = {
        "keyword": "AI Fintech",
        "articlesPage": 1,
        "articlesCount": NUM_AI_ARTICLES,
        "resultType": "articles",
        "lang": "eng",
        "apiKey": NEWSAPI_AI_KEY,
    }
    try:
        resp = requests.get(NEWSAPI_AI_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(
            "\u274c Failed to fetch articles from EventRegistry. Please check if your API key is valid or if the network is blocking access."
        )
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


def fetch_and_store() -> List[Dict]:
    """Fetch raw articles, score them and return the top results."""
    articles = fetch_newsapi_ai_articles()
    keywords_cfg = load_keywords()
    all_keywords = [kw for group in keywords_cfg.values() for kw in group]
    for art in articles:
        text = f"{art.get('title', '')} {art.get('content', '')}"
        art["score"] = (
            0.5 * len(art.get("content", ""))
            + 5 * keyword_score(text, all_keywords)
            + source_weight(art.get("source", {}).get("name", ""))
        )
    articles = sorted(articles, key=lambda x: x["score"], reverse=True)[:20]
    return articles


def main() -> None:
    # Ensure the output directory exists so tests can run without extra setup
    os.makedirs("data", exist_ok=True)

    articles = fetch_and_store()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
