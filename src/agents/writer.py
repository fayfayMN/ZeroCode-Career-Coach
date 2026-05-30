"""Agent 2 — Writer (Application Tailor).

Turns the resume + JD + fit report into a tailored application kit: rewritten
bullets (ATS keywords + quantified + authentic voice), a personable cover
letter, and optional LinkedIn copy. A humanize pass keeps it sounding like a
real person.
"""
from __future__ import annotations

from ..contracts.schemas import ApplicationKit, FitReport, JobDescription, ResumeDoc
from .base import Agent


class Writer(Agent):
    persona = (
        "You are the Writer agent in Career Coach: a career storyteller who makes "
        "candidates sound like the strongest, most authentic version of themselves "
        "while staying 100% truthful to their real experience."
    )
    skills = ("resume-tailoring", "ats-keywords", "cover-letter", "voice-humanize")

    def build(
        self,
        resume: ResumeDoc,
        jd: JobDescription,
        fit: FitReport | None,
        personality_notes: str = "",
    ) -> ApplicationKit:
        missing = ", ".join(fit.keywords.missing) if fit else ""
        matched = ", ".join(fit.keywords.matched) if fit else ""

        prompt = f"""Create a tailored application kit for this candidate and role.

# JOB
Title: {jd.title}  |  Company: {jd.company}
JOB DESCRIPTION:
{jd.raw_text[:6000]}

# RESUME
{resume.raw_text[:6000]}

# CANDIDATE PERSONALITY / VOICE NOTES
{personality_notes or "(none provided — keep voice natural and specific)"}

# KEYWORD CONTEXT (from the recruiter analysis)
Already present: {matched or "n/a"}
Worth adding IF TRUE for the candidate: {missing or "n/a"}

Produce an ApplicationKit:
- bullets: rewrite 4-8 of the candidate's real bullets using the XYZ formula. For each give
  original, improved, keywords_used, and a one-line rationale. Do NOT invent metrics — if a
  number is needed, leave a clear [bracketed placeholder] for the candidate to fill.
- cover_letter: 3 short paragraphs (~250-300 words), personable, specific to this company,
  reflecting the candidate's voice notes. No clichés.
- linkedin_headline: one punchy line.
- linkedin_about: a short first-person summary (3-4 sentences).
- voice_notes: 2-3 notes on how you preserved the candidate's authentic personality.
Apply the humanize rules: vary rhythm, kill buzzwords, stay truthful."""

        return self.run_json(prompt, ApplicationKit, temperature=0.6)
