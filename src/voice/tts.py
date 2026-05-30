"""Optional text-to-speech so the Coach can read questions aloud.

Uses edge-tts (free, no key). Returns MP3 bytes that Streamlit can play with
st.audio. Falls back silently (returns None) if edge-tts isn't available or
offline.
"""
from __future__ import annotations

import asyncio

DEFAULT_VOICE = "en-US-AriaNeural"


def synthesize(text: str, voice: str = DEFAULT_VOICE) -> bytes | None:
    """Return MP3 bytes for `text`, or None if TTS is unavailable."""
    if not text.strip():
        return None
    try:
        import edge_tts
    except ImportError:
        return None

    async def _run() -> bytes:
        chunks = bytearray()
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.extend(chunk["data"])
        return bytes(chunks)

    try:
        return asyncio.run(_run())
    except Exception:  # noqa: BLE001 - network/runtime; degrade gracefully
        return None
