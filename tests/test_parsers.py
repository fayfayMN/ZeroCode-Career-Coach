from src.parsers.jd_parser import parse_jd
from src.parsers.resume_parser import parse_resume


def test_parse_resume_txt(tmp_path):
    p = tmp_path / "resume.txt"
    p.write_text("Jane Dev\n\n\n\nPython engineer\n", encoding="utf-8")
    doc = parse_resume(p)
    assert doc.filename == "resume.txt"
    assert "Python engineer" in doc.raw_text
    # blank-line collapse keeps at most one blank between blocks
    assert "\n\n\n" not in doc.raw_text


def test_parse_resume_filelike():
    import io

    buf = io.BytesIO(b"Sample resume text")
    buf.name = "cv.txt"
    doc = parse_resume(buf)
    assert doc.raw_text == "Sample resume text"
    assert doc.filename == "cv.txt"


def test_parse_jd_basic():
    jd = parse_jd("Senior Python Engineer\nDo backend work.", company="Acme",
                  company_info="Series B startup")
    assert jd.company == "Acme"
    assert jd.company_info == "Series B startup"
    assert jd.title == "Senior Python Engineer"
