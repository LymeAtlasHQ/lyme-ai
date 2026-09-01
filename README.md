# lyme-ai

AI systems for evidence-based Lyme disease research and knowledge management.

## Telegram bot

The first Lymewire Telegram bot entrypoint is `telegram_bot.py`.

### Required environment variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
MODEL=gpt-5.5
APP_NAME=Lymewire
```

Create the Telegram token with BotFather:

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`.
3. Pick a display name, for example `Lymewire`.
4. Pick a username ending in `bot`, for example `lymewire_ai_bot` if available.
5. Copy the token into `TELEGRAM_BOT_TOKEN` in Railway or your local `.env` file.

### Run locally

```bash
pip install -r requirements.txt
python telegram_bot.py
```

### Railway start command

For a bot-only service, set the Railway start command to:

```bash
python telegram_bot.py
```

For the FastAPI service, keep using:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The bot uses polling in this first version, so it does not need a public webhook URL yet.

## Safety boundary

Lymewire is a research and patient-support assistant. It does not diagnose, prescribe, or replace urgent medical care. Emergency or worsening symptoms should be handled through local emergency medical services.
