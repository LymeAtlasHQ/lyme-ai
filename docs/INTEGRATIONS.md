# LymeWire integration ownership

Verified 2026-09-05.

| Service | Role | Status |
| --- | --- | --- |
| GitHub LymeAtlasHQ/lyme-ai | Canonical bot source | Read/write verified |
| Railway | Bot hosting | Existing GitHub deployment pipeline |
| GitLab LymeAtlasHQ/lyme-ai | Supporting project documentation | Access verified; not an automatic mirror |
| Gmail project account | Human-supervised project correspondence | Profile access verified; no mail sent; not connected to bot |
| Healthcare Public Data / PubMed | Research in the development workspace | Search verified |
| Telegram PubMed E-utilities | Runtime literature retrieval | Existing adapter; explicit natural-language routing added |
| ClinicalTrials.gov | Registered-trial retrieval | Existing /trial adapter; not live-tested in this change |
| DailyMed, openFDA, RxNorm | Potential drug reference adapters | Tools available here; not connected to runtime |

## Runtime boundary

ChatGPT connector login does not grant Railway or a public web application the same access. Never export session tokens. Email access and private records are not public chatbot tools. Future runtime integrations require their own supported authentication and user-scoped authorization.

## Research route

Explicit literature requests mentioning Lyme, Borrelia, PTLDS or babesiosis can trigger the existing PubMed adapter without a slash command. Only allowlisted biomedical concepts leave the conversation for that automatic search; names, addresses and contact text are excluded. Unsupported topics use the normal conversation path. Retrieval failures are reported, not replaced with fabricated citations. This is topic search, not guaranteed coverage of the newest literature.

## Next integrations

- Authenticated web chat with per-user data isolation and deletion controls.
- Durable opt-in memory; current Telegram memory is transient.
- Official center verification, separate from literature search.
- Drug label adapter with source date and jurisdiction; no prescribing.
- No automatic cross-repository mirror or email sender is configured.
