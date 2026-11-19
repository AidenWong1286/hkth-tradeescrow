"""Ink-illustration kit for the paper-style deck: transparent PNG vignettes drawn procedurally (original artwork).
Run: python presentation/v3/inkkit.py  -> presentation/v3/ink/*.png"""
import math, random, subprocess
from pathlib import Path
from PIL import Image, ImageFilter, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "ink"; OUT.mkdir(exist_ok=True)
INK = "#1d1b18"; PAPER = "#F7F3EB"; TEAL = "#1F8A82"; GOLD = "#C9922F"; GOLDW = "#E2A84B"; RED = "#B8342A"


class Ink:
    def __init__(self, w, h, seed=1):
        self.w, self.h, self.P, self.defs = w, h, [], []
        self.r = random.Random(seed)
        self.defs.append('<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="9"/></filter>')
        self.defs.append('<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="24"/></filter>')

    def j(self, a): return self.r.uniform(-a, a)

    def line(self, x0, y0, x1, y1, w=2.2, op=0.92, col=INK, wob=1.6, sketch=True):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 130) + 1)
        pts = [(x0 + (x1 - x0) * i / n + (self.j(wob) if 0 < i < n else 0), y0 + (y1 - y0) * i / n + (self.j(wob) if 0 < i < n else 0)) for i in range(n + 1)]
        self.P.append(f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" stroke="{col}" stroke-width="{w:.2f}" stroke-opacity="{op}" fill="none" stroke-linecap="round"/>')
        if sketch and w >= 1.8 and self.r.random() < 0.5:
            self.line(x0 + self.j(2.5), y0 + self.j(2.5), x1 + self.j(2.5), y1 + self.j(2.5), w * 0.45, op * 0.45, col, 2.5, False)

    def poly(self, pts, w=2.2, op=0.92, col=INK, close=True, fill=None, fop=1):
        if fill:
            self.P.append(f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in pts)} Z" fill="{fill}" fill-opacity="{fop}"/>')
        seq = pts + ([pts[0]] if close else [])
        for a, b in zip(seq, seq[1:]): self.line(a[0], a[1], b[0], b[1], w, op, col)

    def path(self, d, w=2.2, col=INK, op=0.92, fill="none", dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.P.append(f'<path d="{d}" stroke="{col}" stroke-width="{w}" stroke-opacity="{op}" fill="{fill}" stroke-linecap="round"{da}/>')

    def hatch(self, clip, step=9, ang=55, w=1.0, op=0.5, col=INK):
        cid = f"c{len(self.defs)}"
        self.defs.append(f'<clipPath id="{cid}"><path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in clip)} Z"/></clipPath>')
        xs, ys = [p[0] for p in clip], [p[1] for p in clip]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        a = math.radians(ang); L = (x1 - x0) + (y1 - y0)
        self.P.append(f'<g clip-path="url(#{cid})">')
        k = -L
        while k < L * 2:
            sx, sy = x0 + k, y1
            self.line(sx, sy, sx + math.cos(a) * L * 2, sy - math.sin(a) * L * 2, w, op * self.r.uniform(0.7, 1), col, 1.1, False)
            k += step * self.r.uniform(0.85, 1.15)
        self.P.append("</g>")

    def wash(self, pts, col, op=0.35):
        self.P.append(f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in pts)} Z" fill="{col}" fill-opacity="{op}" filter="url(#soft)"/>')

    def circle(self, cx, cy, r, w=2.2, col=INK, op=0.92, n=36):
        pts = [(cx + (r + self.j(1.5)) * math.cos(2 * math.pi * i / n), cy + (r + self.j(1.5)) * math.sin(2 * math.pi * i / n)) for i in range(n)]
        self.poly(pts, w, op, col)

    def save(self, name):
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><defs>{"".join(self.defs)}</defs>{"".join(self.P)}</svg>'
        sp = OUT / f"{name}.svg"; sp.write_text(svg)
        subprocess.run(["rsvg-convert", "-o", str(OUT / f"{name}.png"), str(sp)], check=True)
        sp.unlink()
        return OUT / f"{name}.png"


# ── 1. nautical chart: HK → Bangkok route (problem slide) ────────────────
def nautical():
    c = Ink(1500, 1300, 4)
    for x in range(100, 1450, 150): c.line(x, 60, x, 1240, 1.0, 0.22, wob=0.6, sketch=False)
    for y in range(110, 1240, 150): c.line(60, y, 1440, y, 1.0, 0.22, wob=0.6, sketch=False)
    # abstract coastlines (not to scale)
    rr = random.Random(2)
    def coast(pts, hatch_side):
        c.poly(pts, 2.0, 0.85, close=False)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for t in (0.25, 0.6):
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                c.line(x + 8 * hatch_side, y + 6, x + 30 * hatch_side, y + 18, 1.0, 0.4, sketch=False)
    coast([(1180, 60), (1210, 150), (1260, 210), (1330, 250), (1450, 260)], 1)
    coast([(60, 600), (160, 640), (230, 720), (260, 830), (330, 880), (360, 1000), (300, 1120), (330, 1240)], -1)
    # waves
    for _ in range(140):
        x, y = rr.uniform(420, 1350), rr.uniform(320, 1200)
        c.path(f"M{x},{y} q10,-8 20,0 q10,8 20,0", 1.2, INK, 0.28)
    # compass rose
    cx, cy = 1180, 1030
    c.circle(cx, cy, 120, 1.6, op=0.7); c.circle(cx, cy, 92, 1.0, op=0.5)
    for a in range(0, 360, 45):
        L = 150 if a % 90 == 0 else 95
        ra = math.radians(a)
        tip = (cx + L * math.sin(ra), cy - L * math.cos(ra))
        l1 = (cx + 22 * math.sin(ra + 1.2), cy - 22 * math.cos(ra + 1.2)); l2 = (cx + 22 * math.sin(ra - 1.2), cy - 22 * math.cos(ra - 1.2))
        c.poly([l1, tip, l2], 1.8, 0.85, fill=(INK if a % 90 == 0 else None), fop=0.75)
    c.P.append(f'<text x="{cx - 14}" y="{cy - 165}" font-family="Gelasio, Georgia, serif" font-size="44" font-weight="bold" fill="{INK}">N</text>')
    # route + ports
    hk, bk = (1250, 330), (300, 930)
    c.path(f"M{hk[0]},{hk[1]} C1000,520 700,560 {bk[0]},{bk[1]}", 6, TEAL, 0.95, dash="24 16")
    c.path(f"M{hk[0]},{hk[1]} C1000,520 700,560 {bk[0]},{bk[1]}", 22, TEAL, 0.12)
    for (x, y) in (hk, bk):
        c.P.append(f'<circle cx="{x}" cy="{y}" r="24" fill="{PAPER}" stroke="{TEAL}" stroke-width="6"/><circle cx="{x}" cy="{y}" r="9" fill="{TEAL}"/>')
    # small ship on route
    sx, sy = 790, 600
    c.poly([(sx - 70, sy), (sx + 70, sy), (sx + 55, sy + 26), (sx - 60, sy + 26)], 2.2, fill=PAPER)
    for k in range(5):
        col = [TEAL, RED, GOLDW, TEAL, RED][k]
        c.P.append(f'<rect x="{sx - 58 + k * 22}" y="{sy - 20}" width="20" height="20" fill="{col}" fill-opacity="0.4"/>')
        c.poly([(sx - 58 + k * 22, sy - 20), (sx - 38 + k * 22, sy - 20), (sx - 38 + k * 22, sy), (sx - 58 + k * 22, sy)], 1.2, 0.8)
    return c.save("nautical")


# ── 2. three gates (arches) leading to the vault ─────────────────────────
def gates():
    c = Ink(2600, 900, 6)
    base = 820
    c.line(40, base, 2560, base, 2.6)
    # perspective path
    c.poly([(80, base + 0), (2200, base - 40), (2200, base + 0)], 1.2, 0.0, close=False)
    for i, x in enumerate((260, 900, 1540)):
        w, h = 430, 640
        top = base - h
        # pillars
        for px in (x, x + w - 90):
            pts = [(px, base), (px, top + 120), (px + 90, top + 120), (px + 90, base)]
            c.P.append(f'<path d="M{px},{base} V{top + 120} h90 V{base} Z" fill="{PAPER}"/>')
            c.hatch(pts, 10, 70, op=0.45)
            c.poly(pts, 2.4)
            for yy in range(top + 170, base, 70): c.line(px + 4, yy, px + 86, yy, 1.0, 0.5, sketch=False)
        # arch
        c.path(f"M{x},{top + 120} Q{x + w / 2},{top - 90} {x + w},{top + 120}", 2.8)
        c.path(f"M{x + 90},{top + 120} Q{x + w / 2},{top + 10} {x + w - 90},{top + 120}", 2.2)
        c.line(x - 30, top + 120, x + w + 30, top + 120, 2.4)
        # keystone medallion
        c.P.append(f'<circle cx="{x + w / 2}" cy="{top + 30}" r="44" fill="{PAPER}" stroke="{TEAL}" stroke-width="5"/>')
        c.path(f"M{x + w / 2 - 20},{top + 30} l14,16 l26,-30", 6, TEAL)
    # path stones through the gates
    rr = random.Random(3)
    for k in range(34):
        x = 120 + k * 62 + rr.uniform(-8, 8)
        c.path(f"M{x},{base + 30} q22,-10 44,0", 1.4, INK, 0.5)
    # vault
    vx, vy = 2380, base - 260
    c.P.append(f'<circle cx="{vx}" cy="{vy}" r="200" fill="{GOLDW}" opacity="0.35" filter="url(#glow)"/>')
    c.P.append(f'<circle cx="{vx}" cy="{vy}" r="170" fill="{PAPER}"/>')
    c.circle(vx, vy, 170, 3.2); c.circle(vx, vy, 130, 1.8, op=0.7)
    for a in range(0, 360, 30):
        ra = math.radians(a)
        c.line(vx + 130 * math.cos(ra), vy + 130 * math.sin(ra), vx + 150 * math.cos(ra), vy + 150 * math.sin(ra), 2.0, 0.8, sketch=False)
    for a in (0, 120, 240):
        ra = math.radians(a)
        c.line(vx, vy, vx + 95 * math.cos(ra), vy + 95 * math.sin(ra), 6, 0.9, GOLD, sketch=False)
    c.P.append(f'<circle cx="{vx}" cy="{vy}" r="34" fill="{GOLD}"/>')
    c.line(vx - 120, base, vx - 120, vy + 150, 2.0); c.line(vx + 120, base, vx + 120, vy + 150, 2.0)
    return c.save("gates")


# ── 3. laptop (screen area returned in fractions) ────────────────────────
def laptop():
    c = Ink(2400, 1560, 8)
    sx0, sy0, sx1, sy1 = 300, 60, 2100, 1250
    c.P.append(f'<rect x="{sx0}" y="{sy0}" width="{sx1 - sx0}" height="{sy1 - sy0}" rx="40" fill="#2A2724"/>')
    c.poly([(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)], 3.0)
    c.P.append(f'<rect x="{sx0 + 46}" y="{sy0 + 46}" width="{sx1 - sx0 - 92}" height="{sy1 - sy0 - 92}" fill="#FFFFFF"/>')
    c.P.append(f'<circle cx="{(sx0 + sx1) / 2}" cy="{sy0 + 24}" r="7" fill="#555"/>')
    base = [(120, 1300), (2280, 1300), (2380, 1450), (20, 1450)]
    c.P.append(f'<path d="M120,1300 L2280,1300 L2380,1450 L20,1450 Z" fill="{PAPER}"/>')
    c.hatch(base, 9, 20, op=0.4)
    c.poly(base, 3.0)
    c.poly([(sx0 - 60, 1250), (sx1 + 60, 1250), (2280, 1300), (120, 1300)], 2.4)
    c.poly([(1000, 1300), (1400, 1300), (1390, 1330), (1010, 1330)], 1.8)
    c.line(20, 1450, 2380, 1450, 3.0)
    c.line(60, 1500, 2340, 1500, 1.2, 0.35)
    p = c.save("laptop")
    return p, ((sx0 + 46) / 2400, (sy0 + 46) / 1560, (sx1 - sx0 - 92) / 2400, (sy1 - sy0 - 92) / 1560)


# ── 4. red seal (chop) stamp ─────────────────────────────────────────────
def seal(name, cn, en, col=RED, size=600):
    c = Ink(size, size, hash(name) % 100)
    m = 40
    c.P.append(f'<rect x="{m}" y="{m}" width="{size - 2 * m}" height="{size - 2 * m}" rx="34" fill="none" stroke="{col}" stroke-width="30"/>')
    c.P.append(f'<rect x="{m + 46}" y="{m + 46}" width="{size - 2 * m - 92}" height="{size - 2 * m - 92}" rx="18" fill="{col}"/>')
    c.P.append(f'<text x="{size / 2}" y="{size / 2 + 52}" text-anchor="middle" font-family="Noto Serif CJK TC, Noto Serif CJK HK, serif" font-weight="900" font-size="190" fill="{PAPER}">{cn}</text>')
    c.P.append(f'<text x="{size / 2}" y="{size - m - 70}" text-anchor="middle" font-family="Gelasio, Georgia, serif" font-weight="bold" font-size="54" letter-spacing="8" fill="{PAPER}">{en}</text>')
    p = c.save(name)
    im = Image.open(p).convert("RGBA")
    # distress: knock out speckles so it reads as a real ink chop
    rr = random.Random(5)
    noise = Image.effect_noise(im.size, 70).filter(ImageFilter.GaussianBlur(1.6))
    big = Image.effect_noise((im.size[0] // 6, im.size[1] // 6), 60).resize(im.size).filter(ImageFilter.GaussianBlur(3))
    mask = ImageChops.multiply(noise.point(lambda v: 0 if v > 172 else 255), big.point(lambda v: 0 if v > 168 else 255))
    a = ImageChops.multiply(im.split()[3], mask)
    im.putalpha(a.point(lambda v: int(v * 0.9)))
    im = im.rotate(rr.uniform(-6, 6), resample=Image.BICUBIC, expand=False)
    im.save(p)
    return p


# ── 5. balance scale (financing) ─────────────────────────────────────────
def scale():
    c = Ink(1800, 1200, 9)
    cx, top = 900, 180
    c.poly([(cx - 40, 1120), (cx + 40, 1120), (cx + 18, 260), (cx - 18, 260)], 2.4, fill=PAPER)
    c.hatch([(cx, 1120), (cx + 40, 1120), (cx + 18, 260), (cx, 260)], 8, 70, op=0.45)
    c.poly([(cx - 220, 1160), (cx + 220, 1160), (cx + 180, 1110), (cx - 180, 1110)], 2.6, fill=PAPER)
    c.circle(cx, top + 40, 40, 2.6)
    # beam tilted: importer side (left) heavier
    ang = math.radians(9)
    L = 560
    lx, ly = cx - L * math.cos(ang), top + 60 + L * math.sin(ang)
    rx, ry = cx + L * math.cos(ang), top + 60 - L * math.sin(ang)
    c.line(lx, ly, rx, ry, 5.0)
    for (px, py, side) in ((lx, ly, "L"), (rx, ry, "R")):
        pan_y = py + 420
        c.line(px, py, px - 190, pan_y, 1.6); c.line(px, py, px + 190, pan_y, 1.6)
        c.path(f"M{px - 220},{pan_y} Q{px},{pan_y + 120} {px + 220},{pan_y}", 2.8, fill=PAPER)
        c.line(px - 220, pan_y, px + 220, pan_y, 2.4)
        if side == "L":  # stack of coins (importer cash, teal)
            for k in range(6):
                y = pan_y - 30 - k * 34
                c.P.append(f'<ellipse cx="{px}" cy="{y}" rx="110" ry="26" fill="{TEAL}" fill-opacity="0.35" stroke="{INK}" stroke-width="2.2"/>')
        else:  # a parcel (exporter goods) + hourglass
            c.poly([(px - 120, pan_y - 10), (px + 40, pan_y - 10), (px + 40, pan_y - 150), (px - 120, pan_y - 150)], 2.4, fill=PAPER)
            c.wash([(px - 120, pan_y - 10), (px + 40, pan_y - 10), (px + 40, pan_y - 150), (px - 120, pan_y - 150)], GOLDW, 0.45)
            c.line(px - 40, pan_y - 150, px - 40, pan_y - 10, 1.6, 0.8)
            hx = px + 110
            c.poly([(hx - 45, pan_y - 160), (hx + 45, pan_y - 160), (hx, pan_y - 85)], 2.0, fill=PAPER)
            c.poly([(hx - 45, pan_y - 10), (hx + 45, pan_y - 10), (hx, pan_y - 85)], 2.0, fill=PAPER)
            c.wash([(hx - 30, pan_y - 12), (hx + 30, pan_y - 12), (hx, pan_y - 55)], GOLDW, 0.6)
    return c.save("scale")


def paper_bg(name="paper", w=1920, h=1080, sketch=None):
    paper = Image.new("RGB", (w, h), (247, 243, 235))
    noise = Image.effect_noise((w // 2, h // 2), 18).resize((w, h)).convert("RGB")
    paper = ImageChops.multiply(paper, Image.eval(noise, lambda v: 246 + (v - 128) // 14))
    vig = Image.new("L", (w, h), 0); ImageDraw.Draw(vig).ellipse((-w * 0.15, -h * 0.25, w * 1.15, h * 1.25), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    paper = Image.composite(paper, Image.new("RGB", (w, h), (232, 225, 211)), vig)
    paper.save(HERE / f"bg_{name}.png")


if __name__ == "__main__":
    paper_bg()
    print(nautical(), gates(), laptop()[1], scale())
    for nm, cn, en in (("seal_tests", "通過", "PASS"), ("seal_block", "攔截", "BLOCKED"), ("seal_zero", "零誤", "ZERO"), ("seal_caught", "捕獲", "CAUGHT")):
        print(seal(nm, cn, en))


# ── informative pieces (v2) ──────────────────────────────────────────────
def sheet(name, w=600, h=760, seed=1):
    c = Ink(w + 40, h + 40, seed)
    f = 70
    pts = [(20, 20), (20 + w - f, 20), (20 + w, 20 + f), (20 + w, 20 + h), (20, 20 + h)]
    c.P.append(f'<path d="M{" L".join(f"{x},{y}" for x, y in pts)} Z" fill="#FFFDF8"/>')
    c.poly(pts, 2.4)
    fold = [(20 + w - f, 20), (20 + w - f, 20 + f), (20 + w, 20 + f)]
    c.poly(fold, 1.8, close=False); c.hatch(fold + [(20 + w - f, 20)], 7, 45, op=0.4)
    return c.save(name)


def vault(name, open_=False):
    c = Ink(900, 760, 12)
    c.poly([(60, 40), (840, 40), (840, 700), (60, 700)], 2.8, fill=PAPER)
    c.hatch([(60, 40), (120, 40), (120, 700), (60, 700)], 9, 70, op=0.4)
    c.hatch([(780, 40), (840, 40), (840, 700), (780, 700)], 9, 70, op=0.4)
    cx, cy = 450, 370
    if open_:
        c.P.append(f'<circle cx="{cx}" cy="{cy}" r="250" fill="{GOLDW}" opacity="0.35" filter="url(#glow)"/>')
        c.P.append(f'<ellipse cx="{cx}" cy="{cy}" rx="230" ry="230" fill="#2A2724" opacity="0.85"/>')
        for k in range(5):
            c.P.append(f'<ellipse cx="{cx - 40 + k * 22}" cy="{cy + 120 - k * 34}" rx="90" ry="22" fill="{GOLDW}" fill-opacity="0.85" stroke="{INK}" stroke-width="2"/>')
        # swung door (thin ellipse on the right)
        c.P.append(f'<ellipse cx="{cx + 300}" cy="{cy}" rx="55" ry="235" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>')
        c.hatch([(cx + 250, cy - 230), (cx + 350, cy - 230), (cx + 350, cy + 230), (cx + 250, cy + 230)], 8, 80, op=0.35)
    else:
        c.P.append(f'<circle cx="{cx}" cy="{cy}" r="230" fill="{PAPER}"/>')
        c.circle(cx, cy, 230, 3.2); c.circle(cx, cy, 180, 1.8, op=0.7)
        for a in range(0, 360, 30):
            ra = math.radians(a); c.line(cx + 180 * math.cos(ra), cy + 180 * math.sin(ra), cx + 205 * math.cos(ra), cy + 205 * math.sin(ra), 2, 0.8, sketch=False)
        for a in (90, 210, 330):
            ra = math.radians(a); c.line(cx, cy, cx + 130 * math.cos(ra), cy + 130 * math.sin(ra), 8, 0.9, GOLD, sketch=False)
        c.P.append(f'<circle cx="{cx}" cy="{cy}" r="44" fill="{GOLD}"/>')
    return c.save(name)


def coins(name, n=5, col=TEAL):
    c = Ink(420, 120 + n * 46, 3)
    for k in range(n):
        y = 60 + n * 46 - k * 46
        c.P.append(f'<ellipse cx="210" cy="{y}" rx="150" ry="36" fill="{col}" fill-opacity="0.38" stroke="{INK}" stroke-width="2.6"/>')
        c.line(60, y, 60, y - 20, 2.0, sketch=False); c.line(360, y, 360, y - 20, 2.0, sketch=False)
    return c.save(name)


def ship_small(name):
    c = Ink(900, 380, 21)
    x, y, L = 60, 220, 760
    hull = [(x, y), (x + L, y), (x + L - 40, y + 90), (x + 40, y + 90)]
    c.P.append(f'<path d="M{x},{y} L{x + L},{y} L{x + L - 40},{y + 90} L{x + 40},{y + 90} Z" fill="{PAPER}"/>')
    c.hatch(hull, 8, 20, op=0.5); c.poly(hull, 2.8)
    rr = random.Random(4)
    bx = x + 50
    while bx < x + L - 190:
        for s_ in range(rr.randint(2, 3)):
            col = rr.choice([TEAL, RED, GOLDW, None])
            yy = y - (s_ + 1) * 46
            if col: c.P.append(f'<rect x="{bx}" y="{yy}" width="80" height="46" fill="{col}" fill-opacity="0.4"/>')
            c.poly([(bx, yy), (bx + 80, yy), (bx + 80, yy + 46), (bx, yy + 46)], 1.6, 0.85)
        bx += 84
    c.poly([(x + L - 170, y), (x + L - 170, y - 170), (x + L - 70, y - 170), (x + L - 70, y)], 2.2, fill=PAPER)
    for k in range(3): c.line(x + L - 160, y - 140 + k * 40, x + L - 80, y - 140 + k * 40, 1.2, 0.6, sketch=False)
    for k in range(10):
        wx = 20 + k * 85; c.path(f"M{wx},{y + 115} q20,-14 40,0 q20,14 40,0", 2, INK, 0.45)
    return c.save(name)


def dice(name):
    c = Ink(640, 380, 31)
    def die(x, y, s, rot, pips):
        r = math.radians(rot); co, si = math.cos(r), math.sin(r)
        P = lambda u, v: (x + u * co - v * si, y + u * si + v * co)
        pts = [P(0, 0), P(s, 0), P(s, s), P(0, s)]
        c.poly(pts, 2.8, fill="#FFFDF8")
        for (u, v) in pips:
            px, py = P(u * s, v * s); c.P.append(f'<circle cx="{px}" cy="{py}" r="{s * 0.075}" fill="{INK}"/>')
    die(40, 110, 190, -12, [(0.25, 0.25), (0.75, 0.75), (0.5, 0.5)])
    die(260, 60, 190, 14, [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75), (0.5, 0.5)])
    return c.save(name)


def guard_wall(name):
    """the release guard as a wall; attempts bounce off"""
    c = Ink(260, 900, 41)
    c.poly([(40, 30), (220, 30), (220, 870), (40, 870)], 3.0, fill=PAPER)
    for row, y in enumerate(range(30, 870, 60)):
        c.line(40, y, 220, y, 1.2, 0.6, sketch=False)
        off = 0 if row % 2 else 45
        for x in range(40 + off, 220, 90): c.line(x, y, x, y + 60, 1.2, 0.6, sketch=False)
    c.hatch([(160, 30), (220, 30), (220, 870), (160, 870)], 9, 65, op=0.35)
    return c.save(name)


def all_v2():
    for i in range(3): sheet(f"sheet{i}", seed=i + 1)
    sheet("sheet_wide", 900, 560, 7)
    vault("vault_open", True); vault("vault_closed", False)
    coins("coins_teal", 5, TEAL); coins("coins_gold", 5, GOLDW)
    ship_small("ship_small"); dice("dice"); guard_wall("guard_wall")
