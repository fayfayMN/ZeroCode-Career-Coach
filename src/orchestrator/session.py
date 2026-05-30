"""The CareerFile — the single source of truth for one job application.

Everything the user produces (inputs, fit report, application kit, interview
plan, mock transcript) lives here. The dossier builder serialises it to one
downloadable HTML file. In Streamlit a single CareerFile is stored in
`st.session_state`.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..contracts.schemas import (
    ApplicationKit,
    FitReport,
    InterviewPlan,
    JobDescription,
    MockTurn,
    ResumeDoc,
)


class CareerFile(BaseModel):
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # Step 1 — inputs
    resume: ResumeDoc = Field(default_factory=ResumeDoc)
    jd: JobDescription = Field(default_factory=JobDescription)
    personality_notes: str = ""  # the seeker's own reflections (drives voice/fit)

    # Step 2 — Recruiter
    fit: FitReport | None = None

    # Step 3 — Writer
    kit: ApplicationKit | None = None

    # Step 4 — Coach
    interview: InterviewPlan | None = None
    mock_transcript: list[MockTurn] = Field(default_factory=list)

    # convenience -------------------------------------------------------------
    @property
    def ready_for_fit(self) -> bool:
        return bool(self.resume.raw_text and self.jd.raw_text)

    @property
    def title_line(self) -> str:
        bits = [b for b in (self.jd.title, self.jd.company) if b]
        return " @ ".join(bits) if bits else "Untitled application"
