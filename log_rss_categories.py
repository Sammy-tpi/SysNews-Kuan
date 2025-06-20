import feedparser
import json
from collections import defaultdict

# Load RSS sources
with open("config/sources.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    rss_sources = [
        s for s in config.get("rss_sources", []) + config.get("rsshub_sources", [])
        if s["source_type"] == "rss"
    ]

category_report = {}

for source in rss_sources:
    url = source.get("rss_url")
    name = source.get("name", "Unnamed Source")
    if not url:
        continue

    try:
        feed = feedparser.parse(url)
        tag_counter = defaultdict(int)

        for entry in feed.entries:
            tags = entry.get("tags", [])
            for tag in tags:
                term = tag.get("term", "").strip().lower()
                if term:
                    tag_counter[term] += 1

        category_report[name] = {
            "url": url,
            "total_articles": len(feed.entries),
            "articles_with_tags": sum(1 for entry in feed.entries if entry.get("tags")),
            "unique_categories": list(tag_counter.keys()),
            "category_counts": dict(tag_counter)
        }

    except Exception as e:
        category_report[name] = {
            "url": url,
            "error": str(e)
        }

# Write to file
output_path = "category_terms_report.json"
with open(output_path, "w", encoding="utf-8") as out_file:
    json.dump(category_report, out_file, ensure_ascii=False, indent=2)

print(f"✅ 分類結果已儲存至：{output_path}")
