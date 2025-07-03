import json
import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Any, Dict, List

from utils import load_keywords, keyword_score, source_weight

INPUT_FILE = "data/recent_articles.json"
OUTPUT_FILE = "data/classified_articles.json"
MAX_CONTENT_TOKENS = 1000  # Adjust based on your model's token limit

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


PROMPT_TEMPLATE = """
You are an AI-powered news filter working at TPIsoftware, a software company based in Taiwan that specializes in AI development, enterprise platforms, and financial technologies.

Each day, your job is to help the product and strategy teams scan hundreds of global and East Asian news articles and identify only the ones that are relevant to our company’s interests.

We are specifically interested in news articles related to:
Artificial Intelligence (AI), including new applications, tools, models, or platforms.
Financial Technology (FinTech), such as digital banking, fraud detection, robo-advisors, AI in risk control or personal finance.
Blockchain and Crypto technologies, especially their use in automation, intelligent agents, or AI-enhanced Web3 projects.

We do not want articles that are mainly about politics, lifestyle, sports, culture, general economy, or unrelated industries.
Make sure the article provides meaningful insight, we only want the content offer helpful, new, or actionable information to professionals.

Please focus on whether the article has any real or potential connection to AI, FinTech, or Blockchain innovation, especially if it has product, funding, technical value.

Scoring Criteria:
 Topic Relevance (topic_score)

How directly is the article focused on AI, FinTech, or Blockchain?
	•	10  The article is entirely focused on a real-world application, product, or strategic move in AI/FinTech/Blockchain.
	•	7-9 The article is strongly related, but the target topic is not the main theme.
	•	4-6  The article contains general or brief mentions but not as a key focus.
	•	1-3  Only a passing or marginal reference.
	•	0  Completely unrelated to our target topics.

⸻

Source Credibility (source_score)

How trustworthy and professional is the source of the article?
	•	10  Top-tier industry or financial media (e.g., Bloomberg, TechCrunch, Reuters, 36Kr).
	•	7-9 Reputable mainstream or regional tech/finance publications.
	•	4-6 Aggregators, secondary news platforms.
	•	1-3 Blogs, promotional content, unclear authorship.
	•	0  Unverifiable or untrustworthy source.

⸻

 Practical Value & Depth (value_score)

Does the article provide concrete, useful information for business or technical insights?
	•	10  Includes specific applications, architecture, investment details, or strategic decisions.
	•	7-9  Offers relevant perspectives or analysis, but lacks detail.
	•	4-6  Mostly general commentary or trend summaries.
	•	1-3  Superficial or vague content.
	•	0  No informative value.

Instructions:
Carefully read the article’s title and content.
Think step by step. First, identify the topic. Second, judge relevance. Third, decide if it should be kept. Fourth, accumulate a total score.
Output a single line of JSON with both keys, for example: {"keep": true, "score": 18}

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
