import json
import os
from typing import List, Dict

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Toggle this flag to ``False`` when running in production
TEST_MODE = True

# Load keys from environment or fallback for test mode
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY") or "9d217822f10348cda2442c455e120ef2"
GNEWS_KEY = os.getenv("GNEWS_KEY") or "0e5e3a8d6f331bfdc614553393804bae"
NEWSAPI_AI_KEY = os.getenv("NEWSAPI_AI_KEY") or "ef315c01-6412-4e85-b81e-8953cda71193"

NUM_ARTICLES = 3 if TEST_MODE else 10
NUM_AI_ARTICLES = 1 if TEST_MODE else 10

NEWSAPI_URL = (
    "https://newsapi.org/v2/everything?q=AI%20Fintech&language=en&"
    f"pageSize={NUM_ARTICLES}&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
)

GNEWS_URL = (
    "https://gnews.io/api/v4/search?q=AI%20Fintech&lang=en&country=us&"
    f"max={NUM_ARTICLES}&apikey={GNEWS_KEY}"
)

NEWSAPI_AI_URL = "https://eventregistry.org/api/v1/article/getArticles"

DATA_DIR = "data"


def fetch_newsapi_articles() -> List[Dict]:
    resp = requests.get(NEWSAPI_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for item in data.get("articles", []):
        articles.append(
            {
                "title": item.get("title"),
                "description": item.get("description"),
                "url": item.get("url"),
                "source": {"name": item.get("source", {}).get("name")},
                "publishedAt": item.get("publishedAt"),
            }
        )
    return articles


def fetch_gnews_articles() -> List[Dict]:
    resp = requests.get(GNEWS_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for item in data.get("articles", []):
        articles.append(
            {
                "title": item.get("title"),
                "description": item.get("description"),
                "url": item.get("url"),
                "source": {"name": item.get("source", {}).get("name")},
                "publishedAt": item.get("publishedAt"),
            }
        )
    return articles


def fetch_newsapi_ai_articles() -> List[Dict]:
    params = {
        "keyword": "AI Fintech",
        "articlesPage": 1,
        "articlesCount": NUM_AI_ARTICLES,
        "resultType": "articles",
        "lang": "eng",
        "apiKey": NEWSAPI_AI_KEY,
    }
    resp = requests.get(NEWSAPI_AI_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for item in data.get("articles", {}).get("results", []):
        articles.append(
            {
                "title": item.get("title"),
                "content": item.get("body"),
                "url": item.get("url"),
                "source": {"name": item.get("source", {}).get("title")},
                "publishedAt": item.get("date"),
            }
        )
    return articles


def save_json(data: List[Dict], filename: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    newsapi_articles = fetch_newsapi_articles()
    newsapi_filename = "newsapi_articles_test.json" if TEST_MODE else "newsapi_articles.json"
    save_json(newsapi_articles, newsapi_filename)

    gnews_articles = fetch_gnews_articles()
    gnews_filename = "gnews_articles_test.json" if TEST_MODE else "gnews_articles.json"
    save_json(gnews_articles, gnews_filename)

    ai_articles = fetch_newsapi_ai_articles()
    ai_filename = "newsapi_ai_articles_test.json" if TEST_MODE else "newsapi_ai_articles.json"
    save_json(ai_articles, ai_filename)

    
if __name__ == "__main__":
    main()

