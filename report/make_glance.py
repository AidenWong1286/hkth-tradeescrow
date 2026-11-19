"""'Report at a glance' — the page after the cover (A4, 300 dpi). White page in the cover's palette.
All figures from results/metrics.csv and results/events/TC-001.jsonl. Writes report/figs/glance_a4.png."""
import csv, json, math, subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figs"
W, H, M = 2480, 3508, 200
NAVY, INK, SUB, MUTE, RULE = "#0B1730", "#1C2433", "#3E4A5E", "#7A8496", "#D9DEE7"
TEAL, TEALL, GOLD, GOLDL, RED, CREAM = "#1F8A82", "#E4F2EF", "#B07A22", "#F6ECD6", "#B8342A", "#EDE4CE"
# v6 (2026-11-19): modern restyle to match the colour cover; Windows system fonts, rendered by Edge.
SERIF, SANS, MONO = "Segoe UI", "Segoe UI", "Consolas"
MAN = json.load(open(ROOT / "results/run_manifest.json", encoding="utf-8"))
MET = {r[0]: r for r in csv.reader(open(ROOT / "results/metrics.csv", encoding="utf-8"))}
v = lambda k: MET[k][2]
d = lambda k: MET[k][3]
EV = [json.loads(l) for l in open(ROOT / "results/events/TC-001.jsonl")]
esc = lambda t: str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
N = lambda x: f"{int(float(x)):,}"

P = []
def T(x, y, t, sz=30, c=INK, a="start", f=SANS, wt="400", ls=0, it=False, op=1):
    if it:
        it, wt = False, "300"                        # modern: light instead of italic
    if ls and str(t).upper() == str(t):
        ls = min(float(ls), 2.5)
    P.append(f'<text x="{x}" y="{y}" text-anchor="{a}" font-family="{f}" font-weight="{wt}" font-size="{sz}" letter-spacing="{ls}" fill="{c}" fill-opacity="{op}" {"font-style=\"italic\"" if it else ""}>{esc(t)}</text>')
def R(x, y, w, h, fill="none", st="none", sw=2, rx=0, dash=None, op=1):
    P.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" fill-opacity="{op}" stroke="{st}" stroke-width="{sw}" {f"stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""}/>')
def L(x1, y1, x2, y2, c=RULE, w=2, dash=None):
    P.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}" {f"stroke-dasharray={chr(34)}{dash}{chr(34)}" if dash else ""}/>')
def C(x, y, r, fill="none", st="none", sw=2):
    P.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{st}" stroke-width="{sw}"/>')
def label(x=0, y=0, t="", c=TEAL):
    T(x, y, t, 22, c, wt="600", ls=6)
def chip(x, y, t, c):
    w = 28 + len(t) * 14.6
    R(x, y - 26, w, 36, "white", c, 2, 18); T(x + w / 2, y - 1, t, 19, c, "middle", wt="600", ls=2)
    return w

# ── header band (continues the cover) ───────────────────────────────────
R(0, 0, W, 150, NAVY)
T(M, 92, "HK–TH TRADEESCROW  ·  FINAL REPORT", 24, CREAM, wt="600", ls=6, op=0.9)
bx = W - M - 12 * 52
for i in range(12):  # journal-strip progress: this is page "1 of the story"
    R(bx + i * 52, 64, 40, 30, GOLD if i == 0 else "none", GOLD if i == 0 else CREAM, 2, 5, op=1)
    if i < 11: L(bx + i * 52 + 40, 79, bx + i * 52 + 52, 79, CREAM, 1.5)
T(bx - 24, 89, "AT A GLANCE", 20, CREAM, "end", wt="600", ls=5, op=0.7)

# ── answer first ────────────────────────────────────────────────────────
y = 300
R(M, y, 8, 250, GOLD)
label(M + 44, y + 40, "REPORT AT A GLANCE")
T(M + 40, y + 160, "Our answer: a qualified yes.", 120, NAVY, f=SERIF, wt="600", ls=-1)
T(M + 44, y + 236, "Can a pre-funded escrow of simulated tokenised deposits make HK–TH trade settlement more efficient, traceable and", 34, SUB, f=SERIF, it=True)
T(M + 44, y + 282, "auditable — without weakening compliance controls?", 34, SUB, f=SERIF, it=True)

# three verdicts
y = 680
cw = (W - 2 * M - 80) / 3
verd = [("Safer and auditable", "SUPPORTED · SIMULATED", TEAL, "Every release, review and freeze rule held under", "attack; every action is reconstructable."),
        ("Modestly more efficient", "SUPPORTED · MODELLED", GOLD, f"Manual settlement tasks 7 → 5 at matched scope", f"(−{v('M-32')}%) — a process model, not measurement."),
        ("Not free", "CONFIRMED TRADE-OFF", RED, f"Exporter risk {float(v('M-21')):g} → 0 days, but importer cash is", f"committed {v('M-24')} → {v('M-25')} days. Escrow moves the cost.")]
for i, (t, tag, c, l1, l2) in enumerate(verd):
    x = M + i * (cw + 40)
    L(x, y, x + cw, y, c, 6)
    T(x, y + 72, t, 50, NAVY, f=SERIF, wt="600")
    chip(x, y + 128, tag, c)
    T(x, y + 190, l1, 27, SUB); T(x, y + 230, l2, 27, SUB)

# ── four numbers ────────────────────────────────────────────────────────
y = 1000
R(M, y, W - 2 * M, 300, "#F5F7FA", "none", rx=14)
kp = [(f"{v('M-01')}/{d('M-01')}", "automated tests pass", "TESTED", TEAL),
      (f"{v('M-04')}/{d('M-04')}", "unsafe release attempts refused", "TESTED", TEAL),
      (f"0 / {N(d('M-09'))}", f"violations · {N(v('M-10'))} random commands", "TESTED", TEAL),
      (f"{v('M-11')}/{d('M-11')}", "deliberately planted bugs caught", "TESTED", TEAL)]
kw = (W - 2 * M) / 4
for i, (big, lab, tag, c) in enumerate(kp):
    x = M + i * kw + 50
    if i: L(M + i * kw, y + 50, M + i * kw, y + 250, RULE, 2)
    T(x, y + 140, big, 92, NAVY, f=SERIF, wt="600")
    T(x, y + 196, lab, 25, SUB)
    chip(x, y + 258, tag + " · SYNTHETIC DATA", c)

# ── how it works (light blueprint) ──────────────────────────────────────
y = 1420
label(M, y, "HOW THE MONEY MOVES"); T(M + 470, y, "the release guard checks all three gates at the moment of release", 26, MUTE, f=SERIF, it=True)
top = y + 50
R(M, top, 520, 560, "none", GOLD, 2.5, 16, "14 10")
T(M + 260, top + 44, "OFF-CHAIN ATTESTATIONS", 19, GOLD, "middle", wt="600", ls=4)
docs = [("BILL OF LADING", "BL-001 · SH-001"), ("INVOICE & CONTRACT", "HKD 250,000 · HS 6912"), ("KYC / AML", "PASS · fresh ≤ 48 h")]
gx0 = M + 640
for i, (a, b) in enumerate(docs):
    yy = top + 80 + i * 158
    P.append(f'<path d="M{M + 36},{yy} h380 l40,40 v90 h-420 Z" fill="white" stroke="{NAVY}" stroke-width="2.5"/>')
    P.append(f'<path d="M{M + 416},{yy} v40 h40" fill="none" stroke="{NAVY}" stroke-width="2"/>')
    T(M + 66, yy + 52, a, 21, NAVY, wt="600", ls=3); T(M + 66, yy + 98, b, 21, MUTE, f=MONO)
    L(M + 470, yy + 65, gx0 - 10, yy + 65, NAVY, 2)
    P.append(f'<path d="M{gx0},{yy + 130} v-90 a70,40 0 0 1 140,0 v90" fill="none" stroke="{TEAL}" stroke-width="4"/>')
    C(gx0 + 70, yy + 70, 22, "white", TEAL, 3); P.append(f'<path d="M{gx0 + 59},{yy + 70} l8,9 l16,-18" fill="none" stroke="{TEAL}" stroke-width="4"/>')
    T(gx0 + 175, yy + 78, ["SHIPMENT", "DOCUMENTS", "COMPLIANCE"][i], 21, TEAL, wt="600", ls=4)
    L(gx0 + 360, yy + 70, gx0 + 500, top + 300, NAVY, 2)
vx, vy = gx0 + 640, top + 300
C(vx, vy, 175, GOLDL, "none"); C(vx, vy, 122, "white", GOLD, 5); C(vx, vy, 90, "none", GOLD, 2)
for a in range(0, 360, 30):
    r = math.radians(a); L(vx + 90 * math.cos(r), vy + 90 * math.sin(r), vx + 108 * math.cos(r), vy + 108 * math.sin(r), GOLD, 2)
for a in (90, 210, 330):
    r = math.radians(a); L(vx, vy, vx + 60 * math.cos(r), vy + 60 * math.sin(r), GOLD, 7)
C(vx, vy, 19, GOLD)
T(vx, vy + 170, "ESCROW · HKD 250,000", 21, GOLD, "middle", wt="600", ls=4)
ex = W - M - 110
L(vx + 128, vy, ex - 115, vy, GOLD, 4); P.append(f'<path d="M{ex - 128},{vy - 14} l22,14 l-22,14" fill="none" stroke="{GOLD}" stroke-width="4"/>')
R(ex - 105, vy - 75, 215, 150, "white", NAVY, 2.5, 14)
T(ex + 2, vy - 18, "THAI", 19, MUTE, "middle", wt="600", ls=4); T(ex + 2, vy + 16, "EXPORTER", 19, MUTE, "middle", wt="600", ls=4); T(ex + 2, vy + 54, "paid once", 28, NAVY, "middle", f=SERIF)
T(gx0 - 20, top + 610, "If a gate fails: document mismatch → Under Review (a reviewer decides) · AML alert → Frozen (compliance decides). Money never moves on a guess.", 24, SUB, f=SERIF, it=True)

# ── lower row: trade-off · evidence ladder · rubric map ─────────────────
y = 2160
L(M, y - 50, W - M, y - 50, RULE, 2)
c1, c2, c3 = M, M + 720, M + 1430
# trade-off
label(c1, y, "WHO CARRIES THE WAIT", GOLD)
rows = [("Open account", [("exporter at risk", float(v('M-21')), RED), ("importer cash", float(v('M-24')), TEAL)]),
        ("Escrow", [("exporter at risk", 0.0, RED), ("importer cash", float(v('M-25')), TEAL)])]
sc = 52
for i, (nm, bars) in enumerate(rows):
    yy = y + 70 + i * 250
    T(c1, yy + 10, nm, 36, NAVY, f=SERIF, wt="600")
    for k, (bl, val, c) in enumerate(bars):
        by = yy + 50 + k * 70
        T(c1, by + 26, bl, 22, MUTE)
        if val > 0: R(c1 + 215, by, val * sc, 34, c, rx=4)
        else: L(c1 + 215, by + 2, c1 + 215, by + 32, c, 4)
        T(c1 + 230 + val * sc, by + 27, f"{val:g} d", 24, c, wt="600")
T(c1, y + 600, "simulated days, normal trade, base assumptions", 25, MUTE, f=SERIF, it=True)
# evidence ladder
label(c2, y, "HOW STRONG IS THE EVIDENCE?")
rungs = [("Measured", "real banks, real trades", "—", MUTE), ("Simulated", "executed on our prototype", "H2  H3  H4", TEAL), ("Modelled", "process & timing model", "H1  H5", GOLD), ("Assumed", "inputs we chose", "durations · 48 h · limits", MUTE)]
for i, (nm, sub, hs, c) in enumerate(rungs):
    yy = y + 80 + i * 135
    L(c2 + 44, yy + 62, c2 + 620, yy + 62, RULE, 1.5)
    C(c2 + 14, yy, 12, c if nm != "Measured" else "white", c, 3)
    T(c2 + 44, yy + 10, nm, 34, NAVY if nm != "Measured" else MUTE, f=SERIF, wt="600")
    T(c2 + 44, yy + 36, sub, 20, MUTE)
    T(c2 + 620, yy + 12, hs, 26, c, "end", wt="600", f=SANS if i != 3 else SERIF, it=(i == 3))
L(c2 + 14, y + 80, c2 + 14, y + 80 + 3 * 135, RULE, 2)
T(c2, y + 640, "Top rung empty: no hypothesis has real-world evidence yet.", 25, MUTE, f=SERIF, it=True)
# rubric map
label(c3, y, "WHERE TO FIND IT")
rub = [("Background & motivation", "§1–2"), ("Weaknesses of current practice", "§1.2, §2"), ("Innovative elements", "§4.1"), ("System design", "§4–5"),
       ("Experimentation", "§6"), ("Outcome evaluation", "§7–8"), ("Feedback & revisions", "§7.4, App. G"), ("Self-reflections", "§10")]
for i, (a, b) in enumerate(rub):
    yy = y + 70 + i * 68
    T(c3, yy, a, 27, INK); T(W - M, yy, b, 25, TEAL, "end", f=MONO)
    L(c3, yy + 22, W - M, yy + 22, RULE, 1.5, "4 6")

# ── journal strip (links to the cover) ───────────────────────────────────
y = 2900
label(y=y, x=M, t="THE LIFE OF TRADE TR-001  ·  12 HASH-LINKED JOURNAL ENTRIES")
SH = {"CONTRACT": "CONTRACT", "CUSTOMS_DECLARATION": "CUSTOMS", "INVOICE": "INVOICE", "BILL_OF_LADING": "B/L"}
AT = {"KYC_AML_CREATION_PASS": "KYC", "SHIPMENT_PASS": "SHIPPED", "DOCS_CONSISTENT": "DOCS OK", "KYC_AML_PRE_RELEASE_PASS": "KYC"}
bw = 150; gap = (W - 2 * M - 12 * bw) / 11
for i, e in enumerate(EV):
    x = M + i * (bw + gap); yy = y + 40
    op = e["operation"]
    nm = SH.get(e["details"].get("doc_type"), "DOC") if op == "SUBMIT_DOCUMENT" else AT.get(e["reason_code"], op) if op == "ATTEST" else {"ACKNOWLEDGE": "ACK"}.get(op, op)
    rel = op == "RELEASE"; ch = e["prior_state"] != e["new_state"] and e["new_state"]
    c = GOLD if rel else (TEAL if ch else NAVY)
    R(x, yy, bw, 104, GOLDL if rel else (TEALL if ch else "white"), c, 3 if (rel or ch) else 1.5, 10)
    T(x + bw / 2, yy + 40, nm, 21, c, "middle", wt="600", ls=1)
    T(x + bw / 2, yy + 74, e["hash"][:6], 19, MUTE, "middle", f=MONO)
    if ch or rel: T(x + bw / 2, yy + 140, "→ " + e["new_state"], 25, c, "middle", f=SERIF, it=True)
    if i < 11: L(x + bw + 3, yy + 52, x + bw + gap - 3, yy + 52, NAVY, 2)
T(M, y + 230, "Each entry stores the hash of the one before it, so any later edit or deletion is detectable (verified in test TC-018).", 23, MUTE, f=SERIF, it=True)

# ── footer ──────────────────────────────────────────────────────────────
L(M, 3340, W - M, 3340, RULE, 2)
T(M, 3395, f"Every figure on this page is read from results/ of the run of record (code {MAN['code_sha256_16'][:8]}) · all data synthetic", 24, MUTE)
T(W - M, 3395, "ii", 26, NAVY, "end", f=SERIF, wt="600")

svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="white"/>{"".join(P)}</svg>'
from playwright.sync_api import sync_playwright
with sync_playwright() as _pw:
    _b = _pw.chromium.launch(channel="msedge", headless=True)
    _pg = _b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    _pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
    _pg.screenshot(path=str(OUT / "glance_a4.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
    _b.close()
Image.open(OUT / "glance_a4.png").convert("RGB").save(OUT / "glance_a4.pdf", resolution=300)
print("wrote glance_a4")
