import json
import os
import math
from typing import Dict, List
import logging

import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

logging.basicConfig(level=logging.ERROR)

INPUT_FILE = "data/selected_articles.json"
OUTPUT_FILE = "data/news_data.json"

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def load_articles() -> List[Dict]:
    if not os.path.exists(INPUT_FILE):
        return []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {INPUT_FILE}")


semaphore = asyncio.Semaphore(3)


def _parse_summary(text: str) -> str:
    raw_text = text
    try:
        for line in raw_text.splitlines():
            if line.startswith("Summary:"):
                return line.replace("Summary:", "").strip()
        return raw_text.strip()
    except Exception as exc:
        logging.error("Failed to parse model response: %s", exc)
        logging.debug("Raw text: %r", raw_text)
        return ""


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

VERSION = "v1"
PROMPT_PATH = f"prompts/summarize_article_{VERSION}.txt"
PROMPT_TEMPLATE = load_prompt(PROMPT_PATH)


async def gemma_summarize(title: str, body: str) -> str:
    """Return a Traditional Chinese summary of the article using Gemini."""
    prompt = PROMPT_TEMPLATE.format(title=title, body=body)

    async with semaphore:
        try:
            resp = await model.generate_content_async(prompt)
            text = resp.text
            print("📩 Model raw response:", text)
            summary = _parse_summary(text)

            # ✅ Log prompt, response, summary
            log_entry = {
                "title": title,
                "version": VERSION,
                "prompt": prompt,
                "response": text,
                "summary": summary,
            }
            os.makedirs("logs", exist_ok=True)
            log_path = f"logs/summarize_log_{VERSION}.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            return summary

        except Exception as exc:
            logging.error("Gemini API call failed: %s", exc)
            return ""



async def main_async() -> None:
    articles = load_articles()
    summarized = []

    valid_articles = [a for a in articles if a.get('title') and a.get('content')]

    tasks = [gemma_summarize(a['title'], a['content']) for a in valid_articles]
    summaries = await asyncio.gather(*tasks)

    for art, summary_zh in zip(valid_articles, summaries):
        if not summary_zh:
            continue

        region = art.get('region') or "Global"
        category = art.get('category') 

        print("✅ Title:", art['title'])
        print("📝 Category:", category)
        print("🈶 Summary:", summary_zh)
        print("-----")

        src = art.get('source')
        if isinstance(src, dict):
            src = src.get('name')
        source_name = src or 'Unknown Source'

        published = art.get('publishedAt') or art.get('published_at')

        word_count = len(art['content'].split())
        read_time_min = max(1, math.ceil(word_count / 200))

        summarized.append({
            'region': region,
            'category': category,
                'title': art['title'],
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
    print(f"\U0001F4DD \u6210\u529F\u6458\u8981\u7684\u6587\u7AE0\u7E3D\u6578: {len(summarized)}")


if __name__ == '__main__':
    asyncio.run(main_async())
