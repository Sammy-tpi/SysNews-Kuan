import json
import math
from datetime import datetime
from jinja2 import Template
from collections import defaultdict
import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

TEMPLATE_FILE = "templates/digest_single_column.html"
JSON_PATH = "data/news_data.json"
OUTPUT_FILE = "result/digest.html"
REGIONS = ["Taiwan", "Global"]

CATEGORY_DISPLAY_NAME = {
    "Research": "Research",
    "Startup": "Startup",
    "Infrastructure": "Infrastructure",
    "FinTech": "FinTech",
}
CATEGORIES = list(CATEGORY_DISPLAY_NAME.keys())

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
summary_model = genai.GenerativeModel("gemini-2.5-flash")

def load_articles(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {path}") from e


def normalize(cat: str) -> str:
    cat = cat or ""
    if "\u2013" in cat:
        cat = cat.split("\u2013", 1)[1].strip()
    if "-" in cat and cat.split("-", 1)[0].strip() in ["Global", "Taiwan"]:
        cat = cat.split("-", 1)[1].strip()
    return {
        "Research": "Research",
        "Startup": "Startup",
        "Infrastructure": "Infrastructure",
        "FinTech": "FinTech",
    }.get(cat, cat)


def prepare_articles(articles):
    for article in articles:
        src = article.get("source")
        if isinstance(src, dict):
            src = src.get("name")
        article["source"] = src or "Unknown Source"

        if not article.get("read_time"):
            content = article.get("content", "")
            word_count = len(content.split())
            article["read_time"] = f"{max(1, math.ceil(word_count / 200))} min read"

        article["published_at"] = article.get("published_at") or article["read_time"]
        article["url"] = article.get("url") or "#"
        article["tags"] = article.get("tags") or ["General"]

        cat_key = normalize(article.get("category", ""))
        article["category_key"] = cat_key
        article["category_display"] = CATEGORY_DISPLAY_NAME.get(cat_key, cat_key)


def group_articles_by_region(articles):
    grouped = {r: [] for r in REGIONS}
    for article in articles:
        region = article.get("region", "Global")
        if region not in grouped:
            region = "Global"
        grouped[region].append(article)
    return grouped


def group_articles_by_category(articles_list):
    grouped = defaultdict(list)
    for article in articles_list:
        grouped[article["category_key"]].append(article)
    for cat_key in CATEGORIES:
        if cat_key not in grouped or not grouped[cat_key]:
            grouped[cat_key].append({
                "title": "(No article selected)",
                "summary_zh": "今日沒有相關新聞。",
                "category_key": cat_key,
                "category_display": CATEGORY_DISPLAY_NAME.get(cat_key, cat_key),
                "source": "",
                "url": "#",
                "tags": [],
                "read_time": "",
                "published_at": "",
            })
    return grouped


def generate_html(articles):
    prepare_articles(articles)
    grouped = group_articles_by_region(articles)

    global_articles = grouped.get("Global", [])
    taiwan_articles = grouped.get("Taiwan", []) 

    filtered_global_articles = [a for a in global_articles if a.get("title") and a["title"] != "(No article selected)"]
    filtered_taiwan_articles = [a for a in taiwan_articles if a.get("title") and a["title"] != "(No article selected)"] 

    grouped_global = group_articles_by_category(filtered_global_articles)
    grouped_taiwan = group_articles_by_category(filtered_taiwan_articles) 

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = Template(f.read())

    date_str = datetime.now().strftime("%Y-%m-%d")
    return template.render(
        date=date_str,
        global_articles=grouped_global,
        taiwan_articles=grouped_taiwan,
    )


def main():
    articles = load_articles(JSON_PATH)
    html = generate_html(articles)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Generated {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
