import json
import sys
from datetime import datetime
from jinja2 import Template

TEMPLATE_FILE = "digest_two_column.html"

CATEGORIES = [
    "General Tech & Startups",
    "Applied AI & Fintech",
    "Blockchain & Crypto",
]
EMOJIS = {
    "General Tech & Startups": "📱",
    "Applied AI & Fintech": "💳",
    "Blockchain & Crypto": "🪙",
}
REGIONS = ["East Asia", "Global"]

def load_articles(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def group_articles_by_region(articles):
    grouped = {r: {c: [] for c in CATEGORIES} for r in REGIONS}
    for article in articles:
        region = article.get('region', 'Global')
        category = article.get('category')
        if region in grouped and category in grouped[region]:
            grouped[region][category].append(article)
    return grouped

def generate_html(articles):
    grouped = group_articles_by_region(articles)
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = Template(f.read())
    date_str = datetime.now().strftime('%Y-%m-%d')
    return template.render(date=date_str, grouped=grouped, emoji=EMOJIS)

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
