import json
import sys
from datetime import datetime
from jinja2 import Template

# Base64-encoded background image. Embedding avoids using a binary file.
BACKGROUND_BASE64 = """
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
"""

TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
<title>Polaris Daily Digest — {{ date }}</title>
    <style>
    body {
        margin: 0;
        padding: 0;
        font-family: Arial, Helvetica, sans-serif;
        background: url("data:image/png;base64,{{ background }}") no-repeat center fixed;
        background-size: cover;
    }
    .page {
        padding: 20px;
    }
    h1 {
        font-family: Georgia, 'Times New Roman', serif;
        font-weight: 600;
        margin: 20px 0;
    }
    h1 .date {
        font-size: 0.6em;
        color: #666;
    }
    .card {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .title a {
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 16px;
        font-weight: bold;
        color: #1a0dab;
        text-decoration: none;
    }
    .title a:hover {
        text-decoration: underline;
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
<div class="page">
<h1>📬 Polaris Daily Digest <span class="date">– {{ date }}</span></h1>
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
    return template.render(date=date_str, grouped=grouped, emoji=EMOJIS,
                          background=BACKGROUND_BASE64)

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
