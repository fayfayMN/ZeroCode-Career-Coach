"""Central configuration for Career Coach.

Defaults to a free, local Ollama setup. A hosted fallback (Groq / OpenRouter
free tiers) can be enabled with environment variables so the same app can be
deployed to a free public host (e.g. Streamlit Community Cloud) where Ollama
cannot run.

All settings are read from environment variables so they can be supplied via a
local `.env`, the shell, or Streamlit's `secrets.toml` on the cloud.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Auto-load .env from project root if present (no manual export needed).
# This lets users drop a .env file with CC_PROVIDER=hosted + their API key
# and run the app without touching their shell or Streamlit secrets.
try:
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parent.parent
    _env_file = _root / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass  # python-dotenv optional — env vars still work


def _env(name: str, default: str) -> str:
    val = os.environ.get(name)
    return val if val not in (None, "") else default


@dataclass
class Settings:
    # "ollama" (default, local/free) or "hosted" (Groq/OpenRouter for cloud demo)
    provider: str = field(default_factory=lambda: _env("CC_PROVIDER", "ollama").lower())

    # --- Ollama (local) ---
    ollama_host: str = field(default_factory=lambda: _env("CC_OLLAMA_HOST", "http://localhost:11434"))
    chat_model: str = field(default_factory=lambda: _env("CC_CHAT_MODEL", "qwen3:14b-q4_K_M"))
    embed_model: str = field(default_factory=lambda: _env("CC_EMBED_MODEL", "nomic-embed-text"))

    # --- Hosted fallback (OpenAI-compatible Chat Completions API) ---
    # Works with Groq (https://api.groq.com/openai/v1) or OpenRouter
    # (https://openrouter.ai/api/v1). Set CC_PROVIDER=hosted to use it.
    hosted_base_url: str = field(default_factory=lambda: _env("CC_HOSTED_BASE_URL", "https://api.groq.com/openai/v1"))
    hosted_api_key: str = field(default_factory=lambda: _env("CC_HOSTED_API_KEY", ""))
    hosted_chat_model: str = field(default_factory=lambda: _env("CC_HOSTED_CHAT_MODEL", "llama-3.3-70b-versatile"))

    # Generation controls
    temperature: float = field(default_factory=lambda: float(_env("CC_TEMPERATURE", "0.4")))
    request_timeout: int = field(default_factory=lambda: int(_env("CC_TIMEOUT", "180")))
    ollama_num_ctx: int = field(default_factory=lambda: int(_env("CC_NUM_CTX", "8192")))
    hosted_max_tokens: int = field(default_factory=lambda: int(_env("CC_MAX_TOKENS", "4096")))

    # Voice
    whisper_model: str = field(default_factory=lambda: _env("CC_WHISPER_MODEL", "base"))
    # CPU/int8 is the portable default (no CUDA libs required). Set
    # CC_WHISPER_DEVICE=cuda + CC_WHISPER_COMPUTE=float16 to use a GPU; the STT
    # layer auto-falls back to CPU if the GPU libraries can't be loaded.
    whisper_device: str = field(default_factory=lambda: _env("CC_WHISPER_DEVICE", "cpu"))
    whisper_compute: str = field(default_factory=lambda: _env("CC_WHISPER_COMPUTE", "int8"))
    enable_voice: bool = field(default_factory=lambda: _env("CC_ENABLE_VOICE", "1") == "1")

    @property
    def uses_ollama(self) -> bool:
        return self.provider == "ollama"


# Single shared instance.
settings = Settings()
