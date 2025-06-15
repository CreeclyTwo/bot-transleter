import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import logging
import sys
import requests
from urllib.parse import quote

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_TOKEN = "7417545301:AAHqxallRESyfKIcVQNpELV6HqEaVCxfK1Q"
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


def adapt_to_colombian_spanish(text: str) -> str:
    """Добавляем только действительно распространенные колумбийские выражения"""
    colombian_slang = {
        r"\bamigo\b": "parcero",
        r"\bcompañero\b": "parcero",
        r"\bgenial\b": "chévere",
        r"\bexcelente\b": "bacano",
        r"\bfeo\b": "chimbo",
        r"\bmalo\b": "chimbo",
        r"\bestúpido\b": "güevón",
        r"\bcafé\b": "tinto",
        r"\bcerveza\b": "pola",
        r"\bdinero\b": "plata",
        r"\bhablar\b": "parlar",
        r"\bproblema\b": "lío",
        r"\bfiesta\b": "rumba",
        r"\btrabajo\b": "camello",
    }

    for pattern, replacement in colombian_slang.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def sanitize_text(text: str) -> str:
    """Очистка текста с сохранением только одного конечного знака"""
    if not text:
        return ""

    # Удаляем все знаки препинания, кроме последнего
    cleaned_text = re.sub(r'[.,!?;:¡¿"“”()\[\]{}—–]', '', text)

    # Добавляем последний знак из оригинала, если он был
    last_char = ''
    if text and text[-1] in '.!?;:':
        last_char = text[-1]

    # Применяем колумбийские адаптации
    result = adapt_to_colombian_spanish(cleaned_text)

    # Добавляем только один конечный знак
    if last_char:
        result += last_char

    # Удаляем лишние пробелы
    return re.sub(r'\s+', ' ', result).strip()


def translate_text(text: str) -> str:
    """Перевод через Google Translate API"""
    if not text.strip():
        return ""

    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=es&dt=t&q={quote(text)}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return ''.join(item[0] for item in data[0] if item[0])
        else:
            logger.error(f"Translation error: Status {response.status_code}")
            return ""
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return ""


@dp.message()
async def handle_message(message: types.Message):
    user_text = message.text.strip()

    if not user_text:
        return

    logger.info(f"Received: {user_text}")

    try:
        translated = translate_text(user_text)

        if translated:
            # Сохраняем ваш последний знак препинания
            last_char = user_text[-1] if user_text and user_text[-1] in '.!?;:' else ''

            # Очищаем и адаптируем
            cleaned = sanitize_text(translated)

            # Для приветствий используем базовые формы
            if user_text.lower().split()[0] in ["hello", "hi", "hey", "привет"]:
                cleaned = "Hola" + (last_char if last_char else '')
            elif user_text.lower().split()[0] in ["пока", "до свидания", "bye"]:
                cleaned = "Adiós" + (last_char if last_char else '')

            logger.info(f"Translated: {cleaned}")
            await message.reply(cleaned)
        else:
            await message.reply("Translation service unavailable")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await message.reply("Translation error")


async def main():
    logger.info("BOT STARTED: COLOMBIAN SPANISH TRANSLATOR")
    logger.info("Features: Single punctuation at end")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Явное завершение предыдущих экземпляров (для Windows)
    import os

    os.system("taskkill /f /im python.exe > nul 2>&1")

    # Исправление кодировки для Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)