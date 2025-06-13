import json
import sys
from datetime import datetime
from jinja2 import Template

TEMPLATE = """
<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
    <meta charset=\"UTF-8\">
    <title>📬 Polaris Daily Digest – {{ date }}</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap\" rel=\"stylesheet\">
    <style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f2f1ee;
        color: #2b211d;
        margin: 20px;
    }
    .container {
        width: 90%;
        max-width: 1024px;
        margin: 0 auto;
        padding: 24px;
    }
    h1 {
        font-family: 'Playfair Display', serif;
        font-size: 28px;
        font-weight: 700;
        color: #2b211d;
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
        color: #5c2c35;
        text-decoration: none;
    }
    .title a:hover {
        text-decoration: underline;
        color: #2b211d;
    }
    .summary {
        font-size: 16px;
        color: #2b211d;
        margin: 10px 0;
        line-height: 1.6;
    }
    .source {
        font-size: 12px;
        color: #5c2c35;
    }
    .category-title {
        font-size: 18px;
        font-weight: bold;
        margin: 30px 0 10px;
        color: #2b211d;
    }
    .region-toggle button {
        font-size: 1.1rem;
        font-weight: bold;
        padding: 8px 16px;
        margin: 4px;
        border: none;
        border-radius: 6px;
        background-color: #f2f2f2;
        cursor: pointer;
    }
    .region-toggle button.active {
        background-color: #1c1c1c;
        color: white;
    }
    </style>
    <script>
    function showRegion(id, btn) {
        document.querySelectorAll('.region').forEach(function(el) {
            el.style.display = 'none';
        });
        document.getElementById(id).style.display = 'block';
        document.querySelectorAll('.region-toggle button').forEach(function(b){
            b.classList.remove('active');
        });
        if (btn) {
            btn.classList.add('active');
        }
    }
    </script>
</head>
<body>
<div class=\"container\">
<h1>📬 Polaris Daily Digest – {{ date }}</h1>
<div class=\"region-toggle\">
  <button onclick=\"showRegion('east-asia', this)\" class=\"active\">🌏 East Asia</button>
  <button onclick=\"showRegion('global', this)\">🌍 Global</button>
</div>
{% for region, categories in grouped.items() %}
<div class=\"region\" id=\"{{ region_ids[region] }}\" {% if not loop.first %}style=\"display:none;\"{% endif %}>
{% for category, articles in categories.items() %}
<div class=\"category-title\">{{ emoji[category] }} {{ category }}</div>
{% for article in articles %}
<div class=\"card\">
    <div class=\"title\">
        <a href=\"{{ article.url }}\">{{ article.title }}</a>
    </div>
    <div class=\"summary\">
        {{ article.summary }}
    </div>
    <div class=\"source\">
        {{ article.source }} ┃ {{ article.read_time }}
    </div>
</div>
{% endfor %}
{% endfor %}
</div>
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
REGIONS = ["East Asia", "Global"]
REGION_IDS = {"East Asia": "east-asia", "Global": "global"}

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
    template = Template(TEMPLATE)
    date_str = datetime.now().strftime('%Y-%m-%d')
    return template.render(date=date_str, grouped=grouped, emoji=EMOJIS, region_ids=REGION_IDS)

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
