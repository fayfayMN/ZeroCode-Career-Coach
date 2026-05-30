"""Deterministic, explainable JD↔resume match scoring.

The score is a blend a recruiter can defend, not an LLM guess:
  * keyword coverage  — which JD skills appear in the resume (rapidfuzz handles
    minor spelling/spacing variants),
  * semantic similarity — cosine similarity of resume vs JD embeddings (Ollama).
    Degrades gracefully to keyword-only when embeddings aren't available.

`compute_match` returns a `ScoreBreakdown` plus the matched/missing keyword
lists; the Recruiter agent layers qualitative judgement on top.
"""
from __future__ import annotations

from rapidfuzz import fuzz

from ..contracts.schemas import KeywordGap, ScoreBreakdown
from ..parsers.jd_parser import extract_keywords

# JD keywords that, when present, count as "must have" vs "nice to have".
# We treat the first ~60% of distinct JD keywords as must-haves (JDs front-load
# core requirements). Simple, transparent, and good enough as a heuristic.
_MUST_HAVE_FRACTION = 0.6
_FUZZ_THRESHOLD = 88  # rapidfuzz partial ratio to count a keyword as "matched"


def _keyword_present(keyword: str, resume_lc: str) -> bool:
    if keyword in resume_lc:
        return True
    # Fuzzy fallback for variants like "postgres" vs "postgresql".
    return fuzz.partial_ratio(keyword, resume_lc) >= _FUZZ_THRESHOLD


def keyword_gap(jd_text: str, resume_text: str) -> tuple[KeywordGap, list[str]]:
    """Return (matched/missing gap, ordered list of JD keywords)."""
    jd_keywords = extract_keywords(jd_text)
    resume_lc = resume_text.lower()
    matched, missing = [], []
    for kw in jd_keywords:
        (matched if _keyword_present(kw, resume_lc) else missing).append(kw)
    return KeywordGap(matched=matched, missing=missing), jd_keywords


def _cosine(a: list[float], b: list[float]) -> float:
    import numpy as np

    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if va.size == 0 or vb.size == 0:
        return 0.0
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1.0
    return float(np.dot(va, vb) / denom)


def _semantic_similarity(jd_text: str, resume_text: str) -> int | None:
    """Embedding cosine similarity mapped to 0-100, or None if unavailable."""
    try:
        from ..llm.client import embed

        jd_vec = embed(jd_text[:4000])
        res_vec = embed(resume_text[:4000])
        cos = _cosine(jd_vec, res_vec)
        # Cosine for related docs typically sits ~0.4-0.9; rescale to spread it.
        scaled = max(0.0, min(1.0, (cos - 0.2) / 0.7))
        return round(scaled * 100)
    except Exception:  # noqa: BLE001 - embeddings optional
        return None


def _seniority_fit(jd_text: str, resume_text: str) -> int:
    """Cheap heuristic: do experience-level signals roughly align?"""
    jd, res = jd_text.lower(), resume_text.lower()
    senior_terms = ("senior", "staff", "principal", "lead", "10+ years", "8+ years")
    junior_terms = ("intern", "new grad", "entry level", "junior", "0-2 years")
    jd_senior = any(t in jd for t in senior_terms)
    jd_junior = any(t in jd for t in junior_terms)
    res_senior = any(t in res for t in senior_terms)
    if not jd_senior and not jd_junior:
        return 75  # unspecified -> neutral-positive
    if jd_senior and res_senior:
        return 90
    if jd_junior and not res_senior:
        return 90
    if jd_senior and not res_senior:
        return 55  # may be under-levelled
    return 70


def compute_match(jd_text: str, resume_text: str) -> tuple[ScoreBreakdown, KeywordGap]:
    """Compute the full deterministic match breakdown."""
    gap, ordered = keyword_gap(jd_text, resume_text)

    n = len(ordered)
    if n == 0:
        must_cov = nice_cov = 0
    else:
        cut = max(1, round(n * _MUST_HAVE_FRACTION))
        must, nice = set(ordered[:cut]), set(ordered[cut:])
        matched = set(gap.matched)
        must_cov = round(100 * len(must & matched) / len(must)) if must else 0
        nice_cov = round(100 * len(nice & matched) / len(nice)) if nice else 100

    semantic = _semantic_similarity(jd_text, resume_text)
    seniority = _seniority_fit(jd_text, resume_text)

    # Weighting: must-haves dominate, semantic & seniority refine.
    if semantic is None:
        # keyword-only fallback
        overall = round(0.7 * must_cov + 0.2 * nice_cov + 0.1 * seniority)
        semantic_val = 0
    else:
        overall = round(0.45 * must_cov + 0.15 * nice_cov + 0.3 * semantic + 0.1 * seniority)
        semantic_val = semantic

    breakdown = ScoreBreakdown(
        overall=max(0, min(100, overall)),
        must_have_coverage=must_cov,
        nice_to_have_coverage=nice_cov,
        semantic_similarity=semantic_val,
        seniority_fit=seniority,
    )
    return breakdown, gap
