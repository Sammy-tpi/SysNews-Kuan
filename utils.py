import json
from typing import Dict, List

KEYWORDS_FILE = "config/keywords.json"


def load_keywords(path: str = KEYWORDS_FILE) -> Dict[str, List[str]]:
    """Load keyword categories from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def keyword_score(article_text: str, keywords: List[str]) -> int:
    """Return how many keywords appear in the given text (case-insensitive)."""
    lowered = article_text.lower()
    return sum(1 for kw in keywords if kw.lower() in lowered)


def source_weight(source_name: str) -> int:
    """Return a simple weight for a news source. Extend as needed."""
    weights = {
        "TechCrunch": 3,
        "VentureBeat": 3,
        "Decrypt": 2,
    }
    return weights.get(source_name, 1)
