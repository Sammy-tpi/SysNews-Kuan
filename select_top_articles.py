import json
import os
from typing import List, Dict, Optional

CATEGORY_DIR = "data/categorized"
OUTPUT_FILE = "data/selected_articles.json"

FILES = [
    "global_startup_ai.json",
    "global_finance_ai.json",
    "global_blockchain_ai.json",
    "east asia_startup_ai.json",
    "east asia_finance_ai.json",
    "east asia_blockchain_ai.json",
]

def load_json(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {path}")
        return []

def select_top_article(articles: List[Dict]) -> Optional[Dict]:
    if not articles:
        return None
    return max(articles, key=lambda x: x.get("score", 0))


def main() -> None:
    os.makedirs("data", exist_ok=True)
    selected: List[Dict] = []

    for fname in FILES:
        path = os.path.join(CATEGORY_DIR, fname)
        articles = load_json(path)
        top = select_top_article(articles)
        if not top:
            continue
        selected.append(
            {
                "title": top.get("title"),
                "content": top.get("content"),
                "category": top.get("category"),
                "region": top.get("region"),
                "score": top.get("score"),
            }
        )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(selected)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
