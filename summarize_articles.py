import json
import os
import math
from typing import Dict, List, Tuple
import logging

import openai
from dotenv import load_dotenv

logging.basicConfig(level=logging.ERROR)

# Read the top-scoring articles selected for summarization
INPUT_FILE = "data/selected_articles.json"
OUTPUT_FILE = "data/news_data.json"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")


def load_articles() -> List[Dict]:
    """Load the pre-selected top articles."""
    if not os.path.exists(INPUT_FILE):
        return []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {INPUT_FILE}")


def gpt_summarize(title: str, body: str) -> Tuple[str, str]:
    """Return a Traditional Chinese summary and its classified category."""
    
    prompt = f'''
You are a bilingual AI assistant working for TPIsoftware, a Taiwan-based company specializing in enterprise platforms, AI development, and financial technologies.

Your task is to help internal teams — including product managers, developers, and data scientists — quickly understand news articles related to AI, FinTech, and emerging technology. Your summaries will appear in our internal daily news digest.

You will be given full-text news articles in either English or Chinese.

## Your Goals:
1. Summarize the article in **Traditional Chinese**, using up to **4 concise sentences**.
2. Be accurate — do **not invent** or infer information not in the original article.
3. Keep important **technical terms**, and include the **English term in parentheses** if needed.
4. Avoid generic phrases like "the company" or "the startup" — use specific names and dates when available.
5. Classify the article into the most appropriate category listed below.

## Categories:
1. Global – General Tech & Startups  
2. Global – Applied AI & FinTech  
3. Global – Blockchain & Crypto  
4. East Asia – General Tech & Startups  
5. East Asia – Applied AI & FinTech  
6. East Asia – Blockchain & Crypto

## Classification Rules:
- If the article discusses **startup activities**, new tech products, or funding rounds, use "General Tech & Startups".
- If the article focuses on AI in **finance, banking, insurance, or enterprise automation**, use "Applied AI & FinTech".
- If it focuses on **crypto, DeFi, NFTs, or blockchain technology**, use "Blockchain & Crypto".
- Use "East Asia" if the article is about Taiwan, China, Japan, Korea, or Hong Kong; otherwise, use "Global".

## Input
**Title**:  
{title}

**Article Content**:  
{body}

## Output (in the following format):
---
Summary: [Your Traditional Chinese summary here]  
Category: [Best-fit category from the list above]
'''
    return prompt


    messages = [
        {"role": "system", "content": prompt}
    ]
    try:
        response = openai.chat.completions.create(
            model="gpt-4o", messages=messages)
    except Exception as exc:  # noqa: BLE001
        logging.error("OpenAI API call failed: %s", exc)
        return "", ""
    output = response.choices[0].message.content.strip()

    summary = ""
    category = ""
    for line in output.splitlines():
        if line.startswith("Summary:"):
            summary = line.replace("Summary:", "").strip()
        elif line.startswith("Category:"):
            category = line.replace("Category:", "").strip()

    return summary, category


def parse_region(category: str) -> str:
    """Infer region from the category."""
    return "East Asia" if category.startswith("East Asia") else "Global"


def main() -> None:
    articles = load_articles()
    summarized = []

    for art in articles:
        title = art.get('title', '')
        body = art.get('content', '')
        if not title or not body:
            continue

        summary_zh, gpt_category = gpt_summarize(title, body)
        if not summary_zh or not gpt_category:
            continue
        region = art.get('region') or parse_region(gpt_category)
        category = art.get('category') or gpt_category

        print("✅ Title:", title)
        print("📝 Category:", category)
        if category != gpt_category:
            print("🛈 GPT Suggested:", gpt_category)
        print("🈶 Summary:", summary_zh)
        print("-----")

        src = art.get('source')
        if isinstance(src, dict):
            src = src.get('name')
        source_name = src or 'Unknown Source'

        published = art.get('publishedAt') or art.get('published_at')

        word_count = len(body.split())
        read_time_min = max(1, math.ceil(word_count / 200))

        summarized.append({
            'region': region,
            'category': category,
            'title': title,
            'summary_zh': summary_zh,
            'source': source_name,
            'read_time': f"{read_time_min} min read",
            'url': art.get('url'),
            'published_at': published,
            'tags': []
        })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(summarized, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote summaries to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
