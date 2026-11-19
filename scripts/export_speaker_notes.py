"""Write the speaker scripts from the decks' own notes, so script and slides cannot drift.
Usage: python scripts/export_speaker_notes.py"""
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parent.parent
DECKS = [("presentation/HKTH_TradeEscrow_Final_Presentation_paper.pptx", "presentation/speaker_script.md",
          "Final presentation — speaker script",
          "Slides 1–16 are the talk (Part 3 = slides 9–12, Wong Ho Ming); slides after 16 are backups. Confirm the slot length with the instructor.")]

for src, dst, title, intro in DECKS:
    prs = Presentation(ROOT / src)
    out = [f"# {title}", "", intro, "", "_Generated from the deck's speaker notes by scripts/export_speaker_notes.py._", ""]
    for i, sl in enumerate(prs.slides, 1):
        t = sl.shapes.title.text_frame.text if sl.shapes.title is not None else "(untitled)"
        notes = sl.notes_slide.notes_text_frame.text.strip() if sl.has_notes_slide else ""
        out += [f"## Slide {i}: {t}", "", notes or "_(section divider)_", ""]
    (ROOT / dst).write_text("\n".join(out), encoding="utf-8")
    print(dst, len(prs.slides), "slides")
