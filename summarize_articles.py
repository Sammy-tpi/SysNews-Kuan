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
You are a bilingual AI assistant helping summarize and classify news articles related to AI, FinTech, and emerging technology.

Task:
1. Summarize the article in **Traditional Chinese** (4-5 sentences). Include key technical terms such as AI, FinTech, Blockchain, Machine Learning, NLP, etc. For each term, place its **original English term in parentheses** after the Traditional Chinese term.
2. Classify the article into one of the following **6 fixed categories**. Return only the best-fitting one.

**Categories**:
1. Global – General Tech & Startups  
2. Global – Applied AI & FinTech  
3. Global – Blockchain & Crypto  
4. East Asia – General Tech & Startups  
5. East Asia – Applied AI & FinTech  
6. East Asia – Blockchain & Crypto

**Title**:  
{title}

**Article Content**:  
{body}

**Output Format**:
---
Summary: [Your Traditional Chinese summary here]  
Category: [Best-fit category from the list above]
'''

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
