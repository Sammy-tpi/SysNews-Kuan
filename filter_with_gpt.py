import json
import os
from typing import Dict, List

import openai
from dotenv import load_dotenv

INPUT_FILE = "data/recent_articles.json"
OUTPUT_ALL_FILE = "data/classified_articles.json"
CATEGORY_DIR = "data/categorized"

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")


PROMPT_TEMPLATE = """You are an AI news filter.You are an AI-powered news analyst working for TPIsoftware, a Taiwan-based software company specializing in enterprise solutions, AI development, and financial technologies.

Your job is to help our internal AI team and product managers stay updated on the most relevant global trends by selecting and scoring news articles in three focus areas:
- startup_ai: startups that use or build AI-based products and services
- finance_ai: the use of AI in banking, insurance, fintech, or digital finance transformation
- blockchain_ai: the use of blockchain, DeFi, Web3, or crypto projects that relate to AI or intelligent automation

Each day, we receive many news articles. You are given the **title and full content** of each article. Your task is to:

1. Decide if the article is relevant to any of the three categories (startup_ai / finance_ai / blockchain_ai)
2. Assign the correct category
3. Give the article a score from 1.0 to 10.0 based on how valuable it is for business insights

Please use the following criteria to evaluate **relevance and value**:
- Does the article report a new product, feature, or strategic move involving AI in one of the three domains?
- Is there real business impact, like partnerships, launches, funding rounds, or policy changes?
- Is the story recent, non-generic, and likely to inspire product or business ideas?
- Is it specific (not just abstract tech talk), from a credible source, and related to East Asia or global markets?

Your response must be a valid JSON object like this:
{{"is_relevant": true, "category": "finance_ai", "score": 8.2}}
"""


def load_articles(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON in {path}")


def classify_article(title: str, content: str) -> Dict:
    prompt = f"{PROMPT_TEMPLATE}\n\nTitle: {title}\n\nArticle Content:\n{content}"
    messages = [{"role": "system", "content": prompt}]
    try:
        resp = openai.chat.completions.create(model=MODEL_NAME, messages=messages)
    except Exception as exc:
        print(f"❌ OpenAI API error: {exc}")
        return {"is_relevant": False, "category": "", "score": 0.0}
    text = resp.choices[0].message.content.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("❌ Failed to parse GPT response as JSON")
        return {"is_relevant": False, "category": "", "score": 0.0}


def main() -> None:
    articles = load_articles(INPUT_FILE)
    os.makedirs(CATEGORY_DIR, exist_ok=True)

    categorized = {"startup_ai": [], "finance_ai": [], "blockchain_ai": []}
    results: List[Dict] = []

    for art in articles:
        title = art.get("title", "")
        content = art.get("content") or art.get("description", "")
        if not title or not content:
            continue
        result = classify_article(title, content)
        art.update(result)
        results.append(art)
        if result.get("is_relevant"):
            cat = result.get("category")
            if cat in categorized:
                categorized[cat].append(art)

    with open(OUTPUT_ALL_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    for cat, items in categorized.items():
        path = os.path.join(CATEGORY_DIR, f"{cat}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(results)} articles with classifications to {OUTPUT_ALL_FILE}")


if __name__ == "__main__":
    main()
