import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация API ключей из переменных окружения
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAnmIxt6lrfNsoUKa2YKaX-_9G7QASD9wM')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7623168300:AAHYt7EAB2w4KaLW38HD1Tk-_MjyWTIiciM')

# Инициализация Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Очередь запросов для избежания перегрузки
import asyncio
from collections import deque

request_queue = deque()
MAX_CONCURRENT_REQUESTS = 3
current_requests = 0

async def process_with_gemini(text: str) -> str:
    """Обработка запроса через Gemini AI с ограничением одновременных запросов"""
    global current_requests
    
    # Ждем, если слишком много одновременных запросов
    while current_requests >= MAX_CONCURRENT_REQUESTS:
        await asyncio.sleep(0.1)
    
    current_requests += 1
    try:
        response = model.generate_content(text)
        return response.text
    except Exception as e:
        logger.error(f"Ошибка Gemini: {e}")
        return "Извините, произошла ошибка при обработке запроса. Попробуйте позже."
    finally:
        current_requests -= 1

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Привет! Я бот с интеграцией Gemini AI.

Отправьте мне любой текст или вопрос, и я постараюсь помочь!

Примеры запросов:
• "Напиши план для изучения Python"
• "Объясни квантовую физику простыми словами"
• "Помоги с идеей для проекта"
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 Доступные команды:
/start - начать работу
/help - показать эту справку
/about - информация о боте

Просто отправьте мне сообщение, и я обработаю его с помощью Gemini AI!
    """
    await update.message.reply_text(help_text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(about_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    
    # Показываем, что бот печатает
    await update.message.chat.send_action(action="typing")
    
    try:
        # Обрабатываем запрос через Gemini
        response = await process_with_gemini(user_message)
        
        # Разбиваем длинные сообщения (Telegram ограничение 4096 символов)
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
                await asyncio.sleep(0.1)
        else:
            await update.message.reply_text(response)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке запроса. Попробуйте еще раз.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Произошла непредвиденная ошибка.")

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
