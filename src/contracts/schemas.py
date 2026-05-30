"""Typed contracts shared across agents and the orchestrator.

Agents return JSON validated against these Pydantic models, so the UI and the
dossier builder never deal with free-text handoffs.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
class ResumeDoc(BaseModel):
    """Parsed resume."""
    raw_text: str = ""
    filename: str = ""


class JobDescription(BaseModel):
    """Parsed job description + company context."""
    raw_text: str = ""
    title: str = ""
    company: str = ""
    company_info: str = ""  # optional notes the user pastes about the company


# --------------------------------------------------------------------------- #
# Agent 1 — Recruiter (Fit & Strategy)
# --------------------------------------------------------------------------- #
class ScoreBreakdown(BaseModel):
    overall: int = Field(0, ge=0, le=100)
    must_have_coverage: int = Field(0, ge=0, le=100)
    nice_to_have_coverage: int = Field(0, ge=0, le=100)
    semantic_similarity: int = Field(0, ge=0, le=100)
    seniority_fit: int = Field(0, ge=0, le=100)


class KeywordGap(BaseModel):
    matched: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class FitReport(BaseModel):
    score: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    keywords: KeywordGap = Field(default_factory=KeywordGap)
    strengths: list[str] = Field(default_factory=list)          # green flags
    weaknesses: list[str] = Field(default_factory=list)         # gaps / red flags
    culture_fit_questions: list[str] = Field(default_factory=list)  # self-reflection prompts
    new_grad_friendly: str = ""                                  # assessment text
    action_plan: list[str] = Field(default_factory=list)        # "what you should do"
    summary: str = ""                                           # recruiter's verdict


# --------------------------------------------------------------------------- #
# Agent 2 — Writer (Application Tailor)
# --------------------------------------------------------------------------- #
class TailoredBullet(BaseModel):
    original: str = ""
    improved: str = ""
    keywords_used: list[str] = Field(default_factory=list)
    rationale: str = ""


class ApplicationKit(BaseModel):
    bullets: list[TailoredBullet] = Field(default_factory=list)
    cover_letter: str = ""
    linkedin_headline: str = ""
    linkedin_about: str = ""
    voice_notes: list[str] = Field(default_factory=list)  # how personality was preserved


# --------------------------------------------------------------------------- #
# Agent 3 — Coach (Interview Trainer)
# --------------------------------------------------------------------------- #
class InterviewQuestion(BaseModel):
    stage: str = ""        # "recruiter_screen" | "behavioral" | "technical"
    question: str = ""
    why_asked: str = ""
    answer_tips: str = ""


class InterviewPlan(BaseModel):
    questions: list[InterviewQuestion] = Field(default_factory=list)
    technical_topics: list[str] = Field(default_factory=list)
    sample_problems: list[str] = Field(default_factory=list)


class AnswerFeedback(BaseModel):
    score: int = Field(0, ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    star_check: str = ""        # did the answer follow Situation-Task-Action-Result?
    follow_up: str = ""         # the coach's next probing question
    model_answer: str = ""      # a strong example answer


class MockTurn(BaseModel):
    """A single recorded exchange in the mock interview transcript."""
    question: str = ""
    answer: str = ""
    feedback: AnswerFeedback | None = None
