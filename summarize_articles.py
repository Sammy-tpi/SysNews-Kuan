import json
import os
from typing import Dict, List, Tuple

import openai
from dotenv import load_dotenv

INPUT_FILE = "data/newsapi_ai_articles.json"
OUTPUT_FILE = "data/news_data.json"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")


def load_articles() -> List[Dict]:
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def gpt_summarize(title: str, body: str) -> Tuple[str, str]:
    """Return English and Traditional Chinese summaries using GPT-4o."""
    prompt = (
        "Summarize the following news article in 2-3 sentences in English, "
        "then in 2-3 sentences in Traditional Chinese."
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Title: {title}\n\n{body}"},
    ]
    response = openai.chat.completions.create(model="gpt-4o", messages=messages)
    content = response.choices[0].message.content.split("\n")
    # Assume first block is English, second is Chinese
    summary_en = content[0].strip()
    summary_zh = content[-1].strip()
    return summary_en, summary_zh


def main() -> None:
    articles = load_articles()
    summarized = []
    for art in articles:
        title = art.get('title', '')
        body = art.get('content', '')
        summary_en, summary_zh = gpt_summarize(title, body)
        print('EN:', summary_en)
        print('ZH:', summary_zh)
        summarized.append({
            'region': 'Global',
            'category': 'General Tech & Startups',
            'title': title,
            'summary_en': summary_en,
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
