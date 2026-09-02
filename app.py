from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

BRAND_NAME = os.getenv("APP_NAME", "LymeWire")

app = FastAPI(
    title=f"{BRAND_NAME} API",
    description="Evidence-aware Lyme and tick-borne illness AI network.",
    version="0.3.0",
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Question(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "brand": BRAND_NAME,
        "status": "online",
        "network": "LymeWire evidence and care-navigation wires",
        "entrypoints": {
            "telegram": "primary MVP interface",
            "ask": "/ask",
            "health": "/health",
            "wires": "/wires",
        },
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "brand": BRAND_NAME,
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
                "id": "doctorbrief",
                "name": "Doctor Brief Wire",
                "purpose": "Clinician-facing appointment summaries.",
            },
        ],
    }


@app.post("/ask")
def ask(data: Question):
    response = client.responses.create(
        model=os.getenv("MODEL", "gpt-5.5"),
        input=data.question,
    )

    return {
        "brand": BRAND_NAME,
        "wire": "ask",
        "answer": response.output_text,
    }
