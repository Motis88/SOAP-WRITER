"""
FastAPI application entry point for the Veterinary SOAP Writer.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router

app = FastAPI(
    title="Veterinary SOAP Writer",
    description=(
        "Converts audio / text / IDEXX PDF into a structured veterinary SOAP note. "
        "Strictly transcription and extraction — no medical reasoning."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
