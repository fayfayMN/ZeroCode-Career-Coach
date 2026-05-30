"""Parse a job description and extract ATS-relevant keywords.

Keyword extraction is deterministic (no LLM) so the match score is reproducible
and explainable. It combines:
  * a curated tech/skill lexicon (multi-word aware), and
  * salient capitalised / hyphenated tokens found in the JD.
"""
from __future__ import annotations

import re

from ..contracts.schemas import JobDescription

# A pragmatic lexicon of skills/tools recruiters scan for. Extend freely.
SKILL_LEXICON: set[str] = {
    # languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "scala", "kotlin", "swift", "ruby", "php", "r", "matlab", "sql",
    # web / frameworks
    "react", "angular", "vue", "node.js", "node", "django", "flask", "fastapi",
    "spring", "express", "next.js", ".net", "rails", "graphql", "rest", "grpc",
    # data / ml
    "pandas", "numpy", "pytorch", "tensorflow", "scikit-learn", "keras",
    "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake", "databricks",
    "machine learning", "deep learning", "nlp", "computer vision", "llm",
    "data analysis", "data engineering", "etl", "statistics", "tableau",
    "power bi", "looker",
    # cloud / devops
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "ci/cd", "github actions", "linux",
    "microservices", "serverless", "lambda", "ec2", "s3",
    # databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cassandra", "sqlite",
    # practices / soft
    "agile", "scrum", "tdd", "unit testing", "system design", "api design",
    "git", "code review", "communication", "leadership", "collaboration",
    "problem solving", "stakeholder management", "mentoring",
}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def extract_keywords(text: str) -> list[str]:
    """Return the lexicon skills present in `text`, preserving lexicon casing."""
    norm = _normalise(text)
    found: list[str] = []
    for skill in SKILL_LEXICON:
        # Word-boundary match; allow '.', '+', '#', '/' inside skill tokens.
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, norm):
            found.append(skill)
    return sorted(set(found))


def _guess_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if 3 <= len(line) <= 80 and not line.endswith(":"):
            return line
    return ""


def _guess_seniority(text: str) -> str:
    norm = _normalise(text)
    for level in ("intern", "new grad", "entry level", "junior", "associate",
                  "senior", "staff", "principal", "lead", "manager"):
        if level in norm:
            return level
    return "unspecified"


def parse_jd(raw_text: str, company: str = "", company_info: str = "") -> JobDescription:
    """Build a `JobDescription` from pasted text + optional company context."""
    return JobDescription(
        raw_text=raw_text.strip(),
        title=_guess_title(raw_text),
        company=company.strip(),
        company_info=company_info.strip(),
    )
