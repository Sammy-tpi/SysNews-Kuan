"""Second-layer GPT classifier.

This module runs after ``filter_relevance_gpt.py``. It assigns a
human-readable category and region label to each article. The results
are stored for later summarization.
"""

import json
import os
import re
import asyncio
from typing import Dict, List, Any

import openai
from dotenv import load_dotenv
import tiktoken

INPUT_FILE = "data/classified_articles.json"
OUTPUT_ALL_FILE = "data/news_data.json"
CATEGORY_DIR = "data/categorized"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

CATEGORIES = [
    "General Tech & Startups",
    "Applied AI & FinTech",
    "Blockchain & Crypto",
]

REGIONS = ["Global", "East Asia"]

async_client = openai.AsyncOpenAI(api_key=openai.api_key)

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")

# Limit the request size to avoid exceeding the model's context window
MAX_CONTENT_TOKENS = 800


def truncate_by_tokens(text: str, max_tokens: int = MAX_CONTENT_TOKENS) -> str:
    """Return text truncated to the given token length."""
    enc = tiktoken.encoding_for_model(MODEL_NAME)
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])

PROMPT_TEMPLATE = """
You are an AI-powered news classifier working for TPIsoftware, a Taiwan-based software company specializing in AI and financial technologies.

Your goal is to analyze each article and output a JSON object describing its topic and geographic focus. Use **only** the exact labels provided below.

Categories (choose the best fit):
- General Tech & Startups
- Applied AI & FinTech
- Blockchain & Crypto

Region options:
- East Asia – Taiwan, China, Japan, Korea, Hong Kong
- Global – all other regions

Return a JSON object like:
{"category": "Applied AI & FinTech", "region": "East Asia"}

Return only the JSON object with no additional commentary. Be consistent with the labels.
"""



def load_articles(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {path}")


def _parse_response(text: str) -> Dict[str, Any]:
    """Parse the JSON returned by GPT and normalize keys."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None
        else:
            data = None

    if isinstance(data, dict):
        return {
            "category": data.get("category", ""),
            "region": data.get("region", "Global"),
        }

    print("❌ Failed to parse GPT response as JSON")
    return {"category": "", "region": "Global"}


async def call_with_retry(client: openai.AsyncOpenAI, **kwargs: Any) -> Any:
    for attempt in range(5):
        try:
            return await client.chat.completions.create(**kwargs)
        except openai.RateLimitError:
            wait = 2 ** attempt
            print(f"Rate limit hit. Retry in {wait} sec...")
            await asyncio.sleep(wait)
        except Exception as e:  # noqa: BLE001
            print("Other GPT error:", e)
            return None
    return None


semaphore = asyncio.Semaphore(3)


async def classify_article_async(article: Dict[str, Any]) -> Dict[str, Any] | None:
    title = article.get("title", "")
    content = article.get("content") or article.get("description", "")
    if not title or not content:
        return None
    short_content = truncate_by_tokens(content)
    prompt = f"{PROMPT_TEMPLATE}\n\nTitle: {title}\n\nArticle Content:\n{short_content}"
    messages = [{"role": "system", "content": prompt}]
    params = {
        "model": MODEL_NAME,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 100,
    }
    async with semaphore:
        resp = await call_with_retry(async_client, **params)
    if not resp:
        return {"category": "", "region": "Global"}
    text = resp.choices[0].message.content.strip()
    return _parse_response(text)


async def main_async() -> None:
    articles = load_articles(INPUT_FILE)
    os.makedirs(CATEGORY_DIR, exist_ok=True)

    grouped = {region: {cat: [] for cat in CATEGORIES} for region in REGIONS}
    results: List[Dict[str, Any]] = []

    tasks = []
    valid_articles: List[Dict[str, Any]] = []
    for art in articles:
        title = art.get("title", "")
        content = art.get("content") or art.get("description", "")
        if not title or not content:
            continue
        valid_articles.append(art)
        tasks.append(classify_article_async(art))

    if tasks:
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
            filename = f"{region.lower()}_{cat}.json"
            path = os.path.join(CATEGORY_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
    print(
        f"Wrote {len(results)} articles with classifications to {OUTPUT_ALL_FILE}"
    )


if __name__ == "__main__":
    asyncio.run(main_async())
