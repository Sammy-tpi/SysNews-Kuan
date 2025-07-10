import json
import math
from datetime import datetime
from jinja2 import Template

TEMPLATE_FILE = "templates/digest_single_column.html"
JSON_PATH = "data/news_data.json"
OUTPUT_FILE = "digest.html"
REGIONS = ["East Asia", "Global"]


def load_articles(path: str):
    """Load the news articles from ``path``.

    Returns an empty list if the file does not exist. Raises ``RuntimeError`` if
    the JSON is malformed.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {path}") from e


def group_articles_by_region(articles):
    grouped = {r: [] for r in REGIONS}
    for article in articles:
        region = article.get("region", "Global")
        if region not in grouped:
            region = "Global"
        grouped[region].append(article)
    return grouped


def generate_html(articles):
    grouped = group_articles_by_region(articles)
    global_articles = grouped.get("Global", [])
    east_asian_articles = grouped.get("East Asia", [])

    print("Global categories:", [a.get("category") for a in global_articles])
    print("East Asia categories:", [a.get("category")
          for a in east_asian_articles])

    CATEGORY_DISPLAY_NAME = {
        "Research_ai": "Research",
        "Startup_ai": "Startup",
        "Infrastructure_ai": "Infrastructure",
        "FinTech_ai": "FinTech",
    }
    CATEGORIES = ["Research_ai", "Startup_ai", "Infrastructure_ai", "FinTech_ai"]

    def normalize(cat: str) -> str:
        cat = cat or ""
        if "\u2013" in cat:
            cat = cat.split("\u2013", 1)[1].strip()
        if "-" in cat and cat.split("-", 1)[0].strip() in ["Global", "East Asia"]:
            cat = cat.split("-", 1)[1].strip()
        return {
            "Research": "Research_ai",
            "Startup": "Startup_ai",
            "Infrastructure": "Infrastructure_ai",
            "FinTech": "FinTech_ai",
        }.get(cat, cat)

    for article in global_articles + east_asian_articles:
        # Log the raw category for debugging
        print("Category:", article.get("category"))

        src = article.get("source")
        if isinstance(src, dict):
            src = src.get("name")
        article["source"] = src or "Unknown Source"

        if not article.get("read_time"):
            content = article.get("content", "")
            word_count = len(content.split())
            article["read_time"] = f"{max(1, math.ceil(word_count / 200))} min read"

        article["published_at"] = article.get(
            "published_at") or article.get("read_time", "1 min read")
        article["url"] = article.get("url") or "#"
        article["tags"] = article.get("tags") or ["General"]

        cat_key = normalize(article.get("category", ""))
        article["category_key"] = cat_key
        article["category_display"] = CATEGORY_DISPLAY_NAME.get(
            cat_key, cat_key)

    def ensure_categories(articles_list):
        existing = {a.get("category_key") for a in articles_list}
        for cat_key in CATEGORIES:
            if cat_key not in existing:
                articles_list.append({
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

    ensure_categories(global_articles)
    ensure_categories(east_asian_articles)

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = Template(f.read())

    date_str = datetime.now().strftime("%Y-%m-%d")
    return template.render(
        date=date_str,
        global_articles=global_articles,
        east_asian_articles=east_asian_articles,
    )


def main():
    articles = load_articles(JSON_PATH)
    html = generate_html(articles)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Generated {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
