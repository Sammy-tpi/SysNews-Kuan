import json
from typing import List, Dict

INPUT_FILE = "data/newsapi_ai_articles.json"
OUTPUT_FILE = "news_data.json"


def load_articles() -> List[Dict]:
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def simple_summary(text: str, limit: int = 2) -> str:
    """Return the first few sentences of the text as a crude summary."""
    if not text:
        return ""
    sentences = text.split('. ')
    return '. '.join(sentences[:limit]).strip()


def main() -> None:
    articles = load_articles()
    summarized = []
    for art in articles:
        summary = simple_summary(art.get('content', ''))
        summarized.append({
            'region': 'Global',
            'category': 'General Tech & Startups',
            'title': art.get('title'),
            'summary': summary,
            'source': art.get('source', {}).get('name'),
            'read_time': '1 min read',
            'url': art.get('url'),
            'tags': []
        })
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(summarized, f, ensure_ascii=False, indent=2)
    print(f"Wrote summaries to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
