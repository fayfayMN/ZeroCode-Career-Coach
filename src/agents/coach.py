"""Agent 3 — Coach (Interview Trainer).

Builds a tailored interview plan and runs an interactive mock interview:
generates questions, evaluates spoken/typed answers with STAR-aware feedback,
and asks natural follow-ups.
"""
from __future__ import annotations

from ..contracts.schemas import (
    AnswerFeedback,
    InterviewPlan,
    JobDescription,
    ResumeDoc,
)
from .base import Agent


class Coach(Agent):
    persona = (
        "You are the Coach agent in Career Coach: a supportive but honest interview "
        "coach who has prepped hundreds of engineers and analysts. You build tailored "
        "prep and give feedback that actually improves answers."
    )
    skills = ("interview-behavioral", "interview-technical")

    def build_plan(self, resume: ResumeDoc, jd: JobDescription) -> InterviewPlan:
        prompt = f"""Design an interview prep plan for this candidate and role.

# JOB
Title: {jd.title}  |  Company: {jd.company}
JOB DESCRIPTION:
{jd.raw_text[:6000]}

# RESUME
{resume.raw_text[:5000]}

Produce an InterviewPlan:
- questions: 8-12 tailored questions across stages "recruiter_screen", "behavioral",
  and "technical". For each: stage, question, why_asked, answer_tips (specific to THIS
  candidate's background).
- technical_topics: the topics most likely tested, ordered by likelihood, calibrated to level.
- sample_problems: 3-5 representative technical problems/questions for this role and level."""
        return self.run_json(prompt, InterviewPlan)

    def evaluate_answer(
        self, question: str, answer: str, jd: JobDescription, resume: ResumeDoc
    ) -> AnswerFeedback:
        prompt = f"""Evaluate the candidate's interview answer.

ROLE: {jd.title} @ {jd.company}
QUESTION: {question}
CANDIDATE'S ANSWER (transcribed from voice or typed):
\"\"\"{answer}\"\"\"

Relevant candidate background:
{resume.raw_text[:3000]}

Return AnswerFeedback:
- score: 0-10.
- strengths: what worked (be specific).
- improvements: concrete fixes.
- star_check: which of Situation/Task/Action/Result were present or missing.
- follow_up: ONE natural follow-up question a real interviewer would ask next.
- model_answer: a strong ~90-second example answer built from the candidate's real background."""
        return self.run_json(prompt, AnswerFeedback, temperature=0.3)

    def next_question(self, plan: InterviewPlan, asked: list[str]) -> str:
        """Pick the next unasked question from the plan (deterministic)."""
        for q in plan.questions:
            if q.question not in asked:
                return q.question
        return ""
