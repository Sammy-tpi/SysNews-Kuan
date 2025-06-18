import json
from typing import List


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


def source_weight(source_name: str) -> int:
    """Return a simple weight for a news source. Extend as needed."""
    weights = {
        "TechCrunch": 3,
        "VentureBeat": 3,
        "Decrypt": 2,
    }
    return weights.get(source_name, 1)
