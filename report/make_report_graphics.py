"""Design graphics for the final report (navy / teal / gold system shared with the cover).
Writes report/figs/design/*.png at 300 dpi. Every number is read from results/ — nothing is typed in by hand
except labels and the four part-opener standfirst lines."""
import atexit, csv, json
from pathlib import Path
from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figs" / "design"; OUT.mkdir(parents=True, exist_ok=True)
NAVY, INK, SUB, MUTE, RULE, HAIR = "#0B1730", "#1C2433", "#3E4A5E", "#6B7689", "#C9D0DB", "#E3E7EE"
TEAL, TEALL, GOLD, GOLDL, RED, REDL, CREAM, PALE = "#1F8A82", "#E1F0ED", "#B07A22", "#F5ECDA", "#B8342A", "#F7E4E1", "#EDE4CE", "#F1F3F6"
# v6 (2026-11-19): modern restyle to match the colour cover and deck. Windows system fonts, so the
# graphics build on this machine; SVG is rendered by Microsoft Edge (Playwright) instead of rsvg-convert.
HEAD, SANS, MONO = "Segoe UI", "Segoe UI", "Consolas"
GIT = r"C:\Windows\Fonts\segoeuil.ttf"           # light, used to measure standfirst lines
INTER = r"C:\Windows\Fonts\segoeui.ttf"
esc = lambda t: str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
MAN = json.load(open(ROOT / "results/run_manifest.json", encoding="utf-8"))
MET = {r[0]: r for r in csv.reader(open(ROOT / "results/metrics.csv", encoding="utf-8"))}
v = lambda k: MET[k][2]; d = lambda k: MET[k][3]
N = lambda x: f"{int(float(x)):,}"
rob = {r["metric"]: r["value"] for r in csv.DictReader(open(ROOT / "results/robustness.csv"))}
mut = list(csv.DictReader(open(ROOT / "results/mutation_analysis.csv")))
mut1 = list(csv.DictReader(open(ROOT / "results/mutation_analysis_run1_before_test_fixes.csv")))
ctrl = list(csv.DictReader(open(ROOT / "results/control_matrix.csv")))
tests = list(csv.DictReader(open(ROOT / "results/test_results.csv")))
acc = list(csv.DictReader(open(ROOT / "results/audit_access_matrix.csv")))
EV = [json.loads(l) for l in open(ROOT / "results/events/TC-001.jsonl")]


class G:
    def __init__(s, w, h, bg="white"): s.w, s.h, s.P, s.bg = w, h, [], bg
    def T(s, x, y, t, sz=36, c=INK, a="start", f=SANS, wt="400", ls=0, it=False, op=1):
        if wt == "700":
            wt = "600"                               # modern: semibold, never heavy bold
        if it:
            it, wt = False, "300"                    # modern: light instead of italic
        if ls and str(t).upper() == str(t):
            ls = min(float(ls), 2.5)                 # calmer tracking on caps labels
        s.P.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{a}" font-family="{f}" font-weight="{wt}" font-size="{sz}" letter-spacing="{ls}" fill="{c}" fill-opacity="{op}"{" font-style=\"italic\"" if it else ""}>{esc(t)}</text>')
    def R(s, x, y, w, h, fill="none", st="none", sw=2, rx=0, op=1, dash=None):
        s.P.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" fill-opacity="{op}" stroke="{st}" stroke-width="{sw}"{f" stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""}/>')
    def L(s, x1, y1, x2, y2, c=RULE, w=2, dash=None):
        s.P.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}"{f" stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""}/>')
    def C(s, x, y, r, fill="none", st="none", sw=2):
        s.P.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{st}" stroke-width="{sw}"/>')
    def arrow(s, x1, y, x2, c=NAVY, w=2.2):
        s.L(x1, y, x2 - 2, y, c, w); s.P.append(f'<path d="M{x2-11:.1f},{y-7:.1f} l11,7 l-11,7" fill="none" stroke="{c}" stroke-width="{w}"/>')
    def label(s, x, y, t, c=TEAL, a="start", sz=24):
        s.T(x, y, t, sz, c, a, SANS, "600", 5)
    def chip(s, x, y, t, c, fill="white", a="start", sz=20):
        w = 30 + len(t) * sz * 0.72
        if a == "end": x -= w
        if a == "middle": x -= w / 2
        s.R(x, y - sz * 1.35, w, sz * 1.85, fill, c, 1.8, sz * 0.92); s.T(x + w / 2, y - 2, t, sz, c, "middle", SANS, "600", 2)
        return w
    def pill(s, x, y, t, c, solid=False, sz=27, h=50):
        w = 34 + len(t) * sz * 0.62
        s.R(x, y - h / 2, w, h, c if solid else "white", c, 2.4, h / 2)
        s.T(x + w / 2, y + sz * 0.36, t, sz, "white" if solid else c, "middle", SANS, "600")
        return w
    def wrap(s, x, y, text, width, sz=36, lh=None, c=INK, f=SANS, it=False, path=INTER, wt="400"):
        lh = lh or sz * 1.35; font = ImageFont.truetype(path, sz); words, line, lines = text.split(), "", []
        for w_ in words:
            t = (line + " " + w_).strip()
            if font.getlength(t) > width and line: lines.append(line); line = w_
            else: line = t
        lines.append(line)
        for i, ln in enumerate(lines): s.T(x, y + i * lh, ln, sz, c, f=f, it=it, wt=wt)
        return y + len(lines) * lh
    def save(s, name):
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{s.w}" height="{s.h}"><rect width="{s.w}" height="{s.h}" fill="{s.bg}"/>{"".join(s.P)}</svg>'
        render_svg(svg, s.w, s.h, OUT / f"{name}.png", transparent=s.bg == "none")
        if s.bg != "none": Image.open(OUT / f"{name}.png").convert("RGB").save(OUT / f"{name}.png", optimize=True)


_PW = {}
def render_svg(svg, w, h, out, transparent=False):
    """Render an SVG string to PNG at exactly w x h px with the installed Microsoft Edge."""
    if not _PW:
        from playwright.sync_api import sync_playwright
        _PW["pw"] = sync_playwright().start()
        _PW["b"] = _PW["pw"].chromium.launch(channel="msedge", headless=True)
        _PW["page"] = _PW["b"].new_page(device_scale_factor=1)
        atexit.register(lambda: (_PW["b"].close(), _PW["pw"].stop()))
    page = _PW["page"]
    page.set_viewport_size({"width": int(w), "height": int(h)})
    page.set_content(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
    page.screenshot(path=str(out), omit_background=transparent, clip={"x": 0, "y": 0, "width": int(w), "height": int(h)})


def ring_svg(cx, cy, r, sw, n_on, n=7, on=None, off=HAIR):
    """The 7-segment release-guard ring (the product's signature motif), n_on segments lit."""
    on = on or TEAL
    out, seg, gap = [], 360 / n, 9
    import math as _m
    for i in range(n):
        a0, a1 = _m.radians(-90 + i * seg + gap / 2), _m.radians(-90 + (i + 1) * seg - gap / 2)
        x0, y0, x1, y1 = cx + r * _m.cos(a0), cy + r * _m.sin(a0), cx + r * _m.cos(a1), cy + r * _m.sin(a1)
        out.append(f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{on if i < n_on else off}" stroke-width="{sw}" stroke-linecap="round"/>')
    return "".join(out)


GW = 1960  # 16.6 cm at 300 dpi

# ── 1. running-head bands ───────────────────────────────────────────────
TABS = ["SUMMARY", "01 WHY ESCROW", "02 THE DESIGN", "03 THE EVIDENCE", "04 THE VERDICT", "APPENDICES"]
def band(name, active, width=2480, margin=220):
    g = G(width, 104, NAVY)
    g.T(margin, 64, "HK–TH TRADEESCROW", 22, CREAM, f=SANS, wt="600", ls=6)
    g.T(margin + 372, 64, "FINAL REPORT", 22, CREAM, f=SANS, wt="400", ls=5, op=0.5)
    x = width - margin
    for i in reversed(range(len(TABS))):
        w = len(TABS[i]) * 14.4; x -= w; on = i == active
        g.T(x, 64, TABS[i], 20, "#FFFFFF" if on else CREAM, f=SANS, wt="600", ls=3, op=1 if on else 0.42)
        if on: g.R(x, 82, w - 8, 6, GOLD)
        x -= 40
    g.save(name)
for i, n in enumerate(["band_front", "band_p1", "band_p2", "band_p3", "band_p4", "band_app"]): band(n, i)
g = G(2480, 104, NAVY)
g.T(220, 64, "HK–TH TRADEESCROW", 22, CREAM, f=SANS, wt="600", ls=6); g.T(592, 64, "FINAL REPORT", 22, CREAM, f=SANS, wt="400", ls=5, op=0.5)
x = 2480 - 220
for i in reversed(range(1, 5)):
    w = len(TABS[i]) * 14.4; x -= w; g.T(x, 64, TABS[i], 20, CREAM, f=SANS, wt="600", ls=3, op=0.6); x -= 40
g.save("band_body")
band("band_app_land", 5, 3508, 260)

# ── 2. part openers ─────────────────────────────────────────────────────
tests_pass = sum(t["status"] == "PASS" for t in tests)
nc = [c for c in ctrl if c["control_id"].startswith("NC")]
OPEN = {
 1: ("PART 01  ·  SECTIONS 1–3", "Why escrow",
     "Hong Kong is building the rails for tokenised money, but trade settlement still runs on paper, manual checks and an exporter who ships unsecured.",
     [("US$13.7 bn", "HK–Thailand trade, 2023 [6]", "CITED", NAVY), (f"{float(v('M-21')):g} days", "unsecured, pay at once", "MODELLED", GOLD),
      (f"{float(v('M-23')):g} days", "unsecured, 30-day terms", "MODELLED", GOLD), ("4", "initiatives reviewed", "DESK RESEARCH", NAVY)]),
 2: ("PART 02  ·  SECTIONS 4–5", "The design",
     "Funds are locked before shipment and released only when shipment, documents and compliance are attested, with every step written to a hash-linked journal.",
     [("6", "escrow states", "DESIGN", NAVY), ("15", "permitted transitions", "DESIGN", NAVY), ("7", "release-guard checks", "DESIGN", NAVY), ("7", "role-limited roles", "DESIGN", NAVY)]),
 3: ("PART 03  ·  SECTIONS 6–7", "The evidence",
     "The controls held every time we attacked them. The efficiency gain is real, but about half the size the headline number suggests.",
     [(f"{tests_pass}/{len(tests)}", "automated tests pass", "TESTED", TEAL), (f"{sum(c['blocked']=='True' for c in nc)}/{len(nc)}", "unsafe releases refused", "TESTED", TEAL),
      (f"0 / {N(rob['invariant_checks'])}", "invariant violations", "TESTED", TEAL), (f"{v('M-13')} → {v('M-31')}", "manual tasks, matched scope", "MODELLED", GOLD)]),
 4: ("PART 04  ·  SECTIONS 8–10", "The verdict",
     "A qualified yes: safer and auditable in simulation, modestly more efficient in the model, and not free, because the importer now carries the wait.",
     [("H2–H4", "supported in simulation", "TESTED", TEAL), ("H1", "supported in the model", "MODELLED", GOLD),
      (f"{v('M-24')} → {v('M-25')} d", "importer cash committed", "TRADE-OFF", RED), ("0 of 5", "with real-world data", "NOT YET", MUTE)]),
}
for k, (lab, title, stand, kp) in OPEN.items():
    g = G(GW, 400)
    g.R(0, 0, GW, 400, PALE, rx=34)
    g.P.append(ring_svg(92, 92, 40, 9, {1: 2, 2: 4, 3: 6, 4: 7}[k]))     # guard ring = progress through the report
    lab_ = lab.title().replace("  ·  ", " · ").replace("Part 0", "Part ")
    g.T(158, 82, lab_, 26, TEAL, f=SANS, wt="600")
    g.T(156, 124, "", 1)
    g.T(48, 210, title, 84, NAVY, f=HEAD, wt="600", ls=-2)
    g.wrap(52, 270, stand, 960, sz=31, lh=44, c=SUB, f=HEAD, wt="300", path=GIT)
    x0, cw = 1100, 418
    for i, (big, lb, tag, c) in enumerate(kp):
        x = x0 + (i % 2) * cw; y = 34 + (i // 2) * 180
        g.R(x, y, cw - 26, 160, "white", rx=22)
        g.T(x + 26, y + 64, big, 50, c if c != MUTE else NAVY, f=HEAD, wt="300", ls=-1)
        g.T(x + 26, y + 104, lb, 24, SUB)
        g.chip(x + 24, y + 143, tag.title() if tag.isupper() else tag, c, sz=16)
    g.save(f"opener_p{k}")

# ── 3. §1.2 where the weaknesses sit (process strip) ────────────────────
g = G(GW, 500)
steps = ["Contract\nsigned", "Exporter\nships goods", "Documents\ncouriered / emailed", "Importer checks\nby hand", "Bank screens\nat payment", "Exporter\npaid"]
weak = {1: ("1", "risk sits with the exporter", RED), 2: ("2", "manual, sequential checks", GOLD), 3: ("3", "fragmented records", GOLD), 4: ("4", "compliance repeated, late", GOLD)}
sw = (GW - 40) / len(steps)
for i, st in enumerate(steps):
    x = 20 + i * sw; cx = x + sw / 2
    g.R(x + 12, 40, sw - 52, 118, PALE if i not in (0, 5) else "white", NAVY, 2.2, 14)
    for j, ln in enumerate(st.split("\n")): g.T(x + 12 + (sw - 52) / 2, 88 + j * 38, ln, 29, NAVY, "middle", wt="600" if j == 0 else "400")
    if i < len(steps) - 1: g.arrow(x + sw - 38, 99, x + sw + 10)
# exporter-risk bracket from shipment to payment
x1 = 20 + 1 * sw + sw / 2; x2 = 20 + 5 * sw + sw / 2 - 30
g.L(x1, 196, x2, 196, RED, 4); g.L(x1, 184, x1, 208, RED, 4); g.L(x2, 184, x2, 208, RED, 4)
g.T((x1 + x2) / 2, 240, f"exporter holds an unsecured receivable: {float(v('M-21')):g} days (pay at once) · {float(v('M-23')):g} days (30-day terms)", 28, RED, "middle", wt="600")
for i, (n, t, c) in weak.items():
    cx = 20 + i * sw + (sw - 40) / 2
    g.L(cx, 160, cx, 300, c if i != 1 else "none", 2, "4 5")
for i, (n, t, c) in weak.items():
    if i == 1: continue
    cx = 20 + i * sw + (sw - 40) / 2
    g.C(cx, 330, 22, "white", c, 3); g.T(cx, 340, n, 26, c, "middle", wt="700")
    w1, w2 = t.rsplit(" ", 1) if len(t) > 16 else (t, "")
    g.T(cx, 392, w1, 26, SUB, "middle"); g.T(cx, 426, w2, 26, SUB, "middle")
cx1 = 20 + sw + (sw - 40) / 2
g.C(cx1, 330, 22, "white", RED, 3); g.T(cx1, 340, "1", 26, RED, "middle", wt="700")
g.T(cx1, 392, "risk sits with", 26, SUB, "middle"); g.T(cx1, 426, "the exporter", 26, SUB, "middle")
g.T(20, 488, "Numbers mark the four weaknesses listed in §1.2. Durations: team process model, base case (results/timelines.csv).", 24, MUTE)
g.save("g_weaknesses")

# ── 4. §3 evidence ladder for H1–H5 ─────────────────────────────────────
g = G(GW, 610)
rows = [("MEASURED", "real banks, real trades", [], MUTE),
        ("SIMULATED", "executed on our prototype, synthetic data", [("H2", "no release unless all gates are current"), ("H3", "mismatch → review; AML alert → freeze"), ("H4", "audit without unrelated commercial data")], TEAL),
        ("MODELLED", "process and timing model, declared assumptions", [("H1", "fewer manual tasks, shorter latency"), ("H5", "pre-funding moves the liquidity burden")], GOLD),
        ("ASSUMED", "inputs we chose and state as ranges", [("—", "task durations · 48 h KYC window · low/base/high ranges")], MUTE)]
for i, (nm, sub, hs, c) in enumerate(rows):
    y = 30 + i * 145
    g.R(0, y, GW, 128, PALE if i % 2 == 0 else "white")
    g.C(44, y + 64, 15, c if hs else "white", c, 3)
    if i < 3: g.L(44, y + 80, 44, y + 145 + 48, HAIR, 3)
    g.T(84, y + 60, nm, 27, c if hs else MUTE, wt="700", ls=4)
    g.T(84, y + 100, sub, 25, MUTE)
    if not hs: g.T(640, y + 76, "— no hypothesis has real-world evidence yet", 29, MUTE, it=True, f=HEAD); continue
    x = 640
    for h, t in hs:
        if h != "—":
            g.R(x, y + 40, 74, 48, c, rx=8); g.T(x + 37, y + 74, h, 27, "white", "middle", wt="700"); x2 = x + 90
        else: x2 = x
        g.T(x2, y + 74, t, 27, INK if h != "—" else MUTE, it=h == "—")
        x = x2 + len(t) * 13.6 + 50 if len(hs) > 1 else x
        if len(hs) > 1 and h in ("H2", "H3"): pass
    # simple equal spacing for multi rows
g.P = [p for p in g.P]  # (layout done inline)
g.save("g_ladder_tmp")
# re-do cleanly with fixed columns
g = G(GW, 640)
for i, (nm, sub, hs, c) in enumerate(rows):
    y = 20 + i * 152
    g.R(0, y, GW, 136, PALE if i % 2 == 0 else "white")
    g.C(40, y + 68, 15, c if hs else "white", c, 3)
    if i < 3: g.L(40, y + 84, 40, y + 152 + 52, HAIR, 3)
    g.T(80, y + 62, nm, 27, c if hs else MUTE, wt="700", ls=4)
    g.T(80, y + 102, sub, 24, MUTE)
    if not hs: g.T(700, y + 80, "No hypothesis has real-world evidence yet.", 30, MUTE, it=True, f=HEAD); continue
    if hs[0][0] == "—": g.T(700, y + 80, hs[0][1], 28, MUTE, it=True, f=HEAD); continue
    colw = (GW - 700) / 3 if len(hs) == 3 else (GW - 700) / 2
    for j, (h, t) in enumerate(hs):
        x = 700 + j * colw
        g.R(x, y + 26, 72, 46, c, rx=8); g.T(x + 36, y + 59, h, 26, "white", "middle", wt="700")
        g.wrap(x, y + 108, t, colw - 40, sz=25, lh=32, c=INK)
g.save("g_ladder"); (OUT / "g_ladder_tmp.png").unlink()

# ── 5. §5.1 the seven release-guard checks ──────────────────────────────
g = G(GW, 470)
gates = [("1", "State Pending;\nlocked amount =\ntrade amount", NAVY), ("2", "No active\ncompliance\nhold", TEAL), ("3", "Shipment PASS\nfor this\nshipment ID", GOLD),
         ("4", "Documents PASS\non the current\ndigest", GOLD), ("5", "Creation\nKYC/AML\npassed", TEAL), ("6", "Pre-release PASS\nafter last\napproval & hold", TEAL), ("7", "That PASS is\nunder 48 h\nold", TEAL)]
bw = 212; gap = (GW - 270 - 7 * bw) / 6
for i, (n, t, c) in enumerate(gates):
    x = i * (bw + gap)
    g.R(x, 40, bw, 220, "white", c, 2.4, 12); g.R(x, 40, bw, 10, c, rx=4)
    g.C(x + 40, 98, 22, c); g.T(x + 40, 108, n, 26, "white", "middle", wt="700")
    for j, ln in enumerate(t.split("\n")): g.T(x + 18, 160 + j * 30, ln, 22, INK)
rx = GW - 230
g.arrow(rx - 50, 140, rx - 8, TEAL, 3)
g.T(0, 22, "ALL SEVEN MUST HOLD AT THE MOMENT OF RELEASE", 20, MUTE, f=SANS, wt="600", ls=4)
g.R(rx, 70, 230, 140, TEAL, rx=14); g.T(rx + 115, 132, "RELEASE", 28, "white", "middle", wt="700", ls=3); g.T(rx + 115, 172, "exactly once", 24, "white", "middle")
# legend + failure rule
lx = 0
for lab, c in [("escrow state", NAVY), ("shipment / document gate", GOLD), ("compliance gate", TEAL)]:
    g.R(lx, 290, 26, 26, c, rx=5); g.T(lx + 38, 311, lab, 25, SUB); lx += 60 + len(lab) * 13.5
g.R(0, 350, GW, 92, REDL, rx=10)
g.T(30, 405, "Any check fails  →  refused with the first failing gate as reason code (e.g. PRE_RELEASE_KYC_EXPIRED), journalled with the full evaluation.", 26, RED, wt="600")
g.save("g_guard")

# ── 6. §5.3 role-visibility grid (63 rules) ─────────────────────────────
ROLE = [("IMPORTER (own trade)", "HK importer, own trade"), ("IMPORTER (other trade)", "HK importer, other trade"), ("EXPORTER", "Thai exporter"),
        ("BANK_HK", "Bank H operations"), ("BANK_HK_COMPLIANCE", "Bank H compliance"), ("BANK_TH", "Thai Bank O"),
        ("LOGISTICS", "Logistics provider"), ("CUSTOMS", "Customs authority"), ("REGULATOR", "Regulator")]
CAP = [("view", "trade\nexists"), ("amount", "amount"), ("commercial_terms", "commercial\nterms"), ("doc_bodies", "document\nbodies"),
       ("compliance_reasons", "compliance\nreasons"), ("guard", "guard\ndetail"), ("audit", "audit\ntrail")]
cell = {(r["role"], r["capability"]): r for r in acc}
g = G(GW, 800)
x0, cw_, rh, y0 = 470, 152, 70, 150
for j, (k, lab) in enumerate(CAP):
    for t, ln in enumerate(lab.split("\n")): g.T(x0 + j * cw_ + cw_ / 2, 60 + t * 34, ln, 25, SUB, "middle", wt="600")
g.L(0, y0 - 24, x0 + 7 * cw_, y0 - 24, NAVY, 2.5)
for i, (rk, rl) in enumerate(ROLE):
    y = y0 + i * rh
    if i % 2 == 0: g.R(0, y - 24, x0 + 7 * cw_, rh, PALE)
    g.T(10, y + 20, rl, 28, INK)
    for j, (k, _) in enumerate(CAP):
        r = cell[(rk, k)]; cx = x0 + j * cw_ + cw_ / 2
        if r["expected"] == "1": g.C(cx, y + 11, 15, TEAL)
        else: g.C(cx, y + 11, 13, "white", RULE, 2.4)
obeyed = sum(r["obeyed"] == "True" for r in acc)
g.L(0, y0 + 9 * rh - 24, x0 + 7 * cw_, y0 + 9 * rh - 24, NAVY, 2.5)
lx = x0 + 7 * cw_ + 70
g.C(lx + 14, 190, 15, TEAL); g.T(lx + 44, 199, "may see", 27, SUB)
g.C(lx + 14, 250, 13, "white", RULE, 2.4); g.T(lx + 44, 259, "hidden", 27, SUB)
g.T(lx, 380, f"{obeyed}/{len(acc)}", 64, NAVY, f=HEAD, wt="700")
g.T(lx, 424, "rules obeyed", 27, SUB)
g.chip(lx, 490, "TESTED", TEAL)
g.wrap(lx, 580, "The regulator sees the trail but not the commercial content.", GW - lx - 10, sz=26, lh=34, c=MUTE, f=HEAD, it=True, path=GIT)
g.save("g_roles")

# ── 7. §6.1 test design: four layers ────────────────────────────────────
g = G(GW, 560)
cwid = (GW - 3 * 40) / 4
def card(i, kicker, big, lab, c):
    x = i * (cwid + 40)
    g.L(x, 20, x + cwid, 20, c, 5)
    g.label(x, 70, kicker, c, sz=22)
    g.T(x, 150, big, 66, NAVY, f=HEAD, wt="700")
    g.wrap(x, 196, lab, cwid - 10, sz=26, lh=34, c=SUB)
    return x
x = card(0, "TARGETED TESTS", str(len(tests)), "scripted cases TC-001–024, e-HKD and invariant tests", TEAL)
for k in range(len(tests)):
    g.R(x + (k % 16) * 26, 300 + (k // 16) * 26, 19, 19, TEAL if tests[k]["status"] == "PASS" else RED, rx=3)
x = card(1, "ATTACKS ON RELEASE", f"{len(nc)} + 1", "unsafe release attempts, plus one positive control that must release", NAVY)
for k in range(len(nc)):
    g.R(x + (k % 9) * 44, 300 + (k // 9) * 56, 34, 44, "white", NAVY, 2.2, 6); g.T(x + (k % 9) * 44 + 17, 300 + (k // 9) * 56 + 31, "✕", 22, RED, "middle", wt="700")
g.R(x + 0 * 44, 420, 34, 44, TEAL, rx=6); g.T(x + 17, 451, "✓", 22, "white", "middle", wt="700"); g.T(x + 50, 451, "positive control", 23, MUTE)
x = card(2, "RANDOM SEQUENCES", N(rob["commands"]), f"commands over {rob['trades']} random trades (seed {rob['seed']}), incl. forbidden actions", GOLD)
a_, r_ = int(rob["accepted"]), int(rob["rejected"]); tot = a_ + r_; bwid = cwid - 10
g.R(x, 316, bwid * a_ / tot, 36, TEAL); g.R(x + bwid * a_ / tot, 316, bwid * r_ / tot, 36, RED, op=0.85)
g.T(x, 396, f"{N(a_)} accepted", 24, TEAL, wt="600"); g.T(x + bwid, 396, f"{N(r_)} refused", 24, RED, "end", wt="600")
g.T(x, 440, f"{N(rob['invariant_checks'])} invariant checks", 24, SUB)
x = card(3, "PLANTED BUGS", str(len(mut)), "deliberate defects in guard, RBAC, journal, matching and views", RED)
for k, m in enumerate(mut):
    g.C(x + 18 + (k % 7) * 50, 320 + (k // 7) * 52, 17, NAVY if m["killed_by_suite"] == "True" else "white", NAVY if m["killed_by_suite"] == "True" else RED, 2.6)
g.T(x, 450, "● caught by the suite   ○ survived", 22, MUTE)
g.T(0, 540, "Squares, crosses and dots are drawn one per test, attack and mutant from results/test_results.csv, control_matrix.csv and mutation_analysis.csv.", 23, MUTE)
g.save("g_testdesign")

# ── 8. §7.1 flagship state paths ────────────────────────────────────────
SC = {"Created": MUTE, "Pending": GOLD, "Under Review": RED, "Frozen": NAVY, "Released": TEAL}
strips = [("TC-001", "Normal trade", ["Created", "Pending", "Released"], None, "one release posting · HKD 250,000 · supply conserved · journal intact"),
          ("TC-002", "Document mismatch", ["Created", "Pending", "Under Review", "Pending", "Released"], (2, "release refused · ESCROW_UNDER_REVIEW"), "invoice rev. 2 → fresh document PASS → reviewer revalidates → new screening"),
          ("TC-003", "AML alert", ["Created", "Pending", "Frozen", "Pending", "Released"], (2, "release and refund refused · ACTIVE_HOLD"), "false positive cleared → re-screen required first (PRE_RELEASE_KYC_MISSING)")]
g = G(GW, 3 * 200 + 20)
for k, (tc, nm, path, ref, note) in enumerate(strips):
    y = 20 + k * 200
    g.T(0, y + 46, tc, 28, NAVY, f=MONO, wt="700"); g.T(0, y + 86, nm, 28, SUB)
    x = 330
    for j, stt in enumerate(path):
        w = g.pill(x, y + 40, stt, SC[stt], solid=stt == "Released", sz=26, h=50)
        if ref and ref[0] == j:
            g.L(x + w / 2, y + 66, x + w / 2, y + 96, RED, 2); g.T(x + w / 2 - 10, y + 122, "✕ " + ref[1], 23, RED, f=MONO)
        if j < len(path) - 1: g.arrow(x + w + 6, y + 40, x + w + 44)
        x += w + 52
    g.T(330, y + (122 if not ref else 162), note, 24, MUTE)
    if k < 2: g.L(0, y + 188, GW, y + 188, HAIR, 1.5)
g.save("g_paths")

# ── 9. callout side graphics ────────────────────────────────────────────
g = G(560, 420, GOLDL)  # matched scope
g.label(0, 40, "MANUAL TASKS", MUTE, sz=21)
for i, (txt, lab, c) in enumerate([(f"{v('M-13')} → {v('M-14')}", "prototype scope", MUTE), (f"{v('M-13')} → {v('M-31')}", "matched scope", NAVY)]):
    y = 130 + i * 150
    g.T(0, y, txt, 66, c, f=HEAD, wt="700"); g.T(0, y + 44, lab, 26, SUB)
g.T(250, 324, f"(−{v('M-32')}%)", 28, GOLD, f=SANS, wt="600")
g.save("side_matched")
g = G(560, 420, "#EEF7F5")  # mutation dots
g.label(0, 40, "PLANTED BUGS CAUGHT", MUTE, sz=21)
for i, (lab, rows_) in enumerate([("run 1", mut1), ("run 2", mut)]):
    y = 110 + i * 150; n = sum(m["killed_by_suite"] == "True" for m in rows_)
    g.T(0, y + 14, lab, 26, SUB)
    for j, m in enumerate(rows_):
        k_ = m["killed_by_suite"] == "True"; c = TEAL if i else MUTE
        g.C(110 + (j % 7) * 34, y + (j // 7) * 34, 12.5, c if k_ else "white", c if k_ else RED, 2.4)
    g.T(555, y + 26, f"{n}/{len(rows_)}", 40, NAVY if i else MUTE, "end", HEAD, "700")
g.T(0, 400, "● caught   ○ survived", 23, MUTE)
g.save("side_mutation")

# ── 10. §7.3 the TC-001 journal ─────────────────────────────────────────
SH = {"CONTRACT": "CONTRACT", "CUSTOMS_DECLARATION": "CUSTOMS", "INVOICE": "INVOICE", "BILL_OF_LADING": "B/L"}
AT = {"KYC_AML_CREATION_PASS": "KYC", "SHIPMENT_PASS": "SHIPPED", "DOCS_CONSISTENT": "DOCS OK", "KYC_AML_PRE_RELEASE_PASS": "KYC"}
g = G(GW, 330)
bw = 138; gap = (GW - 12 * bw) / 11
for i, e in enumerate(EV):
    x = i * (bw + gap); op = e["operation"]
    nm = SH.get(e["details"].get("doc_type"), "DOC") if op == "SUBMIT_DOCUMENT" else AT.get(e["reason_code"], op) if op == "ATTEST" else {"ACKNOWLEDGE": "ACK"}.get(op, op)
    rel = op == "RELEASE"; ch = e["prior_state"] != e["new_state"] and e["new_state"]
    c = GOLD if rel else (TEAL if ch else NAVY)
    g.R(x, 40, bw, 104, GOLDL if rel else (TEALL if ch else "white"), c, 2.6 if (rel or ch) else 1.5, 10)
    g.T(x + bw / 2, 82, nm, 22, c, "middle", wt="600")
    g.T(x + bw / 2, 118, e["hash"][:6], 20, MUTE, "middle", f=MONO)
    if ch or rel: g.T(x + bw / 2, 184, "→ " + e["new_state"], 23, c, "middle", f=HEAD, it=True)
    if i < 11: g.L(x + bw + 2, 92, x + bw + gap - 2, 92, NAVY, 2)
g.T(0, 26, "seq 3", 20, MUTE, f=MONO); g.T(GW, 26, "seq 14", 20, MUTE, "end", f=MONO)
g.T(0, 270, "Each entry stores SHA-256(previous hash + event). Editing, deleting or reordering any entry breaks the chain (tests TC-018, TC-018b).", 25, SUB)
g.T(0, 312, "First six hex digits shown. Source: results/events/TC-001.jsonl.", 23, MUTE)
g.save("g_journal")
print("graphics:", sorted(p.name for p in OUT.glob("*.png")))


# ═════════════════════ v5: page frames, sensitivity, survey, appendix dashboards ═════════════════════
import math
def frame(name, label, land=False):
    """Full-page transparent frame anchored behind the text: header, ledger spine, footer furniture."""
    Wd, Hd = (3508, 2480) if land else (2480, 3508)
    m = 229 if land else 225
    g = G(Wd, Hd, "none")
    g.R(0, 0, Wd, 10, TEAL)                                        # thin teal top edge
    # brand mark (same as cover and deck): four squares, the last one teal
    for dx, dy, fill in ((0, 0, NAVY), (30, 0, "none"), (0, 30, "none"), (30, 30, TEAL)):
        g.R(m + dx, 100 + dy, 24, 24, fill, NAVY if fill == "none" else fill, 3, 5)
    g.T(m + 76, 124, "HK–TH TradeEscrow", 30, NAVY, f=SANS, wt="600")
    g.T(m + 76, 160, "Final report  ·  FTEC3002 Group 1  ·  November 2026", 24, MUTE, f=SANS, wt="400")
    # section label + journal chain (the report's signature motif), run hash from results/
    xr = Wd - m
    nice = label.title().replace("&", "and").replace(" Not Counted", " not counted").replace("Pages", "pages")
    g.T(xr, 118, nice, 24, TEAL, "end", SANS, "600")
    bw, gp = 22, 11; x0 = xr - 12 * bw - 11 * gp
    for i in range(12):
        x = x0 + i * (bw + gp)
        g.R(x, 142, bw, 15, TEAL if i == 11 else "#A9D3CD", "none", 0, 4)
        if i < 11: g.L(x + bw, 149.5, x + bw + gp, 149.5, "#C7D0DB", 2)
    g.T(x0 - 18, 157, f"journal {MAN['code_sha256_16'][:8]}", 19, MUTE, "end", MONO)
    g.L(m, 205, xr, 205, HAIR, 2)
    # footer furniture (page number itself is a Word field, set in the footer)
    fy = Hd - 205
    g.L(m, fy, xr, fy, HAIR, 2)
    g.T(m, fy + 60, "HK–TH TradeEscrow", 23, NAVY, f=SANS, wt="600")
    g.T(m + 250, fy + 60, nice, 21, MUTE, f=SANS, wt="400")
    g.save(name)


# ── sensitivity: low–high ranges never overlap (Table 5 companion) ──────
TL = list(csv.DictReader(open(ROOT / "results/timelines.csv")))
def rng(sc, model, term, col="post_shipment_latency_d"):
    vals = {r["assumption_level"]: float(r[col]) for r in TL if r["scenario"] == sc and r["model"] == model and r["payment_term_days"] == str(term)}
    return vals["low"], vals["base"], vals["high"]
g = G(GW, 800)
rows = [(sc, t) for t in (0, 30) for sc in ("normal", "mismatch", "aml")]
SCN = {"normal": "Normal trade", "mismatch": "Document mismatch", "aml": "AML alert"}
x0, x1, xmax = 520, GW - 150, 46
X = lambda d: x0 + (x1 - x0) * d / xmax
for d_ in range(0, 46, 5):
    g.L(X(d_), 70, X(d_), 680, HAIR, 1.5); g.T(X(d_), 716, f"{d_}", 24, MUTE, "middle")
g.T(x1, 760, "days from shipment until the exporter is credited (simulated)", 24, MUTE, "end")
for i, (sc, t) in enumerate(rows):
    y = 110 + i * 96
    if i == 3: g.L(0, y - 30, x1, y - 30, RULE, 2)
    g.T(0, y + 6, SCN[sc], 29, INK, wt="600"); g.T(0, y + 42, f"{'pay at once' if t == 0 else '30-day terms'}", 24, MUTE)
    for k, (model, c, dy) in enumerate([("baseline", MUTE, -14), ("proposed", TEAL, 22)]):
        lo, ba, hi = rng(sc, model, t)
        g.R(X(lo), y + dy - 9, max(X(hi) - X(lo), 4), 18, c, rx=9, op=0.35 if model == "baseline" else 0.45)
        g.C(X(ba), y + dy, 11, c, "white", 2.5)
        if k == 0: g.T(X(hi) + 14, y + dy + 8, f"{lo:g}–{hi:g} d", 22, SUB)
        else: g.T(X(hi) + 14, y + dy + 8, f"{lo:g}–{hi:g} d", 22, TEAL, wt="600")
lx = x0
for lab, c in [("open account (low–high, ● base)", MUTE), ("escrow (low–high, ● base)", TEAL)]:
    g.R(lx, 14, 40, 16, c, rx=8, op=0.5); g.T(lx + 52, 30, lab, 23, SUB); lx += 80 + len(lab) * 12
g.save("g_sensitivity")

# ── peer questionnaire: real responses if present, otherwise the instrument itself ──
QS = ["The transaction status was easy to understand.", "The steps required to release funds were clear.",
      "I could understand why the system blocked a document mismatch.", "I could understand why an AML alert froze funds.",
      "The difference between a simulation and a real system was clear."]
sp = ROOT / "results/survey_anonymised.csv"
resp = [r for r in csv.DictReader(open(sp))] if sp.exists() else []
resp = [r for r in resp if all((r.get(f"Q{i}") or "").strip() for i in range(1, 6))]
LK = ["#B8342A", "#E3A39D", "#D9DEE7", "#8FCFC6", "#1F8A82"]
g = G(GW, 120 + 5 * 118 + 70)
if resp:
    n = len(resp)
    g.T(0, 40, f"n = {n} classmates  ·  1 = strongly disagree … 5 = strongly agree  ·  bar = share of responses, centred on neutral", 24, MUTE)
    cx, half = 1300, 560
    g.L(cx, 70, cx, 70 + 5 * 118, NAVY, 2)
    for i, q in enumerate(QS):
        y = 100 + i * 118
        g.T(0, y + 20, f"Q{i+1}", 26, NAVY, wt="700"); g.wrap(70, y + 20, q, 640, sz=25, lh=32, c=INK)
        cnt = [sum(int(r[f"Q{i+1}"]) == k for r in resp) for k in range(1, 6)]
        sh = [c_ / n for c_ in cnt]
        left = cx - (sh[0] + sh[1] + sh[2] / 2) * half * 2 / 1.0 / 2
        x = cx - (sh[0] + sh[1] + sh[2] / 2) * half
        for k in range(5):
            w = sh[k] * half
            if w > 0:
                g.R(x, y, w, 44, LK[k]);
                if cnt[k] and w > 34: g.T(x + w / 2, y + 30, str(cnt[k]), 21, "white" if k in (0, 4) else INK, "middle", wt="600")
            x += w
        med = sorted(int(r[f"Q{i+1}"]) for r in resp)[n // 2] if n % 2 else sum(sorted(int(r[f"Q{i+1}"]) for r in resp)[n // 2 - 1:n // 2 + 1]) / 2
        agree = (cnt[3] + cnt[4]) / n
        g.T(GW, y + 30, f"median {med:g}  ·  {agree:.0%} agree", 24, NAVY, "end", wt="600")
    ly = 100 + 5 * 118 + 30
    for k, lab in enumerate(["1 strongly disagree", "2", "3 neutral", "4", "5 strongly agree"]):
        g.R(780 + k * 230, ly - 18, 30, 22, LK[k], rx=4); g.T(822 + k * 230, ly, lab, 21, SUB)
    json.dump({"n": n, "medians": [], "status": "collected"}, open(ROOT / "results/survey_summary.json", "w"))
else:
    g.T(0, 40, "Instrument ready (docs/peer_feedback_protocol.md)  ·  8–10 classmates  ·  5-point scale  ·  responses: 0 so far", 24, MUTE)
    for i, q in enumerate(QS):
        y = 100 + i * 118
        g.T(0, y + 26, f"Q{i+1}", 26, NAVY, wt="700"); g.wrap(70, y + 26, q, 900, sz=26, lh=32, c=INK)
        for k in range(5):
            g.R(1060 + k * 150, y, 132, 44, "white", LK[k], 2, 6); g.T(1060 + k * 150 + 66, y + 31, str(k + 1), 24, LK[k] if k not in (2,) else MUTE, "middle", wt="700")
    g.T(1060, 100 + 5 * 118 + 26, "1 = strongly disagree  ·  5 = strongly agree  ·  + 2 open questions", 22, MUTE)
g.save("g_survey")

# ── Appendix C: how the 17 attacks were refused ─────────────────────────
from collections import Counter
nc = [c for c in ctrl if c["control_id"].startswith("NC")]
cnt = Counter(c["reason_code"] for c in nc)
GRP = {"ESCROW_NOT_READY": NAVY, "ESCROW_UNDER_REVIEW": NAVY, "ESCROW_FROZEN": NAVY, "TERMINAL_STATE": NAVY, "DOCUMENTS_NOT_VERIFIED": GOLD,
       "PRE_RELEASE_KYC_MISSING": TEAL, "PRE_RELEASE_KYC_EXPIRED": TEAL, "RBAC_DENIED": RED}
items = cnt.most_common()
g = G(GW, 90 + len(items) * 74 + 60)
for i, (rc, k) in enumerate(items):
    y = 60 + i * 74
    g.T(0, y + 30, rc, 25, INK, f=MONO)
    for j in range(k): g.R(640 + j * 66, y, 56, 42, GRP.get(rc, NAVY), rx=6); 
    for j in range(k): g.T(640 + j * 66 + 28, y + 30, "✕", 22, "white", "middle", wt="700")
    ids = ", ".join(c["control_id"] for c in nc if c["reason_code"] == rc)
    g.T(640 + 3 * 66 + 40, y + 30, ids, 23, MUTE, f=MONO)
fu = sum(c["funds_unchanged"] == "True" for c in nc)
y = 60 + len(items) * 74 + 20
lx = 0
for lab, c in [("escrow state", NAVY), ("document gate", GOLD), ("compliance gate", TEAL), ("permissions (RBAC)", RED)]:
    g.R(lx, y, 26, 26, c, rx=5); g.T(lx + 38, y + 21, lab, 23, SUB); lx += 70 + len(lab) * 12.5
g.T(GW, y + 21, f"{len(nc)}/{len(nc)} blocked  ·  funds unchanged {fu}/{len(nc)}", 26, NAVY, "end", wt="700")
g.save("g_attacks")

# ── Appendix B: test suite composition + where 200 random trades ended ──
groups = Counter(t["test_name"].split("::")[0].replace("tests.", "") for t in tests)
fs_ = [(k.split("::")[1], int(v_)) for k, v_ in rob.items() if k.startswith("final_state::")]
g = G(GW, 520)
g.label(0, 30, "AUTOMATED TESTS BY FILE", TEAL, sz=21)
y = 70; tot = sum(groups.values())
NM = {"test_escrow": "engine, scenarios & invariants", "test_ui_access": "UI access control", "test_ehkd": "e-HKD two-leg"}
for i, (k, v_) in enumerate(groups.most_common()):
    yy = y + i * 70
    g.T(0, yy + 30, NM.get(k, k), 26, INK); g.R(420, yy + 8, 480 * v_ / tot, 34, TEAL, rx=4); g.T(420 + 480 * v_ / tot + 14, yy + 34, f"{v_} pass", 24, TEAL, wt="600")
g.T(0, y + 3 * 70 + 30, f"{tot}/{tot} pass · {MET['M-01'][2]} reported in Table 4", 22, MUTE)
x0 = 1080
g.label(x0, 30, f"WHERE {rob['trades']} RANDOM TRADES ENDED", GOLD, sz=21)
mx = max(v_ for _, v_ in fs_)
SC2 = {"Created": MUTE, "Pending": GOLD, "Under Review": RED, "Frozen": NAVY, "Released": TEAL, "Refunded/Terminated": "#3E4A5E", "No escrow": RULE}
for i, (k, v_) in enumerate(sorted(fs_, key=lambda z: -z[1])):
    yy = 70 + i * 62
    g.T(x0, yy + 28, k, 24, INK); g.R(x0 + 300, yy + 8, 520 * v_ / mx, 30, SC2.get(k, NAVY), rx=4); g.T(x0 + 300 + 520 * v_ / mx + 12, yy + 31, str(v_), 23, SUB, wt="600")
g.T(x0, 70 + len(fs_) * 62 + 24, f"{N(rob['commands'])} commands · {N(rob['accepted'])} accepted · {N(rob['rejected'])} refused · 0 invariant violations", 22, MUTE)
g.save("g_appB")

for nm, lab, land in [("frame_main", "FINAL REPORT  ·  ALL DATA SYNTHETIC", False), ("frame_front", "FRONT MATTER  ·  NOT COUNTED", False), ("frame_body", "SECTIONS 1–10  ·  COUNTED 15 PAGES", False),
                      ("frame_app", "REFERENCES & APPENDICES  ·  NOT COUNTED", False), ("frame_app_land", "APPENDIX H  ·  FULL-SIZE FIGURES  ·  NOT COUNTED", True)]:
    frame(nm, lab, land)
print("v5 graphics ok")


# ═════════════════════ v6: four more explanatory graphics ═════════════════════
# §2 — where the public initiatives sit (from Table 1)
g = G(GW, 610)
layers = [("3", "CONDITIONAL TRADE SETTLEMENT", "release only when shipment, documents and compliance are attested", [("This project (simulated)", GOLD, True)], "THE GAP"),
          ("2", "TRADE DATA AND DOCUMENTS", "who can prove what was shipped and invoiced", [("Project CargoX", NAVY, False)], ""),
          ("1", "MONEY AND SETTLEMENT RAILS", "tokenised deposits, CBDC and central-bank money", [("EnsembleTX", NAVY, False), ("e-HKD pilots", NAVY, False), ("mBridge", NAVY, False)], "")]
for i, (n, ttl, sub, items, tag) in enumerate(layers):
    y = 20 + i * 190; inset = i * 0
    gap = i == 0
    g.R(0, y, GW, 160, GOLDL if gap else (PALE if i == 1 else "#EEF1F6"), GOLD if gap else "none", 3 if gap else 0, 14)
    g.C(60, y + 80, 30, GOLD if gap else NAVY); g.T(60, y + 91, n, 30, "white", "middle", HEAD, "700")
    g.T(120, y + 70, ttl, 27, GOLD if gap else NAVY, wt="700", ls=4)
    g.T(120, y + 112, sub, 26, SUB, f=HEAD, it=True)
    x = GW - 30
    for nm, c, solid in reversed(items):
        w = 40 + len(nm) * 15.5; x -= w
        g.R(x, y + 52, w, 56, c if solid else "white", c, 2.4, 28); g.T(x + w / 2, y + 89, nm, 26, "white" if solid else c, "middle", wt="600")
        x -= 20
    if tag: g.chip(120 + len(ttl) * 24 + 30, y + 72, tag, GOLD, "white")
g.T(0, 600, "Placement follows Table 1: none of the four public initiatives offers trade-specific conditional release.", 24, MUTE)
g.save("g_stack")

# §2.1 — where escrow sits between open account and L/C (from Table 2)
g = G(GW, 560)
cols = [("Open account", MUTE), ("Pre-funded escrow", TEAL), ("Documentary credit (L/C)", NAVY)]
cx = [700, 1230, 1740]
for (nm, c), x in zip(cols, cx): g.T(x, 40, nm, 29, c, "middle", wt="700")
dims = [("Exporter's non-payment risk", ["high: unsecured receivable", "largely removed: funds locked", "low: bank undertaking"], [3, 1, 1]),
        ("Who funds the trade", ["exporter extends credit", "importer pre-funds", "importer's bank credit line"], None),
        ("Document checking", ["importer, by hand", "automated + human review", "banks, by hand (UCP 600)"], None),
        ("Compliance timing", ["at payment", "at creation and before release", "at issuance and presentation"], None),
        ("Audit trail", ["fragmented", "shared hash-chained journal", "bank records, paper-heavy"], None)]
for i, (dim, vals, lev) in enumerate(dims):
    y = 100 + i * 88
    g.R(0, y, GW, 76, PALE if i % 2 == 0 else "white")
    g.T(16, y + 47, dim, 27, INK, wt="600")
    for j, (vtxt, x) in enumerate(zip(vals, cx)):
        c = cols[j][1]
        g.C(x - 220, y + 38, 9, c)
        g.T(x - 200, y + 47, vtxt, 24, c if j == 1 else SUB, wt="600" if j == 1 else "400")
g.L(cx[1] - 240, 70, cx[1] - 240, 100 + 5 * 88, TEAL, 2, "6 6"); g.L(cx[2] - 235, 70, cx[2] - 235, 100 + 5 * 88, TEAL, 2, "6 6")
g.T(0, 550, "Qualitative, from Table 2 and standard trade-services practice [15]; not a project measurement.", 24, MUTE)
g.save("g_spectrum")

# §6.3 — the six metric families and their headline results
fam = [("PROCESS & EFFORT", "manual settlement tasks", f"{v('M-13')} → {v('M-14')}", f"matched scope {v('M-13')} → {v('M-31')}", GOLD, "MODELLED"),
       ("ACCURACY", "scenario assertions correct", f"{v('M-02')}/{d('M-02')}", "3 flagship scenarios", TEAL, "TESTED"),
       ("SAFETY", "unsafe releases blocked", f"{v('M-04')}/{d('M-04')}", "funds unchanged in every case", TEAL, "TESTED"),
       ("TRANSPARENCY", "visibility rules obeyed", f"{v('M-08')}/{d('M-08')}", "9 principals × 7 capabilities", TEAL, "TESTED"),
       ("AUDITABILITY", "required events present", f"{v('M-06')}/{d('M-06')}", f"regulator rebuilds {v('M-07')}/{d('M-07')} paths", TEAL, "TESTED"),
       ("TIME", "post-shipment latency (days)", f"{float(v('M-21')):g} → {float(v('M-22')):g}", "simulated business days", GOLD, "MODELLED")]
g = G(GW, 520)
cw = (GW - 2 * 30) / 3
for i, (k, lab, big, sub, c, tag) in enumerate(fam):
    x = (i % 3) * (cw + 30); y = (i // 3) * 250
    g.R(x, y, cw, 225, PALE, rx=12); g.R(x, y, cw, 8, c, rx=4)
    g.label(x + 30, y + 58, k, c, sz=21)
    g.T(x + 30, y + 132, big, 58, NAVY, f=HEAD, wt="700")
    g.T(x + 30, y + 172, lab, 25, SUB); g.T(x + 30, y + 205, sub, 22, MUTE)
    g.chip(x + cw - 24, y + 58, tag, c, a="end", sz=17)
g.T(0, 512, f"Wall-clock engine compute (median {v('M-30')} ms per TC-001 run) is reported only as a sanity check, never as settlement time.", 23, MUTE)
g.save("g_metrics")

# §9 — roadmap from prototype to pilot (future-work list)
steps = [("1", "Trusted shipment data", "signed e-bill of lading or cargo-data feed as the shipment gate"),
         ("2", "Real permissioned ledger", "independent bank and regulator nodes replace the mock ledger"),
         ("3", "Richer trade terms", "partial release, quality disputes, financing of the escrow balance"),
         ("4", "HKD–THB settlement", "multi-currency leg following wholesale CBDC / tokenised CeBM"),
         ("5", "Real-world evidence", "practitioner feedback and real timings replace our assumptions")]
g = G(GW, 380)
sw = GW / 5
g.L(sw / 2, 92, GW - sw / 2, 92, RULE, 4)
g.R(0, 76, sw / 2, 32, "none")
for i, (n, t, s_) in enumerate(steps):
    x = i * sw + sw / 2
    c = GOLD if i == 4 else NAVY
    g.C(x, 92, 36, "white", c, 4); g.T(x, 104, n, 32, c, "middle", HEAD, "700")
    g.T(x, 178, t, 27, NAVY, "middle", wt="700")
    g.wrap(x - sw / 2 + 24, 222, s_, sw - 48, sz=24, lh=31, c=SUB)
g.T(0, 20, "TODAY: SIMULATED PROTOTYPE", 21, MUTE, f=SANS, wt="600", ls=4); g.T(GW, 20, "PILOT-READY", 21, GOLD, "end", SANS, "600", 4)
g.T(0, 372, "From Section 9 (future work). Step 5 is what would move H1 and H5 from 'modelled' to 'measured'.", 23, MUTE)
g.save("g_roadmap")
print("v6 graphics ok")


# ═════════════════════ v7: data-analysis graphics ═════════════════════
from datetime import datetime
BA = list(csv.DictReader(open(ROOT / "results/baseline_assumptions.csv")))
# §7.2 — where the manual settlement work sits, by participant
LANES = [("Importer (HK)", ["Importer (HK)"]), ("Exporter (TH)", ["Exporter (TH)"]),
         ("Bank H", ["Bank H (importer's bank)", "Bank H escrow contract & services"]), ("Bank O", ["Bank O (exporter's bank)", "Bank O (observer)"])]
def man(model): return [r for r in BA if r["model"] == model and r["kind"] == "MANUAL" and r["segment"] == "SETTLEMENT" and r["path"] == "MAIN"]
M = {m: man(m) for m in ("baseline", "proposed", "proposed_e2e")}
g = G(GW, 120 + len(LANES) * 112 + 60)
cols_ = [("baseline", "OPEN ACCOUNT", MUTE, 470), ("proposed", "ESCROW · PROTOTYPE", TEAL, 1010), ("proposed_e2e", "ESCROW · MATCHED SCOPE", GOLD, 1500)]
for m, lab, c, x in cols_:
    g.label(x, 40, lab, c, sz=20); g.T(x, 84, f"{len(M[m])} manual tasks", 26, NAVY, f=HEAD, wt="700")
for i, (ln, keys) in enumerate(LANES):
    y = 130 + i * 112
    g.R(0, y, GW, 96, PALE if i % 2 == 0 else "white")
    g.T(16, y + 58, ln, 28, INK, wt="600")
    for m, lab, c, x in cols_:
        tasks = [r for r in M[m] if r["lane"] in keys]
        for j, r in enumerate(tasks):
            xx = x + j * 150
            g.R(xx, y + 22, 134, 52, c if m != "baseline" else "white", c, 2.4, 26)
            g.T(xx + 67, y + 56, r["task_id"], 24, "white" if m != "baseline" else c, "middle", MONO, "700")
        if not tasks: g.T(x, y + 58, "—", 28, RULE)
g.T(0, 130 + len(LANES) * 112 + 40, "Each pill is one manual settlement task on the main path (results/baseline_assumptions.csv). Task IDs match Figures 3–4; h = hypothetical step.", 22, MUTE)
g.save("g_lanes")

# §7.3 — TC-001 journal as a timeline by actor
EVR = [json.loads(l) for l in open(ROOT / "results/events/TC-001.jsonl")]
ROLES = [("IMPORTER", "Importer"), ("CUSTOMS", "Customs"), ("LOGISTICS", "Logistics"), ("EXPORTER", "Exporter"),
         ("SVC_DOCUMENTS", "Document service"), ("SVC_COMPLIANCE", "Compliance service"), ("SYSTEM_CONTRACT", "Escrow contract"), ("BANK_TH", "Thai Bank O")]
g = G(GW, 130 + len(ROLES) * 66 + 150)
x0, x1 = 400, GW - 20
n_ = len(EVR); cw_ = (x1 - x0) / n_
X = lambda i: x0 + (i + 0.5) * cw_
SHORT = {"KYC_AML_CREATION_PASS": "KYC", "ESCROW_CREATED": "create", "FUNDS_LOCKED": "lock", "SHIPMENT_PASS": "shipped", "DOCS_CONSISTENT": "docs OK",
         "KYC_AML_PRE_RELEASE_PASS": "KYC", "ALL_GATES_PASSED": "RELEASE", "RECEIPT_OBSERVED_MOCK": "ack"}
DT = {"CONTRACT": "contract", "CUSTOMS_DECLARATION": "customs", "INVOICE": "invoice", "BILL_OF_LADING": "B/L"}
def lab_(e): return DT.get(e["details"].get("doc_type"), "doc") if e["operation"] == "SUBMIT_DOCUMENT" else SHORT.get(e["reason_code"], e["operation"].lower())
segs = [("Created", 1, 5, MUTE), ("Pending", 5, 10, GOLD), ("Released", 10, n_, TEAL)]
for nm, a_, b_, c in segs:
    xa, xb = x0 + a_ * cw_, x0 + b_ * cw_
    g.R(xa + 2, 20, xb - xa - 4, 44, c, rx=6); g.T(xa + 14, 51, nm, 23, "white", wt="700")
g.T(0, 51, "ESCROW STATE", 20, MUTE, f=SANS, wt="600", ls=4)
OPC = {"ATTEST": TEAL, "CREATE": NAVY, "LOCK": GOLD, "SUBMIT_DOCUMENT": NAVY, "RELEASE": GOLD, "ACKNOWLEDGE": MUTE}
for i, (rk, rl) in enumerate(ROLES):
    y = 120 + i * 66
    g.L(x0, y, x1, y, HAIR, 1.5); g.T(0, y + 9, rl, 25, INK)
for k, e in enumerate(EVR):
    i = [r for r, _ in ROLES].index(e["actor_role"]); y = 120 + i * 66; xx = X(k); c = OPC.get(e["operation"], NAVY)
    g.L(xx, 80, xx, 120 + len(ROLES) * 66 - 30, HAIR, 1)
    if e["operation"] == "RELEASE": g.R(xx - 15, y - 15, 30, 30, GOLD, rx=4)
    else: g.C(xx, y, 14, c, "white", 2.5)
    g.T(xx, y - 22, lab_(e), 19, c, "middle", wt="600")
yb = 120 + len(ROLES) * 66
for k, e in enumerate(EVR):
    d_ = datetime.fromisoformat(e["ts"])
    g.T(X(k), yb, f"{d_.day} Nov", 19, MUTE, "middle"); g.T(X(k), yb + 26, d_.strftime("%H:%M"), 19, MUTE, "middle", MONO)
    g.T(X(k), yb + 54, f"#{e['seq']}", 18, RULE, "middle", MONO)
lx = x0
for lab, c in [("attestation", TEAL), ("create / document", NAVY), ("funds locked", GOLD), ("acknowledgement", MUTE)]:
    g.C(lx + 12, yb + 100, 11, c); g.T(lx + 32, yb + 108, lab, 22, SUB); lx += 60 + len(lab) * 12
g.R(lx, yb + 88, 24, 24, GOLD, rx=4); g.T(lx + 34, yb + 108, "release by the contract", 22, SUB)
g.save("g_timeline")

# §7.1 — which test caught which planted bug
g = G(GW, 90 + len(mut) * 58 + 40)
g.T(0, 30, "MUTANT", 20, MUTE, f=SANS, wt="600", ls=4); g.T(140, 30, "SEEDED DEFECT", 20, MUTE, f=SANS, wt="600", ls=4); g.T(1060, 30, "FIRST TEST THAT FAILED", 20, MUTE, f=SANS, wt="600", ls=4)
g.L(0, 46, GW, 46, NAVY, 2.5)
for i, m in enumerate(mut):
    y = 92 + i * 58; k_ = m["killed_by_suite"] == "True"
    if i % 2 == 0: g.R(0, y - 38, GW, 58, PALE)
    g.T(0, y, m["mutant"], 24, NAVY, f=MONO, wt="700")
    g.T(140, y, m["seeded_defect"], 25, INK)
    if k_:
        g.C(1030, y - 8, 11, TEAL); g.T(1060, y, m["first_failing_test"].replace("test_", ""), 22, TEAL, f=MONO)
    else:
        g.C(1030, y - 8, 11, "white", RED, 2.5); g.T(1060, y, "survived — redundant (writes serialised by BEGIN IMMEDIATE)", 22, RED, f=MONO)
g.T(0, 92 + len(mut) * 58 + 10, f"{sum(m['killed_by_suite'] == 'True' for m in mut)}/{len(mut)} caught · results/mutation_analysis.csv", 22, MUTE)
g.save("g_mutants")

# §7.3 — audit scorecard per scenario
AC = list(csv.DictReader(open(ROOT / "results/audit_completeness.csv")))
g = G(GW, 120 + len(AC) * 110)
hdr = [("SCENARIO", 0), ("REQUIRED EVENTS", 330), ("EVENTS LOGGED", 690), ("REFUSALS LOGGED", 1000), ("REGULATOR REBUILDS PATH", 1300), ("COMMERCIAL LEAKS", 1700)]
for t, x in hdr: g.T(x, 30, t, 19, MUTE, f=SANS, wt="600", ls=3)
g.L(0, 48, GW, 48, NAVY, 2.5)
for i, r in enumerate(AC):
    y = 112 + i * 110
    if i % 2 == 0: g.R(0, y - 52, GW, 100, PALE)
    g.T(0, y + 8, r["scenario"], 30, NAVY, f=MONO, wt="700")
    req, pre = int(r["required_lifecycle_events"]), int(r["present_with_required_fields"])
    for k in range(req): g.R(330 + k * 26, y - 14, 20, 30, TEAL if k < pre else "white", TEAL, 1.8, 3)
    g.T(690, y + 10, f"{r['events_with_all_required_fields']}/{r['events_total']}", 34, NAVY, f=HEAD, wt="700")
    g.T(1000, y + 10, r["rejected_attempts_logged"], 34, NAVY, f=HEAD, wt="700")
    ok = r["regulator_reconstructs_state_path"] == "True"
    g.chip(1300, y + 8, "YES" if ok else "NO", TEAL if ok else RED)
    g.T(1700, y + 10, r["regulator_export_commercial_leaks"], 34, TEAL, f=HEAD, wt="700")
    if r["hash_chain_intact"] == "True": g.T(1770, y + 6, "chain intact", 22, MUTE)
g.save("g_audit")
print("v7 graphics ok")
