import json
import re
from typing import List


def load_keywords():
    """Return the flat keyword list."""
    with open("config/keywords.json", "r", encoding="utf-8") as f:
        return json.load(f)["keywords"]


def keyword_score(article_text: str, keywords: List[str]) -> int:
    """Return the total number of keyword hits in ``article_text``."""

    lowered = article_text.lower()
    score = 0
    for kw in keywords:
        kw_lower = kw.lower()
        # English keywords use word boundaries but allow hyphenated forms
        if re.search(r"[a-zA-Z0-9]", kw_lower):
            pattern = rf"\b{re.escape(kw_lower)}(?!\w)"
        else:
            pattern = re.escape(kw_lower)
        score += len(re.findall(pattern, lowered))
    return score


def source_weight(source_name: str) -> int:
    """Return a simple weight for a news source. Extend as needed."""
    weights = {
        "TechCrunch": 3,
        "VentureBeat": 3,
        "Decrypt": 2,
    }
    return weights.get(source_name, 1)
