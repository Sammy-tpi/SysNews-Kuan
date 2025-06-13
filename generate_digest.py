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

    for article in global_articles + east_asian_articles:
        if "published_at" not in article:
            article["published_at"] = article.get("read_time", "")

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
