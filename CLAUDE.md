# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Career Coach — a Streamlit job-search assistant running on a **free local Ollama model**. A
deliberate redesign of an older 7-agent pipeline down to **3 LLM agents + 1 deterministic
orchestrator**. Flow: upload resume + JD → recruiter fit/score → tailored resume & cover letter
→ interview prep + voice mock → one downloadable HTML dossier.

## Environment caveat

This Windows machine currently has **git only** — Python, Ollama, and Node are **not installed**
(the `python.exe` on PATH is the Microsoft Store stub). Nothing here can run until Python 3.11+
and Ollama are installed (`winget install Python.Python.3.12`, `winget install Ollama.Ollama`).
Node is **not** needed.

## Commands

```powershell
# Setup
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Pull local models (one-time). Default chat model is qwen3:14b-q4_K_M.
ollama pull qwen3:14b-q4_K_M ; ollama pull nomic-embed-text

# Run the app
streamlit run app.py                 # http://localhost:8501

# Tests (LLM is mocked — no Ollama required)
pytest                               # whole suite
pytest tests/test_scoring.py         # one file
pytest tests/test_agents.py::test_writer_returns_kit   # one test

# Verify the model backend is reachable/ready
python scripts/smoke_check.py
```

## Architecture (the big picture)

**Two-tier separation is the core idea: deterministic orchestration vs. LLM judgement.**

- `src/orchestrator/` is **LLM-free**. `scoring.py` computes the match score deterministically
  (rapidfuzz keyword coverage + Ollama embedding cosine, with a keyword-only fallback when
  embeddings are unavailable). `session.py` defines `CareerFile`, the single source of truth for
  one application (held in `st.session_state`). `dossier.py` renders the whole `CareerFile` into
  one self-contained HTML file via `templates/dossier.html.j2`. **Numbers and keyword lists come
  from here, never from an agent** — the Recruiter agent's deterministic score/keywords overwrite
  whatever the LLM returns (see `agents/recruiter.py`).

- `src/agents/` is the **LLM tier**. `base.Agent` is the shared pattern: `persona` + a tuple of
  `skills` → `system_prompt()`; `run_json()` calls the LLM in JSON mode and validates against a
  Pydantic model from `contracts/schemas.py`, with one corrective retry (small local models often
  need it). The three agents — `recruiter`, `writer`, `coach` — each subclass `Agent`.

- **"Skills" are prompt modules, not Claude Code skills.** `src/skills/*.md` are distilled expert
  frameworks (ATS rules, XYZ/STAR, scoring rubric, humanize rules). `base.load_skill()` reads them
  (cached) and concatenates them into the agent's system prompt. **To change an agent's behaviour,
  edit the relevant `.md` — usually no Python change is needed.** Each agent declares which modules
  it loads via its `skills` tuple.

- `src/llm/client.py` is the **only** place that talks to a model. One interface, two providers
  selected by `settings.provider`: `ollama` (local REST, default) and `hosted` (any
  OpenAI-compatible endpoint — Groq/OpenRouter — for a free public cloud demo). Embeddings are
  Ollama-only and degrade gracefully. Use `chat`, `chat_json`, `embed`, `health` from here.

- `src/config.py` — all settings come from env vars (`CC_*`) via a single `settings` dataclass
  instance, so the same code runs locally and on Streamlit Cloud (which maps `secrets.toml` →
  env). `CC_PROVIDER=hosted` switches to the cloud path; see `.streamlit/secrets.toml.example`.

- `src/ui/steps.py` holds the five Streamlit step views; `app.py` is a thin shell (sidebar nav +
  session state). `src/voice/` is optional: `stt.py` (local faster-whisper) and `tts.py`
  (edge-tts); both fail soft so the app still works as text-only if the packages or audio are
  unavailable.

## Conventions

- Agents return **validated Pydantic models**, never free text (except the open mock-interview
  chat). Add a contract to `contracts/schemas.py` before adding an agent method that returns it.
- Keep deterministic, reproducible logic (scoring, keyword extraction, file packaging) **out of
  the LLM**. Extend the skill lexicon in `parsers/jd_parser.py:SKILL_LEXICON` rather than asking
  the model to extract keywords.
- Heavy/optional imports (`pdfplumber`, `docx`, `faster_whisper`, `edge_tts`, `numpy`) are
  imported lazily inside functions so core paths and tests run without them.
