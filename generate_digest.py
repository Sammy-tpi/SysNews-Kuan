import json
from datetime import datetime
from jinja2 import Template

TEMPLATE_FILE = "templates/digest_single_column.html"
JSON_PATH = "data/news_data.json"
OUTPUT_FILE = "digest.html"
REGIONS = ["East Asia", "Global"]


def load_articles(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


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
        "finance_ai": "Applied AI & Fintech",
        "startup_ai": "General Tech & Startups",
        "blockchain_ai": "Blockchain & Crypto",
    }
    CATEGORIES = ["finance_ai", "startup_ai", "blockchain_ai"]

    def normalize(cat: str) -> str:
        cat = cat or ""
        if "\u2013" in cat:
            cat = cat.split("\u2013", 1)[1].strip()
        if "-" in cat and cat.split("-", 1)[0].strip() in ["Global", "East Asia"]:
            cat = cat.split("-", 1)[1].strip()
        return {
            "Applied AI & FinTech": "finance_ai",
            "Applied AI & Fintech": "finance_ai",
            "General Tech & Startups": "startup_ai",
            "Blockchain & Crypto": "blockchain_ai",
        }.get(cat, cat)

    for article in global_articles + east_asian_articles:
        # Log the raw category for debugging
        print("Category:", article.get("category"))

        article["published_at"] = article.get(
            "published_at") or article.get("read_time", "1 min read")
        article["url"] = article.get("url") or "#"
        article["source"] = article.get("source") or "Unknown"
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
