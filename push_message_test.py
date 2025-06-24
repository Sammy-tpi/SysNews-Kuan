from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, PushMessageRequest
from dotenv import load_dotenv
import os

# 載入 .env 檔
load_dotenv()

def main() -> None:
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")
    if not token or not user_id:
        raise RuntimeError("Missing LINE credentials")

    configuration = Configuration(access_token=token)
    with ApiClient(configuration) as client:
        api = MessagingApi(client)
        msg = TextMessage(text="👋 這是一則主動推送的測試訊息")
        req = PushMessageRequest(to=user_id, messages=[msg])
        try:
            api.push_message(req)
            print("✅ 成功發送訊息！")
        except Exception as e:
            print("❌ 發送失敗：", e)


if __name__ == "__main__":
    main()


