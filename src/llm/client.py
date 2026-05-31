"""Unified LLM client: chat + embeddings.

Two providers behind one interface:
  * "ollama"  -> local Ollama REST API (free, private; default)
  * "hosted"  -> any OpenAI-compatible Chat Completions endpoint
                 (Groq / OpenRouter free tiers) for public cloud demos.

Implemented with `requests` only, so the app runs even if the optional
`ollama` python package isn't installed. JSON-mode helpers make agents return
strict, parseable structured output.
"""
from __future__ import annotations

import json
import re
from typing import Any

import requests

from ..config import settings


class LLMError(RuntimeError):
    """Raised when the model backend is unreachable or returns an error."""


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #
def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    json_mode: bool = False,
) -> str:
    """Send a chat conversation and return the assistant's text reply.

    `messages` is a list of {"role": "system"|"user"|"assistant", "content": str}.
    When `json_mode` is True we ask the backend to emit a JSON object.
    """
    temp = settings.temperature if temperature is None else temperature
    if settings.uses_ollama:
        raw = _ollama_chat(messages, temp, json_mode)
    else:
        raw = _hosted_chat(messages, temp, json_mode)
    return _strip_think(raw)


def _strip_think(text: str) -> str:
    """Remove <think>...</think> reasoning blocks emitted by thinking models
    (e.g. qwen3, deepseek-r1) so they never leak into answers or break JSON."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Also drop an unclosed leading <think> with no closing tag.
    cleaned = re.sub(r"^\s*<think>.*$", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()


def _ollama_chat(messages: list[dict[str, str]], temperature: float, json_mode: bool) -> str:
    url = f"{settings.ollama_host}/api/chat"
    payload: dict[str, Any] = {
        "model": settings.chat_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        payload["format"] = "json"
    try:
        resp = requests.post(url, json=payload, timeout=settings.request_timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network
        raise LLMError(
            f"Could not reach Ollama at {settings.ollama_host}. "
            f"Is `ollama serve` running and is '{settings.chat_model}' pulled? ({exc})"
        ) from exc
    data = resp.json()
    return data.get("message", {}).get("content", "")


def _hosted_chat(messages: list[dict[str, str]], temperature: float, json_mode: bool) -> str:
    if not settings.hosted_api_key:
        raise LLMError(
            "No API key provided. Paste your Groq or OpenRouter key in the sidebar "
            "Model setup section to enable AI features."
        )
    url = f"{settings.hosted_base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": settings.hosted_chat_model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {settings.hosted_api_key}"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=settings.request_timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network
        raise LLMError(f"Hosted provider request failed: {exc}") from exc
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------- #
# Structured (JSON) chat
# --------------------------------------------------------------------------- #
def chat_json(
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
) -> dict[str, Any]:
    """Chat and parse the reply as a JSON object, tolerating code fences."""
    raw = chat(messages, temperature=temperature, json_mode=True)
    return _extract_json(raw)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    # Strip markdown code fences if the model added them.
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last resort: grab the outermost {...} block.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    raise LLMError(f"Model did not return valid JSON. Got:\n{text[:500]}")


# --------------------------------------------------------------------------- #
# Embeddings (used by the deterministic semantic match score)
# --------------------------------------------------------------------------- #
def embed(text: str) -> list[float]:
    """Return an embedding vector for `text`.

    Only the Ollama provider supports local embeddings here; hosted demos fall
    back to a keyword-only score in scoring.py when this raises.
    """
    if not settings.uses_ollama:
        raise LLMError("Embeddings require the local Ollama provider.")
    url = f"{settings.ollama_host}/api/embeddings"
    payload = {"model": settings.embed_model, "prompt": text}
    try:
        resp = requests.post(url, json=payload, timeout=settings.request_timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network
        raise LLMError(f"Embedding request failed: {exc}") from exc
    return resp.json().get("embedding", [])


# --------------------------------------------------------------------------- #
# Health check
# --------------------------------------------------------------------------- #
def health() -> tuple[bool, str]:
    """Return (ok, message) describing whether the backend is usable."""
    try:
        if settings.uses_ollama:
            resp = requests.get(f"{settings.ollama_host}/api/tags", timeout=10)
            resp.raise_for_status()
            tags = [m.get("name", "") for m in resp.json().get("models", [])]
            have_chat = any(settings.chat_model.split(":")[0] in t for t in tags)
            if not have_chat:
                return False, (
                    f"Ollama is running but '{settings.chat_model}' is not pulled. "
                    f"Run: ollama pull {settings.chat_model}"
                )
            return True, f"Ollama OK — models: {', '.join(tags) or 'none'}"
        # hosted
        if not settings.hosted_api_key:
            return False, "No API key provided — paste your Groq or OpenRouter key in the sidebar."
        chat([{"role": "user", "content": "ping"}], temperature=0)
        return True, f"Hosted provider OK ({settings.hosted_chat_model})"
    except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
        return False, str(exc)
