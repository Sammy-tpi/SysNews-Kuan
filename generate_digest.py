import json
import sys
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))

REGIONS = ["East Asia", "Global"]

def load_articles(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def group_articles_by_region(articles):
    """Return lists of articles for each region."""
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
    template = env.get_template("digest_single_column.html")
    date_str = datetime.now().strftime("%Y-%m-%d")
    return template.render(
        date=date_str,
        global_articles=global_articles,
        east_asian_articles=east_asian_articles,
    )

def main():
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = 'news_data.json'
    articles = load_articles(json_path)
    html = generate_html(articles)
    output_file = 'digest.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated {output_file}")

if __name__ == '__main__':
    main()
