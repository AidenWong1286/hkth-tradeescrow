"""Original pen-and-ink cover illustration: Hong Kong (left) — trade route & escrow (centre) — Bangkok (right).
Procedurally drawn (no source images). Output: presentation/v3/cover_art.png (3840x2160) + cover_art.svg.
Run: python presentation/v3/cover_art.py"""
import math, random, subprocess
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
W, H = 3840, 2160
WATER = 1480
PAPER = "#F7F3EB"
INK = "#1d1b18"
random.seed(3002)
P = []  # svg fragments
defs = []


def jit(a):
    return random.uniform(-a, a)


def hline(x0, y0, x1, y1, w=2.0, op=0.9, col=INK, wob=1.6, cls=None):
    """hand-drawn line: slight wobble + occasional double stroke"""
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 140) + 1)
    pts = []
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if 0 < i < n:
            x += jit(wob); y += jit(wob)
        pts.append((x, y))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    P.append(f'<path d="{d}" stroke="{col}" stroke-width="{w:.2f}" stroke-opacity="{op}" fill="none" stroke-linecap="round"/>')


def poly(pts, w=2.2, op=0.92, col=INK, close=True, fill=None, fop=1.0):
    if fill:
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
        P.append(f'<path d="{d}" fill="{fill}" fill-opacity="{fop}" stroke="none"/>')
    seq = pts + ([pts[0]] if close else [])
    for a, b in zip(seq, seq[1:]):
        hline(a[0], a[1], b[0], b[1], w, op, col)
        if w >= 1.8 and random.random() < 0.55:
            hline(a[0] + jit(2.5), a[1] + jit(2.5), b[0] + jit(2.5), b[1] + jit(2.5), w * 0.45, op * 0.45, col, wob=2.5)


def hatch(clip_pts, x0, y0, x1, y1, step=9, ang=55, w=1.0, op=0.55, col=INK):
    cid = f"c{len(defs)}"
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in clip_pts) + " Z"
    defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
    P.append(f'<g clip-path="url(#{cid})">')
    a = math.radians(ang)
    L = (x1 - x0) + (y1 - y0)
    k = -L
    while k < L * 2:
        sx, sy = x0 + k, y1
        ex, ey = sx + math.cos(a) * L * 2, sy - math.sin(a) * L * 2
        hline(sx, sy, ex, ey, w, op * random.uniform(0.7, 1.0), col, wob=1.2)
        k += step * random.uniform(0.85, 1.15)
    P.append("</g>")


def wash(pts, col, op=0.35, blur=6):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    P.append(f'<path d="{d}" fill="{col}" fill-opacity="{op}" filter="url(#soft{blur})"/>')


def rect_pts(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def windows(x, y, w, h, cw=14, rh=18, op=0.42, vert=True, horiz=True):
    if vert:
        xx = x + cw
        while xx < x + w - 3:
            hline(xx, y + 4, xx, y + h - 2, 0.8, op, wob=0.6); xx += cw
    if horiz:
        yy = y + rh
        while yy < y + h - 3:
            hline(x + 2, yy, x + w - 2, yy, 0.8, op, wob=0.6); yy += rh


def tower(x, top, w, base=WATER, cw=14, rh=18, shade=True, crown=None):
    h = base - top
    P.append(f'<path d="M{x},{top} h{w} v{h} h{-w} Z" fill="{PAPER}" stroke="none"/>')
    windows(x, top, w, h, cw, rh)
    if shade:
        sw = w * random.uniform(0.28, 0.4)
        hatch(rect_pts(x + w - sw, top, sw, h), x + w - sw, top, x + w, base, step=8, ang=62, op=0.5)
    poly(rect_pts(x, top, w, h), 2.3)
    if crown == "mast":
        hline(x + w / 2, top, x + w / 2, top - 70, 2.0)
    elif crown == "stepped":
        poly([(x + w * 0.15, top), (x + w * 0.15, top - 30), (x + w * 0.85, top - 30), (x + w * 0.85, top)], 2.0, close=False)
        hline(x + w / 2, top - 30, x + w / 2, top - 85, 1.8)
    elif crown == "pyramid":
        poly([(x, top), (x + w / 2, top - w * 0.55), (x + w, top)], 2.1, close=False)
        hline(x + w / 2, top - w * 0.55, x + w / 2, top - w * 0.55 - 80, 1.8)


def boc_tower(cx, base=WATER, top=300, w=240):
    """triangular-braced tower (Bank-of-China-style massing), drawn with X bracing"""
    x0, x1 = cx - w / 2, cx + w / 2
    tiers = [(base, x0, x1), (base - (base - top) * 0.42, x0, x1), (base - (base - top) * 0.68, cx - w * 0.5, cx + w * 0.25),
             (base - (base - top) * 0.86, cx - w * 0.5, cx), (top, cx - w * 0.5, cx - w * 0.1)]
    P.append(f'<path d="M{x0},{base} L{x0},{top} L{cx - w * 0.1},{top} L{cx},{tiers[3][0]} L{cx + w * 0.25},{tiers[2][0]} L{x1},{tiers[1][0]} L{x1},{base} Z" fill="{PAPER}"/>')
    cid = f"c{len(defs)}"
    defs.append(f'<clipPath id="{cid}"><path d="M{x0},{base} L{x0},{top} L{cx - w * 0.1},{top} L{cx},{tiers[3][0]} L{cx + w * 0.25},{tiers[2][0]} L{x1},{tiers[1][0]} L{x1},{base} Z"/></clipPath>')
    P.append(f'<g clip-path="url(#{cid})">'); windows(x0, top, w, base - top, 10, 12, op=0.32); P.append('</g>')
    # facade glass hatch on the right faces
    hatch([(cx, tiers[3][0]), (cx + w * 0.25, tiers[2][0]), (x1, tiers[1][0]), (x1, base), (cx, base)], cx, top, x1, base, step=7, ang=70, op=0.45)
    outline = [(x0, base), (x0, top), (cx - w * 0.1, top), (cx, tiers[3][0]), (cx + w * 0.25, tiers[2][0]), (x1, tiers[1][0]), (x1, base)]
    poly(outline, 2.6, close=False)
    # X bracing in stacked squares
    seg = (base - top) / 5.0
    for i in range(5):
        y_b, y_t = base - i * seg, base - (i + 1) * seg
        left, right = x0, (x1 if y_t >= tiers[1][0] else (cx + w * 0.25 if y_t >= tiers[2][0] else (cx if y_t >= tiers[3][0] else cx - w * 0.1)))
        hline(left, y_b, right, y_t, 3.2, 0.95); hline(left, y_t, right, y_b, 3.2, 0.95)
        hline(left, y_t, right, y_t, 2.6, 0.95)
    hline(cx - w * 0.42, top, cx - w * 0.42, top - 150, 2.4); hline(cx - w * 0.22, top, cx - w * 0.22, top - 120, 2.4)


def ifc_tower(cx, top, w, base=WATER):
    x0 = cx - w / 2
    P.append(f'<path d="M{x0},{base} L{x0},{top + 160} Q{cx},{top + 40} {x0 + w},{top + 160} L{x0 + w},{base} Z" fill="{PAPER}"/>')
    windows(x0, top + 160, w, base - top - 160, 9, 22, op=0.34)
    hatch(rect_pts(x0 + w * 0.62, top + 120, w * 0.38, base - top), x0 + w * 0.6, top, x0 + w, base, 7, 65, op=0.45)
    poly([(x0, base), (x0, top + 160)], 2.4, close=False); poly([(x0 + w, top + 160), (x0 + w, base)], 2.4, close=False)
    for k in range(6):  # crown fins
        fx = x0 + w * (0.12 + k * 0.152)
        hline(fx, top + 175, fx + jit(4), top + 30 + abs(k - 2.5) * 22, 1.8)
    P.append(f'<path d="M{x0},{top + 160} Q{cx},{top + 40} {x0 + w},{top + 160}" stroke="{INK}" stroke-width="2.4" fill="none"/>')


def mountain(x0, x1, base, peak, seed, op=0.85):
    rnd = random.Random(seed)
    pts = []
    n = 60
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = base - (base - peak) * (math.sin(math.pi * t) ** 1.3) * (0.85 + 0.15 * math.sin(t * 13 + seed)) + rnd.uniform(-6, 6)
        pts.append((x, y))
    pass
    for a, b in zip(pts, pts[1:]):
        hline(a[0], a[1], b[0], b[1], 2.2, op)
    # contour strokes
    for _ in range(900):
        i = rnd.randrange(1, n)
        x = pts[i][0] + rnd.uniform(-20, 20)
        y = pts[i][1] + rnd.uniform(15, (base - pts[i][1]) * 0.9 + 20)
        L = rnd.uniform(14, 34)
        hline(x, y, x + L * 0.8, y + L * 0.45, 1.0, 0.35 * op, wob=0.8)


def prang(cx, base, h, w, gold=True):
    """Wat-Arun-style prang: stepped terraces + corncob tower + trident finial"""
    terr = 4
    th = h * 0.32 / terr
    y = base
    for i in range(terr):
        ww = w * (1 - i * 0.16)
        x = cx - ww / 2
        P.append(f'<path d="M{x},{y - th} h{ww} v{th} h{-ww} Z" fill="{PAPER}"/>')
        poly(rect_pts(x, y - th, ww, th), 2.1)
        # balustrade ticks
        k = x + 10
        while k < x + ww - 6:
            hline(k, y - th + 6, k, y - 6, 0.9, 0.5); k += 13
        # stairs
        hline(cx - 18, y, cx - 10, y - th, 1.6); hline(cx + 18, y, cx + 10, y - th, 1.6)
        y -= th
    # tower body: stacked bulging segments
    body_h = h * 0.6
    segs = 9
    bw = w * 0.42
    pts_l, pts_r = [], []
    for i in range(segs + 1):
        t = i / segs
        wd = bw * (1 - t ** 1.6) * (1 + 0.08 * math.sin(t * math.pi))
        yy = y - body_h * t
        pts_l.append((cx - wd / 2, yy)); pts_r.append((cx + wd / 2, yy))
    outline = pts_l + pts_r[::-1]
    if gold:
        wash(outline, "#E2A84B", 0.42, 10)
    for i in range(segs):
        (lx, ly), (rx, ry) = pts_l[i], pts_r[i]
        (lx2, ly2), (rx2, ry2) = pts_l[i + 1], pts_r[i + 1]
        P.append(f'<path d="M{lx},{ly} Q{lx - 10},{(ly + ly2) / 2} {lx2},{ly2}" stroke="{INK}" stroke-width="2.2" fill="none"/>')
        P.append(f'<path d="M{rx},{ry} Q{rx + 10},{(ry + ry2) / 2} {rx2},{ry2}" stroke="{INK}" stroke-width="2.2" fill="none"/>')
        hline(lx, ly, rx, ry, 1.6, 0.8)
        # ornament: little arcs + dots on each band
        n = max(3, int((rx - lx) / 16))
        for k in range(n):
            ox = lx + (rx - lx) * (k + 0.5) / n
            P.append(f'<path d="M{ox - 5},{ly - 4} q5,-9 10,0" stroke="{INK}" stroke-width="1" stroke-opacity="0.6" fill="none"/>')
    # niche with figure
    hline(cx - 14, y - 6, cx - 14, y - 70, 1.6); hline(cx + 14, y - 6, cx + 14, y - 70, 1.6)
    P.append(f'<path d="M{cx - 14},{y - 70} Q{cx},{y - 98} {cx + 14},{y - 70}" stroke="{INK}" stroke-width="1.6" fill="none"/>')
    ty = y - body_h
    hline(cx, ty, cx, ty - h * 0.12, 2.0)
    for dx in (-10, 0, 10):
        hline(cx + dx, ty - h * 0.08, cx + dx * 0.4, ty - h * 0.16, 1.3)


def thai_roof(x, base, w, h, layers=3, gold=True):
    # walls + pillars
    wall_top = base - h * 0.4
    P.append(f'<path d="M{x},{wall_top} h{w} v{h * 0.4} h{-w} Z" fill="{PAPER}"/>')
    poly(rect_pts(x, wall_top, w, h * 0.4), 2.0)
    k = x + w / 7
    while k < x + w - 5:
        hline(k, wall_top + 4, k, base - 2, 1.6, 0.8); k += w / 7
    hatch(rect_pts(x, wall_top, w, h * 0.12), x, wall_top, x + w, wall_top + h * 0.12, 6, 30, op=0.45)
    cx = x + w / 2
    for i in range(layers):
        ww = w * (1.12 - i * 0.2)
        rb = wall_top - i * h * 0.13
        rt = rb - h * 0.36
        pts = [(cx - ww / 2, rb), (cx, rt), (cx + ww / 2, rb)]
        if gold:
            wash(pts, "#C8553D" if i % 2 == 0 else "#E2A84B", 0.32, 6)
        P.append(f'<path d="M{pts[0][0]},{pts[0][1]} L{pts[1][0]},{pts[1][1]} L{pts[2][0]},{pts[2][1]}" fill="{PAPER}" fill-opacity="0.0"/>')
        poly(pts, 2.2, close=False)
        # tiles
        for t in (0.25, 0.5, 0.75):
            hline(cx - ww / 2 * (1 - t) - 0, rb - (rb - rt) * t, cx + ww / 2 * (1 - t), rb - (rb - rt) * t, 0.9, 0.45)
        # chofa hook at apex + nagas at eaves
        P.append(f'<path d="M{cx},{rt} q6,-28 22,-34 q-12,2 -14,14" stroke="{INK}" stroke-width="2" fill="none"/>')
        for sx in (-1, 1):
            ex = cx + sx * ww / 2
            P.append(f'<path d="M{ex},{rb} q{sx * 16},-4 {sx * 20},-26" stroke="{INK}" stroke-width="1.8" fill="none"/>')


def palm(x, base, h, lean=1):
    tx, ty = x + lean * h * 0.18, base - h
    P.append(f'<path d="M{x},{base} Q{x + lean * h * 0.05},{base - h * 0.55} {tx},{ty}" stroke="{INK}" stroke-width="3" fill="none"/>')
    for k in range(10):
        yy = base - h * (k / 10)
        hline(x + lean * h * 0.18 * (k / 10) ** 2 - 5, yy, x + lean * h * 0.18 * (k / 10) ** 2 + 5, yy - 3, 1.0, 0.6)
    for ang in (-160, -130, -100, -70, -40, -15, 15, 200):
        a = math.radians(ang)
        L = h * random.uniform(0.32, 0.42)
        ex, ey = tx + math.cos(a) * L, ty + math.sin(a) * L * 0.55 + L * 0.35
        mx, my = tx + math.cos(a) * L * 0.5, ty - L * 0.18
        P.append(f'<path d="M{tx},{ty} Q{mx},{my} {ex},{ey}" stroke="{INK}" stroke-width="2" fill="none"/>')
        for f in range(1, 7):
            t = f / 7
            px = (1 - t) ** 2 * tx + 2 * (1 - t) * t * mx + t * t * ex
            py = (1 - t) ** 2 * ty + 2 * (1 - t) * t * my + t * t * ey
            hline(px, py, px + 7, py + 14, 0.9, 0.6)
            hline(px, py, px - 7, py + 14, 0.9, 0.6)


def ship(x, y, L):
    hull = [(x, y), (x + L, y), (x + L * 0.96, y + 46), (x + L * 0.06, y + 46)]
    P.append(f'<path d="M{x},{y} L{x + L},{y} L{x + L * 0.96},{y + 46} L{x + L * 0.06},{y + 46} Z" fill="{PAPER}"/>')
    hatch(hull, x, y, x + L, y + 46, 6, 20, op=0.55)
    poly(hull, 2.3)
    # containers
    cols = ["#1F8A82", None, "#C8553D", None, "#E2A84B", None, "#1F8A82", None]
    bx = x + L * 0.08
    rnd = random.Random(7)
    while bx < x + L * 0.78:
        stack = rnd.randint(2, 4)
        for s in range(stack):
            c = rnd.choice(cols)
            yy = y - (s + 1) * 24
            if c:
                P.append(f'<rect x="{bx}" y="{yy}" width="44" height="24" fill="{c}" fill-opacity="0.38"/>')
            poly(rect_pts(bx, yy, 44, 24), 1.3, op=0.85)
            for k in (11, 22, 33):
                hline(bx + k, yy + 3, bx + k, yy + 21, 0.7, 0.5)
        bx += 46
    # bridge
    poly(rect_pts(x + L * 0.82, y - 92, 60, 92), 1.8)
    windows(x + L * 0.82, y - 92, 60, 92, 12, 15, 0.5)
    hline(x + L * 0.82 + 30, y - 92, x + L * 0.82 + 30, y - 130, 1.6)
    # wake
    for k in range(14):
        wx = x - 30 - k * 38
        hline(wx, y + 50 + k * 1.5, wx - 28, y + 52 + k * 1.5, 1.1, 0.5 - k * 0.03)


def longtail(x, y, L):
    P.append(f'<path d="M{x},{y} Q{x + L * 0.5},{y + 26} {x + L},{y - 18}" stroke="{INK}" stroke-width="2.4" fill="none"/>')
    P.append(f'<path d="M{x},{y} L{x + L * 0.9},{y - 6}" stroke="{INK}" stroke-width="1.6" fill="none"/>')
    P.append(f'<path d="M{x - 6},{y - 14} L{x + 30},{y + 14}" stroke="{INK}" stroke-width="1.8" fill="none"/>')
    hline(x + L * 0.6, y - 4, x + L * 0.62, y - 30, 1.6)
    P.append(f'<circle cx="{x + L * 0.61}" cy="{y - 36}" r="7" fill="none" stroke="{INK}" stroke-width="1.6"/>')


def water():
    rnd = random.Random(11)
    for i in range(1500):
        y = WATER + 10 + (rnd.random() ** 2.4) * (H - WATER - 10)
        x = rnd.uniform(-50, W + 50)
        L = 12 + (y - WATER) * 0.06 * rnd.uniform(0.5, 1.4)
        op = 0.45 * (1 - (y - WATER) / (H - WATER)) ** 1.5
        hline(x, y, x + L, y + rnd.uniform(-1, 1), 1.0, op, wob=0.6)


# ── compose ──────────────────────────────────────────────────────────────
defs.append('<filter id="soft6" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>')
defs.append('<filter id="soft10" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="10"/></filter>')
defs.append('<filter id="sky" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="140"/></filter>')
defs.append('<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="22"/></filter>')
defs.append('<radialGradient id="sun"><stop offset="0" stop-color="#F2C46B" stop-opacity="0.75"/><stop offset="0.6" stop-color="#EBAF59" stop-opacity="0.35"/><stop offset="1" stop-color="#EBAF59" stop-opacity="0"/></radialGradient>')

# sky washes: cool Hong Kong teal (left) → warm Thai dawn (right)
P.append('<ellipse cx="700" cy="620" rx="1150" ry="620" fill="#7CC4BB" opacity="0.16" filter="url(#sky)"/>')
P.append('<ellipse cx="3150" cy="820" rx="1000" ry="640" fill="#F0B866" opacity="0.20" filter="url(#sky)"/>')
P.append('<circle cx="3170" cy="860" r="420" fill="url(#sun)"/>')
# birds
for bx, by, sc in [(1880, 420, 1.0), (1960, 470, 0.8), (2050, 400, 0.9), (2140, 455, 0.7), (2600, 360, 0.8)]:
    P.append(f'<path d="M{bx},{by} q{14*sc},{-12*sc} {26*sc},0 q{12*sc},{-12*sc} {26*sc},0" stroke="{INK}" stroke-width="2" fill="none" opacity="0.7"/>')

# ---- Hong Kong (left)
mountain(-160, 1700, 1250, 560, 1, 0.8)
mountain(650, 1950, 1320, 930, 5, 0.55)
random.seed(21)
P.append('<g opacity="0.42">')  # back layer
for x, top, w in [(40, 980, 80), (260, 900, 70), (400, 1010, 60), (900, 950, 60), (1010, 880, 70), (1120, 990, 60), (1500, 1100, 70), (1580, 1180, 60)]:
    tower(x, top, w, cw=10, rh=14, shade=False)
P.append('</g>')
xs = [(-20, 860, 120, "mast"), (95, 1060, 95, None), (185, 720, 135, "stepped"), (330, 960, 110, None),
      (450, 610, 120, "pyramid"), (845, 820, 120, None), (965, 1000, 90, "mast"), (1060, 880, 105, "stepped"),
      (1365, 1080, 90, None), (1455, 1170, 80, None)]
for x, top, w, cr in xs:
    tower(x, top, w, cw=random.choice([12, 14, 16]), rh=random.choice([14, 18, 22]), crown=cr)
boc_tower(700, base=WATER, top=300, w=230)
wash([(585, WATER), (585, 300), (700, 300), (815, 620), (815, WATER)], "#5FB3AA", 0.22, 10)
ifc_tower(1250, 260, 150)
wash([(1175, WATER), (1175, 420), (1325, 420), (1325, WATER)], "#7DA7C9", 0.18, 10)
tower(560, 1120, 100, cw=12, rh=16)
tower(1150, 1150, 70, cw=10, rh=14)
for x in range(-20, 1500, 70):
    hh = random.randint(60, 140)
    tower(x, WATER - hh, 66, cw=11, rh=13, shade=random.random() < 0.5)

# container cranes (trade) on the HK waterfront
def crane(x, base, h, col):
    legs = [(x, base), (x + 18, base - h), (x + 90, base - h), (x + 108, base)]
    for a, b in zip(legs, legs[1:]):
        hline(a[0], a[1], b[0], b[1], 2.4)
    for k in range(4):
        y1 = base - h * k / 4; y2 = base - h * (k + 1) / 4
        hline(x + 18 * k / 4, y1, x + 108 - 18 * (k + 1) / 4, y2, 1.1, 0.6)
    hline(x - 160, base - h - 4, x + 220, base - h - 4, 3.0)
    hline(x - 160, base - h - 28, x + 220, base - h - 28, 1.6)
    for k in range(0, 380, 26):
        hline(x - 160 + k, base - h - 4, x - 160 + k + 13, base - h - 28, 1.0, 0.7)
    hline(x + 40, base - h - 28, x + 54, base - h - 120, 2.2); hline(x + 54, base - h - 120, x - 150, base - h - 28, 1.2, 0.8)
    hline(x + 54, base - h - 120, x + 210, base - h - 28, 1.2, 0.8)
    P.append(f'<rect x="{x + 10}" y="{base - h - 4}" width="88" height="22" fill="{col}" fill-opacity="0.45"/>')
    hline(x - 120, base - h - 4, x - 120, base - h + 160, 0.9, 0.7)
crane(1560, WATER - 6, 300, "#C8553D")
crane(1790, WATER - 6, 250, "#1F8A82")
hline(-20, WATER, 2000, WATER, 2.6)
# stacked containers on the quay
qx = 1550
rq = random.Random(5)
for k in range(9):
    for s_ in range(rq.randint(1, 3)):
        c = rq.choice(["#1F8A82", "#C8553D", "#E2A84B", None, None])
        yy = WATER - 6 - (s_ + 1) * 22
        if c: P.append(f'<rect x="{qx + k * 42}" y="{yy}" width="40" height="22" fill="{c}" fill-opacity="0.4"/>')
        poly(rect_pts(qx + k * 42, yy, 40, 22), 1.2, 0.8)

# ---- Thailand (right)
random.seed(33)
P.append('<g opacity="0.4">')
for x, top, w in [(2380, 1040, 60), (2470, 980, 70), (2560, 930, 60), (2640, 1060, 80), (3560, 960, 70), (3650, 1020, 90), (3760, 940, 70)]:
    tower(x, top, w, cw=12, rh=16, shade=False)
P.append('</g>')
def chedi(cx, base, h, w):
    bell = [(cx - w / 2, base), (cx - w * 0.42, base - h * 0.35), (cx - w * 0.18, base - h * 0.55), (cx, base - h), (cx + w * 0.18, base - h * 0.55), (cx + w * 0.42, base - h * 0.35), (cx + w / 2, base)]
    wash(bell, "#E2A84B", 0.35, 6)
    d = f"M{bell[0][0]},{bell[0][1]} C{cx - w * 0.5},{base - h * 0.45} {cx - w * 0.2},{base - h * 0.5} {cx - w * 0.06},{base - h * 0.62} L{cx},{base - h} L{cx + w * 0.06},{base - h * 0.62} C{cx + w * 0.2},{base - h * 0.5} {cx + w * 0.5},{base - h * 0.45} {cx + w / 2},{base}"
    P.append(f'<path d="{d}" stroke="{INK}" stroke-width="2.2" fill="none"/>')
    for t in (0.66, 0.72, 0.78, 0.84):
        ww = w * 0.12 * (1 - (t - 0.62) * 2)
        hline(cx - ww, base - h * t, cx + ww, base - h * t, 1.2, 0.8)
chedi(2580, WATER - 70, 380, 200)
chedi(3790, WATER - 70, 330, 170)
prang(3170, WATER - 70, 1020, 560)
prang(2840, WATER - 70, 580, 300)
prang(3500, WATER - 70, 580, 300)
P.append(f'<path d="M2460,{WATER - 70} h1400 v70 h-1400 Z" fill="{PAPER}"/>')
poly(rect_pts(2460, WATER - 70, 1400, 70), 2.2, close=False)
k = 2470
while k < 3840:
    hline(k, WATER - 64, k, WATER - 6, 1.0, 0.5); k += 18
thai_roof(2250, WATER, 300, 430)
thai_roof(3610, WATER, 250, 370)
palm(2190, WATER, 360, -1); palm(2660, WATER - 70, 280, 1); palm(3700, WATER - 70, 300, -1); palm(3830, WATER, 380, -1)
hline(2120, WATER, 3860, WATER, 2.6)
longtail(2980, WATER + 110, 260)
longtail(3500, WATER + 190, 200)

# reflections under both shores
rr = random.Random(9)
for x0, x1, op in ((-20, 2000, 0.55), (2120, 3860, 0.5)):
    for _ in range(260):
        x = rr.uniform(x0, x1); y = WATER + 10 + rr.random() ** 2.2 * 200
        L = rr.uniform(16, 46)
        hline(x, y, x + L, y + rr.uniform(-1, 1), 1.1, op * (1 - (y - WATER) / 220))
P.append(f'<ellipse cx="900" cy="{WATER + 60}" rx="1100" ry="120" fill="#7CC4BB" opacity="0.13" filter="url(#sky)"/>')
P.append(f'<ellipse cx="3000" cy="{WATER + 60}" rx="1000" ry="120" fill="#F0B866" opacity="0.15" filter="url(#sky)"/>')

# ---- water + ship
water()
ship(2080, WATER + 120, 560)

# ---- the trade route & escrow (colour)
hk, th, ap = (1250, 1180), (2830, 1250), (2040, 760)
P.append(f'<path d="M{hk[0]},{hk[1]} Q{ap[0]},{ap[1] - 330} {th[0]},{th[1]}" stroke="#1F8A82" stroke-width="7" fill="none" stroke-dasharray="26 18" stroke-linecap="round"/>')
P.append(f'<path d="M{hk[0]},{hk[1]} Q{ap[0]},{ap[1] - 330} {th[0]},{th[1]}" stroke="#1F8A82" stroke-width="22" fill="none" opacity="0.12" filter="url(#soft10)"/>')
for (x, y) in (hk, th):
    P.append(f'<circle cx="{x}" cy="{y}" r="20" fill="{PAPER}" stroke="#1F8A82" stroke-width="6"/>')
    P.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#1F8A82"/>')
# three gate ticks along the arc
def qb(t):
    x = (1 - t) ** 2 * hk[0] + 2 * (1 - t) * t * ap[0] + t * t * th[0]
    y = (1 - t) ** 2 * hk[1] + 2 * (1 - t) * t * (ap[1] - 330) + t * t * th[1]
    return x, y
for t in (0.62, 0.74, 0.86):
    x, y = qb(t)
    P.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="{PAPER}" stroke="#1F8A82" stroke-width="4"/>')
    P.append(f'<path d="M{x - 7:.1f},{y:.1f} l5,6 l10,-12" stroke="#1F8A82" stroke-width="4" fill="none" stroke-linecap="round"/>')
# escrow lock at apex
lx, ly = qb(0.5)
P.append(f'<circle cx="{lx}" cy="{ly}" r="95" fill="#E2A84B" opacity="0.35" filter="url(#glow)"/>')
P.append(f'<circle cx="{lx}" cy="{ly}" r="58" fill="{PAPER}" stroke="#C9922F" stroke-width="5"/>')
P.append(f'<rect x="{lx - 24}" y="{ly - 6}" width="48" height="38" rx="6" fill="#C9922F"/>')
P.append(f'<path d="M{lx - 15},{ly - 6} v-12 a15,15 0 0 1 30,0 v12" stroke="#C9922F" stroke-width="7" fill="none"/>')
P.append(f'<circle cx="{lx}" cy="{ly + 11}" r="5" fill="{PAPER}"/>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       f'<defs>{"".join(defs)}</defs>{"".join(P)}</svg>')
(HERE / "cover_art.svg").write_text(svg)
subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(HERE / "_ink.png"), str(HERE / "cover_art.svg")], check=True)

# paper: warm cream with fibre noise and soft vignette
paper = Image.new("RGB", (W, H), (247, 243, 235))
noise = Image.effect_noise((W // 2, H // 2), 18).resize((W, H)).convert("RGB")
paper = ImageChops.multiply(paper, Image.eval(noise, lambda v: 246 + (v - 128) // 14))
vig = Image.new("L", (W, H), 0); d = ImageDraw.Draw(vig)
d.ellipse((-W * 0.15, -H * 0.25, W * 1.15, H * 1.25), fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(260))
dark = Image.new("RGB", (W, H), (228, 220, 205))
paper = Image.composite(paper, dark, vig)
ink = Image.open(HERE / "_ink.png").convert("RGBA")
paper.paste(ink, (0, 0), ink)
paper.save(HERE / "cover_art.png")
(HERE / "_ink.png").unlink()
print("wrote", HERE / "cover_art.png")
