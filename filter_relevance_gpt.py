import json
import os
import aiohttp
import asyncio
from typing import Any, Dict, List

from utils import load_keywords, keyword_score, source_weight

INPUT_FILE = "data/recent_articles.json"
OUTPUT_FILE = "data/classified_articles.json"
MODEL_ENDPOINT = "http://192.168.32.1:8001/api/v0/llm/rag"
MAX_CONTENT_TOKENS = 1000  # Adjust based on your model's token limit


PROMPT_TEMPLATE = """
You are an AI-powered news filter working at TPIsoftware, a software company based in Taiwan that specializes in AI development, enterprise platforms, and financial technologies.

Each day, your job is to help the product and strategy teams scan hundreds of global and East Asian news articles and identify only the ones that are relevant to our company’s interests.

We are specifically interested in news articles related to:

- Artificial Intelligence (AI), including new applications, tools, models, or platforms.
- Financial Technology (FinTech), such as digital banking, fraud detection, robo-advisors, AI in risk control or personal finance.
- Blockchain and Crypto technologies, especially their use in automation, intelligent agents, or AI-enhanced Web3 projects.

We **do not want** articles that are mainly about politics, lifestyle, sports, culture, general economy, or unrelated industries.

Please focus on whether the article has any real or potential connection to **AI, FinTech, or Blockchain innovation**, especially if it has product, funding, technical, or strategic value.

### Scoring Criteria
- **score = 10:** Article is entirely about a real-world application, product launch, or strategic development in AI, FinTech, or Blockchain, in a technical/business context directly relevant to us.
- **score = 7–9:** Main topic is AI, FinTech, or Blockchain, with substantial detail or industry impact.
- **score = 4–6:** Relevant topics are mentioned, but as a secondary focus or in a general/indirect way.
- **score = 1–3:** Only minor or marginal mention of our focus areas.
- **score = 0:** Completely unrelated.

### Instructions
1. Carefully read the article’s title and content.
2. Think step by step: (1) Identify the topic; (2) Judge relevance; (3) Decide if it should be kept; (4) Assign a score.
3. Output a single line of JSON with **both** keys, e.g. `{"keep": true, "score": 8}`
"""

semaphore = asyncio.Semaphore(3)

def truncate_text(text: str, max_tokens: int = MAX_CONTENT_TOKENS) -> str:
    words = text.split()
    return " ".join(words[:max_tokens])

def load_articles(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {path}")

def _parse_response(full_response: str) -> Dict[str, int]:
    try:
        obj = json.loads(full_response)
        raw_text = obj.get("results", {}).get("text", "")
        if not raw_text:
            return {"keep": False, "score": 0}

        # 🧹 Step 1: Remove markdown block with regex
        import re
        match = re.search(r"\{[^{}]*\}", raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)
        else:
            # fallback: try to remove backticks manually
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        # 🧹 Step 2: Load JSON
        result_obj = json.loads(raw_text)
        keep = bool(result_obj.get("keep", False))
        try:
            score = int(result_obj.get("score", 0))
        except (TypeError, ValueError):
            score = 0
        return {"keep": keep, "score": score}

    except Exception as e:
        print("⚠️ Failed to parse model response:", e)
        print("🧪 Raw inner text was:", repr(raw_text))
        return {"keep": False, "score": 0}

async def check_relevance(session: aiohttp.ClientSession, article: Dict[str, Any]) -> Dict[str, int] | None:
    title = article.get("title", "")
    content = article.get("content") or article.get("description", "")
    if not title or not content:
        return None
    short_content = truncate_text(content)
    prompt = f"{PROMPT_TEMPLATE.strip()}\n\nTitle: {title}\n\nArticle Content:\n{short_content}"

    payload = {
        "query": prompt,
        "sys_prompt": "You are a JSON-only API that determines if an article is relevant to AI, FinTech, or Blockchain.",
        "model_name": "Gemma-3-27B",
        "temperature": 0.1,
        "top_p": 0.1,
        "top_k": 5,
        "max_tokens": 4096,
        "repetition_penalty": 1,
        "parser": "text"
    }

    async with semaphore:
        try:
            async with session.post(MODEL_ENDPOINT, json=payload, timeout=120, ssl=False) as resp:
                text = await resp.text()
                print("📩 Model raw response:", text)
                return _parse_response(text)
        except Exception as e:
            print(f"❌ Exception during request: {e.__class__.__name__} - {e}")
            return None

async def main_async() -> None:
    articles = load_articles(INPUT_FILE)
    keywords = load_keywords()
    valid_articles = []
    results = []

    for art in articles:
        if art.get("title") and (art.get("content") or art.get("description")):
            valid_articles.append(art)

    async with aiohttp.ClientSession() as session:
        tasks = [check_relevance(session, art) for art in valid_articles]
        responses = await asyncio.gather(*tasks)

        for art, resp in zip(valid_articles, responses):
            if resp and resp.get("keep"):
                text = f"{art.get('title', '')} {art.get('content') or art.get('description', '')}"
                kw_score = keyword_score(text, keywords)
                source_name = art.get("source", {}).get("name", "")
                kw_score *= source_weight(source_name)
                gpt_score = resp.get("score", 0)
                art["score"] = gpt_score + kw_score
                results.append(art)
            elif resp is None:
                print(f"⚠️ Skipped article due to LLM error: {art['title']}")

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ Wrote {len(results)} relevant articles to {OUTPUT_FILE}")
    relevant_articles = results
    print(f"\U0001F9E0 GPT \u5224\u5B9A\u70BA\u76F8\u95DC\u7684\u6587\u7AE0\u6578\u91CF: {len(relevant_articles)}")

if __name__ == "__main__":
    asyncio.run(main_async())
