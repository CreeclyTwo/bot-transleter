import asyncio
from openai import OpenAI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

# Конфигурация
BOT_TOKEN = "7417545301:AAHqxallRESyfKIcVQNpELV6HqEaVCxfK1Q"
GROQ_API_KEY = "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"

# Настройка клиента OpenAI с поддержкой Groq
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

TRANSLATE_PROMPT = """
Ты профессиональный переводчик-синхронист, специализирующийся на колумбийском испанском.

Твоя задача — переводить любой текст так, чтобы он звучал, как разговорная речь в мессенджерах.

🔒 Жёсткие правила:
1. Ты ТОЛЬКО переводишь. НЕ даёшь пояснений, НЕ говоришь от себя.
2. НИКАКИХ знаков препинания — кроме двух:
   - Стави `!` в конце эмоциональных фраз или команд.
   - Стави `?` в конце вопросительных фраз.
3. Не используй `¡`, `¿`, точки, запятые, двоеточия или тире — ни при каких обстоятельствах.
4. Перевод должен звучать просто, как будто два колумбийца общаются в чате.
5. Если текст уже на испанском — верни его как есть, ничего не меняя.

📌 Важно: ТЫ ОБЯЗАН использовать `!` и `?` там, где это соответствует смыслу. Например:
"Ты где?" → "donde estas?"
"Быстро сюда!" → "ven ya!"
"Чего тебе?" → "que quieres?"

Игнорирование этих двух символов считается ошибкой.
"""


MAX_INPUT_TOKENS = 6000
MAX_OUTPUT_LENGTH = 4096

def split_text(text, max_length):
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

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
        input_chunks = split_text(original_text, MAX_INPUT_TOKENS // 2)
        translations = []

        for chunk in input_chunks:
            response = client.chat.completions.create(
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
        output_chunks = split_text(full_translation, MAX_OUTPUT_LENGTH)

        for i, chunk in enumerate(output_chunks):
            if i == 0:
                await message.reply(chunk)
            else:
                await bot.send_message(chat_id=message.chat.id, text=chunk)

    except Exception as e:
        print(f"Translation error: {e}")
        await message.reply("❌ Error de traducción. Inténtalo de nuevo.")

async def main():
    print("🤖 Traductor universal iniciado")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
