import os
import tempfile

_model = None
_model_size = os.getenv("WHISPER_MODEL", "base")


def _get_model():
    global _model
    if _model is None:
        import whisper
        _model = whisper.load_model(_model_size)
    return _model


async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    model = _get_model()

    ext = os.path.splitext(filename)[1].lower() or ".webm"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(
            tmp_path,
            language=None,   # auto-detect Hebrew / English / mixed
            task="transcribe",
            fp16=False,
        )
        return result["text"].strip()
    finally:
        os.unlink(tmp_path)
