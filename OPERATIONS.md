# LymeWire Operations Map

## Purpose

This file keeps the connected work tools aligned so LymeWire does not scatter across GitHub, Railway, Linear, Floot, and Telegram.

## Source of truth

Engineering source of truth:

- GitHub repo: `LymeAtlasHQ/lyme-ai`
- Production runtime: Railway project `gregarious-freedom`, service `lyme-ai`
- User-facing MVP: Telegram bot

Planning source of truth:

- GitHub Issues for engineering tasks.
- Linear can mirror the same issues if connected/available.
- Floot can be used for operations dashboards: sales, partnerships, revenue, deals, and recent leads.

## Current GitHub Sprint

Open issues created for the next sprint:

- #5 Finalize logo assets for Telegram, GitHub, web, iOS, and Android
- #6 Run Telegram MVP test plan with first testers
- #7 Add user-owned symptom timeline and doctor brief schema
- #8 Prototype LymeWire web app home screen
- #9 Build shared Wire router for Telegram and future app
- #10 Add curated Knowledge Wire retrieval

## Linear Mirror

If Linear is used, create or mirror these work items:

| Priority | Linear Title | GitHub Issue | Area |
| --- | --- | --- | --- |
| P0 | Finalize logo assets for Telegram, GitHub, web, iOS, and Android | #5 | Brand/App |
| P0 | Run Telegram MVP test plan with first testers | #6 | Telegram/QA |
| P1 | Prototype LymeWire web app home screen | #8 | Web/App |
| P1 | Build shared Wire router for Telegram and future app | #9 | Backend |
| P1 | Add curated Knowledge Wire retrieval | #10 | Research/Sources |
| P2 | Add user-owned symptom timeline and doctor brief schema | #7 | Health Data/Privacy |

## Floot Role

Floot should not replace the medical product backend yet. Use it for internal operations first:

- sales dashboard,
- partnerships pipeline,
- leads,
- revenue/deals tracking,
- operations views for LymeWire Business.

Do not store sensitive health data in Floot until privacy and consent rules are designed.

## Railway Role

Railway runs the current Telegram bot deployment.

Current expected settings:

- Source: `LymeAtlasHQ/lyme-ai`, branch `main`
- Start command: `python telegram_bot.py`
- Required variables: `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `MODEL`, `APP_NAME`, `BOT_DISPLAY_NAME`, `BOT_SHORT_DESCRIPTION`, `BOT_DESCRIPTION`

## GitHub Role

GitHub stores:

- bot code,
- product docs,
- architecture,
- test plan,
- mobile app spec,
- brand kit,
- sprint issues.

## Telegram Role

Telegram is the live MVP and tester interface.

Use Telegram to validate:

- tone,
- answer quality,
- source-card usefulness,
- care route usefulness,
- panic/calm behavior,
- follow-up continuity.

## Immediate Ops Checklist

1. Upload selected logo manually to Telegram BotFather.
2. Mirror GitHub issues #5-#10 into Linear if desired.
3. Run `TEST_PLAN.md` prompts in Telegram.
4. Put failures back into GitHub Issues.
5. Use Floot for business dashboard only, not medical records.
6. Keep Railway deployment green after each commit.
