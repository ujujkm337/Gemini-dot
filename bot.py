import os
import asyncio
import threading
# НОВОЕ: Импортируем Router
from aiogram import Bot, Dispatcher, types, Router 
from google import genai
from google.genai.errors import APIError
from flask import Flask 

# ... (Инициализация ключей и клиента Gemini остается прежней) ...
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
GEMINI_MODEL = 'gemini-2.5-flash'

client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Ошибка инициализации Gemini: {e}")

if not BOT_TOKEN:
    print("TG_BOT_TOKEN не установлен. Бот не будет работать.")
    
bot = Bot(token=BOT_TOKEN)
# Инициализация Dispatcher (без аргумента bot)
dp = Dispatcher() 

# НОВОЕ: Создаем Router для обработки сообщений
router = Router()

# НОВОЕ: Подключаем Router к Dispatcher
dp.include_router(router)


### Обработчики сообщений (Теперь используют router.message) ###

# ИСПРАВЛЕНИЕ: Используем @router.message
@router.message(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    welcome_text = (
        "👋 Привет! Я бот на базе **Gemini 2.5 Flash**.\n"
        "Просто отправь мне свой вопрос, и я постараюсь на него ответить."
    )
    await message.answer(welcome_text, parse_mode='Markdown')

# ИСПРАВЛЕНИЕ: Используем @router.message
@router.message()
async def handle_message(message: types.Message):
    if not client:
        await message.answer("❌ Бот временно не работает: не удалось подключиться к Gemini API.")
        return

    thinking_message = await message.answer("🧠 Думаю... Пожалуйста, подождите.")

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=message.text
        )
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=thinking_message.message_id,
            text=response.text,
            parse_mode='Markdown' 
        )

    except Exception as e:
        error_text = f"❌ Произошла ошибка: {e}"
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=thinking_message.message_id,
            text=error_text
        )

# ... (Остальная часть кода Keep-Alive и main() остается прежней) ...

### ФУНКЦИЯ KEEP-ALIVE (Flask) ###

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Telegram Bot is Running!", 200

def run_flask_server():
    port = int(os.environ.get('PORT', 5000)) 
    print(f"Starting Flask Keep-Alive server on port {port}...")
    web_app.run(host='0.0.0.0', port=port, debug=False)

### Запуск Бота ###

async def main():
    if BOT_TOKEN:
        # 1. Запуск Flask в отдельном потоке для Keep-Alive
        flask_thread = threading.Thread(target=run_flask_server)
        flask_thread.daemon = True 
        flask_thread.start()
        
        # 2. Запуск Polling
        print("Бот polling запущен. Ожидание входящих сообщений...")
        await dp.skip_updates() 
        # start_polling теперь принимает объект bot
        await dp.start_polling(bot) 
    else:
        print("Бот не может запуститься, так как нет TG_BOT_TOKEN.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
