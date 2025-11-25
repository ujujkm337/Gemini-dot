import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация API ключей
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAnmIxt6lrfNsoUKa2YKaX-_9G7QASD9wM')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7623168300:AAHYt7EAB2w4KaLW38HD1Tk-_MjyWTIiciM')

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Инициализация Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Ограничение одновременных запросов
MAX_CONCURRENT_REQUESTS = 3
current_requests = 0
request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def process_with_gemini(text: str) -> str:
    """Обработка запроса через Gemini AI с ограничением одновременных запросов"""
    async with request_semaphore:
        try:
            response = await asyncio.to_thread(model.generate_content, text)
            return response.text
        except Exception as e:
            logger.error(f"Ошибка Gemini: {e}")
            return "❌ Извините, произошла ошибка при обработке запроса. Попробуйте позже."

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Привет! Я бот с интеграцией Gemini AI.

Отправьте мне любой текст или вопрос, и я постараюсь помочь!

Примеры запросов:
• "Напиши план для изучения Python"
• "Объясни квантовую физику простыми словами" 
• "Помоги с идеей для проекта"

Команды:
/start - начать работу
/help - справка
/about - информация о боте
    """
    await message.answer(welcome_text)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
📖 Доступные команды:
/start - начать работу
/help - показать эту справку
/about - информация о боте

Просто отправьте мне сообщение, и я обработаю его с помощью Gemini AI!
    """
    await message.answer(help_text)

@dp.message(Command("about"))
async def cmd_about(message: Message):
    """Обработчик команды /about"""
    about_text = """
ℹ️ О боте:
Этот бот использует Gemini AI от Google для обработки запросов.

Особенности:
• Бесплатная версия Gemini
• Поддержка текстовых запросов
• Ограничение одновременных запросов
• Работает на Render.com
    """
    await message.answer(about_text)

@dp.message(F.text)
async def handle_message(message: Message):
    """Обработчик текстовых сообщений"""
    user_message = message.text
    
    # Показываем, что бот печатает
    await message.answer_chat_action("typing")
    
    try:
        # Обрабатываем запрос через Gemini
        response = await process_with_gemini(user_message)
        
        # Разбиваем длинные сообщения (Telegram ограничение 4096 символов)
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await message.answer(chunk)
                await asyncio.sleep(0.1)
        else:
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("❌ Произошла ошибка при обработке запроса. Попробуйте еще раз.")

async def main():
    """Основная функция запуска бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
