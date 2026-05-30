"""Extract plain text from an uploaded resume (PDF / DOCX / TXT).

Accepts either a filesystem path or a file-like object (Streamlit's
UploadedFile), so it works both in tests and in the app.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

from ..contracts.schemas import ResumeDoc


def _read_pdf(stream: BinaryIO) -> str:
    import pdfplumber  # imported lazily so tests for .txt don't need it

    parts: list[str] = []
    with pdfplumber.open(stream) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _read_docx(stream: BinaryIO) -> str:
    import docx  # python-docx, lazy import

    document = docx.Document(stream)
    return "\n".join(p.text for p in document.paragraphs)


def parse_resume(file: str | Path | BinaryIO, filename: str | None = None) -> ResumeDoc:
    """Parse a resume into a `ResumeDoc`. Format is chosen by extension."""
    if isinstance(file, (str, Path)):
        path = Path(file)
        name = filename or path.name
        data = path.read_bytes()
    else:  # file-like (e.g. Streamlit UploadedFile)
        name = filename or getattr(file, "name", "resume")
        data = file.read()

    suffix = Path(name).suffix.lower()
    stream = io.BytesIO(data)

    if suffix == ".pdf":
        text = _read_pdf(stream)
    elif suffix in (".docx", ".doc"):
        text = _read_docx(stream)
    else:  # .txt / .md / unknown -> best-effort decode
        text = data.decode("utf-8", errors="ignore")

    return ResumeDoc(raw_text=_clean(text), filename=name)


def _clean(text: str) -> str:
    # Collapse excessive blank lines while keeping paragraph structure.
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: list[str] = []
    blank = 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank <= 1:
                out.append("")
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip()
