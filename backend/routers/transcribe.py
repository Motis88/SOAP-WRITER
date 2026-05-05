from fastapi import APIRouter, UploadFile, File, HTTPException
from services.whisper_service import transcribe_audio

router = APIRouter(prefix="/api", tags=["transcribe"])

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/wav", "audio/mpeg",
    "audio/mp4", "audio/x-m4a", "video/webm",
}


@router.post("/transcribe")
async def transcribe_endpoint(audio: UploadFile = File(...)):
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        text = await transcribe_audio(data, audio.filename or "recording.webm")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")

    return {"text": text}
