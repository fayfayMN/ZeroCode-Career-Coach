"""Developer end-to-end smoke test against a live local Ollama.

Runs the deterministic scorer + the Recruiter agent on tiny sample inputs and
builds a dossier, printing key results. Not a unit test — needs Ollama running.

    ~/cc-venv/bin/python scripts/dev_e2e.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.llm import client  # noqa: E402

SAMPLE_RESUME = (
    "Jane Doe — Software Engineer\n"
    "- Built REST APIs in Python and FastAPI serving 2M requests/day.\n"
    "- Deployed microservices on Kubernetes with CI/CD via GitHub Actions.\n"
    "- Wrote SQL on PostgreSQL; some AWS (S3, Lambda).\n"
)
SAMPLE_JD = (
    "Backend Engineer. Required: Python, Kubernetes, PostgreSQL, AWS, Terraform. "
    "Nice to have: Go, Kafka. You will design microservices and own CI/CD."
)


def main() -> int:
    print("== health ==")
    ok, msg = client.health()
    print(("OK  " if ok else "FAIL") + " | " + msg)
    if not ok:
        return 1

    from src.contracts.schemas import JobDescription, ResumeDoc
    from src.parsers.jd_parser import parse_jd

    resume = ResumeDoc(raw_text=SAMPLE_RESUME, filename="sample.txt")
    jd = parse_jd(SAMPLE_JD, company="Acme", company_info="Series B infra startup")

    print("\n== deterministic score ==")
    from src.orchestrator.scoring import compute_match

    breakdown, gap = compute_match(jd.raw_text, resume.raw_text)
    print("overall:", breakdown.overall, "| must:", breakdown.must_have_coverage,
          "| semantic:", breakdown.semantic_similarity)
    print("matched:", gap.matched)
    print("missing:", gap.missing)

    print("\n== Recruiter agent (live LLM) ==")
    from src.agents.recruiter import Recruiter

    fit = Recruiter().analyze(resume, jd, personality_notes="I like ownership and fast pace.")
    print("score.overall:", fit.score.overall)
    print("summary:", fit.summary[:300])
    print("strengths:", fit.strengths[:3])
    print("weaknesses:", fit.weaknesses[:3])
    print("action_plan[0]:", (fit.action_plan or ["(none)"])[0])

    print("\n== dossier build ==")
    from src.orchestrator.dossier import build_dossier_html
    from src.orchestrator.session import CareerFile

    cf = CareerFile(resume=resume, jd=jd, fit=fit)
    html = build_dossier_html(cf)
    out = Path(__file__).resolve().parent.parent / "_dev_dossier.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html)} bytes)")

    print("\nALL GOOD ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
