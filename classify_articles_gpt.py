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
model = genai.GenerativeModel("gemini-1.5-flash")

CATEGORIES = [
    "General Tech & Startups",
    "Applied AI & FinTech",
    "Blockchain & Crypto",
]

REGIONS = ["global", "east asia"]

# Limit the request size to avoid exceeding the model's context window
MAX_CONTENT_TOKENS = 1000  # Adjust based on your model's token limit


def truncate_text(text: str, max_tokens: int = MAX_CONTENT_TOKENS) -> str:
    words = text.split()
    return " ".join(words[:max_tokens])

PROMPT_TEMPLATE = """
You are a news classification AI assistant working for the AI Innovation Department at TPIsoftware, a Taiwan-based software company specializing in artificial intelligence, financial technology, and enterprise software solutions.

Our team is building an internal news intelligence system to help product managers, researchers, and engineers stay updated on real-world applications of AI and emerging technologies across global and East Asian markets.

Your task is to analyze each article and assign:
1. One category — the article’s primary topic
2. One region — where the article is geographically focused
3. Decide whether the article provides meaningful insight, Does the content offer helpful, new, or actionable information to professionals in AI, FinTech, or Blockchain?
4. If the article is not relevant, you are authorized to delete it from the dataset.


❌ Do NOT keep articles that:
	•	Focus on social trends, youth culture, education inequality, or politics with no technical application
	•	Mention crypto or AI without real content (e.g. just as a cultural or economic metaphor)
	•	Discuss geopolitical conflicts, cyberattacks, or hacker activity unrelated to product innovation or enterprise adoption
	•	Are overly vague, speculative, or lack product, funding, or technical depth



Why this matters:
Your classifications help us identify real-world use cases of AI and FinTech, track innovation across Asia and the world, and surface relevant news for internal strategy, product planning, and technical research.

Categories (choose one only):

General Tech & Startups
For news about general technology trends, enterprise tools, consumer apps, or startup activity.
Example: A startup launches a productivity tool or a SaaS company raises funding.

Applied AI & FinTech
For articles about practical uses of artificial intelligence or financial technology. Includes LLM applications, algorithmic trading, AI customer service, robo-advisors, fraud detection, and similar topics.
Example: A bank uses a large language model to automate customer service.

Blockchain & Crypto
For content about crypto exchanges, smart contracts, Web3 infrastructure, blockchain applications in finance, or central bank digital currencies. It should be realted to AI or FinTech.
Example: The company applied AI in trading.

Regions (choose one only):

East Asia
For news focused on Taiwan, China, Japan, South Korea, or Hong Kong. This region is our strategic priority and we track its trends closely.

Global
For all other regions, such as the United States, Europe, India, or if the article discusses global technology trends, multinational initiatives, or broad international applications.

Output Format:
Return only a JSON object on a single line, with no formatting or explanation.
For example: {"category": "Applied AI & FinTech", "region": "East Asia"}

"""


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
        region = str(data.get("region", "global")).lower()
        return {
            "category": data.get("category", ""),
            "region": region,
        }
    except Exception as e:
        print("⚠️ Failed to parse model response:", e)
        print("🧪 Raw inner text was:", repr(raw_text))
        return {"category": "", "region": "global"}


async def classify_article(article: Dict[str, Any]) -> Dict[str, Any] | None:
    title = article.get("title", "")
    content = article.get("content") or article.get("description", "")
    if not title or not content:
        return None
    short_content = truncate_text(content)
    prompt = f"{PROMPT_TEMPLATE.strip()}\n\nTitle: {title}\n\nArticle Content:\n{short_content}"

    full_prompt = (
        prompt
        + "\nPlease return JSON like {\"category\": \"Applied AI & FinTech\", \"region\": \"East Asia\"}."
    )

    async with semaphore:
        try:
            resp = await model.generate_content_async(full_prompt)
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
        art["region"] = str(result.get("region", "global")).lower()
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
