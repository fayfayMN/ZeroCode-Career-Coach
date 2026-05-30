"""Developer test for the voice mock-interview pipeline.

Round-trips through the app's OWN voice modules so we exercise real code:
  1. edge-tts (tts.synthesize)  -> speech audio for a sample answer
  2. faster-whisper (stt.transcribe_bytes) -> transcribe it back to text
  3. Coach.evaluate_answer       -> STAR feedback on the (transcribed) answer

The browser mic widget (streamlit-mic-recorder) can't run headless, but it's a
thin wrapper that just hands raw bytes to stt.transcribe_bytes — which is what
we test here.

    ~/cc-venv/bin/python scripts/dev_voice_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ANSWER_SPOKEN = (
    "At my last job I led a team of three engineers to migrate our monolith to "
    "microservices, which cut our deployment time by forty percent."
)
QUESTION = "Tell me about a time you led a technical project."


def main() -> int:
    from src.voice import tts

    print("== 1. edge-tts synthesize ==")
    audio = tts.synthesize(ANSWER_SPOKEN)
    if not audio:
        print("FAIL: edge-tts returned no audio (needs internet). "
              "Voice TTS unavailable; STT can still work from a real mic.")
        return 1
    print(f"OK: {len(audio)} bytes of speech audio")

    print("\n== 2. faster-whisper transcribe (first run downloads the model) ==")
    from src.voice import stt

    text = stt.transcribe_bytes(audio)
    print("transcript:", text)
    if not text.strip():
        print("FAIL: empty transcript")
        return 1

    print("\n== 3. Coach feedback on the transcribed answer ==")
    from src.agents.coach import Coach
    from src.contracts.schemas import JobDescription, ResumeDoc

    jd = JobDescription(raw_text="Engineering Manager. Lead teams, drive migrations.",
                        title="Eng Manager", company="Acme")
    resume = ResumeDoc(raw_text="Led microservices migration; managed 3 engineers.")
    fb = Coach().evaluate_answer(QUESTION, text, jd, resume)
    print("score:", fb.score, "/10")
    print("star_check:", fb.star_check)
    print("improvements:", fb.improvements[:3])
    print("follow_up:", fb.follow_up)

    print("\nVOICE PIPELINE OK ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
