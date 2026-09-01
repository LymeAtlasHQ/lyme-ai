import logging
import os
from textwrap import dedent

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger = logging.getLogger("lymewire.telegram")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-5.5")
APP_NAME = os.getenv("APP_NAME", "Lymewire")

SYSTEM_PROMPT = dedent(
    """
    You are Lymewire, an evidence-aware Lyme disease research and patient-support assistant.
    Answer in the user's language when possible. Be clear, calm, and practical.

    Important boundaries:
    - You are not a doctor and you do not diagnose, prescribe, or replace urgent care.
    - Encourage users to work with qualified clinicians for diagnosis and treatment decisions.
    - For emergency symptoms, advise urgent local medical help immediately.
    - Prefer reliable sources and explain uncertainty instead of overstating evidence.
    - Keep Telegram replies compact, readable, and action-oriented.
    """
).strip()

START_TEXT = dedent(
    f"""
    {APP_NAME} aktif.

    Lyme, kene kaynakli enfeksiyonlar, semptom takibi, kaynak okuma ve doktorla konusmaya hazirlik icin bana yazabilirsin.

    Komutlar:
    /start - botu tanitir
    /help - nasil kullanilir
    /safety - acil uyari sinirlari

    Not: Tani koymam, ilac/tedavi emri vermem. Acil veya kotulesen belirtilerde yerel acil saglik hizmetine basvur.
    """
).strip()

SAFETY_TEXT = dedent(
    """
    Acil destek gerektirebilecek durumlar:
    - Nefes darligi, gogus agrisi, bayilma, yeni felc/konusma bozuklugu
    - Yuksek ates, ense sertligi, siddetli bas agrisi, bilinç bulanıklığı
    - Hizla artan dokuntu, yuz/dil/ses tellerinde sisme
    - Siddetli karin agrisi, yogun kanama, hamilelik supheli acil durumlar
    - Kendine zarar verme dusuncesi

    Boyle bir durumda botla bekleme; bulundugun yerdeki acil saglik hattini ara veya en yakin acile git.
    """
).strip()


def require_env() -> None:
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Sorunu normal mesaj olarak yaz. Belirti listesi, lab sonucu yorumu, makale ozeti veya doktora sorulacak sorular gibi konularda yardim edebilirim."
    )


async def safety(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(SAFETY_TEXT)


async def answer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()
    if not question:
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        response = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        )
        answer = response.output_text.strip()
    except Exception:
        logger.exception("Telegram answer failed")
        answer = "Su an cevap uretirken sorun yasadim. Birazdan tekrar dener misin?"

    if len(answer) > 3900:
        answer = answer[:3900].rstrip() + "\n\n[Devami icin soruyu biraz daraltip tekrar yaz.]"

    await update.message.reply_text(answer)


def build_application() -> Application:
    require_env()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("safety", safety))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_message))
    return application


def main() -> None:
    application = build_application()
    logger.info("Starting %s Telegram bot with model %s", APP_NAME, MODEL)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
