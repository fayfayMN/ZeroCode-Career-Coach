"""Scoring is deterministic, so we can assert exact-ish behaviour without an LLM.
Embeddings are monkeypatched off so we test the keyword-only path."""
from src.orchestrator import scoring
from src.parsers.jd_parser import extract_keywords


def test_extract_keywords_finds_multiword_and_single():
    jd = "We need Python, machine learning, and AWS. Experience with CI/CD is a plus."
    kws = extract_keywords(jd)
    assert "python" in kws
    assert "machine learning" in kws
    assert "aws" in kws
    assert "ci/cd" in kws


def test_keyword_gap_splits_matched_and_missing():
    jd = "Looking for Python, Kubernetes, and Terraform."
    resume = "Built services in Python. Deployed with Kubernetes."
    gap, ordered = scoring.keyword_gap(jd, resume)
    assert "python" in gap.matched
    assert "kubernetes" in gap.matched
    assert "terraform" in gap.missing
    assert set(ordered) == {"python", "kubernetes", "terraform"}


def test_compute_match_keyword_only(monkeypatch):
    # Force embeddings unavailable -> keyword-only path.
    monkeypatch.setattr(scoring, "_semantic_similarity", lambda *a, **k: None)
    jd = "Python, SQL, AWS, Docker required."
    resume = "Python and SQL expert. Some AWS. No containers."
    breakdown, gap = scoring.compute_match(jd, resume)
    assert 0 <= breakdown.overall <= 100
    assert breakdown.semantic_similarity == 0
    assert "docker" in gap.missing
    # partial coverage -> not a perfect score
    assert breakdown.overall < 100


def test_compute_match_perfect_coverage(monkeypatch):
    monkeypatch.setattr(scoring, "_semantic_similarity", lambda *a, **k: None)
    jd = "Python and SQL."
    resume = "Python, SQL, Python, SQL."
    breakdown, gap = scoring.compute_match(jd, resume)
    assert gap.missing == []
    assert breakdown.must_have_coverage == 100
