import os
import logging
from threading import Thread
from flask import Flask
from waitress import serve  # Более надежный сервер
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ ---
GEMINI_KEY = "AIzaSyAnmIxt6lrfNsoUKa2YKaX-_9G7QASD9wM"
TG_TOKEN = "7623168300:AAHYt7EAB2w4KaLW38HD1Tk-_MjyWTIiciM"

# Настраиваем логи, чтобы видеть ошибки в Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- GEMINI ---
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ВЕБ-СЕРВЕР (FIX ДЛЯ RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_web_server():
    # Render автоматически дает порт в переменную окружения PORT
    # Если переменной нет, используем 8080
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 ЗАПУСК ВЕБ-СЕРВЕРА НА ПОРТУ: {port}")
    # Используем waitress вместо app.run для надежности
    serve(app, host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# --- БОТ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я снова тут! Пиши.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Ошибка Gemini: {e}")

def main():
    # 1. Сначала запускаем веб-сервер в отдельном потоке
    keep_alive()
    
    # 2. Запускаем бота
    application = Application.builder().token(TG_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🤖 Бот начинает работу...")
    application.run_polling()

if __name__ == '__main__':
    main()
