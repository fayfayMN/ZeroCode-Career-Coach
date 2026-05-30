from src.contracts.schemas import (
    ApplicationKit,
    FitReport,
    InterviewPlan,
    InterviewQuestion,
    JobDescription,
    ResumeDoc,
    ScoreBreakdown,
    TailoredBullet,
)
from src.orchestrator.dossier import build_dossier_html, dossier_filename
from src.orchestrator.session import CareerFile


def _full_careerfile() -> CareerFile:
    cf = CareerFile()
    cf.resume = ResumeDoc(raw_text="Python engineer", filename="r.txt")
    cf.jd = JobDescription(raw_text="Need Python", title="SWE", company="Acme Corp",
                           company_info="Series B")
    cf.fit = FitReport(
        score=ScoreBreakdown(overall=78, must_have_coverage=80),
        strengths=["Strong Python"], weaknesses=["No Go"],
        action_plan=["Learn Go"], summary="Solid match.",
    )
    cf.kit = ApplicationKit(
        bullets=[TailoredBullet(original="did stuff", improved="Did X by Y")],
        cover_letter="Dear hiring team,\nI am excited.",
    )
    cf.interview = InterviewPlan(
        questions=[InterviewQuestion(stage="behavioral", question="Tell me about yourself.")],
        technical_topics=["system design"],
    )
    return cf


def test_dossier_renders_all_sections():
    cf = _full_careerfile()
    html = build_dossier_html(cf)
    assert "<!DOCTYPE html>" in html
    assert "Acme Corp" in html
    assert "78" in html                 # overall score
    assert "Strong Python" in html
    assert "Did X by Y" in html
    assert "Dear hiring team" in html
    assert "Tell me about yourself." in html


def test_dossier_handles_empty_sections():
    # Only inputs present; agent outputs are None.
    cf = CareerFile()
    cf.resume = ResumeDoc(raw_text="hello")
    cf.jd = JobDescription(raw_text="world")
    html = build_dossier_html(cf)
    assert "<!DOCTYPE html>" in html  # renders without crashing


def test_dossier_filename_is_safe():
    cf = _full_careerfile()
    name = dossier_filename(cf)
    assert name.endswith(".html")
    assert " " not in name
