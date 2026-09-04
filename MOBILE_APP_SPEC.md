# LymeWire Mobile App Spec

## Goal

LymeWire will become a cross-platform product for iOS, Android, and web. Telegram remains the MVP and early testing surface, but the long-term interface should be a dedicated app where users can move between care navigation, research cards, treatment questions, guideline comparisons, trial discovery, and personal doctor-brief preparation.

## Product promise

Find the signal.

LymeWire helps users turn scattered Lyme, PTLDS, and tick-borne illness information into safer next steps. It should not diagnose, prescribe, promise cure, rank doctors by unverifiable success rates, or replace urgent care.

## Core users

- Patients with confirmed Lyme disease.
- People with suspected Lyme or tick-borne illness.
- People with persistent symptoms after treatment.
- Caregivers and advocates.
- Clinicians or researchers who want quick evidence summaries.

## MVP surfaces

### 1. Chat

A warm AI chat interface with strong memory inside the current session and clear safety boundaries.

Must support:
- ordinary questions,
- follow-ups like "dedim ya" or "ustte var",
- panic-safe replies,
- evidence-heavy mode suggestions.

### 2. Wires

The app should show the product as a network of focused wires:

- Care Wire: doctor, hospital, center, and treatment-route navigation.
- Research Wire: PubMed paper search and Evidence Cards.
- Treatment Wire: treatment claim review, benefit/risk framing, uncertainty labels.
- Guideline Wire: CDC, NICE, IDSA/AAN/ACR, ILADS summaries and comparisons.
- Trial Wire: ClinicalTrials.gov discovery and trial status summaries.
- Doctor Brief Wire: appointment preparation and clinician-ready summary.
- Calm Wire: panic and fear support without dismissing symptoms.

### 3. Personal timeline

Users should be able to enter and edit:

- symptom start date,
- tick exposure or rash history,
- test results,
- antibiotics and other treatments,
- CRP/ESR and key labs,
- neurologic, cardiac, joint, skin, and systemic symptoms,
- questions for the next clinician visit.

The first version can store this locally or in user-controlled export form. Medical record sync must wait for a privacy/legal design pass.

### 4. Doctor brief export

The app should generate a concise clinician-facing summary:

- one paragraph patient story,
- timeline,
- tests,
- treatments tried,
- current top symptoms,
- objective findings,
- red flags,
- questions for the visit.

Export targets:
- copy text,
- PDF later,
- share sheet later.

## Platform strategy

Recommended first build path:

1. Keep Telegram bot as working MVP.
2. Build a responsive web app backed by the same API.
3. Wrap or rebuild with React Native / Expo for iOS and Android.
4. Keep shared prompts, commands, and wire logic in the backend so the app and Telegram do not drift.

Why this path:
- fastest path to web + iOS + Android,
- easier iteration before App Store review,
- one shared product brain,
- lower cost while testing with early users.

## Mobile navigation

Suggested tabs:

- Chat
- Wires
- Timeline
- Brief
- Sources

The first screen should be usable immediately, not a marketing page.

## Home screen

Primary screen:

- Brand: LymeWire
- Slogan: Find the signal.
- One chat input.
- Quick actions:
  - Care route
  - Research paper
  - Treatment claim
  - Compare guidelines
  - Prepare doctor brief
  - Calm mode

## Safety requirements

The app must always keep these boundaries:

- no diagnosis,
- no prescribing,
- no medication changes,
- no fake certainty,
- no guaranteed treatment success claims,
- no doctor ranking unless backed by objective and cited public data,
- emergency symptom escalation.

Emergency warning examples:

- chest pain,
- fainting,
- severe shortness of breath,
- new facial droop,
- limb weakness,
- meningitis-like symptoms,
- severe confusion,
- rapidly worsening fever,
- severe antibiotic-associated diarrhea or blood in stool,
- self-harm risk.

## Data and privacy

Near-term:

- keep user-entered timeline minimal,
- make export user-controlled,
- do not claim medical record integration yet,
- avoid storing sensitive health data without explicit consent and a real privacy architecture.

Later:

- account system,
- consent-driven health data import,
- audit log,
- encrypted storage,
- deletion/export rights,
- legal review for Turkey, UK/EU, and US paths.

## Brand and icon direction

App icon must be simple enough for iOS, Android, Telegram, GitHub, Railway, favicon, and future merch.

Current safe direction:

- dark graphite background,
- lime/mint LymeWire mark,
- minimal shape,
- no generic medical cross,
- no awareness-ribbon dependency,
- no scary disease imagery.

Open decision:

- final logo candidate is not locked yet. Do not overwrite public assets with a generated concept until the selected mark is confirmed.

## V1 acceptance criteria

LymeWire V1 is ready when:

- Telegram bot runs on Railway production.
- Bot profile name and descriptions are LymeWire.
- `/care`, `/research`, `/paper`, `/treatment`, `/compare`, `/guideline`, `/trial`, `/doctorbrief`, `/calm`, `/safety` work.
- API exposes `/`, `/health`, `/wires`, and `/ask`.
- README explains setup and commands.
- Architecture and mobile spec are present.
- Brand kit exists.
- App icon candidate is selected and exported.
- At least three real test conversations are run and reviewed.

## Next build tasks

1. Create a shared backend router for wires so Telegram and future app share logic.
2. Add `/ask` retrieval over curated knowledge files.
3. Add timeline intake schema.
4. Add doctor brief export endpoint.
5. Create web app prototype.
6. Convert web prototype into mobile-ready React Native / Expo app.
7. Add privacy and account design before any durable health storage.
