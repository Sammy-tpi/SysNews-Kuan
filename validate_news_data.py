import json
import os
from typing import Dict, List, Tuple

INPUT_FILE = "data/news_data.json"
OUTPUT_FILE = "data/news_data.json"

CATEGORY_MAPPING = {
    "Startup_ai": "Startup_ai",
    "finance_ai": "finance_ai",
    "blockchain_ai": "blockchain_ai",
    "General Tech & Startups": "Startup_ai",
    "Applied AI & FinTech": "finance_ai",
    "Applied AI & Fintech": "finance_ai",
    "Blockchain & Crypto": "blockchain_ai",
}

REGIONS = ["Global", "East Asia"]
CATEGORIES = ["Research_ai", "Infrastructure_ai", "Startup_ai", "FinTech_ai"]


def normalize_category(cat: str) -> str:
    cat = cat.strip()
    if not cat:
        return "Startup_ai"
    # remove region prefix like "Global – "
    if "–" in cat:
        # ndash or hyphen
        cat = cat.split("\u2013", 1)[1].strip()
    if "-" in cat:
        # fallback hyphen
        parts = cat.split("-", 1)
        if parts[0].strip() in ["Global", "East Asia"]:
            cat = parts[1].strip()
    return CATEGORY_MAPPING.get(cat, cat)


def load_articles() -> List[Dict]:
    if not os.path.exists(INPUT_FILE):
        return []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def deduplicate(articles: List[Dict]) -> List[Dict]:
    seen: set[Tuple[str, str]] = set()
    result = []
    for art in articles:
        region = art.get("region", "Global")
        cat_key = normalize_category(art.get("category", ""))
        pair = (region, cat_key)
        if pair in seen:
            continue
        seen.add(pair)
        art["category"] = cat_key
        result.append(art)
    return result


def ensure_all_categories(articles: List[Dict]) -> List[Dict]:
    existing = {(art.get("region", "Global"), normalize_category(
        art.get("category", ""))) for art in articles}
    for region in REGIONS:
        for cat in CATEGORIES:
            if (region, cat) not in existing:
                articles.append({
                    "region": region,
                    "category": cat,
                    "title": "(No article selected)",
                    "summary_zh": "今日沒有相關新聞。",
                    "source": "",
                    "read_time": "",
                    "url": "#",
                    "tags": []
                })
    return articles


def main() -> None:
    articles = load_articles()
    articles = deduplicate(articles)
    articles = ensure_all_categories(articles)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Validated {len(articles)} articles and wrote to {OUTPUT_FILE}")
    validated = articles
    print(f"\u2705 \u9a57\u8b49\u5f8c\u4fdd\u7559\u7684\u6709\u6548\u65b0\u805e\u6578\u91CF: {len(validated)}")


if __name__ == "__main__":
    main()
