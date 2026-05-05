import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import transcribe, pdf_route, soap

app = FastAPI(
    title="SOAP Writer API",
    description="Veterinary SOAP record generator — STT + PDF + Structuring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcribe.router)
app.include_router(pdf_route.router)
app.include_router(soap.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SOAP Writer API"}
