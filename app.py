"""Career Coach — Streamlit entry point.

A focused, recruiter-designed job-search assistant powered by a free local
Ollama model. Three agents (Recruiter, Writer, Coach) + a deterministic
orchestrator walk the seeker from "should I apply?" to a downloadable dossier.

Run locally:
    ollama serve              # in another terminal
    ollama pull qwen2.5:7b
    ollama pull nomic-embed-text
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

# --- sidebar -----------------------------------------------------------------
with st.sidebar:
    st.title("🎯 ZeroCode Career Coach")
    st.caption("Local • private • free (Ollama)")

    choice = st.radio("Steps", list(STEPS.keys()), label_visibility="collapsed")

    st.divider()
    st.caption(f"Provider: **{settings.provider}**")
    if settings.uses_ollama:
        st.caption(f"Model: `{settings.chat_model}`")
    if st.button("🔌 Check model connection"):
        ok, msg = client.health()
        (st.success if ok else st.error)(msg)

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
