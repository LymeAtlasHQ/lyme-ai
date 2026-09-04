# LymeWire Roadmap

## Status

LymeWire is currently a Telegram-first MVP deployed on Railway. The product direction is an evidence and care-navigation network for Lyme disease, PTLDS, and tick-borne illness questions.

## Phase 0: Foundation

Status: mostly done

- GitHub repo exists: `LymeAtlasHQ/lyme-ai`.
- Railway service exists and deploys from `main`.
- Telegram bot runs from `telegram_bot.py`.
- OpenAI and Telegram tokens are configured in Railway variables.
- Brand name changed to LymeWire across user-facing docs and runtime variables.
- API skeleton exists in `app.py` and `main.py`.
- Brand kit exists in `brand/`.

Remaining:

- lock final app icon/logo candidate,
- rename visible Railway service/repo metadata manually if tool support is unavailable,
- run manual Telegram test set and note failures.

## Phase 1: Telegram MVP quality

Status: active

Goal: make the bot useful enough for real tester conversations.

Done:

- `/start`, `/help`, `/safety`, `/symptoms`, `/doctorbrief`, `/paper`, `/research`, `/treatment`, `/compare`, `/guideline`, `/trial`, `/care`, `/source`, `/calm`.
- PubMed retrieval for article, research, treatment, and comparison flows.
- ClinicalTrials.gov discovery for trial flow.
- Seeded guideline lookups for CDC, NICE, IDSA/AAN/ACR, and ILADS.
- Care route mode for Turkey/Izmir and international second-opinion framing.
- Short rolling Telegram context for follow-ups.
- Paragraph-aware Telegram message chunking.
- Quality repair pass for bland answers.
- Bot profile configuration at startup.

Next:

- Add a small test transcript set for common prompts.
- Improve `/care` with live source links when public web search is available.
- Add command examples in Turkish and English.
- Add low-alarm mode for panic-heavy Lyme questions.

## Phase 2: Knowledge Wire

Status: planned

Goal: use curated source files, not only live model memory.

Tasks:

- Create a knowledge index over curated CDC/NICE/IDSA/ILADS/PubMed summaries.
- Add `/ask` retrieval over repo knowledge files.
- Keep citations visible.
- Add source freshness dates.
- Separate official guideline facts from interpretation.

Acceptance:

- User asks a Lyme question.
- Bot retrieves matching source snippets.
- Answer states what source was used and what uncertainty remains.

## Phase 3: Personal Timeline and Doctor Brief

Status: planned

Goal: help users stop repeating their story and prepare better appointments.

Tasks:

- Define timeline schema.
- Add guided intake for symptoms, tests, treatments, CRP/ESR, imaging, and red flags.
- Generate doctor brief from structured timeline.
- Add copy/export flow.
- Do not store durable medical data until privacy design is complete.

Acceptance:

- A user can enter a short health story.
- LymeWire converts it into a clinician-facing summary.
- The output separates facts, questions, and urgent flags.

## Phase 4: Web App

Status: planned

Goal: create the first visual product beyond Telegram.

Tasks:

- Build a responsive web interface.
- Use the Wires model as navigation.
- Add chat, wire cards, source cards, timeline, and doctor brief screen.
- Keep first screen usable immediately.
- Add brand colors and selected logo.

Acceptance:

- Web app opens on desktop and mobile.
- User can ask a question and choose a wire.
- User can create a doctor brief draft.

## Phase 5: iOS and Android

Status: planned

Goal: make LymeWire a daily-use mobile app.

Recommended path:

- React Native / Expo for iOS and Android.
- Shared backend API and shared prompt logic.
- Push notifications later only for user-controlled reminders.
- Local-first timeline until account/privacy layer is ready.

Acceptance:

- Same core actions as Telegram and web.
- App icon and name display correctly.
- Timeline and brief are usable on phone.
- Panic/calm mode is one tap away.

## Phase 6: Trusted Health Data Integration

Status: future, legal/privacy dependent

Goal: optional user-controlled import from wearable or health records.

Important boundary:

- Do not build this as a quick hack.
- It needs consent, authentication, privacy policy, deletion/export rights, encryption, and jurisdiction review.

Possible sources later:

- wearable exports,
- Apple Health / Google Fit style data,
- user-uploaded PDFs/labs,
- future official health-system integrations where legally possible.

## Phase 7: Community and Research Network

Status: future

Goal: LymeWire becomes a peer-to-peer evidence network without becoming misinformation.

Tasks:

- Anonymous story patterns only after privacy design.
- Evidence tags for claims.
- Community questions linked to sources.
- Research scouts for weekly updates.
- Clinician and researcher review paths.

## Immediate checklist

1. Confirm final logo candidate.
2. Export icon sizes for Telegram, GitHub, web, iOS, and Android.
3. Run Telegram test prompts.
4. Add failures to issue list.
5. Create first web app prototype.
6. Keep Railway production green.
