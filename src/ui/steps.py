"""Streamlit step views. Each function renders one step and mutates the
CareerFile held in st.session_state.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from ..agents.coach import Coach
from ..agents.recruiter import Recruiter
from ..agents.writer import Writer
from ..config import settings
from ..contracts.schemas import MockTurn
from ..llm.client import LLMError
from ..orchestrator.dossier import build_dossier_html, dossier_filename
from ..orchestrator.session import CareerFile
from ..parsers.jd_parser import parse_jd
from ..parsers.resume_parser import parse_resume

# Check once at import whether voice packages are available, so we can
# hide the Voice radio on Streamlit Cloud where they aren't installed.
try:
    from streamlit_mic_recorder import mic_recorder  # noqa: F401
    from ..voice.stt import transcribe_bytes  # noqa: F401

    _VOICE_AVAILABLE = True
except ImportError:
    _VOICE_AVAILABLE = False


def _run_agent(label: str, fn):
    """Run an agent call with a spinner and friendly error surfacing."""
    try:
        with st.spinner(label):
            return fn()
    except LLMError as exc:
        st.error(f"Model error: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Something went wrong: {exc}")
    return None


# --------------------------------------------------------------------------- #
# Step 1 — Setup
# --------------------------------------------------------------------------- #
def step_setup(cf: CareerFile) -> None:
    st.header("1 · Setup")
    st.write("Upload your resume, paste the job description, and add any company notes. "
             "Everything else builds on this.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Resume")
        up = st.file_uploader("Resume (PDF / DOCX / TXT)", type=["pdf", "docx", "txt", "md"])
        if up is not None:
            doc = parse_resume(up, filename=up.name)
            cf.resume = doc
            st.success(f"Parsed {up.name} — {len(doc.raw_text)} chars")
        if cf.resume.raw_text:
            with st.expander("Preview parsed resume"):
                st.text(cf.resume.raw_text[:3000])

    with col2:
        st.subheader("💼 Job & Company")
        company = st.text_input("Company name", value=cf.jd.company)
        company_info = st.text_area(
            "Company notes (mission, stage, culture — optional)",
            value=cf.jd.company_info, height=90,
        )
        jd_text = st.text_area("Paste the full job description", value=cf.jd.raw_text, height=220)
        if st.button("Save job description", type="primary"):
            cf.jd = parse_jd(jd_text, company=company, company_info=company_info)
            st.success(f"Saved: {cf.title_line}")

    st.divider()
    st.subheader("🧭 A little about you (optional, but makes everything better)")
    cf.personality_notes = st.text_area(
        "What energises you, your working style, values, what you're looking for. "
        "The Writer and Recruiter use this to keep things authentic.",
        value=cf.personality_notes, height=110,
    )

    if cf.ready_for_fit:
        st.success("✅ Ready — head to **2 · Fit & Strategy**.")
    else:
        st.info("Add both a resume and a job description to continue.")


# --------------------------------------------------------------------------- #
# Step 2 — Fit & Strategy (Recruiter)
# --------------------------------------------------------------------------- #
def step_fit(cf: CareerFile) -> None:
    st.header("2 · Fit & Strategy")
    if not cf.ready_for_fit:
        st.warning("Complete **Step 1** first (resume + job description).")
        return

    if st.button("🔍 Analyze fit", type="primary"):
        cf.fit = _run_agent(
            "Recruiter is screening your application…",
            lambda: Recruiter().analyze(cf.resume, cf.jd, cf.personality_notes),
        )

    fit = cf.fit
    if not fit:
        st.caption("Click **Analyze fit** to get a recruiter's read + match score.")
        return

    # Score
    c = st.columns(5)
    c[0].metric("Overall", f"{fit.score.overall}/100")
    c[1].metric("Must-haves", f"{fit.score.must_have_coverage}%")
    c[2].metric("Nice-to-haves", f"{fit.score.nice_to_have_coverage}%")
    c[3].metric("Semantic", f"{fit.score.semantic_similarity}%")
    c[4].metric("Seniority", f"{fit.score.seniority_fit}%")

    if fit.summary:
        st.info(f"**Recruiter's verdict:** {fit.summary}")

    left, right = st.columns(2)
    with left:
        st.subheader("✅ Strengths")
        for s in fit.strengths:
            st.markdown(f"- {s}")
        st.subheader("🔑 Matched keywords")
        st.write(", ".join(fit.keywords.matched) or "_none_")
    with right:
        st.subheader("⚠️ Gaps to address")
        for w in fit.weaknesses:
            st.markdown(f"- {w}")
        st.subheader("❌ Missing keywords")
        st.write(", ".join(fit.keywords.missing) or "_none_")

    if fit.new_grad_friendly:
        st.caption(f"Early-career friendliness: {fit.new_grad_friendly}")

    if fit.culture_fit_questions:
        st.subheader("🪞 Reflect on your fit")
        for q in fit.culture_fit_questions:
            st.markdown(f"- {q}")

    if fit.action_plan:
        st.subheader("🚀 What you should do next")
        for i, a in enumerate(fit.action_plan, 1):
            st.markdown(f"{i}. {a}")


# --------------------------------------------------------------------------- #
# Step 3 — Tailor Application (Writer)
# --------------------------------------------------------------------------- #
def step_tailor(cf: CareerFile) -> None:
    st.header("3 · Tailor Application")
    if not cf.ready_for_fit:
        st.warning("Complete **Step 1** first.")
        return
    if not cf.fit:
        st.info("Tip: run **Step 2** first so the Writer knows which keywords to weave in.")

    if st.button("✍️ Generate tailored resume + cover letter", type="primary"):
        cf.kit = _run_agent(
            "Writer is tailoring your application…",
            lambda: Writer().build(cf.resume, cf.jd, cf.fit, cf.personality_notes),
        )

    kit = cf.kit
    if not kit:
        return

    tab_bullets, tab_cover, tab_linkedin = st.tabs(["📝 Resume Bullets", "💌 Cover Letter", "🔗 LinkedIn"])

    with tab_bullets:
        for b in kit.bullets:
            with st.container(border=True):
                st.markdown(f"**Before:** {b.original}")
                st.markdown(f"**After:** {b.improved}")
                meta = []
                if b.keywords_used:
                    meta.append("keywords: " + ", ".join(b.keywords_used))
                if b.rationale:
                    meta.append(b.rationale)
                if meta:
                    st.caption(" · ".join(meta))
        if kit.voice_notes:
            with st.expander("How your authentic voice was preserved"):
                for n in kit.voice_notes:
                    st.markdown(f"- {n}")

    with tab_cover:
        st.text_area("Editable — tweak then copy", value=kit.cover_letter, height=320, key="cl_edit")

    with tab_linkedin:
        if kit.linkedin_headline or kit.linkedin_about:
            if kit.linkedin_headline:
                st.markdown(f"**Headline:** {kit.linkedin_headline}")
            if kit.linkedin_about:
                st.write(kit.linkedin_about)
        else:
            st.caption("No LinkedIn copy generated — re-run to include it.")


# --------------------------------------------------------------------------- #
# Step 4 — Interview Coach
# --------------------------------------------------------------------------- #
def step_coach(cf: CareerFile) -> None:
    st.header("4 · Interview Coach")
    if not cf.ready_for_fit:
        st.warning("Complete **Step 1** first.")
        return

    tab_plan, tab_mock = st.tabs(["📚 Prep plan", "🎤 Mock interview"])

    # ---- Prep plan ----
    with tab_plan:
        if st.button("Build interview prep plan", type="primary"):
            cf.interview = _run_agent(
                "Coach is building your prep plan…",
                lambda: Coach().build_plan(cf.resume, cf.jd),
            )
        plan = cf.interview
        if plan:
            st.subheader("Question bank")
            for q in plan.questions:
                with st.expander(f"[{q.stage}] {q.question}"):
                    if q.why_asked:
                        st.markdown(f"*Why asked:* {q.why_asked}")
                    if q.answer_tips:
                        st.markdown(f"*Tips:* {q.answer_tips}")
            if plan.technical_topics:
                st.subheader("Technical topics to review")
                st.markdown("\n".join(f"- {t}" for t in plan.technical_topics))
            if plan.sample_problems:
                st.subheader("Sample problems")
                st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(plan.sample_problems, 1)))

    # ---- Mock interview ----
    with tab_mock:
        _render_mock(cf)


def _render_mock(cf: CareerFile) -> None:
    if not cf.interview or not cf.interview.questions:
        st.info("Build a prep plan first (left tab) to seed the question bank.")
        return

    # Track how many answers have been recorded so the mic key rotates
    # after each submission, preventing stale audio from persisting.
    if "_mock_q_idx" not in st.session_state:
        st.session_state._mock_q_idx = 0

    coach = Coach()
    asked = [t.question for t in cf.mock_transcript]
    current = coach.next_question(cf.interview, asked)

    # show transcript so far
    for turn in cf.mock_transcript:
        with st.chat_message("assistant"):
            st.markdown(f"**Q:** {turn.question}")
        with st.chat_message("user"):
            st.markdown(turn.answer)
        if turn.feedback:
            with st.chat_message("assistant"):
                fb = turn.feedback
                st.markdown(f"**Score {fb.score}/10** — STAR: {fb.star_check}")
                if fb.strengths:
                    st.markdown("**Strengths:** " + "; ".join(fb.strengths))
                if fb.improvements:
                    st.markdown("**Improve:** " + "; ".join(fb.improvements))
                if fb.model_answer:
                    with st.expander("Model answer"):
                        st.write(fb.model_answer)
                if fb.follow_up:
                    st.caption(f"Follow-up to consider: {fb.follow_up}")

    if not current:
        st.success("🎉 You've worked through the question bank. Review feedback above, "
                   "or reset the mock to practise again.")
        if st.button("🔄 Restart mock"):
            cf.mock_transcript = []
            st.session_state._mock_q_idx = 0
            st.rerun()
        return

    st.markdown(f"### 🎙️ Current question\n> {current}")

    # optional: coach reads the question aloud (local-only)
    if _VOICE_AVAILABLE and settings.enable_voice and st.toggle("🔊 Read question aloud"):
        from ..voice.tts import synthesize

        audio = synthesize(current)
        if audio:
            st.audio(audio, format="audio/mp3")

    answer = _capture_answer()
    if answer and st.button("Submit answer", type="primary"):
        fb = _run_agent(
            "Coach is reviewing your answer…",
            lambda: coach.evaluate_answer(current, answer, cf.jd, cf.resume),
        )
        cf.mock_transcript.append(MockTurn(question=current, answer=answer, feedback=fb))
        st.session_state._mock_q_idx += 1
        st.rerun()


def _capture_answer() -> str:
    """Answer via voice (local Whisper) or text. Returns the answer text."""
    mode = "Text"
    if settings.enable_voice and _VOICE_AVAILABLE:
        mode = st.radio("Answer by", ["Voice", "Text"], horizontal=True, key="mock_mode")

    if mode == "Voice":
        from streamlit_mic_recorder import mic_recorder
        from ..voice.stt import transcribe_bytes

        # Rotate the mic key per question so a stale recording never survives
        # a submit rerun.
        import streamlit as _st
        q_idx = _st.session_state.get("_mock_q_idx", 0)
        audio = mic_recorder(
            start_prompt="🎤 Record", stop_prompt="⏹ Stop",
            key=f"mock_mic_{q_idx}", format="wav",
        )

        if audio and audio.get("bytes"):
            try:
                with st.spinner("Transcribing…"):
                    text = transcribe_bytes(audio["bytes"])
                st.text_area("Transcript (edit if needed)", value=text, key=f"voice_tx_{q_idx}")
                return st.session_state.get(f"voice_tx_{q_idx}", text)
            except Exception as exc:
                st.error(f"Transcription failed: {exc}")
        else:
            st.caption("Click Record to capture your answer.")

        return st.text_area("Your answer", key=f"mock_text_backup_{q_idx}")

    return st.text_area("Your answer", key="mock_text")


# --------------------------------------------------------------------------- #
# Step 5 — Career Dossier
# --------------------------------------------------------------------------- #
def step_dossier(cf: CareerFile) -> None:
    st.header("5 · Career Dossier")
    st.write("Bundle everything — JD, company notes, resume, tailored bullets, cover letter, "
             "interview prep, and your mock transcript — into one downloadable HTML file. "
             "Open it in any browser and use **Print → Save as PDF**.")

    done = {
        "Resume": bool(cf.resume.raw_text),
        "Job description": bool(cf.jd.raw_text),
        "Fit report": cf.fit is not None,
        "Application kit": cf.kit is not None,
        "Interview plan": cf.interview is not None,
        "Mock transcript": bool(cf.mock_transcript),
    }
    cols = st.columns(len(done))
    for col, (label, ok) in zip(cols, done.items()):
        col.markdown(f"{'✅' if ok else '⬜'} {label}")

    if not cf.ready_for_fit:
        st.warning("Add at least a resume and job description first.")
        return

    html = build_dossier_html(cf)
    st.download_button(
        "⬇️ Download Career Dossier (.html)",
        data=html.encode("utf-8"),
        file_name=dossier_filename(cf),
        mime="text/html",
        type="primary",
    )
    with st.expander("Preview"):
        components.html(html, height=600, scrolling=True)
