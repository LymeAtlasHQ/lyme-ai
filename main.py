from fastapi import FastAPI

app = FastAPI(
    title="Lyme AI",
    description="AI platform for evidence-based Lyme disease research.",
    version="0.1.0",
)


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
