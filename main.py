import asyncio
import openai
from aiogram import Bot, Dispatcher, types

# Конфигурация
BOT_TOKEN = "7417545301:AAHqxallRESyfKIcVQNpELV6HqEaVCxfK1Q"
GROQ_API_KEY = "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"

# Инициализация клиента Groq
groq = openai.OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Системный промт для строгого перевода
TRANSLATE_PROMPT = """
Ты - профессиональный переводчик-синхронист. 
Твоя единственная задача - переводить ЛЮБОЙ входящий текст на испанский язык, чтобы понимали коренные жители Колумбии.
Правила:
1. Никаких пояснений, только перевод
2. Сохраняй оригинальный тон (формальный/неформальный)
3. Никаких приветствий или прощаний
4. Если текст уже на испанском - возвращай его без изменений
"""

# Константы для обработки больших текстов
MAX_INPUT_TOKENS = 6000  # Максимальное количество токенов для ввода (с запасом)
MAX_OUTPUT_LENGTH = 4096  # Максимальная длина сообщения в Telegram


def split_text(text, max_length):
    """Разбивает текст на части по границам слов/предложений."""
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Пытаемся найти границу для разбивки
        split_at = max_length
        for marker in ['. ', '! ', '? ', '\n\n', '\n', ', ', ' ']:
            pos = text.rfind(marker, 0, max_length)
            if pos > 0:
                split_at = pos + len(marker)
                break

        chunk = text[:split_at].strip()
        chunks.append(chunk)
        text = text[split_at:].strip()
    return chunks


@dp.message()
async def translate_message(message: types.Message):
    original_text = message.text
    if not original_text.strip():
        return

    try:
        # Разбиваем текст на части если он слишком длинный
        input_chunks = split_text(original_text, MAX_INPUT_TOKENS // 2)

        translations = []
        for chunk in input_chunks:
            response = groq.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": TRANSLATE_PROMPT},
                    {"role": "user", "content": chunk}
                ],
                temperature=0.1,
                max_tokens=MAX_INPUT_TOKENS
            )
            translation = response.choices[0].message.content.strip()
            translations.append(translation)

        full_translation = " ".join(translations)

        # Разбиваем перевод для отправки в Telegram
        output_chunks = split_text(full_translation, MAX_OUTPUT_LENGTH)

        # Отправляем части перевода
        for i, chunk in enumerate(output_chunks):
            if i == 0:
                await message.reply(chunk)
            else:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=chunk
                )

    except Exception as e:
        print(f"Translation error: {e}")
        await message.reply("❌ Error de traducción. Inténtalo de nuevo.")


async def main():
    print("🤖 Traductor universal iniciado")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())