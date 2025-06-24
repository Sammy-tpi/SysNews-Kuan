import json
import os
from typing import List

from dotenv import load_dotenv
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import (
    FlexBubble,
    FlexBox,
    FlexCarousel,
    FlexMessage,
    PushMessageRequest,
)

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID", "U52d3d8f05063b1c6d2ace4f1acff20d2")
JSON_PATH = "data/news_data.json"

if not ACCESS_TOKEN:
    raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN not set in environment")

CATEGORY_LABELS = {
    "startup_ai": "Startup",
    "finance_ai": "Fintech",
    "blockchain_ai": "Blockchain",
}

REGION_ICONS = {
    "Global": "🌏",
    "East Asia": "🇹🇼",
}


def load_articles(path: str) -> List[dict]:
    if not os.path.exists(path):
        raise RuntimeError(f"{path} not found")
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {path}") from exc


def build_bubble(article: dict) -> FlexBubble:
    region = article.get("region", "Global")
    category = article.get("category", "")
    header = f"{REGION_ICONS.get(region, '')} {region} | {CATEGORY_LABELS.get(category, category)}"

    bubble_dict = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": header,
                    "weight": "bold",
                    "size": "sm",
                    "color": "#AAAAAA",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": article.get("title", ""),
                    "weight": "bold",
                    "size": "md",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": (
                        article.get("summary")
                        or article.get("summary_zh")
                        or "\uff08\u7121\u6458\u8981\uff09"
                    ),
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "\u95b1\u8b80\u5168\u6587",
                        "uri": article.get("url", "#"),
                    },
                }
            ],
            "flex": 0,
        },
    }
    return FlexBubble.from_dict(bubble_dict)


def send_messages(articles: List[dict]) -> None:
    bubbles = [build_bubble(a) for a in articles]
    configuration = Configuration(access_token=ACCESS_TOKEN)

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        for i in range(0, len(bubbles), 5):
            chunk = bubbles[i:i + 5]
            carousel = FlexCarousel.from_dict({
                "type": "carousel",
                "contents": [b.to_dict() for b in chunk],
            })
            message = FlexMessage(alt_text="Polaris Daily Digest", contents=carousel)
            req = PushMessageRequest(to=USER_ID, messages=[message])
            api.push_message(req)
            print(f"✅ Pushed {len(chunk)} article(s)")


def main() -> None:
    articles = load_articles(JSON_PATH)
    if not articles:
        print("No articles to send.")
        return
    send_messages(articles)


if __name__ == "__main__":
    main()
