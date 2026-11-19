"""Two cover concepts for comparison (A4, 300 dpi):
A  'The life of trade TR-001' — title, slim night-harbour band, the real 12-entry hash-chained journal of TC-001.
D  'Harbour + blueprint'      — title, night-harbour band, blueprint of the release mechanism, mini journal strip.
Run after presentation/v3/cover_night_art.py. Writes report/figs/cover_A.png, cover_D.png."""
import json, subprocess, base64, math
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
import csv as _csv
MET_TESTS = next(r[2] for r in _csv.reader(open(ROOT / "results/metrics.csv", encoding="utf-8")) if r and r[0] == "M-01")  # was hard-coded "77"
OUT = ROOT / "report" / "figs"; OUT.mkdir(parents=True, exist_ok=True)
W, H, M = 2480, 3508, 210
NAVY, CREAM, DIM, TEAL, GOLD, RED = "#0B1730", "#EDE4CE", "#9AA6BB", "#7FDCCB", "#E2B867", "#E58B7B"
SERIF, SANS, MONO = "Crimson Text", "Inter", "DejaVu Sans Mono"
EV = [json.loads(l) for l in open(ROOT / "results/events/TC-001.jsonl")]
HASH = EV[-1]["hash"]
CODE = json.load(open(ROOT / "results/run_manifest.json"))["code_sha256_16"][:8]
_IDS = json.load(open(ROOT / "team.local.json", encoding="utf-8"))["ids"] if (ROOT / "team.local.json").exists() else {}
members = [(n, a, _IDS.get(n, "")) for n, a in (("Tang Yu Hin", "Alex"), ("Chow Ka Shing", "Marcus"),
                                                ("Wong Ho Ming", "Michael"), ("So Lai Chun", "Jeff"))]   # IDs: team.local.json (not in git)
ROLE = {"SVC_COMPLIANCE": "Compliance service", "IMPORTER": "HK importer", "CUSTOMS": "Customs", "LOGISTICS": "Logistics",
        "EXPORTER": "Thai exporter", "SVC_DOCUMENTS": "Document service", "SYSTEM_CONTRACT": "Escrow contract", "BANK_TH": "Thai Bank O"}


def doc_kind(e):
    d = e.get("details") or {}
    for k in ("doc_type", "document_type", "kind", "type"):
        if isinstance(d, dict) and d.get(k):
            return str(d[k]).replace("_", " ").lower()
    return None


def label(e):
    op, rc = e["operation"], e["reason_code"]
    if op == "SUBMIT_DOCUMENT":
        k = doc_kind(e)
        return f"submits {k}" if k else "submits document"
    return {"CREATE": "creates escrow", "LOCK": "locks HKD 250,000", "RELEASE": "releases HKD 250,000", "ACKNOWLEDGE": "acknowledges receipt",
            "ATTEST": {"KYC_AML_CREATION_PASS": "creation KYC/AML: PASS", "SHIPMENT_PASS": "shipment on board: PASS",
                       "DOCS_CONSISTENT": "documents consistent: PASS", "KYC_AML_PRE_RELEASE_PASS": "pre-release KYC/AML: PASS"}.get(rc, rc.lower())}.get(op, op.lower())


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def background():
    bg = Image.new("RGB", (W, H)); px = bg.load()
    top, mid, bot = (5, 10, 22), (11, 24, 48), (6, 12, 25)
    for y in range(H):
        t = y / H
        a, b, u = (top, mid, t / 0.4) if t < 0.4 else (mid, bot, (t - 0.4) / 0.6)
        c = tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
        for x in range(W): px[x, y] = c
    return bg.convert("RGBA")


def art_band(bg, y0, crop0, crop1, alpha=1.0):
    art = Image.open(ROOT / "presentation/v3/night_art.png").convert("RGBA")
    ah = int(art.height * W / art.width)
    art = art.resize((W, ah), Image.LANCZOS).crop((0, crop0, W, crop1))
    # soft fade at top and bottom of the band
    mask = Image.new("L", art.size, 255); mp = mask.load(); hh = art.size[1]
    for y in range(hh):
        f = min(1.0, y / 120, (hh - y) / 160) * alpha
        for x in range(0, W): mp[x, y] = int(art.getpixel((x, y))[3] * f)
    art.putalpha(mask)
    bg.alpha_composite(art, (0, y0))


def header_svg():
    return f'''<text x="{M}" y="250" font-family="{SANS}" font-weight="600" font-size="29" letter-spacing="6" fill="{CREAM}" fill-opacity="0.9">THE CHINESE UNIVERSITY OF HONG KONG</text>
<text x="{M}" y="296" font-family="{SANS}" font-size="26" letter-spacing="4" fill="{DIM}">Department of Systems Engineering and Engineering Management</text>
<text x="{W - M}" y="250" text-anchor="end" font-family="{SANS}" font-weight="600" font-size="29" letter-spacing="6" fill="{CREAM}" fill-opacity="0.9">FTEC3002</text>
<text x="{W - M}" y="296" text-anchor="end" font-family="{SANS}" font-size="26" letter-spacing="4" fill="{DIM}">Introduction to Financial Infrastructure</text>
<line x1="{M}" y1="350" x2="{W - M}" y2="350" stroke="{CREAM}" stroke-opacity="0.16" stroke-width="2"/>'''


def title_svg(y):
    return f'''<rect x="{M}" y="{y}" width="8" height="300" fill="{GOLD}"/>
<text x="{M + 50}" y="{y + 50}" font-family="{SANS}" font-weight="600" font-size="27" letter-spacing="9" fill="{TEAL}">FINAL PROJECT REPORT  ·  GROUP 1</text>
<text x="{M + 44}" y="{y + 210}" font-family="{SERIF}" font-weight="600" font-size="182" letter-spacing="-2" fill="{CREAM}">HK–TH <tspan fill="{GOLD}">TradeEscrow</tspan></text>
<text x="{M + 50}" y="{y + 288}" font-family="{SERIF}" font-style="italic" font-size="54" fill="{CREAM}" fill-opacity="0.82">A tokenised-deposit escrow prototype for Hong Kong–Thailand cross-border trade finance</text>'''


def seal_svg(sx, sy, sr):
    txt = "ESCROW ESC-001 · TRADE TR-001 · HKD 250,000 · LAEM CHABANG → HONG KONG · "
    rr = sr - 26
    ring = "".join(
        f'<text x="{sx + rr * math.sin(2 * math.pi * k / len(txt)):.1f}" y="{sy - rr * math.cos(2 * math.pi * k / len(txt)):.1f}" '
        f'transform="rotate({360 * k / len(txt):.2f} {sx + rr * math.sin(2 * math.pi * k / len(txt)):.1f} {sy - rr * math.cos(2 * math.pi * k / len(txt)):.1f})" '
        f'text-anchor="middle" dominant-baseline="middle" font-family="{SANS}" font-weight="600" font-size="13.5" fill="{GOLD}" fill-opacity="0.85">{esc(ch)}</text>'
        for k, ch in enumerate(txt) if ch != " ")
    return f'''<circle cx="{sx}" cy="{sy}" r="{sr}" fill="none" stroke="{GOLD}" stroke-opacity="0.8" stroke-width="3"/>
<circle cx="{sx}" cy="{sy}" r="{sr - 44}" fill="none" stroke="{GOLD}" stroke-opacity="0.5" stroke-width="1.5"/>{ring}
<text x="{sx}" y="{sy + 4}" text-anchor="middle" font-family="{SERIF}" font-weight="700" font-size="27" fill="{GOLD}">RELEASED</text>
<text x="{sx}" y="{sy + 32}" text-anchor="middle" font-family="{SANS}" font-weight="600" font-size="12.5" letter-spacing="2.5" fill="{GOLD}" fill-opacity="0.8">3 / 3 GATES</text>'''


def grid_svg():
    cols = [M, M + 760, M + 1250]
    lab = lambda x, y, t: f'<text x="{x}" y="{y}" font-family="{SANS}" font-weight="600" font-size="22" letter-spacing="6" fill="{TEAL}">{t}</text>'
    val = lambda x, y, t: f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="36" fill="{CREAM}">{t}</text>'
    sub = lambda x, y, t: f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="21" letter-spacing="3" fill="{DIM}">{t}</text>'
    g = f'<line x1="{M}" y1="2860" x2="{W - M}" y2="2860" stroke="{CREAM}" stroke-opacity="0.16" stroke-width="2"/>' + lab(cols[0], 2935, "PREPARED BY")
    for k, (n, e, sid) in enumerate(members):
        y = 2995 + k * 76
        g += val(cols[0], y, f'{n} <tspan font-style="italic" fill="{DIM}">({e})</tspan>') + f'<text x="{cols[0] + 520}" y="{y}" font-family="{SANS}" font-size="22" letter-spacing="3" fill="{DIM}">{sid}</text>'
    g += lab(cols[1], 2935, "SUBMITTED") + val(cols[1], 2995, "19 November 2026") + sub(cols[1], 3040, "FINAL REPORT · V1.0")
    g += lab(cols[1], 3130, "CASE") + val(cols[1], 3190, "Trade TR-001 · ESC-001") + sub(cols[1], 3235, "SYNTHETIC FIXTURE")
    g += lab(cols[2], 2935, "RUN OF RECORD") + val(cols[2], 2995, CODE) + sub(cols[2], 3040, "CODE HASH")
    g += lab(cols[2], 3130, "EVIDENCE") + val(cols[2], 3190, f"{MET_TESTS} tests · 17 attacks") + sub(cols[2], 3235, "RESULTS/ · REPRODUCIBLE")
    g += seal_svg(W - M - 118, 3090, 118)
    g += f'''<line x1="{M}" y1="3330" x2="{W - M}" y2="3330" stroke="{CREAM}" stroke-opacity="0.16" stroke-width="2"/>
<text x="{M}" y="3388" font-family="{SANS}" font-size="22" letter-spacing="2" fill="{DIM}" fill-opacity="0.85">All transaction data are synthetic. No live bank, tokenised deposit, e-HKD, EnsembleTX or mBridge system was used.</text>
<text x="{W - M}" y="3388" text-anchor="end" font-family="{MONO}" font-size="20" fill="{DIM}" fill-opacity="0.85">journal {HASH[:10]}…{HASH[-6:]}</text>'''
    return g


def journal_timeline(y0, rows_h):
    """The 12 real TC-001 journal entries as a lit, hash-linked timeline."""
    xs = {"time": M, "spine": M + 330, "who": M + 400, "what": M + 800, "hash": W - M}
    s = f'''<text x="{M}" y="{y0}" font-family="{SANS}" font-weight="600" font-size="25" letter-spacing="8" fill="{TEAL}">THE LIFE OF TRADE TR-001</text>
<text x="{W - M}" y="{y0}" text-anchor="end" font-family="{SANS}" font-size="23" letter-spacing="4" fill="{DIM}">12 JOURNAL ENTRIES  ·  EACH HASH-LINKED TO THE LAST</text>'''
    top = y0 + 60
    n = len(EV)
    s += f'<line x1="{xs["spine"]}" y1="{top + 10}" x2="{xs["spine"]}" y2="{top + (n - 1) * rows_h + 10}" stroke="{CREAM}" stroke-opacity="0.35" stroke-width="3"/>'
    for i, e in enumerate(EV):
        y = top + i * rows_h
        ts = e["ts"][5:16].replace("T", "  ")  # MM-DD  HH:MM
        mo, dd = ts[:2], ts[3:5]
        when = f"{int(dd)} Nov  {ts[7:]}"
        changed = e["prior_state"] != e["new_state"] and e["new_state"]
        rel = e["operation"] == "RELEASE"
        col = GOLD if rel else (TEAL if changed else CREAM)
        r = 15 if (changed or rel) else 9
        s += f'<text x="{xs["time"]}" y="{y + 18}" font-family="{MONO}" font-size="24" fill="{DIM}">{when}</text>'
        if rel:
            s += f'<circle cx="{xs["spine"]}" cy="{y + 10}" r="34" fill="{GOLD}" fill-opacity="0.18"/>'
        s += f'<circle cx="{xs["spine"]}" cy="{y + 10}" r="{r}" fill="{col if (changed or rel) else NAVY}" stroke="{col}" stroke-width="3"/>'
        s += f'<text x="{xs["who"]}" y="{y + 18}" font-family="{SANS}" font-weight="600" font-size="22" letter-spacing="3" fill="{DIM}">{esc(ROLE.get(e["actor_role"], e["actor_role"]).upper())}</text>'
        what = esc(label(e))
        st = f'  <tspan fill="{col}" font-weight="700">→ {esc(e["new_state"])}</tspan>' if changed else ""
        s += f'<text x="{xs["what"]}" y="{y + 20}" font-family="{SERIF}" font-size="36" fill="{GOLD if rel else CREAM}" {"font-weight=\"700\"" if rel else ""}>{what}{st}</text>'
        s += f'<text x="{xs["hash"]}" y="{y + 18}" text-anchor="end" font-family="{MONO}" font-size="21" fill="{TEAL}" fill-opacity="0.75">{e["hash"][:8]}</text>'
    return s


def blueprint(y0):
    """Cream line-drawing of the mechanism: off-chain documents → three gates → vault → exporter, journal beneath."""
    L = lambda x1, y1, x2, y2, c=CREAM, w=3, d="": f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}" stroke-opacity="0.85" {f"stroke-dasharray={chr(34)}{d}{chr(34)}" if d else ""}/>'
    T = lambda x, y, t, sz=24, c=CREAM, a="middle", f=SANS, wt="400", ls=0: f'<text x="{x}" y="{y}" text-anchor="{a}" font-family="{f}" font-weight="{wt}" font-size="{sz}" letter-spacing="{ls}" fill="{c}">{esc(t)}</text>'
    s = T(M, y0, "HOW THE MONEY MOVES", 25, TEAL, "start", SANS, "600", 8) + T(W - M, y0, "RELEASE GUARD  ·  ALL THREE GATES, EXACTLY ONCE", 23, DIM, "end", SANS, "400", 4)
    top = y0 + 70
    # off-chain documents (trust boundary)
    s += f'<rect x="{M}" y="{top}" width="560" height="560" rx="18" fill="none" stroke="{GOLD}" stroke-width="2.5" stroke-dasharray="14 10" stroke-opacity="0.8"/>'
    s += T(M + 280, top + 44, "OFF-CHAIN ATTESTATIONS", 20, GOLD, "middle", SANS, "600", 5)
    docs = [("BILL OF LADING", "BL-001 · SH-001"), ("INVOICE & CONTRACT", "HKD 250,000 · HS 6912"), ("KYC / AML", "PASS · fresh ≤ 48 h")]
    for i, (a, b) in enumerate(docs):
        y = top + 80 + i * 158
        s += f'<path d="M{M + 40},{y} h400 l40,40 v90 h-440 Z" fill="{NAVY}" stroke="{CREAM}" stroke-width="2.5" stroke-opacity="0.9"/>'
        s += f'<path d="M{M + 440},{y} v40 h40" fill="none" stroke="{CREAM}" stroke-width="2" stroke-opacity="0.7"/>'
        s += T(M + 70, y + 52, a, 22, CREAM, "start", SANS, "600", 3) + T(M + 70, y + 98, b, 22, DIM, "start", MONO)
    # three gates
    gx0 = M + 690
    for i, g in enumerate(["SHIPMENT", "DOCUMENTS", "COMPLIANCE"]):
        y = top + 80 + i * 158
        s += L(M + 520, y + 65, gx0 - 10, y + 65, CREAM, 2)
        s += f'<path d="M{gx0},{y + 130} v-90 a70,40 0 0 1 140,0 v90" fill="none" stroke="{TEAL}" stroke-width="4"/>'
        s += f'<circle cx="{gx0 + 70}" cy="{y + 70}" r="22" fill="{NAVY}" stroke="{TEAL}" stroke-width="3"/><path d="M{gx0 + 59},{y + 70} l8,9 l16,-18" fill="none" stroke="{TEAL}" stroke-width="4"/>'
        s += T(gx0 + 200, y + 78, g, 22, TEAL, "start", SANS, "600", 4)
        s += L(gx0 + 395, y + 70, gx0 + 560, top + 300, CREAM, 2)
    # vault
    vx, vy = gx0 + 700, top + 300
    s += f'<circle cx="{vx}" cy="{vy}" r="200" fill="{GOLD}" fill-opacity="0.08"/><circle cx="{vx}" cy="{vy}" r="140" fill="{NAVY}" stroke="{GOLD}" stroke-width="5"/>'
    s += f'<circle cx="{vx}" cy="{vy}" r="104" fill="none" stroke="{GOLD}" stroke-width="2" stroke-opacity="0.6"/>'
    for a in range(0, 360, 30):
        r = math.radians(a); s += L(vx + 104 * math.cos(r), vy + 104 * math.sin(r), vx + 124 * math.cos(r), vy + 124 * math.sin(r), GOLD, 2)
    for a in (90, 210, 330):
        r = math.radians(a); s += L(vx, vy, vx + 70 * math.cos(r), vy + 70 * math.sin(r), GOLD, 7)
    s += f'<circle cx="{vx}" cy="{vy}" r="22" fill="{GOLD}"/>'
    s += T(vx, vy + 190, "ESCROW · HKD 250,000", 22, GOLD, "middle", SANS, "600", 4)
    # exporter
    ex = W - M - 120
    s += L(vx + 145, vy, ex - 110, vy, GOLD, 4) + f'<path d="M{ex - 125},{vy - 14} l22,14 l-22,14" fill="none" stroke="{GOLD}" stroke-width="4"/>'
    s += f'<rect x="{ex - 100}" y="{vy - 75}" width="220" height="150" rx="14" fill="{NAVY}" stroke="{CREAM}" stroke-width="2.5"/>'
    s += T(ex + 10, vy - 18, "THAI", 20, DIM, "middle", SANS, "600", 4) + T(ex + 10, vy + 18, "EXPORTER", 20, DIM, "middle", SANS, "600", 4) + T(ex + 10, vy + 54, "paid once", 26, CREAM, "middle", SERIF)
    return s


def short(e):
    op = e["operation"]
    if op == "SUBMIT_DOCUMENT":
        return {"CONTRACT": "CONTRACT", "CUSTOMS_DECLARATION": "CUSTOMS", "INVOICE": "INVOICE", "BILL_OF_LADING": "B/L"}.get(e["details"].get("doc_type"), "DOC")
    if op == "ATTEST":
        return {"KYC_AML_CREATION_PASS": "KYC", "SHIPMENT_PASS": "SHIPPED", "DOCS_CONSISTENT": "DOCS OK", "KYC_AML_PRE_RELEASE_PASS": "KYC"}.get(e["reason_code"], "ATTEST")
    return {"ACKNOWLEDGE": "ACK"}.get(op, op)


def journal_strip(y0):
    s = f'<text x="{M}" y="{y0}" font-family="{SANS}" font-weight="600" font-size="22" letter-spacing="7" fill="{TEAL}">TAMPER-EVIDENT JOURNAL · TR-001</text>'
    n = len(EV); bw, gap = 118, (W - 2 * M - len(EV) * 118) / (len(EV) - 1)
    for i, e in enumerate(EV):
        x = M + i * (bw + gap); y = y0 + 34
        rel = e["operation"] == "RELEASE"; ch = e["prior_state"] != e["new_state"] and e["new_state"]
        col = GOLD if rel else (TEAL if ch else CREAM)
        s += f'<rect x="{x:.1f}" y="{y}" width="{bw}" height="70" rx="8" fill="{NAVY}" stroke="{col}" stroke-width="{3 if (rel or ch) else 1.5}" stroke-opacity="{1 if (rel or ch) else 0.5}"/>'
        s += f'<text x="{x + bw / 2:.1f}" y="{y + 32}" text-anchor="middle" font-family="{SANS}" font-weight="600" font-size="16" letter-spacing="1" fill="{col}">{esc(short(e))}</text>'
        s += f'<text x="{x + bw / 2:.1f}" y="{y + 56}" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{DIM}">{e["hash"][:6]}</text>'
        if i < n - 1:
            s += f'<line x1="{x + bw + 4:.1f}" y1="{y + 35}" x2="{x + bw + gap - 4:.1f}" y2="{y + 35}" stroke="{CREAM}" stroke-opacity="0.5" stroke-width="2"/>'
    return s


def render(name, bg, body):
    bgp = OUT / f"_{name}_bg.png"; bg.convert("RGB").save(bgp)
    b64 = base64.b64encode(bgp.read_bytes()).decode()
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><image x="0" y="0" width="{W}" height="{H}" xlink:href="data:image/png;base64,{b64}"/>{body}</svg>'
    sp = OUT / f"_{name}.svg"; sp.write_text(svg)
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(OUT / f"{name}.png"), str(sp)], check=True)
    Image.open(OUT / f"{name}.png").convert("RGB").save(OUT / f"{name}.pdf", resolution=300)
    sp.unlink(); bgp.unlink()


# ── A ──
bg = background(); art_band(bg, 960, 230, 1080, 0.95)
render("cover_A", bg, header_svg() + title_svg(500) + journal_timeline(1930, 72) + grid_svg())
# ── D ──
bg = background(); art_band(bg, 860, 250, 1060, 0.95)
render("cover_D", bg, header_svg() + title_svg(500) + blueprint(1720) + journal_strip(2560) + grid_svg())
print("wrote cover_A, cover_D")
