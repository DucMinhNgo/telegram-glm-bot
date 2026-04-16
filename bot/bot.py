import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://glm:8000/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "THUDM/glm-4-9b-chat")

client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key="dummy"
)

user_histories = {}

SYSTEM_PROMPT = (
    "Bạn là chatbot hỗ trợ người dùng bằng tiếng Việt. "
    "Trả lời rõ ràng, tự nhiên, ngắn gọn khi phù hợp."
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xin chào, mình là chatbot chạy bằng GLM local. Bạn cứ nhắn tin nhé."
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Đã xóa lịch sử hội thoại của bạn.")

def build_messages(user_id: int, user_text: str):
    history = user_histories.get(user_id, [])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    return messages

def save_history(user_id: int, user_text: str, assistant_text: str, max_turns: int = 10):
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": assistant_text})

    if len(history) > max_turns * 2:
        history = history[-max_turns * 2:]

    user_histories[user_id] = history

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if not user_text:
        await update.message.reply_text("Bạn hãy nhập nội dung tin nhắn.")
        return

    await update.message.chat.send_action("typing")

    try:
        messages = build_messages(user_id, user_text)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=512,
        )

        answer = response.choices[0].message.content.strip()
        save_history(user_id, user_text, answer)

        # Telegram có giới hạn độ dài tin nhắn
        chunk_size = 3500
        for i in range(0, len(answer), chunk_size):
            await update.message.reply_text(answer[i:i + chunk_size])

    except Exception as e:
        logging.exception("Error while calling GLM")
        await update.message.reply_text(f"Có lỗi khi gọi model: {str(e)}")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
