"""Agent contract tests with the LLM fully mocked — no Ollama needed."""
import src.llm.client as client
from src.agents.coach import Coach
from src.agents.recruiter import Recruiter
from src.agents.writer import Writer
from src.contracts.schemas import JobDescription, ResumeDoc
from src.orchestrator import scoring

RESUME = ResumeDoc(raw_text="Python engineer. Built Kubernetes pipelines. SQL.", filename="r.txt")
JD = JobDescription(raw_text="Need Python, Kubernetes, Terraform.", title="SWE", company="Acme")


def _patch_json(monkeypatch, payload):
    monkeypatch.setattr(client, "chat_json", lambda *a, **k: payload)


def test_recruiter_merges_deterministic_score(monkeypatch):
    # embeddings off so scoring is deterministic
    monkeypatch.setattr(scoring, "_semantic_similarity", lambda *a, **k: None)
    _patch_json(monkeypatch, {
        "strengths": ["Strong Python"],
        "weaknesses": ["No Terraform"],
        "culture_fit_questions": ["Do you like ambiguity?"],
        "action_plan": ["Learn Terraform basics"],
        "summary": "Decent match.",
        "new_grad_friendly": "Yes.",
    })
    report = Recruiter().analyze(RESUME, JD)
    # qualitative fields come from the mocked LLM
    assert report.strengths == ["Strong Python"]
    # numeric score + keywords come from the deterministic scorer, not the LLM
    assert "terraform" in report.keywords.missing
    assert "python" in report.keywords.matched
    assert 0 <= report.score.overall <= 100


def test_writer_returns_kit(monkeypatch):
    _patch_json(monkeypatch, {
        "bullets": [{"original": "did stuff", "improved": "Did X by Y",
                     "keywords_used": ["python"], "rationale": "quantified"}],
        "cover_letter": "Dear team...",
        "linkedin_headline": "SWE",
        "linkedin_about": "I build things.",
        "voice_notes": ["kept it concrete"],
    })
    kit = Writer().build(RESUME, JD, None)
    assert kit.cover_letter.startswith("Dear")
    assert kit.bullets[0].keywords_used == ["python"]


def test_coach_plan_and_feedback(monkeypatch):
    _patch_json(monkeypatch, {
        "questions": [{"stage": "behavioral", "question": "Tell me about a conflict.",
                       "why_asked": "teamwork", "answer_tips": "use STAR"}],
        "technical_topics": ["system design"],
        "sample_problems": ["Design a URL shortener"],
    })
    plan = Coach().build_plan(RESUME, JD)
    assert plan.questions[0].stage == "behavioral"
    assert Coach().next_question(plan, asked=[]) == "Tell me about a conflict."
    assert Coach().next_question(plan, asked=["Tell me about a conflict."]) == ""

    _patch_json(monkeypatch, {
        "score": 7, "strengths": ["clear"], "improvements": ["add metrics"],
        "star_check": "missing Result", "follow_up": "What was the outcome?",
        "model_answer": "When I...",
    })
    fb = Coach().evaluate_answer("Tell me about a conflict.", "We argued then agreed.", JD, RESUME)
    assert fb.score == 7
    assert "missing Result" in fb.star_check
