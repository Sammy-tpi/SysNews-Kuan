import json
import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Any, Dict, List

INPUT_FILE = "data/recent_articles.json"
OUTPUT_FILE = "data/classified_articles.json"
MAX_CONTENT_TOKENS = 1000  # Adjust based on your model's token limit

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

def load_prompt(version: str) -> str:
    path = f"prompts/filter_relevance_{version}.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

VERSION = "v1"
PROMPT_TEMPLATE = load_prompt(VERSION)


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

def _parse_response(text: str) -> Dict[str, int]:
    try:
        import re
        match = re.search(r"{[^{}]*}", text, re.DOTALL)
        if match:
            text = match.group(0)
        else:
            text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        keep = bool(data.get("keep", False))
        try:
            score = int(data.get("score", 0))
        except (TypeError, ValueError):
            score = 0
        return {"keep": keep, "score": score}
    except Exception as e:
        print("⚠️ Failed to parse model response:", e)
        print("🧪 Raw inner text was:", repr(text))
        return {"keep": False, "score": 0}
    
def load_keywords():
    """Return the flat keyword list."""
    with open("config/keywords.json", "r", encoding="utf-8") as f:
        return json.load(f)["keywords"]


def keyword_score(article_text: str, keywords: List[str]) -> int:
    """Return the number of keyword hits using a loose, case-insensitive match."""

    lowered = article_text.lower()
    score = 0
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in lowered:
            score += 1
    return score


async def check_relevance(article: Dict[str, Any]) -> Dict[str, int] | None:
    title = article.get("title", "")
    content = article.get("content") or article.get("description", "")
    if not title or not content:
        return None
    short_content = truncate_text(content)
    prompt = f"{PROMPT_TEMPLATE.strip()}\n\nTitle: {title}\n\nArticle Content:\n{short_content}"

    full_prompt = prompt + "\nPlease answer only in JSON format like {\"keep\": true, \"score\": 18}."

    async with semaphore:
        try:
            resp = await model.generate_content_async(full_prompt)
            text = resp.text
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

    tasks = [check_relevance(art) for art in valid_articles]
    responses = await asyncio.gather(*tasks)

    for art, resp in zip(valid_articles, responses):
        if resp and resp.get("keep"):
            text = f"{art.get('title', '')} {art.get('content') or art.get('description', '')}"
            kw_score = keyword_score(text, keywords)
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
