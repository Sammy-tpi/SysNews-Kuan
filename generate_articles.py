import json
import os
from typing import List, Dict

import requests

NEWSAPI_KEY = "9d217822f10348cda2442c455e120ef2"
GNEWS_KEY = "0e5e3a8d6f331bfdc614553393804bae"

NEWSAPI_URL = (
    "https://newsapi.org/v2/everything?q=AI%20Fintech&language=en&"
    "pageSize=10&sortBy=publishedAt&apiKey=" + NEWSAPI_KEY
)

GNEWS_URL = (
    "https://gnews.io/api/v4/search?q=AI%20Fintech&lang=en&country=us&max=10&apikey="
    + GNEWS_KEY
)

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


def save_json(data: List[Dict], filename: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    newsapi_articles = fetch_newsapi_articles()
    save_json(newsapi_articles, "newsapi_articles.json")

    gnews_articles = fetch_gnews_articles()
    save_json(gnews_articles, "gnews_articles.json")


if __name__ == "__main__":
    main()
