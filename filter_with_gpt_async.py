import json
import os
import re
import asyncio
from typing import Dict, List, Any

import openai
from dotenv import load_dotenv

INPUT_FILE = "data/recent_articles.json"
OUTPUT_ALL_FILE = "data/classified_articles.json"
CATEGORY_DIR = "data/categorized"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

async_client = openai.AsyncOpenAI(api_key=openai.api_key)

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")

PROMPT_TEMPLATE = """You are an AI news filter.You are an AI-powered news analyst working for TPIsoftware, a Taiwan-based software company specializing in enterprise solutions, AI development, and financial technologies.Each day, we receive dozens of news articles in any languages. You are given the **title** and **full content** of each article.

Only read as much content as you need to confidently classify the article.
You do not need to read the full body.

1. Determine if the article is relevant to any of the following 3 categories:

- 🔹 startup_ai: News about startups using or building AI-driven products or services (e.g. product launches, fundraising, acquisitions, accelerator programs).
  Keywords: generative AI, AI SaaS, AI-powered tools, VC-backed startups, AI apps, AI marketplace.
- 🔹 finance_ai: Applications of AI in banking, insurance, payment, risk control, fraud detection, personal finance, robo-advisors, digital transformation.
  Keywords: FinTech, KYC/AML AI, fraud detection, RPA, AI in credit scoring, algorithmic trading.
- 🔹 blockchain_ai: Blockchain/Web3/Crypto projects that relate to AI, automation, or intelligent agents.
  Keywords: AI+DeFi, smart contracts, on-chain analytics, AI DAOs, NFT + AI, decentralized AI protocols.

2. Assign the correct category
3. Give the article a score from 1.0 to 10.0 based on how valuable it is for business insights
4. Classify the article's region:
   - "East Asia" if it focuses on Taiwan, China, Japan, Korea, or Hong Kong
   - "Global" for all other regions

Please use the following criteria to evaluate **relevance and value**:
- Does the article report a new product, feature, or strategic move involving AI in one of the three domains?
- Is there real business impact, like partnerships, launches, funding rounds, or policy changes?
- Is the story recent, non-generic, and likely to inspire product or business ideas?
- Is it specific (not just abstract tech talk), from a credible source, and related to East Asia or global markets?

Your response must be a valid JSON object like this. Return **only** the JSON object with no additional text:
{"is_relevant": true, "category": "finance_ai", "score": 8.2, "region": "East Asia"}
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
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    print("❌ Failed to parse GPT response as JSON")
    return {"is_relevant": False, "category": "", "score": 0.0, "region": "Global"}


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
    short_content = content[:1200]
    prompt = f"{PROMPT_TEMPLATE}\n\nTitle: {title}\n\nArticle Content:\n{short_content}"
    messages = [{"role": "system", "content": prompt}]
    params = {
        "model": MODEL_NAME,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    async with semaphore:
        resp = await call_with_retry(async_client, **params)
    if not resp:
        return {"is_relevant": False, "category": "", "score": 0.0, "region": "Global"}
    text = resp.choices[0].message.content.strip()
    return _parse_response(text)


async def main_async() -> None:
    articles = load_articles(INPUT_FILE)
    os.makedirs(CATEGORY_DIR, exist_ok=True)

    grouped = {
        "Global": {"startup_ai": [], "finance_ai": [], "blockchain_ai": []},
        "East Asia": {"startup_ai": [], "finance_ai": [], "blockchain_ai": []},
    }
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
            art.update(result)
            results.append(art)
            if result.get("is_relevant"):
                cat = result.get("category")
                region = result.get("region", "Global")
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
