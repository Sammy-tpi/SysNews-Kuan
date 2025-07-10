"""Second-layer GPT classifier.

This module runs after ``filter_relevance_gpt.py``. It assigns a
human-readable category and region label to each article. The results
are stored for later summarization.
"""

import json
import os
import re
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List, Any

INPUT_FILE = "data/classified_articles.json"
OUTPUT_ALL_FILE = "data/news_data.json"
CATEGORY_DIR = "data/categorized"

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

CATEGORIES = [
    "Research",
    "Infrastructure",
    "FinTech",
    "Startup",
]

REGIONS = ["Global", "East Asia"]

# Limit the request size to avoid exceeding the model's context window
MAX_CONTENT_TOKENS = 1000  # Adjust based on your model's token limit


def truncate_text(text: str, max_tokens: int = MAX_CONTENT_TOKENS) -> str:
    words = text.split()
    return " ".join(words[:max_tokens])

def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

VERSION = "v2"
PROMPT_PATH = f"prompts/classify_articles_{VERSION}.txt"
PROMPT_TEMPLATE = load_prompt(PROMPT_PATH)



def load_articles(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {path}")


semaphore = asyncio.Semaphore(3)


def _parse_response(text: str) -> Dict[str, Any]:
    raw_text = text
    try:
        match = re.search(r"\{[^{}]*\}", raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)
        else:
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw_text)
        return {
            "category": data.get("category", ""),
            "region": data.get("region", "Global"),
        }
    except Exception as e:
        print("⚠️ Failed to parse model response:", e)
        print("🧪 Raw inner text was:", repr(raw_text))
        return {"category": "", "region": "Global"}


async def classify_article(article: Dict[str, Any]) -> Dict[str, Any] | None:
    title = article.get("title", "")
    content = article.get("content") or article.get("description", "")
    if not title or not content:
        return None
    short_content = truncate_text(content)
    prompt = f"{PROMPT_TEMPLATE.strip()}\n\nTitle: {title}\n\n Content:\n{short_content}"

    async with semaphore:
        try:
            resp = await model.generate_content_async(prompt)
            text = resp.text
            print("📩 Model raw response:", text)
            return _parse_response(text)
        except Exception as e:
            print(f"❌ Exception during request: {e}")
            return None


async def main_async() -> None:
    articles = load_articles(INPUT_FILE)
    os.makedirs(CATEGORY_DIR, exist_ok=True)

    grouped = {region: {cat: [] for cat in CATEGORIES} for region in REGIONS}
    results: List[Dict[str, Any]] = []

    valid_articles: List[Dict[str, Any]] = []
    for art in articles:
        title = art.get("title", "")
        content = art.get("content") or art.get("description", "")
        if not title or not content:
            continue
        valid_articles.append(art)

    tasks = [classify_article(art) for art in valid_articles]
    responses = await asyncio.gather(*tasks)
    for art, result in zip(valid_articles, responses):
        if not result:
            continue
        art["category"] = result.get("category", "")
        art["region"] = result.get("region", "Global")
        results.append(art)
        cat = art["category"]
        region = art["region"]
        if region in grouped and cat in grouped[region]:
            grouped[region][cat].append(art)

    with open(OUTPUT_ALL_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    for region, cats in grouped.items():
        for cat, items in cats.items():
            filename = f"{region}_{cat}.json"
            path = os.path.join(CATEGORY_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
    print(
        f"Wrote {len(results)} articles with classifications to {OUTPUT_ALL_FILE}"
    )
    print(f"\U0001F3F7\FE0F \u6210\u529F\u5206\u985E\u7684\u6587\u7AE0\u6578\u91CF: {len(results)}")


if __name__ == "__main__":
    asyncio.run(main_async())
