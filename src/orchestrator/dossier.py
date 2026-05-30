"""Build the single-file Career Dossier.

Renders the whole CareerFile (inputs, fit report, application kit, interview
plan, mock transcript) into ONE self-contained HTML file the user can download,
open offline in any browser, and print to PDF. No external assets, no LLM call.
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

from .session import CareerFile

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"

# Autoescape on for everything (the template is *.html.j2, which select_autoescape
# would otherwise miss) so user-supplied resume/JD text is HTML-safe.
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,
)


def _nl2br(value: str) -> Markup:
    # Escape first, then turn newlines into <br>, then mark the result safe so the
    # <br> tags render while the user's text stays escaped.
    return Markup("<br>").join(escape(value or "").split("\n"))


_env.filters["nl2br"] = _nl2br


def build_dossier_html(cf: CareerFile) -> str:
    """Render the CareerFile to a self-contained HTML string."""
    template = _env.get_template("dossier.html.j2")
    return template.render(cf=cf)


def dossier_filename(cf: CareerFile) -> str:
    base = (cf.jd.company or "company").strip().replace(" ", "_")
    title = (cf.jd.title or "role").strip().replace(" ", "_")
    safe = "".join(c for c in f"{base}_{title}" if c.isalnum() or c in "_-")
    return f"career_dossier_{safe or 'application'}.html"
