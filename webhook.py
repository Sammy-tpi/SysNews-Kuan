from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

channel_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

if not channel_token or not channel_secret:
    raise RuntimeError("❌ 未正確讀取 .env 中的 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(channel_token)
handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print("✅ 收到事件：\n", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    print("👤 來自使用者：", event.source.user_id)
    print("💬 訊息內容：", text)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="✅ 收到你說的：「" + text + "」")
    )

if __name__ == "__main__":
    app.run(port=8000)
