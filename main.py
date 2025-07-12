
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
import os

app = FastAPI()

# === LINE 設定 ===
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === Gemini 設定 ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="gemma-3n-e4b-it",
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 1024,
    }
)

# === Render 健康檢查 ===
@app.get("/")
async def root():
    return {"status": "OK", "message": "LINE Gemini Bot is running."}

# === LINE Webhook ===
@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return PlainTextResponse("OK", status_code=200)

# === 訊息處理 ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 檢查指令功能
    if user_message.startswith("#摘要"):
        reply_message = "（暫未串接）這裡會幫你做文章摘要"
    elif user_message.startswith("#翻譯"):
        reply_message = "（暫未串接）這裡會幫你翻譯文字"
    else:
        # 呼叫 Gemini 回覆
        try:
            prompt = f"""
你是阿統，一個有個性的聊天機器人，雖然不喜歡做事，但通常很心軟，會幫我做摘要、解程式，也會聊天。
若用戶沒有特別指令，就用你的個性回應。
以下是用戶的訊息：
{user_message}
"""
            response = model.generate_content(prompt)
            reply_message = response.text
        except Exception as e:
            reply_message = f"目前無法使用 Gemini，已切換簡易回覆：{user_message}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )


