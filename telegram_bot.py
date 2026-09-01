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
MAX_TELEGRAM_MESSAGE = 3900

BASE_PROMPT = dedent(
    """
    You are Lymewire, an evidence-aware Lyme disease and tick-borne illness research assistant.
    Answer in the user's language when possible. Be clear, calm, practical, and honest about uncertainty.

    Product identity:
    - Lymewire is not an AI doctor.
    - Lymewire retrieves, compares, explains, and cites medical/scientific evidence.
    - Lymewire supports patients, suspected patients, clinicians, researchers, and advocates.

    Safety boundaries:
    - Do not diagnose, prescribe, change medication, or replace urgent care.
    - Encourage qualified clinicians for diagnosis and treatment decisions.
    - For emergency symptoms, advise urgent local medical help immediately.
    - For dosing, interactions, pregnancy, children, severe symptoms, or self-harm, use extra caution.
    - Keep Telegram replies compact, readable, and action-oriented.
    """
).strip()

MODE_PROMPTS = {
    "default": BASE_PROMPT,
    "symptoms": BASE_PROMPT
    + "\n\nMode: symptom intake. Structure the reply as: red flags, concise symptom timeline, useful details to track, and what to tell a clinician. Do not claim permanent storage.",
    "doctorbrief": BASE_PROMPT
    + "\n\nMode: doctor brief. Produce a short appointment brief: main concern, timeline, current meds/supplements if provided, tests/results to bring, focused questions to ask, and what would change urgency.",
    "paper": BASE_PROMPT
    + "\n\nMode: paper/article analysis. If the user provides an abstract, title, DOI, PMID, or pasted text, summarize: question, methods, population, findings, limits, evidence strength, and practical meaning. Do not invent missing paper details.",
    "treatment": BASE_PROMPT
    + "\n\nMode: treatment evidence review. Separate established guideline-backed care, plausible but uncertain approaches, unsupported claims, risks, and clinician questions. Do not tell the user to start/stop/change treatment.",
    "source": BASE_PROMPT
    + "\n\nMode: source-aware answer. Separate established evidence from uncertain or controversial claims. Mention source types users should verify, such as CDC, ECDC, NICE, peer-reviewed reviews, NIH trials, IDSA, ILADS, or local guidelines. Do not invent URLs.",
    "calm": BASE_PROMPT
    + "\n\nMode: anxiety support. Use a grounding, non-alarming tone. First check for emergency red flags, then give a short breathing/grounding step and one practical next action. Avoid spiraling possibilities.",
}

START_TEXT = dedent(
    f"""
    {APP_NAME} aktif.

    Lyme, kene kaynakli enfeksiyonlar, makaleler, tedavi iddialari, semptom takibi ve doktor randevusuna hazirlik icin bana yazabilirsin.

    Komutlar:
    /symptoms - belirti kaydi ve doktorluk ozet
    /doctorbrief - randevuya hazirlik ozeti
    /paper - makale/abstract/PMID analizi
    /treatment - tedavi iddiasini kanit-risk acisindan incele
    /source - kaynak/kanit odakli yanit modu
    /calm - panik veya anksiyete aninda sakin mod
    /safety - acil uyari sinirlari
    /help - nasil kullanilir

    Not: Tani koymam, ilac/tedavi emri vermem. Acil veya kotulesen belirtilerde yerel acil saglik hizmetine basvur.
    """
).strip()

HELP_TEXT = dedent(
    """
    Sorunu normal mesaj olarak yazabilirsin.

    Hizli kullanim:
    /symptoms Bugun bas agrisi, carpinti ve halsizlik var. Ates yok.
    /doctorbrief 3 haftadir doksisiklin kullandim, ishal ve halsizlik oldu.
    /paper PMID veya makale ozetini buraya yapistir.
    /treatment Uzun sureli antibiyotik tedavisinin kanit durumu ne?
    /source Kronik Lyme konusunda kanit tartismasi ne?
    /calm Panik oldum, kalbim hizli atiyor.

    Komuttan sonra metin yazarsan direkt cevaplarim. Sadece komutu yazarsan senden gerekli bilgiyi isterim.
    """
).strip()

SAFETY_TEXT = dedent(
    """
    Acil destek gerektirebilecek durumlar:
    - Nefes darligi, gogus agrisi, bayilma, yeni felc/konusma bozuklugu
    - Yuksek ates, ense sertligi, siddetli bas agrisi, bilinc bulanıklığı
    - Hizla artan dokuntu, yuz/dil/ses tellerinde sisme
    - Siddetli karin agrisi, yogun kanama, hamilelik supheli acil durumlar
    - Kendine zarar verme dusuncesi

    Boyle bir durumda botla bekleme; bulundugun yerdeki acil saglik hattini ara veya en yakin acile git.
    """
).strip()

COMMAND_HINTS = {
    "symptoms": "Belirtilerini, ne zaman basladigini, ates olup olmadigini, kullandigin ilaclari ve seni en cok korkutan seyi tek mesajda yaz.",
    "doctorbrief": "Randevu icin sikayetini, sureyi, mevcut ilaclari, test sonuclarini ve doktora sormak istediklerini yaz.",
    "paper": "Makale basligini, DOI/PMID numarasini, abstract'i veya metni yapistir. Ben ozetleyip kanit gucunu ayiracagim.",
    "treatment": "Hangi tedavi veya iddiayi inceleyeyim? Ilac, protokol, destek urunu veya yaklasimi tek mesajda yaz.",
    "source": "Hangi iddia veya konuyu kaynak/kanit acisindan inceleyeyim? Tek mesajda yaz.",
    "calm": "Once guvende misin? Gogus agrisi, bayilma, nefes darligi veya kendine zarar dusuncesi varsa acile yonel. Yoksa ne hissettigini yaz, beraber daraltalim.",
}


def require_env() -> None:
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def command_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    return " ".join(context.args).strip() if context.args else ""


async def send_chunks(update: Update, text: str) -> None:
    if not update.message:
        return
    clean = text.strip() or "Cevap uretilemedi. Biraz daha detay yazar misin?"
    for start in range(0, len(clean), MAX_TELEGRAM_MESSAGE):
        await update.message.reply_text(clean[start : start + MAX_TELEGRAM_MESSAGE])


async def ask_model(update: Update, prompt: str, user_text: str) -> None:
    if not update.message:
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        response = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
        )
        answer = response.output_text.strip()
    except Exception:
        logger.exception("Telegram answer failed")
        answer = "Su an cevap uretirken sorun yasadim. Birazdan tekrar dener misin?"

    await send_chunks(update, answer)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_chunks(update, START_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_chunks(update, HELP_TEXT)


async def safety(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_chunks(update, SAFETY_TEXT)


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str) -> None:
    text = command_text(context)
    if not text:
        await send_chunks(update, COMMAND_HINTS[mode])
        return
    await ask_model(update, MODE_PROMPTS[mode], text)


async def symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "symptoms")


async def doctorbrief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "doctorbrief")


async def paper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "paper")


async def treatment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "treatment")


async def source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "source")


async def calm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await mode_command(update, context, "calm")


async def answer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()
    if not question:
        return

    await ask_model(update, MODE_PROMPTS["default"], question)


def build_application() -> Application:
    require_env()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("safety", safety))
    application.add_handler(CommandHandler("symptoms", symptoms))
    application.add_handler(CommandHandler("doctorbrief", doctorbrief))
    application.add_handler(CommandHandler("paper", paper))
    application.add_handler(CommandHandler("treatment", treatment))
    application.add_handler(CommandHandler("source", source))
    application.add_handler(CommandHandler("calm", calm))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_message))
    return application


def main() -> None:
    application = build_application()
    logger.info("Starting %s Telegram bot with model %s", APP_NAME, MODEL)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
