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
        ollama_model = st.text_input(
            "Chat model", value=preset["model"], key=f"{_k}_model",
            help="Run: ollama pull <model-name>",
        )
        ollama_embed = st.text_input(
            "Embed model (for semantic scoring)",
            value="nomic-embed-text",
            key=f"{_k}_embed",
            help="Run: ollama pull nomic-embed-text  (leave blank to skip semantic scoring)",
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
