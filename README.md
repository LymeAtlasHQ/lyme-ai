# lyme-ai

AI systems for evidence-based Lyme disease research and knowledge management.

## Telegram bot

The Lymewire Telegram bot entrypoint is `telegram_bot.py`.

### Current capabilities

- General Lyme and tick-borne illness Q&A with safety boundaries.
- `/symptoms` for symptom intake and clinician-facing summary structure.
- `/doctorbrief` for appointment preparation.
- `/paper` for PubMed PMID/search-based article analysis.
- `/research` for PubMed search plus a short evidence map.
- `/treatment` for PubMed-backed treatment-claim evidence/risk cards.
- `/compare` for PubMed-backed side-by-side comparison of guidelines, organizations, studies, or claims.
- `/guideline` for seeded official-source summaries of IDSA, ILADS, CDC, or NICE guideline pages.
- `/trial` for ClinicalTrials.gov study search and trial status summaries.
- `/source` for source-aware answers.
- `/calm` for anxiety/panic-safe support.
- `/safety` for emergency warning boundaries.


### Answer quality layer

The bot is tuned to avoid bland, generic medical replies. Ordinary Lyme/tick-borne illness answers should now follow the MVP quality bar:

- Kisa cevap
- Kanit ve belirsizlik
- Ne takip edilmeli
- Doktora sorulacak iyi sorular
- Guvenlik / aciliyet

If a draft answer is too short or exits with a generic “ask a doctor” style response, the bot runs a quality repair pass before sending it. The repair pass must stay safe: no diagnosis, no prescribing, no invented sources, and no fake certainty.

### Evidence Card format

For `/paper`, `/research`, and `/treatment`, the bot tries to retrieve PubMed records and answer with an Evidence Card structure. `/compare` uses a related Comparison Card structure:

- Bottom line
- Evidence Card
- What was retrieved
- What it supports
- What it does NOT prove
- Risks / caveats
- Practical next step

The bot should include central PMID links when available and label evidence strength as High, Moderate, Low, or Very low.

Known IDSA/ILADS comparison queries are seeded with the IDSA/AAN/ACR 2020 guideline PubMed record, the ILADS 2014 guideline PubMed record, a recent PTLDS systematic review, and official guideline pages so the comparison does not fall back to an empty PubMed search.

### Required environment variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
MODEL=gpt-5.5
APP_NAME=Lymewire
```

Optional NCBI/PubMed metadata:

```bash
NCBI_TOOL_NAME=lymewire
NCBI_EMAIL=you@example.com
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

The bot uses polling in this version, so it does not need a public webhook URL yet.

### Example Telegram prompts

```text
/paper 38606630
/paper post-treatment Lyme disease syndrome randomized trial
/research chronic Lyme antibiotic retreatment trial
/treatment long-term antibiotics post-treatment Lyme disease syndrome
/compare IDSA vs ILADS chronic Lyme treatment
/guideline CDC Lyme treatment
/guideline NICE Lyme disease ongoing symptoms
/trial post-treatment Lyme disease syndrome
/trial Lyme vaccine
/doctorbrief 3 weeks doxycycline, diarrhea and fatigue, no fever
/calm I am panicking and my heart is racing
```

## Safety boundary

Lymewire is a research and patient-support assistant. It does not diagnose, prescribe, or replace urgent medical care. Emergency or worsening symptoms should be handled through local emergency medical services.
