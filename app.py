from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI(title="Lyme AI")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Question(BaseModel):
    question: str

@app.get("/")
def root():
    return {
        "project": "Lyme AI",
        "status": "online"
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
