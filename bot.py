import os
from threading import Thread
from flask import Flask
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- КОНФИГУРАЦИЯ (ТВОИ ДАННЫЕ) ---
GEMINI_KEY = "AIzaSyAnmIxt6lrfNsoUKa2YKaX-_9G7QASD9wM"
TG_TOKEN = "7623168300:AAHYt7EAB2w4KaLW38HD1Tk-_MjyWTIiciM"

# Настройка Gemini
genai.configure(api_key=GEMINI_KEY)
# Используем быструю и бесплатную модель
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (KEEP-ALIVE) ---
# Render требует, чтобы приложение слушало порт, иначе он его убьет.
app = Flask('')

@app.route('/')
def home():
    return "Бот работает! (Gemini + Telegram)"

def run_http():
    # Render выдает порт через переменную окружения, или используем 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- ЛОГИКА БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот на базе Gemini. Напиши мне что-нибудь.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Показываем статус "печатает...", пока ИИ думает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        # Отправляем запрос в Gemini
        response = model.generate_content(user_text)
        # Отправляем ответ пользователю
        await update.message.reply_text(response.text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

def main():
    # 1. Запускаем фиктивный веб-сервер в фоне
    keep_alive()
    
    # 2. Запускаем бота
    application = Application.builder().token(TG_TOKEN).build()

    # Хендлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Запуск (polling)
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
