"""Local speech-to-text using faster-whisper (no API key, runs offline).

The Whisper model is loaded lazily and cached, since loading is the slow part.
`transcribe_bytes` accepts raw audio bytes (as produced by streamlit-mic-recorder)
and returns the recognised text.
"""
from __future__ import annotations

import io
import tempfile
from functools import lru_cache

from ..config import settings


@lru_cache(maxsize=2)
def _get_model(device: str, compute_type: str):
    # Imported lazily so the rest of the app runs without faster-whisper installed.
    from faster_whisper import WhisperModel

    return WhisperModel(settings.whisper_model, device=device, compute_type=compute_type)


def _transcribe_path(tmp_path: str) -> str:
    """Transcribe a file, preferring the configured device, falling back to CPU.

    GPU failures often surface only at encode time (e.g. missing libcublas), so
    we catch broadly and retry on CPU/int8, which has no extra dependencies.
    """
    try:
        model = _get_model(settings.whisper_device, settings.whisper_compute)
        segments, _info = model.transcribe(tmp_path, beam_size=1)
        return " ".join(seg.text.strip() for seg in segments).strip()
    except Exception:  # noqa: BLE001 - GPU/runtime issues -> CPU fallback
        if settings.whisper_device == "cpu":
            raise
        model = _get_model("cpu", "int8")
        segments, _info = model.transcribe(tmp_path, beam_size=1)
        return " ".join(seg.text.strip() for seg in segments).strip()


def transcribe_bytes(audio_bytes: bytes) -> str:
    """Transcribe raw audio bytes (wav/webm/mp3) to text."""
    if not audio_bytes:
        return ""
    # faster-whisper accepts a file path or a binary stream; use a temp file for
    # broad format support (webm/wav from the browser mic).
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        return _transcribe_path(tmp_path)
    finally:
        import os

        try:
            os.remove(tmp_path)
        except OSError:
            pass


def transcribe_stream(buf: io.BytesIO) -> str:
    return transcribe_bytes(buf.getvalue())
