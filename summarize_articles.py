import json
import os
from typing import Dict, List

import openai
from dotenv import load_dotenv

NEWSAPI_INPUT_FILE = "data/newsapi_ai_articles.json"
RSS_INPUT_FILE = "data/rss_articles.json"
OUTPUT_FILE = "data/news_data.json"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")


def load_articles() -> List[Dict]:
    """Load raw articles from NewsAPI.ai and RSS sources."""
    articles: List[Dict] = []
    for path in (NEWSAPI_INPUT_FILE, RSS_INPUT_FILE):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            try:
                articles.extend(json.load(f))
            except json.JSONDecodeError:
                raise RuntimeError(f"Invalid JSON in {path}")
    return articles


def gpt_summarize(title: str, body: str) -> str:
    """Return a Traditional Chinese summary highlighting tech terms."""
    prompt = f'''
You are a bilingual AI assistant summarizing news articles about AI and FinTech.

Task:
- Summarize the following article in **Traditional Chinese** (繁體中文).
- Keep the summary concise (3–5 sentences).
- Identify key technical terms related to AI, FinTech, Blockchain, Machine Learning, NLP, etc.
- For each term, include its **original English** in parentheses after the **Chinese term**.

Example output format:
該公司正在開發生成式人工智慧（Generative AI）平台，並使用大型語言模型（LLM）提升金融數據處理效率。

Article:
"""{body}"""
'''
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Title: {title}"},
    ]
    response = openai.chat.completions.create(model="gpt-4o", messages=messages)
    return response.choices[0].message.content.strip()


def main() -> None:
    articles = load_articles()
    summarized = []
    for art in articles:
        title = art.get('title', '')
        body = art.get('content', '')
        summary_zh = gpt_summarize(title, body)
        print('ZH:', summary_zh)
        summarized.append({
            'region': 'Global',
            'category': 'General Tech & Startups',
            'title': title,
            'summary_zh': summary_zh,
            'source': art.get('source', {}).get('name'),
            'read_time': '1 min read',
            'url': art.get('url'),
            'tags': []
        })
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(summarized, f, ensure_ascii=False, indent=2)
    print(f"Wrote summaries to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
