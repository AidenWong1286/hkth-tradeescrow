"""HK–TH TradeEscrow final deck, v4 "Corridor": off-white monochrome, built from the product itself.

    python presentation/build_deck_v4.py [out.pptx]

Design system (see CHANGELOG 2026-11-19):
  paper #F5F5F2 · card #EBEBE7 · ink #111111 · secondary #6E6E73 · hairline #D6D6D0
  signals only: teal #1F8A82 = passed, red #B8342A = refused / risk
  type: Segoe UI Semibold (headlines), Segoe UI Light (big numbers), Segoe UI (body), Consolas (codes)
Motifs from the product: the 7-segment release-guard ring, the hash-chain journal (footer progress),
the console's wave mesh (presentation/v4/mesh), the HK -> Laem Chabang route line, console screenshots.
Every figure is read from results/; speaker notes, presenters and links come from presentation/v4/source_content.json.
Everything except photos, mesh and screenshots is a native, editable PowerPoint shape.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "presentation" / "v4"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "presentation" / "HKTH_TradeEscrow_Final_Presentation_v5_colour.pptx"

# ------------------------------------------------------------------ tokens
# Colour edition (v5): the project palette with fixed meanings, on the v4 layout.
#   navy = structure/text · teal = tested/passed · gold = money/modelled · red = refused/risk
PAPER, CARD, INK, INK2, MUTE, HAIR, WHITE = "F6F5F1", "ECEFF3", "0B1730", "3E4A5E", "6B7689", "D9DEE6", "FFFFFF"
TEAL, RED, GOLD = "1F8A82", "B8342A", "B07A22"
TEAL_T, GOLD_T, RED_T = "E1F0ED", "F5ECDA", "F7E4E1"          # light tints for panels
TEAL_P = "A9D3CD"                                               # past blocks in the footer chain
F_H, F_L, F_T, F_M = "Segoe UI Semibold", "Segoe UI Light", "Segoe UI", "Consolas"
W, H = 13.333, 7.5
MX = 0.75                        # side margin

# ------------------------------------------------------------------ data from results/
MET = {r["metric_id"]: r for r in csv.DictReader(open(ROOT / "results/metrics.csv", encoding="utf-8"))}
v = lambda k: MET[k]["value"]
d = lambda k: MET[k]["denominator"]
fr = lambda k: f"{v(k)}/{d(k)}"
num = lambda x: f"{int(float(x)):,}"
PROC = {(r["scenario"], r["model"]): int(r["manual_settlement_tasks"]) for r in csv.DictReader(open(ROOT / "results/process_counts.csv", encoding="utf-8"))}
TL = {(r["model"], r["payment_term_days"]): r for r in csv.DictReader(open(ROOT / "results/timelines.csv", encoding="utf-8"))
      if r["scenario"] == "normal" and r["assumption_level"] == "base"}
SRC = json.load(open(V4 / "source_content.json", encoding="utf-8"))
NOTES = {int(k): t for k, t in SRC["notes"].items()}
LINKS = {text.strip(): url for lst in SRC["links"].values() for text, url in lst}
# Student IDs live in team.local.json (git-ignored); without it footers show the presenter's name only.
_TEAM = ROOT / "team.local.json"
TEAM_IDS = {n.lower(): i for n, i in json.load(open(_TEAM, encoding="utf-8"))["ids"].items()} if _TEAM.exists() else {}
PRESENTER = {}                                      # slide -> "NAME · student id" (only slides with a named presenter)
for k, f in SRC["footers"].items():
    if "Presented by" in f:
        name = " ".join(f.split("Presented by", 1)[1].split())
        sid = TEAM_IDS.get(name.lower(), "")
        PRESENTER[int(k)] = f"{name} · {sid}" if sid else name

PARTS = ["Why escrow", "The design", "The evidence", "The verdict"]

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]
In = lambda x: Emu(int(round(x * 914400)))


def rgb(h):
    return RGBColor.from_string(h)


def _nostyle(sh):
    """Drop the template's <p:style> (theme line/fill/shadow refs): every look is set explicitly."""
    st = sh._element.find(qn("p:style"))
    if st is not None:
        sh._element.remove(st)
    return sh


# ------------------------------------------------------------------ primitives
def new_slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(PAPER)
    return s


def _style_run(r, size, font, color, bold=False, italic=False, spc=0, strike=False):
    f = r.font
    f.size = Pt(size); f.name = font; f.bold = bold; f.italic = italic
    f.color.rgb = rgb(color)
    rPr = r._r.get_or_add_rPr()
    if spc:
        rPr.set("spc", str(int(spc)))
    if strike:
        rPr.set("strike", "sngStrike")
    for tag in ("a:ea", "a:cs"):                     # East-Asian / complex scripts use the same face
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", font)


def text(s, x, y, w, h, paras, size=14, font=F_T, color=INK, bold=False, align="l", anchor="t",
         spc=0, ls=None, italic=False, after=0, link=None, strike=False):
    """paras: str | list of (str | list of runs). A run is str or (str, {overrides})."""
    box_ = s.shapes.add_textbox(In(x), In(y), In(w), In(h))
    tf = box_.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        if ls:
            p.line_spacing = ls
        if after:
            p.space_after = Pt(after)
        runs = para if isinstance(para, list) else [para]
        for run in runs:
            t, o = (run, {}) if isinstance(run, str) else run
            r = p.add_run()
            r.text = t
            _style_run(r, o.get("size", size), o.get("font", font), o.get("color", color), o.get("bold", bold),
                       o.get("italic", italic), o.get("spc", spc), o.get("strike", strike))
            url = o.get("link", link)
            if url:
                r.hyperlink.address = url
    return box_


def box(s, x, y, w, h, fill=None, line=None, lw=1.0, radius=None, dash=False, shape=None):
    kind = shape or (MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE)
    sh = s.shapes.add_shape(kind, In(x), In(y), In(w), In(h))
    if radius and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = min(0.5, radius / min(w, h))
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = rgb(line); sh.line.width = Pt(lw)
        if dash:
            sh.line.dash_style = MSO_LINE.DASH
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return _nostyle(sh)


def oval(s, cx, cy, r, fill=None, line=None, lw=1.0):
    return box(s, cx - r, cy - r, 2 * r, 2 * r, fill=fill, line=line, lw=lw, shape=MSO_SHAPE.OVAL)


def line(s, x1, y1, x2, y2, color=HAIR, lw=1.0, dash=False):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, In(x1), In(y1), In(x2), In(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(lw)
    if dash:
        c.line.dash_style = MSO_LINE.DASH
    return _nostyle(c)


def poly(s, pts, fill=None, line_color=None, lw=1.0, closed=True):
    fb = s.shapes.build_freeform(In(pts[0][0]), In(pts[0][1]), scale=1.0)
    fb.add_line_segments([(In(x), In(y)) for x, y in pts[1:]], close=closed)
    sh = fb.convert_to_shape()
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    else:
        sh.fill.background()
    if line_color:
        sh.line.color.rgb = rgb(line_color); sh.line.width = Pt(lw)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return _nostyle(sh)


def curve(s, pts_fn, n=60, color=INK, lw=1.25, dash=False):
    sh = poly(s, [pts_fn(i / n) for i in range(n + 1)], fill=None, line_color=color, lw=lw, closed=False)
    if dash:
        sh.line.dash_style = MSO_LINE.DASH
    return sh


def ring(s, cx, cy, r, thick, states, gap_deg=7.0, colors=None):
    """The release guard: 7 annulus segments clockwise from 12 o'clock. states: 'ok' | 'bad' | 'off'."""
    colors = colors or {"ok": TEAL, "bad": RED, "off": HAIR, "gold": GOLD}
    seg = 360.0 / len(states)
    for i, st in enumerate(states):
        a0 = -90 + i * seg + gap_deg / 2
        a1 = a0 + seg - gap_deg
        k = 18
        outer = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * j / k)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * j / k))) for j in range(k + 1)]
        ri = r - thick
        inner = [(cx + ri * math.cos(math.radians(a1 - (a1 - a0) * j / k)), cy + ri * math.sin(math.radians(a1 - (a1 - a0) * j / k))) for j in range(k + 1)]
        poly(s, outer + inner, fill=colors[st])


def picture(s, path, x, y, w, h, focus=(0.5, 0.5), radius=None, shadow=False, contain=False):
    """Cover-fit an image into the frame (crop, never stretch); contain=True fits it inside instead
    (diagrams must never be cropped). Optional rounded corners and soft shadow."""
    iw, ih = Image.open(path).size
    fa, ia = w / h, iw / ih
    if contain:
        w2, h2 = (w, w / ia) if ia > fa else (h * ia, h)
        x, y, w, h = x + (w - w2) / 2, y + (h - h2) / 2, w2, h2
        fa = ia
    pic = s.shapes.add_picture(str(path), In(x), In(y), In(w), In(h))
    if ia > fa:
        extra = 1 - fa / ia
        pic.crop_left = extra * focus[0]; pic.crop_right = extra * (1 - focus[0])
    elif ia < fa:
        extra = 1 - ia / fa
        pic.crop_top = extra * focus[1]; pic.crop_bottom = extra * (1 - focus[1])
    spPr = pic._element.spPr
    if radius:
        geom = spPr.find(qn("a:prstGeom"))
        geom.set("prst", "roundRect")
        av = geom.find(qn("a:avLst"))
        if av is None:
            av = etree.SubElement(geom, qn("a:avLst"))
        gd = etree.SubElement(av, qn("a:gd")); gd.set("name", "adj"); gd.set("fmla", f"val {int(radius / min(w, h) * 100000)}")
    if shadow:
        eff = etree.SubElement(spPr, qn("a:effectLst"))
        sh = etree.SubElement(eff, qn("a:outerShdw"))
        for k_, v_ in (("blurRad", "508000"), ("dist", "127000"), ("dir", "5400000"), ("algn", "t"), ("rotWithShape", "0")):
            sh.set(k_, v_)
        c = etree.SubElement(sh, qn("a:srgbClr")); c.set("val", "000000")
        a = etree.SubElement(c, qn("a:alpha")); a.set("val", "16000")
    return pic


def mesh(s, y, h, crop_top=0.0, crop_bottom=0.0):
    """Wave-mesh band from the console (transparent PNG)."""
    p = s.shapes.add_picture(str(V4 / "mesh" / "mesh_teal.png"), 0, In(y), In(W), In(h))
    p.crop_top, p.crop_bottom = crop_top, crop_bottom
    return p


def tick(s, x, y, ok=True, size=12):
    text(s, x, y, 0.3, 0.3, "✓" if ok else "✕", size=size, font=F_H, color=TEAL if ok else RED)


def dot(s, cx, cy, color, r=0.05):
    oval(s, cx, cy, r, fill=color)


# ------------------------------------------------------------------ chrome: brand, nav, footer, title
def brand(s, x=MX, y=0.42, color=INK):
    for dx, dy, filled, c in [(0, 0, True, color), (0.11, 0, False, color), (0, 0.11, False, color), (0.11, 0.11, True, TEAL)]:
        box(s, x + dx, y + dy, 0.085, 0.085, fill=c if filled else None, line=c, lw=0.9, radius=0.02)
    text(s, x + 0.3, y - 0.035, 2.8, 0.3, [[("TradeEscrow", {"font": F_H, "size": 11}), ("   Hong Kong → Thailand", {"size": 10, "color": MUTE})]], color=color)


def nav(s, part):
    x0 = 8.15
    for i, name in enumerate(PARTS):
        x = x0 + i * 1.2
        on = i == part
        text(s, x, 0.4, 1.15, 0.25, name, size=10, font=F_H if on else F_T, color=INK if on else MUTE)
        line(s, x, 0.7, x + 1.05, 0.7, color=TEAL if on else HAIR, lw=2.0 if on else 0.75)


def footer(s, n, chain_total=16):
    text(s, MX, 7.02, 4.0, 0.25, "HK–TH TradeEscrow  ·  FTEC3002 Group 1", size=9, color=MUTE)
    if n <= chain_total:                            # journal-chain progress: one linked block per main slide
        bw, gap = 0.13, 0.07
        x0 = (W - (chain_total * bw + (chain_total - 1) * gap)) / 2
        for i in range(chain_total):
            x = x0 + i * (bw + gap)
            if i:
                line(s, x - gap, 7.115, x, 7.115, color=HAIR, lw=0.75)
            cur, past = i + 1 == n, i + 1 < n
            box(s, x, 7.07, bw, 0.09, fill=TEAL if cur else (TEAL_P if past else None), line=None if (cur or past) else HAIR,
                lw=0.75, radius=0.02)
    who = PRESENTER.get(n)
    lab = f"Presented by {who}" if who else ("Final presentation" if n <= chain_total else "Backup")
    text(s, W - MX - 5.2, 7.02, 4.6, 0.25, lab, size=9, color=MUTE, align="r")
    text(s, W - MX - 0.45, 7.02, 0.45, 0.25, f"{n:02d}", size=9, font=F_H, color=INK, align="r")


def title(s, t, sub=None, y=1.0, size=34):
    text(s, MX, y, W - 2 * MX, 0.7, t, size=size, font=F_H, color=INK, spc=-60, ls=0.95)
    if sub:
        text(s, MX, y + 0.68, W - 2 * MX, 0.4, sub, size=15, color=MUTE)


def label(s, x, y, w, t, color=MUTE, size=10.5, align="l"):
    text(s, x, y, w, 0.25, t, size=size, font=F_H, color=color, spc=20, align=align)


def notes(s, n):
    s.notes_slide.notes_text_frame.text = NOTES.get(n, "")


def chrome(s, n, part=None):
    brand(s)
    if part is not None:
        nav(s, part)
    footer(s, n)
    notes(s, n)


def backup_chrome(s, n, code, t, sub=None):
    brand(s)
    text(s, W - MX - 3, 0.4, 3, 0.25, f"Backup {code}", size=10, font=F_H, color=MUTE, align="r")
    line(s, W - MX - 1.05, 0.7, W - MX, 0.7, color=TEAL, lw=2.0)
    title(s, t, sub, size=28)
    footer(s, n)
    notes(s, n)


def shot(name):
    p = ROOT / "results" / "screenshots" / "v2" / name
    j = V4 / "shots" / (Path(name).stem + ".jpg")
    j.parent.mkdir(parents=True, exist_ok=True)
    if not j.exists() or j.stat().st_mtime < p.stat().st_mtime:
        im = Image.open(p).convert("RGB")
        im.thumbnail((2600, 2600))
        im.save(j, quality=90, optimize=True)
    return j


PHOTO = lambda n: V4 / "photos_duo" / f"{n}.jpg"      # navy -> teal duotones (presentation/v4/make_duotone.py)


def strike_last(s):
    s.shapes[-1].text_frame.paragraphs[0].runs[0]._r.get_or_add_rPr().set("strike", "sngStrike")


# ================================================================== slides
def s01_cover():
    s = new_slide()
    picture(s, PHOTO("cover_ship"), 6.55, 0, W - 6.55, H, focus=(0.55, 0.5))
    brand(s)
    text(s, MX, 1.45, 5.6, 0.3, "FTEC3002  Introduction to Financial Infrastructure  ·  Final presentation", size=10.5, color=MUTE)
    text(s, MX, 1.9, 5.7, 2.6, ["Pay when", "the goods", "are proven."], size=54, font=F_H, spc=-150, ls=0.9)
    text(s, MX, 4.62, 5.4, 0.9, "A tokenised-deposit escrow that holds HKD 250,000 until shipment, documents and compliance all pass.",
         size=15, color=INK2, ls=1.1)
    y0 = 5.85                                        # route line: Hong Kong -> Laem Chabang
    dot(s, MX + 0.06, y0, TEAL, 0.07)
    curve(s, lambda t: (MX + 0.06 + t * 4.6, y0 - 0.32 * math.sin(math.pi * t)), color=GOLD, lw=1.75)
    oval(s, MX + 4.66, y0, 0.07, fill=PAPER, line=GOLD, lw=1.75)
    text(s, MX, y0 + 0.13, 2, 0.25, "Hong Kong", size=10, font=F_H)
    text(s, MX + 2.9, y0 + 0.13, 1.85, 0.25, "Laem Chabang", size=10, font=F_H, align="r")
    text(s, MX, 6.42, 5.7, 0.5, ["Tang Yu Hin (Alex)  ·  Chow Ka Shing (Marcus)", "Wong Ho Ming (Michael)  ·  So Lai Chun (Jeff)"],
         size=10, color=INK2, ls=1.1)
    text(s, MX, 6.95, 5.6, 0.25, "Group 1  ·  2026  ·  Working prototype, synthetic data", size=9.5, color=MUTE)
    notes(s, 1)


def s02_since_interim():
    s = new_slide(); chrome(s, 2, 0)
    title(s, "From “it runs” to “does it answer the question?”", "What we added after the interim, and what an independent review made us fix")
    steps = [("7 Nov", "Interim snapshot", "prototype runs; 47 tests; 3 scenarios"),
             ("8 Nov", "Independent review", "found a UI data-access bypass, fixed it"),
             ("Final report", "Evaluation built", "hypotheses H1–H5, fair-scope comparison, financing model"),
             ("Today", "Final answer", "a verdict on each hypothesis")]
    bw, gap, y = 2.75, 0.33, 2.2
    for i, (date, head, desc) in enumerate(steps):
        x = MX + i * (bw + gap)
        last = i == len(steps) - 1
        box(s, x, y, bw, 1.25, fill=INK if last else None, line=None if last else INK, lw=1.0, radius=0.1)
        text(s, x + 0.2, y + 0.16, bw - 0.4, 0.25, date, size=10, color="B9B9B4" if last else MUTE)
        text(s, x + 0.2, y + 0.42, bw - 0.4, 0.3, head, size=15, font=F_H, color=WHITE if last else INK)
        text(s, x + 0.2, y + 0.76, bw - 0.4, 0.45, desc, size=11, color="DADAD5" if last else INK2, ls=1.05)
        if i:
            line(s, x - gap, y + 0.62, x, y + 0.62, color=INK, lw=1.0)
    tiles = [("Tests", "47", fr("M-01"), "+30 access-control, +14 console tests", TEAL),
             ("UI data leak", "open", "fixed", "ledger page now role-projected", TEAL),
             ("Efficiency claim", f"−{v('M-15')}%", f"−{v('M-32')}%", "honest matched-scope comparison", GOLD),
             ("Financing cost", "unmeasured", "measured", "who waits, and how long", GOLD),
             ("Interbank leg", "none", fr("M-12"), "conceptual e-HKD two-leg commit", TEAL)]
    tw, tg, ty = 2.25, 0.207, 3.95
    for i, (lab, old, new, cap, sig) in enumerate(tiles):
        x = MX + i * (tw + tg)
        box(s, x, ty, tw, 2.6, fill=TEAL_T if sig == TEAL else GOLD_T, radius=0.14)
        label(s, x + 0.22, ty + 0.22, tw - 0.4, lab, color=INK)
        text(s, x + 0.22, ty + 0.62, tw - 0.4, 0.3, old, size=13, color=MUTE, strike=True)
        text(s, x + 0.22, ty + 0.95, tw - 0.4, 0.8, new, size=34 if len(new) < 8 else 26, font=F_L, spc=-80, color=sig)
        if sig:
            dot(s, x + tw - 0.3, ty + 0.3, sig, 0.055)
        text(s, x + 0.22, ty + 1.9, tw - 0.4, 0.6, cap, size=11, color=INK2, ls=1.05)


def s03_three_ways():
    s = new_slide(); chrome(s, 3, 0)
    title(s, "Three ways to settle the same HKD 250,000 shipment", "Every settlement method is a choice about who carries the risk, and who pays to remove it")
    cols = [("Open account", "today’s baseline"), ("Documentary credit (L/C)", "the traditional safe option"), ("Pre-funded escrow", "this project")]
    rows = [("Exporter paid", ["after the credit term", "on complying documents", "automatically, when 3 gates pass"]),
            ("Non-payment risk", ["exporter (unsecured)", "issuing bank", "largely removed: funds locked"]),
            ("Who funds the trade", ["exporter extends credit", "importer’s bank credit line", "importer pre-funds in cash"]),
            ("Document checking", ["importer, by hand", "banks, by hand (UCP 600)", "machine match + human review"]),
            ("Audit trail", ["fragmented", "bank records, paper", "shared hash-chained journal"])]
    cw, x0, y0, rh = 3.25, 3.35, 2.25, 0.62
    box(s, x0 + 2 * cw - 0.05, y0 - 0.15, cw + 0.05, 0.75 + rh * len(rows) + 0.25, fill=TEAL_T, radius=0.14)
    for j, (head, sub) in enumerate(cols):
        x = x0 + j * cw + 0.2
        text(s, x, y0, cw - 0.4, 0.3, head, size=15, font=F_H)
        text(s, x, y0 + 0.32, cw - 0.4, 0.25, sub, size=11, color=MUTE)
    for i, (rl, cells) in enumerate(rows):
        y = y0 + 0.82 + i * rh
        line(s, MX, y - 0.1, x0 + 3 * cw - 0.05, y - 0.1, color=HAIR, lw=0.75)
        text(s, MX, y, 2.5, 0.3, rl, size=12, font=F_H, color=INK2)
        for j, c in enumerate(cells):
            text(s, x0 + j * cw + 0.2, y, cw - 0.4, 0.4, c, size=13, color=INK if j == 2 else INK2)
    y = y0 + 0.82 + len(rows) * rh + 0.3
    dot(s, MX + 0.06, y + 0.15, RED, 0.06)
    text(s, MX + 0.25, y, 11.5, 0.35, [[("Escrow buys an L/C-like guarantee without bank credit, ", {"font": F_H}),
                                       ("paid for in importer cash.", {"font": F_H, "color": RED})]], size=15)


def s04_rails():
    s = new_slide(); chrome(s, 4, 0)
    title(s, "Hong Kong is building the rails, but not the conditions", "Each programme solves one layer; none holds money against trade conditions")
    picture(s, PHOTO("port_wide"), MX, 2.2, 3.2, 4.4, focus=(0.5, 0.5), radius=0.14)
    layers = [("Data", "Project CargoX", "cargo and trade data for credit decisions; pilot with 21 banks (May 2026)", False),
              ("Conditional settlement", "our prototype", "hold funds against shipment, documents and compliance; route exceptions to people; regulator view", True),
              ("Money", "Ensemble / e-HKD", "tokenised deposits; e-HKD Phase 2 pilots (mainly retail use cases)", False),
              ("Interbank rails", "EnsembleTX · mBridge", "24/7 settlement in tokenised central-bank money (Nov 2026); multi-CBDC cross-border", False)]
    x, w, y0, lh = 4.3, 4.6, 2.2, 1.04
    for i, (lay, prog, desc, ours) in enumerate(layers):
        y = y0 + i * (lh + 0.08)
        if ours:
            box(s, x, y, w, lh, fill=TEAL_T, line=TEAL, lw=1.75, dash=True, radius=0.12)
        else:
            box(s, x, y, w, lh, fill=CARD, radius=0.12)
        text(s, x + 0.22, y + 0.14, 2.4, 0.3, lay, size=14, font=F_H, color=TEAL if ours else INK)
        text(s, x + 2.4, y + 0.16, w - 2.6, 0.3, prog, size=11, font=F_H, color=TEAL if ours else MUTE, align="r", link=LINKS.get(prog))
        text(s, x + 0.22, y + 0.47, w - 0.44, 0.55, desc, size=11, color=INK2, ls=1.05)
    rx = 9.3
    label(s, rx, 2.2, 3.3, "The gap we target", color=INK, size=11)
    for i, t in enumerate(["holds funds against shipment, document and compliance conditions",
                           "routes discrepancies and alerts to an accountable human",
                           "gives the regulator a privacy-limited reconstruction"]):
        y = 2.65 + i * 0.85
        text(s, rx, y, 0.4, 0.4, f"{i + 1}", size=20, font=F_L, color=TEAL)
        text(s, rx + 0.45, y + 0.04, 2.85, 0.7, t, size=12.5, color=INK2, ls=1.05)
    text(s, rx, 5.4, 3.3, 1.1, "None of the public programmes describes this layer. EnsembleTX (2 Nov 2026) is the rail it could sit on; we are not connected to it.",
         size=11, color=MUTE, ls=1.08)
    text(s, MX, 6.68, 11.8, 0.25, "Sources: HKMA press releases and reports, dated as shown; BIS Project mBridge. Click a programme name to open its source.",
         size=9, color=MUTE)


def s05_hypotheses():
    s = new_slide(); chrome(s, 5, 0)
    mesh(s, y=5.75, h=1.25, crop_top=0.83)
    text(s, MX, 1.05, 0.6, 0.9, "“", size=72, font=F_L, color=MUTE)
    text(s, MX + 0.65, 1.2, 11.2, 1.3, "Can a pre-funded escrow of simulated tokenised deposits make HK–TH trade settlement more efficient, transparent and auditable, while preserving compliance controls?",
         size=24, font=F_L, spc=-40, ls=1.08)
    hy = [("Efficiency", "fewer manual tasks and shorter post-shipment latency, under the same assumptions", "BPMN task inventory · timeline model"),
          ("Safe release", "no release unless every gate is current", f"{v('M-04')} unsafe attempts · {num(d('M-09'))} random checks"),
          ("Safe exceptions", "mismatch → review, AML alert → freeze, never a silent release", "TC-002 · TC-003 · exception tests"),
          ("Auditability", "reviewers can reconstruct events without unrelated commercial data", "role-visibility rules · regulator export"),
          ("Honest cost", "pre-funding shifts the liquidity burden, and this must be measured", "who-waits timeline per model")]
    cw, gap, y = 2.25, 0.207, 3.05
    for i, (name, desc, test) in enumerate(hy):
        x = MX + i * (cw + gap)
        line(s, x, y, x + cw, y, color=INK, lw=1.25)
        text(s, x, y + 0.12, cw, 0.6, f"H{i + 1}", size=30, font=F_L, spc=-60, color=TEAL)
        text(s, x, y + 0.78, cw, 0.3, name, size=15, font=F_H)
        text(s, x, y + 1.14, cw - 0.1, 0.9, desc, size=11.5, color=INK2, ls=1.05)
        text(s, x, y + 2.15, cw, 0.25, "Tested by", size=9.5, font=F_H, color=MUTE)
        text(s, x, y + 2.38, cw - 0.1, 0.5, test, size=10.5, color=INK2)


def s06_cannot_see_ship():
    s = new_slide(); chrome(s, 6, 1)
    title(s, "A smart contract cannot see a ship", "The oracle problem: the code can only check what someone accountable tells it, so we drew the boundary explicitly")
    picture(s, PHOTO("ship_top"), MX, 2.2, 3.55, 3.3, focus=(0.5, 0.5), radius=0.14)
    text(s, MX, 5.65, 3.55, 0.9, [[("The real world", {"font": F_H, "color": INK})], "goods loaded?  documents genuine?  buyer on a sanctions list?"],
         size=11.5, color=INK2, ls=1.08)
    bx = 4.62
    line(s, bx, 2.2, bx, 6.55, color=INK, lw=1.25, dash=True)
    text(s, bx - 0.75, 6.6, 1.5, 0.25, "Trust boundary", size=9.5, font=F_H, align="c")
    atts = [("Shipment attestation", "logistics provider", "shipment ID, on-board date"),
            ("Document attestation", "Bank H operations", "field-by-field match, digest of each revision"),
            ("KYC / AML attestation", "Bank H compliance", "PASS / FAIL, timestamp, expiry")]
    cx0, cw = 4.95, 2.47
    for i, (a, who, what) in enumerate(atts):
        x = cx0 + i * (cw + 0.12)
        box(s, x, 2.2, cw, 1.12, fill=TEAL_T, radius=0.12)
        text(s, x + 0.18, 2.32, cw - 0.3, 0.3, a, size=12.5, font=F_H)
        text(s, x + 0.18, 2.6, cw - 0.3, 0.25, f"by {who}", size=10, color=MUTE)
        text(s, x + 0.18, 2.86, cw - 0.3, 0.4, what, size=10, color=INK2)
    lists = [("The engine can verify", True, ["attestation is for this trade", "document revision is the latest", "screening is fresh (≤ 48 h)",
                                              "who issued it, and their role", "amounts add up; supply conserved"]),
             ("It must trust", False, ["the goods were really loaded", "documents are genuine", "the sanctions list was current",
                                       "attesters are not colluding"])]
    for j, (head, ok, items) in enumerate(lists):
        x = cx0 + j * 3.95
        text(s, x, 3.55, 3.6, 0.3, head, size=13, font=F_H)
        for k, it in enumerate(items):
            y = 3.92 + k * 0.3
            text(s, x, y, 0.3, 0.3, "✓" if ok else "?", size=12, font=F_H, color=TEAL if ok else MUTE)
            text(s, x + 0.3, y, 3.4, 0.3, it, size=12, color=INK2)
    box(s, cx0, 5.62, 7.65, 0.93, fill=INK, radius=0.12)
    text(s, cx0 + 0.25, 5.62, 7.2, 0.93, [[("Design consequence.  ", {"font": F_H, "color": WHITE}),
                                           ("Every attestation names an accountable issuer, a trade ID, a content digest and an expiry. The engine re-checks all of them at the moment of release, so a stale, swapped or revised fact cannot release money.",
                                            {"color": "DADAD5"})]], size=11.5, ls=1.08, anchor="m")


def s07_seven_checks():
    s = new_slide(); chrome(s, 7, 1)
    title(s, "Seven release checks, each closing a specific loophole", "The ring is the release guard in the console: funds move only when all seven segments are solid")
    cx, cy, r = 2.55, 4.35, 1.62
    ring(s, cx, cy, r, 0.2, ["ok"] * 7)
    text(s, cx - 1.0, cy - 0.5, 2.0, 0.7, "7", size=44, font=F_L, align="c")
    text(s, cx - 1.0, cy + 0.22, 2.0, 0.3, "checks, all required", size=11, color=MUTE, align="c")
    for i in range(7):
        a = math.radians(-90 + (i + 0.5) * 360 / 7)
        text(s, cx + (r + 0.25) * math.cos(a) - 0.15, cy + (r + 0.25) * math.sin(a) - 0.13, 0.3, 0.26, str(i + 1),
             size=10, font=F_H, color=MUTE, align="c")
    rows = [("Shipment", "shipment attested for this trade’s shipment ID", "use another trade’s shipment evidence", "NC-17", "ESCROW_NOT_READY"),
            ("Documents", "documents PASS on the current revision", "get approval, then quietly revise the invoice", "NC-05", "DOCUMENTS_NOT_VERIFIED"),
            ("Compliance", "pre-release screening less than 48 h old", "rely on an old screening result", "NC-07", "PRE_RELEASE_KYC_EXPIRED"),
            ("Compliance", "screening newer than the last approval and hold", "clear a hold without re-screening", "NC-11", "PRE_RELEASE_KYC_MISSING"),
            ("Compliance", "no active compliance hold", "release after an analyst adds a hold", "NC-10", "ESCROW_FROZEN"),
            ("State", "escrow is Pending and holds the full amount", "release twice, or before shipment", "NC-12", "TERMINAL_STATE"),
            ("Role", "only the contract engine may move funds", "importer, exporter or regulator presses Release", "NC-14–16", "RBAC_DENIED")]
    x0, y0, rh = 4.85, 2.6, 0.52
    for cx_, cw_, h_ in [(x0, 0.35, "#"), (x0 + 0.35, 1.15, "Gate"), (x0 + 1.5, 2.6, "The check"), (x0 + 4.1, 2.35, "The loophole it closes"),
                         (x0 + 6.45, 1.3, "Test · engine says")]:
        text(s, cx_, y0 - 0.32, cw_, 0.25, h_, size=9.5, font=F_H, color=MUTE)
    for i, (gate, check, hole, test, code) in enumerate(rows):
        y = y0 + i * rh
        line(s, x0, y - 0.04, W - MX, y - 0.04, color=HAIR, lw=0.75)
        text(s, x0, y + 0.06, 0.3, 0.3, str(i + 1), size=11, font=F_H, color=MUTE)
        text(s, x0 + 0.35, y + 0.06, 1.15, 0.3, gate, size=11, font=F_H)
        text(s, x0 + 1.5, y + 0.06, 2.5, 0.45, check, size=10.5, color=INK2, ls=1.0)
        text(s, x0 + 4.1, y + 0.06, 2.3, 0.45, [[("✕  ", {"color": RED, "font": F_H}), hole]], size=10.5, color=INK2, ls=1.0)
        text(s, x0 + 6.45, y + 0.04, 1.35, 0.25, test, size=9.5, font=F_H)
        text(s, x0 + 6.45, y + 0.25, 1.4, 0.25, code, size=7.5, font=F_M, color=RED)
    y = y0 + 7 * rh + 0.12
    tick(s, x0, y, True, 13)
    text(s, x0 + 0.3, y, 7.6, 0.3, f"All {fr('M-04')} attempts refused, funds unchanged; the positive control released once.",
         size=12, font=F_H)


def s08_invariants():
    s = new_slide(); chrome(s, 8, 1)
    title(s, "Five properties that hold after every command", "Not features but invariants: if any one breaks, the system is wrong, whatever the screen says")
    cards = [("Conservation", "total token supply never changes; escrow balance = locked amount", "checked after every command", f"0 / {num(d('M-09'))} violations"),
             ("Exactly once", "a release or refund cannot happen twice, even if the command is re-sent", "idempotency keys + terminal states", "duplicate release refused"),
             ("Default deny", "a state change not in the 15-move table is an error, not a choice", "transition table in code", "illegal moves raise and log"),
             ("Least privilege", "each role sees and does only its own part; the regulator sees metadata", "server-side permissions + projections", f"{fr('M-08')} visibility rules"),
             ("Tamper evidence", "every accepted and refused command is chained by SHA-256", "verifier recomputes the chain", "edits and deletions detected")]
    cw, gap, y = 2.25, 0.207, 2.35
    for i, (name, desc, how, res) in enumerate(cards):
        x = MX + i * (cw + gap)
        box(s, x, y, cw, 4.15, fill=CARD, radius=0.14)
        ring(s, x + 0.42, y + 0.45, 0.2, 0.05, ["ok"] * 7, gap_deg=10)
        text(s, x + 0.22, y + 0.85, cw - 0.4, 0.3, name, size=16, font=F_H)
        text(s, x + 0.22, y + 1.25, cw - 0.4, 1.2, desc, size=11.5, color=INK2, ls=1.06)
        line(s, x + 0.22, y + 2.6, x + cw - 0.22, y + 2.6, color=HAIR, lw=0.75)
        text(s, x + 0.22, y + 2.72, cw - 0.4, 0.25, "How we check it", size=9.5, font=F_H, color=MUTE)
        text(s, x + 0.22, y + 2.95, cw - 0.4, 0.5, how, size=11, color=INK2)
        tick(s, x + 0.2, y + 3.55, True, 12)
        text(s, x + 0.48, y + 3.55, cw - 0.6, 0.5, res, size=12, font=F_H)


def s09_live():
    s = new_slide(); chrome(s, 9, 2)
    title(s, "Live: one trade, three outcomes", "Watch the release guard decide, and watch what each role is allowed to see")
    picture(s, shot("light_tc001_released.png"), MX, 2.15, 7.55, 7.55 / 1.764, radius=0.1, shadow=True)
    text(s, MX, 6.62, 7.5, 0.25, "Real console, light theme  ·  synthetic data  ·  TC-001 after release, viewed by Bank H operations", size=9.5, color=MUTE)
    rx = 8.85
    label(s, rx, 2.2, 3.7, "What to watch", color=INK, size=11)
    cues = [("TC-001", "clean trade", "all 7 guard checks pass → Released, once", TEAL),
            ("Regulator", "presses Release", "refused: RBAC_DENIED, and the refusal is logged", RED),
            ("TC-002", "invoice HKD 245,000", "Under Review → reviewer revalidates → Released", INK),
            ("TC-003", "watchlist hit", "Frozen: release and refund both refused", RED)]
    for i, (a, b, c, sig) in enumerate(cues):
        y = 2.65 + i * 0.95
        oval(s, rx + 0.18, y + 0.17, 0.18, line=TEAL, lw=1.25)
        text(s, rx, y + 0.04, 0.36, 0.26, str(i + 1), size=11, font=F_H, align="c")
        text(s, rx + 0.55, y, 3.2, 0.3, [[(a + "  ", {"font": F_H}), (b, {"color": MUTE})]], size=13)
        text(s, rx + 0.55, y + 0.33, 3.2, 0.5, c, size=11.5, color=INK2)
        dot(s, rx + 3.75, y + 0.12, sig, 0.045)
    text(s, rx, 6.45, 3.8, 0.4, "If the live demo fails: backup video, then slide B6 screenshots.", size=10, color=MUTE)


def s10_break_it():
    s = new_slide(); chrome(s, 10, 2)
    title(s, "Four ways we tried to break it", "Each column shows what the test did, and what came out")
    cols = [("The test suite", fr("M-01"), "automated tests pass",
             ["24 planned test cases", "3 flagship scenarios", "role permissions", "hash-chain tamper check", "UI access per role", "e-HKD two-leg commit"]),
            ("Unsafe release attempts", fr("M-04"), "blocked, funds unchanged",
             ["no shipment proof", "invoice ≠ contract", "screening 49 h old", "AML hold active", "regulator presses Release", "+ 12 more, all refused"]),
            ("Random stress test", f"0 / {num(d('M-09'))}", "invariant violations",
             ["200 synthetic trades", f"{num(v('M-10'))} random commands", "fund · attest · freeze", "release · refund · review",
              "after each: token supply still HKD 500,000"]),
            ("Seeded bugs", fr("M-11"), "caught by the tests",
             ["we broke the code on purpose 14 ways", "e.g. “guard ignores holds”", "e.g. “screening never expires”",
              "the one survivor is redundant: the database lock already serialises writes"])]
    cw, gap, y = 2.75, 0.33, 2.25
    for i, (head, big, cap, items) in enumerate(cols):
        x = MX + i * (cw + gap)
        line(s, x, y, x + cw, y, color=INK, lw=1.25)
        label(s, x, y + 0.14, cw, head, color=INK, size=11)
        text(s, x, y + 0.45, cw, 1.0, big, size=50, font=F_L, spc=-120, color=TEAL)
        text(s, x, y + 1.42, cw, 0.3, cap, size=12, font=F_H, color=INK2)
        for k, it in enumerate(items):
            text(s, x, y + 1.85 + k * 0.29, cw - 0.1, 0.3, it, size=10.5, color=INK2, ls=1.0)
    box(s, MX, 6.22, W - 2 * MX, 0.58, fill=GOLD_T, radius=0.1)
    text(s, MX + 0.25, 6.22, W - 2 * MX - 0.5, 0.58, [[("What this does not show.  ", {"font": F_H, "color": GOLD}),
                                                      ("These are our own tests of our own rules on synthetic data. They cannot prove that real attestations are honest, that the system resists attackers, or that it scales.",
                                                       {"color": INK2})]], size=11.5, anchor="m")


def s11_leak():
    s = new_slide(); chrome(s, 11, 2)
    title(s, "47 green tests, and the system was still leaking data", "What an independent review caught, and what we changed because of it")
    lx, rx, cw, y = MX, 6.92, 5.67, 2.2
    label(s, lx, y, cw, "Before  ·  interim build", color=RED, size=11)
    label(s, rx, y, cw, "After  ·  final build", color=TEAL, size=11)
    box(s, lx, y + 0.35, cw, 2.3, fill=WHITE, line=HAIR, lw=0.75, radius=0.12)
    text(s, lx + 0.3, y + 0.5, cw - 0.6, 0.3, "Ledger, acting as importer #2", size=13, font=F_H)
    for i, (acc, bal, bad) in enumerate([("importer_hk_01", "HKD 150,000.00", True), ("importer_hk_02", "HKD 100,000.00", False),
                                         ("exporter_th_01", "HKD 250,000.00", True), ("escrow ESC-001", "HKD 0.00", True)]):
        yy = y + 0.95 + i * 0.4
        line(s, lx + 0.3, yy - 0.06, lx + cw - 0.3, yy - 0.06, color=HAIR, lw=0.75)
        text(s, lx + 0.3, yy, 1.9, 0.3, acc, size=11, font=F_M)
        text(s, lx + 2.25, yy, 1.6, 0.3, bal, size=11, font=F_M)
        if bad:
            text(s, lx + 3.85, yy, 1.6, 0.3, "visible, should not be", size=10, color=RED, italic=True)
    picture(s, shot("light_ledger_regulator.png"), rx, y + 0.35, cw, 2.3, focus=(0.5, 0.05), radius=0.12, shadow=True)
    text(s, lx, y + 2.75, cw, 0.25, "Schematic of the interim page (illustrative balances): every role saw every account", size=9.5, color=MUTE)
    text(s, rx, y + 2.75, cw, 0.25, "Ledger page as the regulator today: metadata only, no balances", size=9.5, color=MUTE)
    for i, t in enumerate(["47 / 47 tests passed", "tests checked the engine, not the web page", "importer #2 could read importer #1’s balance"]):
        text(s, lx, y + 3.12 + i * 0.3, cw, 0.3, [[("✕  ", {"color": RED, "font": F_H}), t]], size=12, color=INK2)
    for i, t in enumerate(["server-side projection per role", "logistics / customs: denied, refusal logged", f"+30 HTTP tests → 77/77 at the time ({fr('M-01')} today)"]):
        text(s, rx, y + 3.12 + i * 0.3, cw, 0.3, [[("✓  ", {"color": TEAL, "font": F_H}), t]], size=12, color=INK2)
    box(s, MX, 6.3, W - 2 * MX, 0.52, fill=INK, radius=0.1)
    text(s, MX + 0.25, 6.3, W - 2 * MX - 0.5, 0.52, [[("Lesson.  ", {"font": F_H, "color": WHITE}),
                                                       (f"Tests only check what you thought of. The same review found our mutation harness scoring 14/14 by mistake; fixed, the honest score is {fr('M-11')}.",
                                                        {"color": "DADAD5"})]], size=12, anchor="m")


def s12_scorecard():
    s = new_slide(); chrome(s, 12, 2)
    title(s, "Scorecard: what the evidence says about H1–H5", "Five different verdicts, because the evidence behind each is different")
    rows = [("H1", "Efficiency", "Supported, model only", "model", f"manual tasks {v('M-13')} → {v('M-14')} ({v('M-31')} at matched scope); latency {v('M-21')} → {v('M-22')} simulated days", "process model and assumed durations, not measurement"),
            ("H2", "Safe release", "Supported in simulation", "ok", f"{fr('M-04')} unsafe releases blocked; 0 violations in {num(d('M-09'))} random checks", "our own tests of our own rules"),
            ("H3", "Safe exceptions", "Supported in simulation", "ok", f"mismatch → Under Review; alert → Frozen; {fr('M-02')} scenario assertions", "synthetic alerts; real AML duties are wider"),
            ("H4", "Auditability", "Supported for our role model", "ok", f"{fr('M-08')} visibility rules; regulator rebuilt {fr('M-07')} state paths from metadata alone", "enforced in code, not cryptographically"),
            ("H5", "Honest cost", "Confirmed trade-off", "cost", f"importer cash committed {v('M-24')} → {v('M-25')} days; exporter risk {v('M-21')} → 0 days", "escrow moves the financing cost (Part 4)")]
    y0 = 2.3
    for x, h_ in [(MX, "Hypothesis"), (3.25, "Verdict"), (6.1, "Evidence"), (10.2, "Caveat")]:
        text(s, x, y0, 2, 0.25, h_, size=9.5, font=F_H, color=MUTE)
    for i, (hid, name, verdict, kind, ev, cav) in enumerate(rows):
        y = y0 + 0.38 + i * 0.8
        line(s, MX, y - 0.08, W - MX, y - 0.08, color=HAIR, lw=0.75)
        text(s, MX, y, 0.7, 0.5, hid, size=24, font=F_L, spc=-40)
        text(s, MX + 0.75, y + 0.1, 1.7, 0.3, name, size=13, font=F_H)
        if kind == "model":
            oval(s, 3.33, y + 0.22, 0.06, line=GOLD, lw=1.5)
        else:
            dot(s, 3.33, y + 0.22, TEAL if kind == "ok" else RED, 0.06)
        text(s, 3.5, y + 0.1, 2.5, 0.3, verdict, size=12, font=F_H, color={"cost": RED, "model": GOLD}.get(kind, INK))
        text(s, 6.1, y + 0.08, 3.9, 0.6, ev, size=11, color=INK2, ls=1.03)
        text(s, 10.2, y + 0.08, 2.4, 0.6, cav, size=10.5, color=MUTE, ls=1.03)


def s13_efficiency():
    s = new_slide(); chrome(s, 13, 3)
    title(s, "How big is the efficiency gain, really?", "Our first figure flattered the escrow. A fair comparison halves the claim, and the direction survives")
    scen = [("normal", "Normal trade"), ("mismatch", "Document mismatch"), ("aml", "AML alert")]
    models = [("baseline", "Open account", "solid"), ("proposed", "Escrow, prototype scope", "outline"), ("proposed_e2e", "Escrow, matched scope", "grey")]
    x0, scale, y0 = 2.75, 0.62, 2.35
    style = {"solid": dict(fill=INK), "outline": dict(fill=TEAL_T, line=TEAL, lw=1.0), "grey": dict(fill=GOLD)}
    for i, (sk, sname) in enumerate(scen):
        y = y0 + i * 1.18
        text(s, MX, y + 0.2, 2.0, 0.3, sname, size=12.5, font=F_H)
        for j, (mk, _, st) in enumerate(models):
            n_ = PROC[(sk, mk)]
            yy = y + j * 0.3
            for t in range(n_):                      # one block per manual settlement task
                box(s, x0 + t * scale, yy, scale - 0.07, 0.22, radius=0.03, **style[st])
            text(s, x0 + n_ * scale + 0.05, yy - 0.02, 0.4, 0.25, str(n_), size=11, font=F_H)
    ly = y0 + 3 * 1.18 + 0.05
    for j, (_, mname, st) in enumerate(models):
        x = x0 + [0, 1.65, 3.85][j]
        box(s, x, ly + 0.04, 0.22, 0.16, radius=0.02, **style[st])
        text(s, x + 0.3, ly, 1.9, 0.3, mname, size=9.5, color=INK2)
    text(s, x0, ly + 0.34, 6.4, 0.25, "One block = one manual settlement task per trade.", size=9.5, color=MUTE)
    rx = 9.4
    label(s, rx, 2.3, 3.2, "Why the first number was unfair", color=INK, size=11)
    text(s, rx, 2.65, 3.2, 1.6, "The baseline ends when Bank O credits the exporter. Our prototype ends earlier, at a Bank H release. Adding the missing steps (redemption, cross-bank payment, Bank O credit, reconciliation) gives a like-for-like count.",
         size=11, color=INK2, ls=1.07)
    text(s, rx, 4.45, 1.7, 0.6, f"−{v('M-15')}%", size=26, font=F_L, color=MUTE, strike=True)
    text(s, rx + 1.75, 4.62, 1.5, 0.3, "prototype scope", size=10, color=MUTE)
    text(s, rx, 5.05, 3.2, 0.9, f"−{v('M-32')}%", size=46, font=F_L, spc=-100, color=GOLD)
    text(s, rx, 5.88, 3.2, 0.5, "matched scope: the claim we stand by", size=11, font=F_H, color=GOLD)
    text(s, MX, 6.62, 11.8, 0.25, "Team process model, not measured: results/process_counts.csv; goods, customs, carriage and FX tasks excluded in all models. Full maps: backup B3–B4.",
         size=9, color=MUTE)


def s14_tradeoff():
    s = new_slide(); chrome(s, 14, 3)
    title(s, "Faster release is paid for by earlier importer funding", "Who waits, and for how long: normal trade, base assumptions, simulated days from contract")
    rows = [("Open account, pay at once", TL[("baseline", "0")]), ("Open account, 30-day term", TL[("baseline", "30")]),
            ("Escrow (prototype)", TL[("proposed", "0")]), ("Escrow + cross-bank leg (hypothetical)", TL[("proposed_e2e", "0")])]
    x0, px, y0, rh = 3.75, 0.135, 2.45, 0.85
    for k in range(0, 50, 5):
        x = x0 + k * px
        line(s, x, y0 - 0.1, x, y0 + 4 * rh - 0.1, color=HAIR, lw=0.5)
        text(s, x - 0.2, y0 + 4 * rh - 0.05, 0.4, 0.25, str(k), size=9, color=MUTE, align="c")
    text(s, x0, y0 + 4 * rh + 0.2, 6.3, 0.25, "days from contract", size=9.5, color=MUTE, align="c")
    for i, (name, r) in enumerate(rows):
        y = y0 + i * rh
        ship, cred = float(r["t_shipment_d"]), float(r["t_credited_d"])
        imp, unsec = float(r["importer_funds_committed_d"]), float(r["exporter_unsecured_receivable_d"])
        text(s, MX, y - 0.04, 2.95, 0.3, name, size=12, font=F_H)
        text(s, MX, y + 0.24, 2.95, 0.3, f"importer {imp:g} d  ·  exporter at risk {unsec:g} d", size=10, color=MUTE)
        box(s, x0 + (cred - imp) * px, y + 0.02, imp * px, 0.17, fill=GOLD, radius=0.02)
        if unsec > 0:
            box(s, x0 + ship * px, y + 0.26, unsec * px, 0.17, fill=RED, radius=0.02)
        else:
            box(s, x0 + ship * px, y + 0.26, max(0.05, (cred - ship) * px), 0.17, fill=TEAL_T, line=TEAL, lw=1.0, radius=0.02)
    ly = y0 + 4 * rh + 0.55
    for j, (lab, kw) in enumerate([("Importer cash committed", dict(fill=GOLD)), ("Exporter unpaid and unsecured", dict(fill=RED)),
                                   ("Exporter waiting (escrow-secured)", dict(fill=TEAL_T, line=TEAL, lw=1.0))]):
        x = MX + j * 3.0
        box(s, x, ly + 0.05, 0.3, 0.14, radius=0.02, **kw)
        text(s, x + 0.4, ly, 2.6, 0.3, lab, size=10, color=INK2)
    rx = 10.35
    box(s, rx, 2.35, W - MX - rx, 3.2, fill=GOLD_T, radius=0.14)
    text(s, rx + 0.22, 2.55, W - MX - rx - 0.44, 1.6, "Escrow does not remove financing cost. It moves it from the exporter to the importer.",
         size=15, font=F_H, ls=1.08)
    text(s, rx + 0.22, 4.25, W - MX - rx - 0.44, 1.1, f"Shipment → release: {v('M-21')} → {v('M-22')} simulated days", size=11, color=INK2)
    text(s, W - MX - 4.5, 6.68, 4.5, 0.25, "Assumed timings, simulated days: results/timelines.csv", size=9, color=MUTE, align="r")


def s15_must_be_true():
    s = new_slide(); chrome(s, 15, 3)
    title(s, "What would have to be true for this to work for real", "Each simplification we made is a question a bank, a regulator or a lawyer would have to answer")
    rows = [("Attestations are honest", "a false bill of lading would pass our gates", "signed e-B/L or CargoX-type trade data, with liability"),
            ("Settlement is final across borders", "Bank O only observes a HKD claim on Bank H", "an interbank leg in tokenised central-bank money (e.g. EnsembleTX)"),
            ("Tokenised escrow is legally sound", "ownership, segregation and insolvency not modelled", "legal opinion in both jurisdictions"),
            ("Someone finances the wait", f"importer locks cash for {v('M-25')} days", "bank finances or remunerates the escrow balance"),
            ("Shared ledger beats a shared database", "one Bank H database could run the same rules", "only true with independent bank and regulator nodes")]
    y0 = 2.3
    for x, h_ in [(1.45, "What must be true"), (5.4, "In our prototype"), (9.0, "What could make it true")]:
        text(s, x, y0, 3.5, 0.25, h_, size=9.5, font=F_H, color=MUTE)
    for i, (a, b, c) in enumerate(rows):
        y = y0 + 0.4 + i * 0.8
        line(s, MX, y - 0.1, W - MX, y - 0.1, color=HAIR, lw=0.75)
        ring(s, MX + 0.25, y + 0.2, 0.19, 0.045, ["gold"] + ["off"] * 6, gap_deg=12)
        text(s, 1.45, y + 0.04, 3.8, 0.4, a, size=13.5, font=F_H)
        text(s, 5.4, y + 0.06, 3.4, 0.6, b, size=11.5, color=INK2, ls=1.03)
        text(s, 9.0, y + 0.06, 3.6, 0.6, c, size=11.5, color=INK2, ls=1.03)
    text(s, MX, 6.68, 11.8, 0.25, [[("HKMA press releases: EnsembleTX (2 Nov 2026), CargoX pilot (7 May 2026).   ", {}),
                                    ("EnsembleTX", {"link": LINKS.get("EnsembleTX"), "font": F_H, "color": INK}), ("   ", {}),
                                    ("CargoX", {"link": LINKS.get("CargoX"), "font": F_H, "color": INK})]], size=9, color=MUTE)


def s16_answer():
    s = new_slide()
    picture(s, PHOTO("hk_harbour"), 0, 0, W, 3.25, focus=(0.5, 0.62))
    text(s, MX, 3.55, 9, 1.1, "A qualified yes.", size=54, font=F_H, spc=-150)
    text(s, MX, 4.45, 9, 0.35, "Within a synthetic simulation, and with the conditions stated", size=15, color=MUTE)
    cols = [("H2 · H3 · H4", "Safer and auditable", "Every release, review and freeze rule held; every action is reconstructable, and the regulator sees only metadata.", TEAL),
            ("H1", "Modestly more efficient", f"About {v('M-32')}% fewer manual settlement tasks at matched scope: a model, not a measurement.", GOLD),
            ("H5", "Not free", "It moves financing cost from exporter to importer. Real value depends on trusted data, finality and law.", RED)]
    cw, gap, y = 3.75, 0.27, 5.0
    for i, (tag, head, body, sig) in enumerate(cols):
        x = MX + i * (cw + gap)
        line(s, x, y, x + cw, y, color=INK, lw=1.0)
        dot(s, x + 0.06, y + 0.3, sig, 0.055)
        text(s, x + 0.22, y + 0.17, cw - 0.3, 0.3, [[(head + "  ", {"font": F_H, "size": 14}), (tag, {"color": MUTE, "size": 10})]])
        text(s, x, y + 0.55, cw - 0.1, 0.9, body, size=11, color=INK2, ls=1.05)
    text(s, MX, 6.6, 9.5, 0.3, "Next: connect the shipment gate to signed trade data · add an interbank leg · replace our assumptions with practitioner timings.",
         size=10.5, color=MUTE)
    text(s, W - MX - 3, 6.5, 3, 0.4, "Thank you. Questions?", size=15, font=F_H, align="r")
    footer(s, 16); notes(s, 16)


def s17_backup_index():
    s = new_slide()
    picture(s, PHOTO("yard_diag"), 7.4, 0, W - 7.4, H, focus=(0.5, 0.5))
    brand(s)
    text(s, MX, 1.3, 6, 1.0, "Backup", size=54, font=F_H, spc=-150)
    items = ["Full architecture", "Escrow state machine", "Baseline BPMN", "Proposed BPMN", "Who may do what",
             "Demo fallback: real screenshots", "e-HKD two-leg cases", "Sources", "Likely questions"]
    for i, t in enumerate(items):
        y = 2.65 + i * 0.44
        line(s, MX, y - 0.06, 6.6, y - 0.06, color=HAIR, lw=0.75)
        text(s, MX, y, 0.6, 0.3, f"B{i + 1}", size=12, font=F_H, color=MUTE)
        text(s, MX + 0.7, y, 5.2, 0.3, t, size=13)
    footer(s, 17); notes(s, 17)


def how_to_read(s, x, items, asked):
    """Side notes on diagram backups; blocks are sized from text length, using the largest font that fits."""
    def layout(size):
        lh, per = size / 72 * 1.22, lambda w_in: int(w_in * 72 / (size * 0.5))
        h_ = lambda t, w_in: math.ceil(len(t) / per(w_in)) * lh
        y_ = 2.58 + sum(h_(t, 3.1) + 0.12 for t in items) + 0.4 + sum(h_(q + "  " + a, 3.4) + 0.14 for q, a in asked)
        return y_, h_
    size = next(sz for sz in (10, 9.5, 9, 8.5) if layout(sz)[0] < 6.9)
    hgt = layout(size)[1]
    label(s, x, 2.25, 3.4, "How to read it", color=INK, size=11)
    y = 2.58
    for i, t in enumerate(items):
        text(s, x, y, 0.3, 0.3, str(i + 1), size=size, font=F_H, color=MUTE)
        text(s, x + 0.3, y, 3.1, hgt(t, 3.1), t, size=size, color=INK2, ls=1.04)
        y += hgt(t, 3.1) + 0.12
    label(s, x, y + 0.08, 3.4, "If asked", color=INK, size=11)
    y += 0.4
    for q, a in asked:
        t = q + "  " + a
        text(s, x, y, 3.4, hgt(t, 3.4), [[(q + "  ", {"font": F_H, "color": INK}), a]], size=size, color=INK2, ls=1.04)
        y += hgt(t, 3.4) + 0.14
    assert y < 6.95, f"side notes overflow the slide (ends at {y:.2f} in)"


def s18_architecture():
    s = new_slide(); backup_chrome(s, 18, "B1", "Full architecture and trust boundaries")
    src = V4 / "architecture_fig1.png"              # report Figure 1 as embedded in the final report
    g = V4 / "shots" / "architecture_mono.png"
    g.parent.mkdir(parents=True, exist_ok=True)
    if not g.exists() or g.stat().st_mtime < src.stat().st_mtime:
        Image.open(src).convert("L").convert("RGB").save(g, optimize=True)
    box(s, MX, 2.15, 8.1, 4.55, fill=WHITE, radius=0.14)
    picture(s, g, MX + 0.15, 2.3, 7.8, 4.25, contain=True)
    how_to_read(s, 9.2, ["Top row: the business roles. Each acts through the same UI; the role is picked in a selector and permissions are checked by the server.",
                         "Dashed box on the left: facts from outside (shipment, documents, KYC/AML). They arrive as attestations; the engine cannot observe them.",
                         "Centre: the engine. It authorises each command, runs the state machine and writes every command to a hash-chained journal.",
                         "Right: token accounts, the SQLite ledger and role-limited views. Bottom right: what is not connected."],
                [("Is this a blockchain?", "No. A single permissioned service with a hash-chained log: tamper-evident, not distributed (slide 15)."),
                 ("Why is Bank H in the middle?", "Bank H holds the escrow account and runs the engine; Bank O only observes.")])


def s19_state_machine():
    s = new_slide(); backup_chrome(s, 19, "B2", "Escrow state machine: six states, fifteen legal moves")
    box(s, MX, 2.15, 8.1, 4.55, fill=WHITE, radius=0.14)
    ox, oy, sc = MX + 0.45, 2.75, 0.0095             # console lifecycle-map geometry (viewBox 760 x 200), scaled
    P = {"Created": (60, 55), "Pending": (320, 55), "Released": (690, 55), "Under Review": (190, 145), "Frozen": (470, 145), "Refunded/Terminated": (690, 145)}
    tx = lambda p: (ox + p[0] * sc, oy + p[1] * sc * 1.9)
    edges = [("Created", "Pending", False), ("Pending", "Released", False), ("Created", "Under Review", True), ("Pending", "Under Review", True),
             ("Created", "Frozen", True), ("Pending", "Frozen", True), ("Under Review", "Frozen", True),
             ("Under Review", "Refunded/Terminated", True), ("Frozen", "Refunded/Terminated", True)]
    for a, b, exc in edges:
        (x1, y1), (x2, y2) = tx(P[a]), tx(P[b])
        line(s, x1, y1, x2, y2, color=MUTE if exc else INK, lw=1.0 if exc else 2.0, dash=exc)
    for name, p in P.items():
        x, y = tx(p)
        fill = TEAL if name == "Released" else (RED if name == "Frozen" else WHITE)
        oval(s, x, y, 0.13, fill=fill, line=INK, lw=1.5)
        if name in ("Released", "Refunded/Terminated"):
            oval(s, x, y, 0.19, line=INK, lw=0.9)
        up = p[1] < 100
        text(s, x - 1.0, y - 0.5 if up else y + 0.24, 2.0, 0.3, name, size=11.5, font=F_H, align="c")
    text(s, MX + 0.3, 6.25, 7.6, 0.3, "Solid: the happy path, release only through the guard.  Dashed: exceptions and exits that need a named human.",
         size=10, color=MUTE)
    how_to_read(s, 9.2, ["Happy path: Created → Pending (shipment attested) → Released, only through the release guard.",
                         "Dashed lines: exceptions. A document failure sends a trade to Under Review; an AML alert sends it to Frozen, from any open state.",
                         "Exits from exceptions need a named human: a reviewer revalidates, compliance clears (then re-screens), or either terminates and refunds.",
                         "Double ring = terminal. Released and Refunded accept no further command; any move not drawn is rejected and logged."],
                [("Can Frozen go straight to Released?", "No. Compliance can only clear it back to Pending; release then needs a fresh screening (NC-11)."),
                 ("Why can Under Review go back to Created?", "If documents are fixed before shipment, there is no shipment attestation yet.")])


def bpmn_slide(n, code, t, img, items, asked):
    s = new_slide(); backup_chrome(s, n, code, t)
    box(s, MX, 2.15, 8.1, 4.55, fill=WHITE, radius=0.14)
    picture(s, ROOT / "diagrams" / "slide" / img, MX + 0.15, 2.3, 7.8, 4.25, contain=True)
    how_to_read(s, 9.2, items, asked)


def s22_permissions():
    s = new_slide(); backup_chrome(s, 22, "B5", "Who may do what, enforced inside the engine")
    rows = [("HK importer", "create & fund escrow; upload contract; dispute", "release; compliance decisions; other trades"),
            ("Thai exporter", "submit invoice / bill of lading; dispute", "clear AML hold; screening; release"),
            ("Bank H operations", "document check; resolve review; trigger release", "terminate during an AML hold"),
            ("Bank H compliance", "screening; raise / clear / confirm holds", "release directly after clearance"),
            ("Thai Bank O", "acknowledge receipt (observation)", "any fund movement"),
            ("Logistics / customs", "shipment attestation / customs declaration", "another trade’s shipment"),
            ("Regulator", "metadata-only audit export", "every state-changing command")]
    y0 = 2.3
    for x, h_ in [(MX, "Role"), (3.6, "May issue"), (8.4, "Refused (tested)")]:
        text(s, x, y0, 3, 0.25, h_, size=9.5, font=F_H, color=MUTE)
    for i, (r, may, no) in enumerate(rows):
        y = y0 + 0.38 + i * 0.58
        line(s, MX, y - 0.08, W - MX, y - 0.08, color=HAIR, lw=0.75)
        text(s, MX, y, 2.8, 0.3, r, size=13, font=F_H)
        text(s, 3.6, y, 4.6, 0.4, [[("✓  ", {"color": TEAL, "font": F_H}), may]], size=12, color=INK2)
        text(s, 8.4, y, 4.2, 0.4, [[("✕  ", {"color": RED, "font": F_H}), no]], size=12, color=INK2)


def s23_fallback():
    s = new_slide(); backup_chrome(s, 23, "B6", "Demo fallback: the three scenarios in the real console")
    shots = [("TC-001  ·  released once", "light_tc001_released.png", "All 7 guard checks pass; HKD 250,000 moves to the exporter exactly once."),
             ("TC-002  ·  Under Review", "light_tc002_review.png", "Invoice HKD 245,000 vs contract 250,000: release refused (ESCROW_UNDER_REVIEW)."),
             ("TC-003  ·  Frozen", "light_tc003_frozen.png", "Watchlist hit: release refused (ESCROW_FROZEN, ACTIVE_HOLD); funds stay locked.")]
    cw, gap = 3.75, 0.27
    for i, (head, f, cap) in enumerate(shots):
        x = MX + i * (cw + gap)
        text(s, x, 2.25, cw, 0.3, head, size=13, font=F_H)
        picture(s, shot(f), x, 2.65, cw, cw / 1.764, radius=0.08, shadow=True)
        text(s, x, 2.65 + cw / 1.764 + 0.2, cw, 0.6, cap, size=11, color=INK2, ls=1.05)


def s24_ehkd():
    s = new_slide(); backup_chrome(s, 24, "B7", "Conceptual e-HKD leg: both legs commit, or neither")
    rows = [("Both legs prepare and commit", "COMMITTED_BOTH"), ("Bank H has insufficient central-bank money: both legs roll back", "ROLLED_BACK"),
            ("Tokenised-deposit leg refuses prepare: both roll back", "ROLLED_BACK"),
            ("Coordinator crashes after prepare, before decision: recovery aborts both", "ROLLED_BACK"),
            ("CeBM commit fails once, retried under the durable COMMIT decision", "COMMITTED_BOTH")]
    y0 = 2.3
    for x, h_ in [(MX, "Case"), (8.2, "Outcome"), (11.0, "All-or-nothing")]:
        text(s, x, y0, 3, 0.25, h_, size=9.5, font=F_H, color=MUTE)
    for i, (c, o) in enumerate(rows):
        y = y0 + 0.4 + i * 0.62
        line(s, MX, y - 0.1, W - MX, y - 0.1, color=HAIR, lw=0.75)
        text(s, MX, y, 7.2, 0.4, c, size=12.5, color=INK2)
        text(s, 8.2, y + 0.02, 2.6, 0.3, o, size=10.5, font=F_M, color=TEAL if o == "COMMITTED_BOTH" else INK)
        text(s, 11.0, y, 1.6, 0.3, [[("✓  ", {"color": TEAL, "font": F_H}), "yes"]], size=12.5)
    text(s, MX, 5.95, 11.8, 0.3, f"{fr('M-12')} cases all-or-nothing. A toy two-phase commit across two mock ledgers: not distributed, not legally final, not HKMA-linked.",
         size=11, color=MUTE)


def s25_sources():
    s = new_slide(); backup_chrome(s, 25, "B8", "Sources (click to open)")
    src = [("EXIM Thailand", "HK 13th-largest partner, US$13.7bn (2023) · 23 Feb 2024"),
           ("ADB", "Global trade-finance gap US$2.5tn in 2025 · 15 Jan 2026"),
           ("HKMA · CargoX report", "p.16: HK 2024 gap HK$311.2–519.1bn (KPMG desktop estimate) · 19 Jan 2026"),
           ("HKMA · CargoX pilot", "Pilot with 21 banks · 7 May 2026"),
           ("HKMA · Project Ensemble", "New phase · 13 Nov 2025"),
           ("HKMA · EnsembleTX", "24/7 tokenised CeBM settlement · 2 Nov 2026"),
           ("HKMA · e-HKD Phase 2", "Report, 28 Oct 2025 (mainly retail use cases)"),
           ("BIS", "Project mBridge")]
    for i, (name, desc) in enumerate(src):
        col, row = i % 2, i // 2
        x, y = MX + col * 6.0, 2.35 + row * 0.95
        line(s, x, y - 0.1, x + 5.6, y - 0.1, color=HAIR, lw=0.75)
        text(s, x, y, 0.5, 0.3, f"[{i + 1}]", size=11, font=F_H, color=MUTE)
        text(s, x + 0.55, y, 5.0, 0.3, name, size=13, font=F_H, link=LINKS.get(name))
        text(s, x + 0.55, y + 0.32, 5.0, 0.3, desc, size=11, color=INK2)
    text(s, MX, 6.3, 11.8, 0.3, "Photographs: Unsplash (Unsplash License), converted to monochrome. Console screenshots: our prototype, synthetic data.",
         size=9.5, color=MUTE)


def s26_questions():
    s = new_slide(); backup_chrome(s, 26, "B9", "Likely questions")
    qa = [("Why not a central database?", "It could enforce the same rules. A shared ledger only adds value with independent bank and regulator nodes (slide 15)."),
          ("Is the efficiency gain real?", f"It is a process model. The claim we stand by is {v('M-32')}% at matched scope (slide 13)."),
          ("Who pays for pre-funding?", "The importer in our model. A real product needs the bank to finance or remunerate the escrow (slide 14)."),
          ("Is the role selector a login?", "No, it is demo impersonation. Permissions are enforced server-side and tested per role (slide 11).")]
    for i, (q, a) in enumerate(qa):
        col, row = i % 2, i // 2
        x, y = MX + col * 6.0, 2.35 + row * 1.9
        box(s, x, y, 5.6, 1.6, fill=CARD, radius=0.14)
        text(s, x + 0.25, y + 0.22, 5.1, 0.35, q, size=15, font=F_H)
        text(s, x + 0.25, y + 0.68, 5.1, 0.8, a, size=12, color=INK2, ls=1.06)


# ================================================================== build
def main():
    s01_cover(); s02_since_interim(); s03_three_ways(); s04_rails(); s05_hypotheses()
    s06_cannot_see_ship(); s07_seven_checks(); s08_invariants()
    s09_live(); s10_break_it(); s11_leak(); s12_scorecard()
    s13_efficiency(); s14_tradeoff(); s15_must_be_true(); s16_answer()
    s17_backup_index(); s18_architecture(); s19_state_machine()
    bpmn_slide(20, "B3", "Baseline BPMN: open-account settlement", "baseline_bpmn_slide.png",
               ["Swimlanes are parties: importer, Bank H, Bank O, exporter, logistics/customs. Read left to right.",
                "Part 1: contract, the exporter ships, documents are couriered and checked by hand. Part 2: after the term the importer instructs payment; banks screen and pay.",
                f"Orange boxes are manual settlement tasks; these are what we count ({v('M-13')} in a normal trade).",
                "Dashed red: exception paths (document discrepancy, screening alert)."],
               [("How did you count manual tasks?", "Orange tasks only, same granularity in both maps; goods, customs, carriage and FX excluded."),
                ("Is this how every bank works?", "No, it is a standard-practice model we drew; a threat to validity in the report.")])
    bpmn_slide(21, "B4", "Proposed BPMN: pre-funded escrow", "proposed_bpmn_slide.png",
               ["Part 1: the importer funds the escrow and passes creation KYC/AML before shipment, so the money is locked first.",
                "Part 2: attestations arrive; teal boxes are automated checks (document matching, pre-release screening, guarded release).",
                f"Only {v('M-14')} manual settlement tasks remain in a normal trade: fund the escrow, upload invoice and B/L, Bank O acknowledges.",
                "Exceptions still go to people: a mismatch to a reviewer, an alert to compliance."],
               [("Why does this map end at Bank H?", f"Our prototype stops at a Bank H release; slide 13 adds the cross-bank steps ({v('M-13')} → {v('M-31')})."),
                ("Are the automated steps free?", "No; we assume 0 days for them, which is optimistic. Time results are scenario analysis.")])
    s22_permissions(); s23_fallback(); s24_ehkd(); s25_sources(); s26_questions()
    # theme hyperlink colours: ink instead of Office blue (links stay underlined)
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    theme = prs.slide_masters[0].part.part_related_by(RT.THEME)
    root = etree.fromstring(theme.blob)
    for tag, col in (("a:hlink", INK), ("a:folHlink", MUTE)):
        el = root.find(".//" + qn(tag))
        for c in list(el):
            el.remove(c)
        etree.SubElement(el, qn("a:srgbClr")).set("val", col)
    theme._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    prs.save(OUT)
    print("saved", OUT, "slides:", len(prs.slides))


if __name__ == "__main__":
    main()
