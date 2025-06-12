import json
import sys
from datetime import datetime
from jinja2 import Template

TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>Polaris 每日 AI 與 Fintech 新聞摘要 — {{ date }}</title>
    <style>
    body {
        font-family: Arial, sans-serif;
        background-color: #fff;
        margin: 20px;
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
        color: #1a0dab;
        text-decoration: none;
    }
    .summary {
        font-size: 14px;
        color: #333;
        margin: 10px 0;
        line-height: 1.6;
    }
    .source {
        font-size: 12px;
        color: #666;
    }
    .category-title {
        font-size: 18px;
        font-weight: bold;
        margin: 30px 0 10px;
    }
    </style>
</head>
<body>
<h1>Polaris 每日 AI 與 Fintech 新聞摘要 — {{ date }}</h1>
<p>由 Polaris 系統生成 ┃ 揭露最新的 AI 與 Fintech 動向</p>
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
