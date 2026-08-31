from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI(
    title="Lyme AI",
    description="AI platform for evidence-based Lyme disease research.",
    version="0.2.0"
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Question(BaseModel):
    question: str

@app.get("/")
def root():
    return {
        "project": "Lyme AI",
        "status": "online",
        "message": "Welcome to Lyme AI."
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.post("/ask")
def ask(data: Question):
    response = client.responses.create(
        model="gpt-5.5",
        input=data.question
    )

    return {
        "answer": response.output_text
    }
