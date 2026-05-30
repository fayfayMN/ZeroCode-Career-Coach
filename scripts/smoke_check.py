"""Quick pre-flight check: is the model backend reachable and ready?

    python scripts/smoke_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings  # noqa: E402
from src.llm import client  # noqa: E402


def main() -> int:
    print(f"Provider : {settings.provider}")
    if settings.uses_ollama:
        print(f"Host     : {settings.ollama_host}")
        print(f"Chat     : {settings.chat_model}")
        print(f"Embed    : {settings.embed_model}")
    ok, msg = client.health()
    print(("✅ " if ok else "❌ ") + msg)

    if ok:
        try:
            reply = client.chat([{"role": "user", "content": "Reply with the single word: ready"}])
            print(f"Sample reply: {reply.strip()[:120]}")
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️  Chat call failed: {exc}")
            return 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
