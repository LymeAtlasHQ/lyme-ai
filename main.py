import os

from fastapi import FastAPI

from core.product import AskRequest, TimelineDraft, answer_product, build_doctor_brief, timeline_schema

BRAND_NAME = os.getenv("APP_NAME", "LymeWire")

app = FastAPI(
    title=f"{BRAND_NAME} API",
    description="Evidence-aware Lyme and tick-borne illness AI network.",
    version="0.4.0",
)


@app.get("/")
def root():
    return {
        "brand": BRAND_NAME,
        "status": "online",
        "message": "Welcome to LymeWire.",
        "network": "LymeWire evidence and care-navigation wires",
        "entrypoints": {
            "telegram": "primary MVP interface",
            "ask": "/ask",
            "brief": "/brief",
            "health": "/health",
            "timeline_schema": "/timeline/schema",
            "wires": "/wires",
        },
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "brand": BRAND_NAME,
        "product_api": "wire-aware",
    }


@app.get("/wires")
def wires():
    return {
        "brand": BRAND_NAME,
        "wires": [
            {
                "id": "care",
                "name": "Care Wire",
                "purpose": "Treatment, doctor, and center navigation without fake success-rate claims.",
            },
            {
                "id": "research",
                "name": "Research Wire",
                "purpose": "PubMed search, paper analysis, and evidence cards.",
            },
            {
                "id": "guideline",
                "name": "Guideline Wire",
                "purpose": "CDC, NICE, IDSA, ILADS, and official-source summaries.",
            },
            {
                "id": "trial",
                "name": "Trial Wire",
                "purpose": "ClinicalTrials.gov study discovery and trial status cards.",
            },
            {
                "id": "compare",
                "name": "Compare Wire",
                "purpose": "Side-by-side comparison of guidelines, sources, studies, or claims.",
            },
            {
                "id": "doctorbrief",
                "name": "Doctor Brief Wire",
                "purpose": "Clinician-facing appointment summaries.",
            },
            {
                "id": "calm",
                "name": "Calm Wire",
                "purpose": "Low-alarm support in panic moments with urgent red-flag screening.",
            },
        ],
    }


@app.post("/ask")
async def ask(data: AskRequest):
    return await answer_product(data)


@app.get("/timeline/schema")
def get_timeline_schema():
    return timeline_schema()


@app.post("/brief")
def brief(data: TimelineDraft):
    return {
        "brand": BRAND_NAME,
        "wire": "doctorbrief",
        "brief": build_doctor_brief(data),
    }
