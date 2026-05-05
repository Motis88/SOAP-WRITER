"""
STT Service — wraps OpenAI Whisper for audio-to-text transcription.
Supports Hebrew, English, and mixed audio.
No medical reasoning is performed here.
"""

from __future__ import annotations

import io
import tempfile
import os
from typing import Optional


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe audio bytes using Whisper.

    Returns:
        {"text": str, "language": str | None}
    """
    try:
        import whisper  # lazy import – not installed in CI
    except ImportError:
        return {"text": "[Whisper not installed — install openai-whisper]", "language": None}

    suffix = os.path.splitext(filename)[-1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path, task="transcribe")
        return {
            "text": result.get("text", "").strip(),
            "language": result.get("language"),
        }
    finally:
        os.unlink(tmp_path)
