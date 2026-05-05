"""
API endpoints for the Veterinary SOAP Writer.

Routes:
  POST /api/transcribe   — audio → text (Whisper STT)
  POST /api/structure    — text  → SOAP note
  POST /api/parse-pdf    — PDF   → lab results
  POST /api/process      — full pipeline: audio/text/PDF → SOAP note
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models import SOAPNote, StructureRequest, TranscribeResponse, PDFParseResponse
from app.services import stt_service, soap_service, pdf_service

router = APIRouter()


# ---------------------------------------------------------------------------
# /transcribe
# ---------------------------------------------------------------------------

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio to text using Whisper.
    Accepts any audio format supported by Whisper (webm, mp3, wav, m4a …).
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")
    result = stt_service.transcribe_audio(audio_bytes, filename=file.filename or "audio.webm")
    return TranscribeResponse(**result)


# ---------------------------------------------------------------------------
# /structure
# ---------------------------------------------------------------------------

@router.post("/structure", response_model=SOAPNote)
async def structure_text(request: StructureRequest):
    """
    Structure free text into a SOAP note (S and O only; A and P are empty).
    No medical reasoning is performed.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    return soap_service.structure_text(request.text)


# ---------------------------------------------------------------------------
# /parse-pdf
# ---------------------------------------------------------------------------

@router.post("/parse-pdf", response_model=PDFParseResponse)
async def parse_pdf(file: UploadFile = File(...)):
    """
    Parse an IDEXX PDF report (ProCyte / Catalyst / SNAP / UA).
    Returns extracted lab results verbatim — no interpretation.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        # Allow octet-stream for broad compatibility
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF file")

    return pdf_service.parse_pdf(pdf_bytes)


# ---------------------------------------------------------------------------
# /process  (full pipeline)
# ---------------------------------------------------------------------------

@router.post("/process", response_model=SOAPNote)
async def process(
    text: str = Form(default=""),
    audio: UploadFile = File(default=None),
    pdf: UploadFile = File(default=None),
):
    """
    Full pipeline endpoint.
    Accepts optional audio (transcribed via Whisper), optional free text,
    and optional PDF (IDEXX lab report).
    Returns a complete SOAP note (S and O; A and P empty).
    """
    combined_text = text.strip()

    # --- STT ---
    if audio is not None:
        audio_bytes = await audio.read()
        if audio_bytes:
            stt_result = stt_service.transcribe_audio(
                audio_bytes, filename=audio.filename or "audio.webm"
            )
            combined_text = (combined_text + "\n" + stt_result["text"]).strip()

    # --- Structure text into SOAP ---
    if combined_text:
        soap_note = soap_service.structure_text(combined_text)
    else:
        soap_note = SOAPNote(flags=["missing_data"])

    # --- PDF parsing ---
    if pdf is not None:
        pdf_bytes = await pdf.read()
        if pdf_bytes:
            pdf_result = pdf_service.parse_pdf(pdf_bytes)
            # Merge lab results into objective
            soap_note.objective.lab_results = pdf_result.lab_results
            for flag in pdf_result.flags:
                if flag not in soap_note.flags:
                    soap_note.flags.append(flag)

    return soap_note
