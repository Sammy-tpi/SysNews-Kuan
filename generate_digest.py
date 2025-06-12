import json
import sys
from datetime import datetime
from jinja2 import Template

TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>📬 Polaris Daily Digest – {{ date }}</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap');
    body {
        font-family: Arial, sans-serif;
        background-color: #fdf6e3;
        color: #3b2f2f;
        margin: 20px;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    h1 {
        font-family: 'Playfair Display', serif;
        font-size: 28px;
        font-weight: 700;
        color: #3b2f2f;
        margin-bottom: 10px;
    }
    .card {
        background-color: #f9f9f9;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .title a {
        font-size: 16px;
        font-weight: bold;
        color: #6e2f3c;
        text-decoration: none;
    }

    .title a:hover {
        text-decoration: underline;
        color: #3b2f2f;
    }
    .summary {
        font-size: 16px;
        color: #3b2f2f;
        margin: 10px 0;
        line-height: 1.6;
    }
    .source {
        font-size: 12px;
        color: #3b2f2f;
    }
    .category-title {
        font-size: 18px;
        font-weight: bold;
        margin: 30px 0 10px;
        color: #3b2f2f;
    }
    </style>
</head>
<body>
<div class="container">
<h1>📬 Polaris Daily Digest – {{ date }}</h1>
{% for category, articles in grouped.items() %}
<div class="category-title">{{ emoji[category] }} {{ category }}</div>
{% for article in articles %}
<div class="card">
    <div class="title">
        <a href="{{ article.url }}">{{ article.title }}</a>
    </div>
    <div class="summary">
        {{ article.summary }}
    </div>
    <div class="source">
        {{ article.source }} ┃ {{ article.read_time }}
    </div>
</div>
{% endfor %}
{% endfor %}
</div>
</body>
</html>
"""

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

def load_articles(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def group_articles(articles):
    grouped = {c: [] for c in CATEGORIES}
    for article in articles:
        cat = article.get('category')
        if cat in grouped:
            grouped[cat].append(article)
    return grouped

def generate_html(articles):
    grouped = group_articles(articles)
    template = Template(TEMPLATE)
    date_str = datetime.now().strftime('%Y-%m-%d')
    return template.render(date=date_str, grouped=grouped, emoji=EMOJIS)

def main():
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = 'sample_articles.json'
    articles = load_articles(json_path)
    html = generate_html(articles)
    output_file = 'digest.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated {output_file}")

if __name__ == '__main__':
    main()
