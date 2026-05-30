"""Generate a demo GIF for the README by running the full pipeline with sample data.

Produces ``docs/demo.gif`` — a walkthrough of the 5 steps using real agent outputs.
Requires Ollama to be running.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# project root on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFont
from PIL import Image as PILImage

from src.config import settings
from src.contracts.schemas import JobDescription, ResumeDoc
from src.llm import client
from src.orchestrator import scoring
from src.orchestrator.dossier import build_dossier_html
from src.orchestrator.session import CareerFile
from src.parsers.jd_parser import parse_jd

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
SAMPLE_RESUME = """Jane Doe — Software Engineer
- Built REST APIs in Python and FastAPI serving 2M requests/day.
- Deployed microservices on Kubernetes with CI/CD via GitHub Actions.
- Wrote SQL on PostgreSQL; some AWS (S3, Lambda).
- Led a 3-person backend team; owned sprint planning and on-call rotations.
- Built internal CLI tools in Go that saved ~15 eng-hours/week."""

SAMPLE_JD = """Backend Engineer @ Acme (Series B infrastructure startup)

Required: Python, Kubernetes, PostgreSQL, AWS, Terraform.
Nice to have: Go, Kafka.

You will design and own microservices, build CI/CD pipelines, and mentor
junior engineers. We value ownership, fast iteration, and blameless postmortems."""

PERSONALITY = "I like ownership and fast pace. I thrive in small, high-trust teams."

WIDTH, HEIGHT = 900, 640
BG = (15, 18, 25)          # dark bg
CARD = (28, 32, 42)        # card bg
ACCENT = (79, 195, 140)    # green accent
ACCENT2 = (239, 131, 84)   # orange accent
TEXT = (230, 235, 245)     # primary text
TEXT_MUTED = (140, 150, 170)  # muted text
WHITE = (255, 255, 255)
FONT_SIZE_TITLE = 28
FONT_SIZE_HEAD = 20
FONT_SIZE_BODY = 15
FONT_SIZE_SMALL = 13
PADDING = 32
LINE_H = 26


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    """Return a reasonable font; falls back to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\consola.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _create_base(step: str, title: str) -> tuple[PILImage.Image, ImageDraw.Draw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # header bar
    draw.rectangle([(0, 0), (WIDTH, 70)], fill=CARD)
    font_title = _find_font(FONT_SIZE_HEAD)
    font_step = _find_font(FONT_SIZE_SMALL)
    draw.text((PADDING, 16), f"🎯 ZeroCode Career Coach", fill=ACCENT, font=font_title)
    draw.text((WIDTH - PADDING - 160, 22), step, fill=TEXT_MUTED, font=font_step,
              anchor="ra")

    # title
    font_h1 = _find_font(FONT_SIZE_TITLE)
    draw.text((PADDING, 90), title, fill=WHITE, font=font_h1)

    return img, draw


def _draw_card(draw, x: int, y: int, w: int, h: int, accent: tuple = None):
    """Draw a rounded-corner card background."""
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=12, fill=CARD,
                           outline=accent or CARD, width=1)


def _text_lines(draw, text: str, max_width: int, font) -> list[str]:
    """Simple word-wrap."""
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for w in words[1:]:
        test = current + " " + w
        if draw.textbbox((0, 0), test, font=font)[2] > max_width:
            lines.append(current)
            current = w
        else:
            current = test
    lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Frame generators — each returns a PIL Image
# ---------------------------------------------------------------------------
def frame_step1_setup() -> PILImage.Image:
    img, draw = _create_base("Step 1 of 5", "📄 Upload Resume + Job Description")
    font = _find_font(FONT_SIZE_BODY)
    font_s = _find_font(FONT_SIZE_SMALL)

    # Left card: resume
    _draw_card(draw, 30, 140, 400, 460, ACCENT)
    draw.text((50, 155), "📄 Resume Uploaded", fill=ACCENT, font=_find_font(FONT_SIZE_HEAD))
    draw.text((50, 188), "Jane Doe — Software Engineer", fill=WHITE, font=font)
    body = _find_font(FONT_SIZE_SMALL)
    y = 218
    for line in SAMPLE_RESUME.strip().split("\n"):
        if y > 560:
            break
        draw.text((55, y), line.strip(), fill=TEXT_MUTED, font=body)
        y += 20

    # Right card: JD
    _draw_card(draw, 460, 140, 410, 460, ACCENT2)
    draw.text((480, 155), "💼 Job Description", fill=ACCENT2, font=_find_font(FONT_SIZE_HEAD))
    draw.text((480, 188), "Backend Engineer @ Acme", fill=WHITE, font=font)
    draw.text((480, 210), "Series B infra startup", fill=TEXT_MUTED, font=font_s)
    y = 240
    for line in SAMPLE_JD.strip().split("\n")[:10]:
        if y > 560:
            break
        draw.text((485, y), line.strip(), fill=TEXT_MUTED, font=body)
        y += 20

    draw.text((50, 590), "🧭 Personality: \"I like ownership and fast pace...\"", fill=TEXT_MUTED, font=font_s)
    return img


def frame_step2_fit(fit) -> PILImage.Image:
    img, draw = _create_base("Step 2 of 5", "🔍 Fit & Strategy — Recruiter Analysis")
    font = _find_font(FONT_SIZE_BODY)
    font_s = _find_font(FONT_SIZE_SMALL)
    font_h = _find_font(FONT_SIZE_HEAD)

    # Score card
    _draw_card(draw, 30, 140, 840, 90, ACCENT)
    s = fit.score
    metrics = [
        (f"{s.overall}/100", "Overall"),
        (f"{s.must_have_coverage}%", "Must-haves"),
        (f"{s.nice_to_have_coverage}%", "Nice-to-haves"),
        (f"{s.semantic_similarity}%", "Semantic"),
        (f"{s.seniority_fit}%", "Seniority"),
    ]
    for i, (val, label) in enumerate(metrics):
        x = 60 + i * 165
        draw.text((x, 152), val, fill=ACCENT, font=font_h)
        draw.text((x, 182), label, fill=TEXT_MUTED, font=font_s)

    # Verdict
    _draw_card(draw, 30, 250, 840, 56)
    summary = fit.summary[:150] + ("…" if len(fit.summary) > 150 else "")
    draw.text((50, 262), f"🗣 Recruiter's verdict: {summary}", fill=TEXT, font=font_s)

    # Strengths & Keywords
    _draw_card(draw, 30, 320, 400, 200)
    draw.text((50, 335), "✅ Strengths", fill=ACCENT, font=font_h)
    y = 365
    for s in fit.strengths[:5]:
        draw.text((55, y), f"• {s[:75]}", fill=TEXT, font=font_s)
        y += 22

    _draw_card(draw, 460, 320, 410, 200)
    draw.text((480, 335), "⚠️ Gaps to Address", fill=ACCENT2, font=font_h)
    y = 365
    for w in fit.weaknesses[:5]:
        draw.text((485, y), f"• {w[:75]}", fill=TEXT, font=font_s)
        y += 22

    # Keywords
    _draw_card(draw, 30, 535, 400, 55)
    kw = ", ".join(fit.keywords.matched[:6]) or "—"
    draw.text((50, 545), f"Matched: {kw}", fill=ACCENT, font=font_s)

    _draw_card(draw, 460, 535, 410, 55)
    kw_m = ", ".join(fit.keywords.missing[:6]) or "—"
    draw.text((480, 545), f"Missing: {kw_m}", fill=ACCENT2, font=font_s)

    return img


def frame_step3_tailor(kit) -> PILImage.Image:
    img, draw = _create_base("Step 3 of 5", "✍️ Tailored Resume & Cover Letter")
    font_s = _find_font(FONT_SIZE_SMALL)
    font_h = _find_font(FONT_SIZE_HEAD)

    # Bullets
    _draw_card(draw, 30, 140, 840, 250)
    draw.text((50, 155), "📝 Tailored Resume Bullets (XYZ Formula)", fill=ACCENT, font=font_h)
    y = 190
    for b in kit.bullets[:4]:
        # Before
        draw.text((55, y), f"Before: {b.original[:80]}", fill=TEXT_MUTED, font=font_s)
        y += 20
        # After
        improved = b.improved[:100] + ("…" if len(b.improved) > 100 else "")
        draw.text((55, y), f"After:  {improved}", fill=TEXT, font=font_s)
        y += 20
        if b.keywords_used:
            draw.text((70, y), f"keywords: {', '.join(b.keywords_used)}", fill=ACCENT, font=font_s)
            y += 20
        y += 8

    # Cover letter
    _draw_card(draw, 30, 405, 840, 210)
    draw.text((50, 420), "💌 Cover Letter", fill=ACCENT2, font=font_h)
    y = 452
    for line in kit.cover_letter[:280].split("\n")[:8]:
        if line.strip():
            draw.text((55, y), line.strip()[:100], fill=TEXT, font=font_s)
            y += 20

    if kit.voice_notes:
        vn = kit.voice_notes[0][:80]
        draw.text((30, 620), f"🔊 Voice preserved: {vn}", fill=TEXT_MUTED, font=font_s)

    return img


def frame_step4_coach(plan) -> PILImage.Image:
    img, draw = _create_base("Step 4 of 5", "🎤 Interview Coach — Prep + Mock")
    font_s = _find_font(FONT_SIZE_SMALL)
    font_h = _find_font(FONT_SIZE_HEAD)
    font = _find_font(FONT_SIZE_BODY)

    # Question bank
    _draw_card(draw, 30, 140, 430, 300)
    draw.text((50, 155), "📚 Question Bank", fill=ACCENT, font=font_h)
    y = 190
    for q in plan.questions[:6]:
        stage_icon = "🗣" if q.stage == "behavioral" else "⚙️"
        draw.text((55, y), f"{stage_icon} [{q.stage}] {q.question[:55]}", fill=TEXT, font=font_s)
        y += 22
        if q.why_asked:
            draw.text((70, y), f"Why: {q.why_asked[:65]}", fill=TEXT_MUTED, font=_find_font(11))
            y += 20
        y += 4

    # Right side: technical + mock
    _draw_card(draw, 480, 140, 390, 140)
    draw.text((500, 155), "⚙️ Technical Topics", fill=ACCENT2, font=font_h)
    y = 190
    for t in plan.technical_topics[:4]:
        draw.text((510, y), f"• {t[:50]}", fill=TEXT, font=font_s)
        y += 22

    _draw_card(draw, 480, 295, 390, 145)
    draw.text((500, 310), "🎤 Mock Interview", fill=ACCENT, font=font_h)
    draw.text((510, 345), "Q: Tell me about a time you", fill=TEXT, font=font_s)
    draw.text((510, 367), "    handled a production incident.", fill=TEXT, font=font_s)
    draw.text((510, 395), "🎙 Voice answer → transcribed locally", fill=TEXT_MUTED, font=_find_font(11))
    draw.text((510, 415), "⭐ STAR feedback with score", fill=TEXT_MUTED, font=_find_font(11))

    if plan.sample_problems:
        _draw_card(draw, 30, 455, 840, 155)
        draw.text((50, 470), "💡 Sample Problems", fill=ACCENT, font=font_h)
        y = 505
        for i, p in enumerate(plan.sample_problems[:5], 1):
            draw.text((55, y), f"{i}. {p[:90]}", fill=TEXT, font=font_s)
            y += 22

    return img


def frame_step5_dossier() -> PILImage.Image:
    img, draw = _create_base("Step 5 of 5", "📁 Career Dossier — One Downloadable File")
    font_s = _find_font(FONT_SIZE_SMALL)
    font_h = _find_font(FONT_SIZE_HEAD)
    font = _find_font(FONT_SIZE_BODY)

    # Checklist
    checklist = ["📄 Resume", "💼 Job Description", "🔍 Fit Report", "✍️ Application Kit",
                 "📚 Interview Plan", "🎤 Mock Transcript"]
    _draw_card(draw, 30, 140, 840, 80)
    for i, item in enumerate(checklist):
        x = 55 + (i % 3) * 270
        y = 155 + (i // 3) * 30
        draw.text((x, y), f"✅ {item}", fill=ACCENT, font=font_s)

    # Dossier preview
    _draw_card(draw, 30, 240, 840, 330)
    draw.text((50, 255), "📄 Self-Contained HTML Dossier", fill=ACCENT, font=font_h)
    draw.text((50, 288), "Everything bundled into ONE file:", fill=TEXT, font=font_s)
    features = [
        "• Full job description + company notes",
        "• Match score breakdown with ATS keywords",
        "• Tailored resume bullets + cover letter",
        "• Interview question bank + sample problems",
        "• Mock interview transcript with STAR feedback",
        "• Open offline · Print to PDF · No data leaves your machine",
    ]
    y = 320
    for f in features:
        draw.text((55, y), f, fill=TEXT_MUTED, font=font_s)
        y += 25

    # Download button look
    _draw_card(draw, 280, 445, 340, 50, ACCENT)
    draw.text((300, 455), "⬇️  Download Career Dossier (.html)", fill=WHITE, font=font)

    # Footer
    draw.text((30, 590), "🔒 100% local · No API keys · No data leaves your machine", fill=TEXT_MUTED, font=font_s)
    draw.text((30, 612), f"Powered by: {settings.chat_model} via Ollama", fill=TEXT_MUTED,
              font=_find_font(11))

    return img


def _generate_dossier_cf(fit, resume, jd):
    """Build a CareerFile with all steps populated for dossier rendering."""
    cf = CareerFile(resume=resume, jd=jd, fit=fit)
    return cf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print("🔌 Checking Ollama connection...")
    ok, msg = client.health()
    if not ok:
        print(f"FAIL: {msg}")
        print("Start Ollama first:  ollama serve")
        return 1
    print(f"OK — {msg}")

    resume = ResumeDoc(raw_text=SAMPLE_RESUME, filename="jane_doe_resume.txt")
    jd = parse_jd(SAMPLE_JD, company="Acme", company_info="Series B infra startup")

    # ---- Step 1: Setup frame (static) ----
    print("\n📸 Generating Step 1 — Setup...")
    frames = [frame_step1_setup()]

    # ---- Step 2: Recruiter ----
    print("🤖 Running Recruiter agent...")
    from src.agents.recruiter import Recruiter
    fit = Recruiter().analyze(resume, jd, personality_notes=PERSONALITY)
    print(f"   Score: {fit.score.overall}/100 | Summary: {fit.summary[:80]}...")
    frames.append(frame_step2_fit(fit))

    # ---- Step 3: Writer ----
    print("🤖 Running Writer agent...")
    from src.agents.writer import Writer
    kit = Writer().build(resume, jd, fit, personality_notes=PERSONALITY)
    print(f"   Bullets: {len(kit.bullets)} | Cover letter: {len(kit.cover_letter)} chars")
    frames.append(frame_step3_tailor(kit))

    # ---- Step 4: Coach ----
    print("🤖 Running Coach agent...")
    from src.agents.coach import Coach
    plan = Coach().build_plan(resume, jd)
    print(f"   Questions: {len(plan.questions)} | Topics: {len(plan.technical_topics)}")
    frames.append(frame_step4_coach(plan))

    # ---- Step 5: Dossier ----
    print("📸 Generating Step 5 — Dossier...")
    frames.append(frame_step5_dossier())

    # ---- Save frames ----
    docs_dir = Path(__file__).resolve().parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    frame_paths = []
    for i, frame in enumerate(frames):
        path = docs_dir / f"demo_step{i + 1}.png"
        frame.save(path, format="PNG", optimize=True)
        frame_paths.append(path)
        print(f"   Saved: {path} ({frame.size})")

    # ---- Create GIF ----
    gif_path = docs_dir / "demo.gif"
    # Resize for reasonable GIF size (max 700px wide)
    gif_frames = []
    for f in frames:
        ratio = 700 / f.width
        new_size = (700, int(f.height * ratio))
        gif_frames.append(f.resize(new_size, Image.LANCZOS))

    gif_frames[0].save(
        gif_path,
        format="GIF",
        save_all=True,
        append_images=gif_frames[1:],
        duration=2500,    # 2.5s per frame
        loop=0,
        optimize=True,
    )
    print(f"\n🎬 Demo GIF saved: {gif_path} ({gif_path.stat().st_size:,} bytes)")
    print("✅ Done! Commit docs/demo.gif + the individual PNGs and update the README.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
