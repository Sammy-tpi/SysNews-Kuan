from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv
import os

# 載入 .env 檔
load_dotenv()

# 從環境變數取出
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
user_id = os.getenv("LINE_USER_ID")

# 初始化 API
line_bot_api = LineBotApi(channel_access_token)

# 發送訊息
try:
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text="👋 這是一則主動推送的測試訊息")
    )
    print("✅ 成功發送訊息！")
except Exception as e:
    print("❌ 發送失敗：", e)


