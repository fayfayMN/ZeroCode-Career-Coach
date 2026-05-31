"""Career Coach — Streamlit entry point.

A focused, recruiter-designed job-search assistant. Users supply their own API
key in the sidebar — no server-side credentials required.

Supported providers:
  * Groq  (free tier, fast) — https://console.groq.com/keys
  * OpenRouter (pay-per-use, 200+ models) — https://openrouter.ai/keys
  * Ollama (local, private) — run `ollama serve` first

Run locally:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from src.config import settings
from src.llm import client
from src.orchestrator.session import CareerFile
from src.ui import steps

st.set_page_config(page_title="ZeroCode Career Coach", page_icon="🎯", layout="wide")

# --- session state -----------------------------------------------------------
if "cf" not in st.session_state:
    st.session_state.cf = CareerFile()
cf: CareerFile = st.session_state.cf

STEPS = {
    "1 · Setup": steps.step_setup,
    "2 · Fit & Strategy": steps.step_fit,
    "3 · Tailor Application": steps.step_tailor,
    "4 · Interview Coach": steps.step_coach,
    "5 · Career Dossier": steps.step_dossier,
}

# Preset options shown in the model dropdown.
_PROVIDER_PRESETS = {
    "Groq (free tier)": {
        "provider": "hosted",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    "OpenRouter": {
        "provider": "hosted",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
    },
    "Ollama (local)": {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "qwen3:14b-q4_K_M",
    },
}

# --- sidebar -----------------------------------------------------------------
with st.sidebar:
    st.title("🎯 ZeroCode Career Coach")
    st.caption("Bring your own API key — nothing is stored server-side.")

    st.divider()
    st.subheader("Model setup")

    preset_name = st.selectbox("Provider", list(_PROVIDER_PRESETS.keys()))
    preset = _PROVIDER_PRESETS[preset_name]

    # Keys include preset_name so widgets reset their defaults when provider changes.
    _k = preset_name.replace(" ", "_").replace("(", "").replace(")", "")

    if preset["provider"] == "ollama":
        ollama_host = st.text_input(
            "Ollama host",
            value=preset["base_url"],
            key=f"{_k}_host",
            help="WSL2 forwards port 11434 automatically — localhost:11434 works from Windows too.",
        )

        # Fetch models from Ollama when the host changes or on first load.
        # Keep the last-known-good list in session state so the selectbox
        # never flickers or collapses to a single entry on transient failures.
        _cache_key = f"_models_{_k}"
        if _cache_key not in st.session_state or st.session_state.get(f"_last_host_{_k}") != ollama_host:
            try:
                import requests as _requests
                _resp = _requests.get(f"{ollama_host}/api/tags", timeout=5)
                _resp.raise_for_status()
                _tags = _resp.json()
                st.session_state[_cache_key] = {
                    "chat": [m["name"] for m in _tags.get("models", [])
                             if not m["name"].startswith("nomic-")],
                    "embed": [m["name"] for m in _tags.get("models", [])
                              if "embed" in m["name"]],
                }
            except Exception:
                # Keep previous list if available; otherwise fall back to preset.
                if _cache_key not in st.session_state:
                    st.session_state[_cache_key] = {"chat": [], "embed": []}
            st.session_state[f"_last_host_{_k}"] = ollama_host

        _chat_models = st.session_state[_cache_key]["chat"]
        _embed_models = st.session_state[_cache_key]["embed"]

        # Always use a selectbox — fall back to [preset default] so the widget
        # type never flips and session state survives transient failures.
        _default_chat = preset["model"]
        if not _chat_models:
            _chat_models = [_default_chat]
        _idx = _chat_models.index(_default_chat) if _default_chat in _chat_models else 0
        ollama_model = st.selectbox(
            "Chat model", _chat_models, index=_idx, key=f"{_k}_model",
            help="Lists models pulled in Ollama. Pull more with `ollama pull <name>`.",
        )

        _default_embed = "nomic-embed-text:latest"
        if not _embed_models:
            _embed_models = [_default_embed]
        _eidx = next((i for i, m in enumerate(_embed_models) if "nomic" in m), 0)
        ollama_embed = st.selectbox(
            "Embed model", _embed_models, index=_eidx, key=f"{_k}_embed",
            help="Used for semantic match scoring. Leave on nomic-embed-text unless you pulled another.",
        )

        # Apply to settings
        settings.provider = "ollama"
        settings.ollama_host = ollama_host
        settings.chat_model = ollama_model
        settings.embed_model = ollama_embed or "nomic-embed-text"
        api_key_ok = True  # no key needed for local Ollama
    else:
        api_key = st.text_input(
            "API key",
            type="password",
            placeholder="Paste your Groq / OpenRouter key here",
            key=f"{_k}_apikey",
            help="Your key is used only for this session and never stored.",
        )
        base_url = st.text_input("Base URL", value=preset["base_url"], key=f"{_k}_base_url")
        model_name = st.text_input("Model", value=preset["model"], key=f"{_k}_model")
        # Apply to settings
        settings.provider = "hosted"
        settings.hosted_api_key = api_key
        settings.hosted_base_url = base_url
        settings.hosted_chat_model = model_name
        api_key_ok = bool(api_key)

    if not api_key_ok:
        st.warning("Paste an API key above to enable the AI features.")

    if st.button("🔌 Check connection"):
        # Refresh the model cache so the dropdown picks up newly pulled models.
        for _k in list(st.session_state.keys()):
            if _k.startswith("_models_") or _k.startswith("_last_host_"):
                del st.session_state[_k]
        ok, msg = client.health()
        (st.success if ok else st.error)(msg)

    st.divider()
    choice = st.radio("Steps", list(STEPS.keys()), label_visibility="collapsed")

    st.divider()
    if cf.resume.raw_text:
        st.caption(f"📄 Resume: {cf.resume.filename or 'loaded'}")
    if cf.jd.raw_text:
        st.caption(f"💼 {cf.title_line}")
    if st.button("🗑️ Reset everything"):
        st.session_state.cf = CareerFile()
        st.rerun()

# --- main --------------------------------------------------------------------
STEPS[choice](cf)
