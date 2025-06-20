"""First-layer GPT relevance filter.

Stage: This script runs after ``filter_articles_by_date.py`` and before
``classify_articles_gpt.py``. It checks whether each article is related to
AI, FinTech, or Blockchain and keeps only relevant ones.
"""

import asyncio
import json
import os
from typing import Any, Dict, List

import openai
from dotenv import load_dotenv
import tiktoken

INPUT_FILE = "data/recent_articles.json"
OUTPUT_FILE = "data/classified_articles.json"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

async_client = openai.AsyncOpenAI(api_key=openai.api_key)

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")

MAX_CONTENT_TOKENS = 800


def truncate_by_tokens(text: str, max_tokens: int = MAX_CONTENT_TOKENS) -> str:
    """Return text truncated to ``max_tokens`` tokens."""
    enc = tiktoken.encoding_for_model(MODEL_NAME)
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])


PROMPT_TEMPLATE = """
You are an AI-powered news filter working at TPIsoftware, a software company based in Taiwan that specializes in AI development, enterprise platforms, and financial technologies.

Each day, your job is to help the product and strategy teams scan hundreds of global and East Asian news articles and identify only the ones that are relevant to our company’s interests.

We are specifically interested in news articles related to:

- Artificial Intelligence (AI), including new applications, tools, models, or platforms.
- Financial Technology (FinTech), such as digital banking, fraud detection, robo-advisors, AI in risk control or personal finance.
- Blockchain and Crypto technologies, especially their use in automation, intelligent agents, or AI-enhanced Web3 projects.

We **do not want** articles that are mainly about politics, lifestyle, sports, culture, general economy, or unrelated industries.

Please focus on whether the article has any real connection to **AI, FinTech, or Blockchain innovation**, especially if it has product, funding, technical, or strategic value.

Respond with a single JSON object like this:
{ "keep": true }
or
{ "keep": false }

Be strict: only return "keep": true if the article clearly touches on our areas of interest.
"""



def load_articles(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {path}")


def _parse_response(text: str) -> bool:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if data.get("keep") is not None:
                return bool(data["keep"])
            if data.get("decision"):
                return data["decision"].lower() == "keep"
            if data.get("is_relevant") is not None:
                return bool(data["is_relevant"])
    except json.JSONDecodeError:
        pass
    return False


async def call_with_retry(client: openai.AsyncOpenAI, **kwargs: Any) -> Any:
    for attempt in range(5):
        try:
            return await client.chat.completions.create(**kwargs)
        except openai.RateLimitError:
            wait = 2 ** attempt
            print(f"Rate limit hit. Retry in {wait} sec...")
            await asyncio.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            print("Other GPT error:", exc)
            return None
    return None


semaphore = asyncio.Semaphore(3)


async def check_relevance_async(article: Dict[str, Any]) -> bool:
    title = article.get("title", "")
    content = article.get("content") or article.get("description", "")
    if not title or not content:
        return False
    short_content = truncate_by_tokens(content)
    prompt = f"{PROMPT_TEMPLATE}\n\nTitle: {title}\n\nArticle Content:\n{short_content}"
    messages = [{"role": "system", "content": prompt}]
    params = {
        "model": MODEL_NAME,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 20,
    }
    async with semaphore:
        resp = await call_with_retry(async_client, **params)
    if not resp:
        return False
    text = resp.choices[0].message.content.strip()
    return _parse_response(text)


async def main_async() -> None:
    articles = load_articles(INPUT_FILE)
    results: List[Dict[str, Any]] = []

    tasks = []
    valid_articles: List[Dict[str, Any]] = []
    for art in articles:
        title = art.get("title", "")
        content = art.get("content") or art.get("description", "")
        if not title or not content:
            continue
        valid_articles.append(art)
        tasks.append(check_relevance_async(art))

    if tasks:
        responses = await asyncio.gather(*tasks)
        for art, keep in zip(valid_articles, responses):
            if keep:
                results.append(art)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(results)} relevant articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main_async())
