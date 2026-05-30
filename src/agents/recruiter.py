"""Agent 1 — Recruiter (Fit & Strategy Analyst).

Screens the application like a real technical recruiter, then hands the seeker
an honest verdict + a concrete action plan. The numeric match score comes from
the deterministic scorer; this agent supplies the qualitative judgement and
merges the two into a FitReport.
"""
from __future__ import annotations

from ..contracts.schemas import FitReport, JobDescription, ResumeDoc
from ..orchestrator.scoring import compute_match
from .base import Agent


class Recruiter(Agent):
    persona = (
        "You are the Recruiter agent in Career Coach. You give job seekers the "
        "unvarnished, expert read a great technical recruiter would — honest, "
        "specific, and actionable."
    )
    skills = ("fit-analysis", "ats-keywords")

    def analyze(
        self, resume: ResumeDoc, jd: JobDescription, personality_notes: str = ""
    ) -> FitReport:
        # 1) deterministic, explainable score + keyword gap
        breakdown, gap = compute_match(jd.raw_text, resume.raw_text)

        # 2) qualitative judgement from the LLM
        prompt = f"""Assess this candidate against the job, as a recruiter.

# JOB
Title: {jd.title or "(unknown)"}
Company: {jd.company or "(unknown)"}
Company info: {jd.company_info or "(none provided)"}

JOB DESCRIPTION:
{jd.raw_text[:6000]}

# CANDIDATE RESUME
{resume.raw_text[:6000]}

# CANDIDATE'S OWN NOTES (personality / what they want)
{personality_notes or "(none provided)"}

# PRE-COMPUTED MATCH (deterministic — do not recompute the numbers)
Overall match: {breakdown.overall}/100
Matched keywords: {", ".join(gap.matched) or "none"}
Missing keywords: {", ".join(gap.missing) or "none"}

Produce a FitReport. Fill ONLY the qualitative fields you are best at:
- strengths: 3-6 concrete green flags, each citing resume/JD evidence.
- weaknesses: 3-6 honest gaps/red flags (esp. missing must-have keywords).
- culture_fit_questions: 3-5 sharp self-reflection questions tied to THIS role/company.
- new_grad_friendly: one or two sentences on early-career friendliness.
- action_plan: 4-6 prioritised, concrete steps (today / this week / before applying).
- summary: a 2-3 sentence recruiter's verdict (would this pass a screen? why?).
Leave the score and keywords fields as empty defaults; they are filled separately."""

        report = self.run_json(prompt, FitReport)

        # 3) merge: trust deterministic numbers + keywords over the model's
        report.score = breakdown
        report.keywords = gap
        return report
