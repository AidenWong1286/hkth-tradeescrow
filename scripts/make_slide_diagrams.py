"""Slide-readable (16:9) versions of the four diagrams. Same content as make_diagrams.py,
re-laid-out with larger text: BPMN maps wrap into two tiers joined by connector 'A'."""
import subprocess, sys, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tradeescrow import process_model as pm

OUT = ROOT / "diagrams" / "slide"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 13.333, 7.5
KC = {"MANUAL": "#fde2c4", "AUTO": "#cdeee9", "EXTERNAL_MANUAL": "#e5e7eb", "WAIT": "#fff1a8"}
KE = {"MANUAL": "#c2410c", "AUTO": "#0f766e", "EXTERNAL_MANUAL": "#4b5563", "WAIT": "#a16207"}
INK = "#14213d"
SMALL, TASK = 0.66, 1.52     # column widths (in)

# tier layouts: list of (node, lane, kind 's'/'t'); exceptions = {node: (lane, column_of)}
LAYOUT = {
    "baseline": {
        "title": "Baseline: traditional open-account settlement (payment after shipment)",
        "tiers": [
            {"label": "① Contract → shipment → documents checked   (continues at Ⓐ)", "cols": ["start", "B01", "B02", "B03", "B04", "B05", "B06", "G1", "A_out"],
             "exc": {"B06x": "B06"}},
            {"label": "② (from Ⓐ) Payment term → bank processing → exporter credited", "cols": ["A_in", "B07", "B08", "B09", "G2", "B10", "B11", "B12", "end"],
             "exc": {"B09x": "B10"}},
        ]},
    "proposed": {
        "title": "Proposed: pre-funded tokenised-deposit escrow with off-chain attestations",
        "tiers": [
            {"label": "① Contract → escrow funded → goods shipped   (continues at Ⓐ)", "cols": ["start", "E01", "E02", "G0", "E03", "E04", "E05", "E06", "A_out"],
             "exc": {"end_rej": "G0"}},
            {"label": "② (from Ⓐ) Attestations → guarded release → audit", "cols": ["A_in", "E07", "E08", "G1", "E09", "G2", "E10", "E11", "E12", "end"],
             "exc": {"E08x": "E09", "E09x": "E10", "end_ref": "E11"}},
        ]},
}


def wrap(s, n):
    return textwrap.wrap(s, n, break_long_words=False, break_on_hyphens=False) or [s]


def bpmn(model):
    lanes, tasks = pm.MODELS[model]
    T = {t.id: t for t in tasks}
    G = pm.GATEWAYS[model]
    E = pm.EVENTS[model]
    lay = LAYOUT[model]
    fig = plt.figure(figsize=(W, H), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    ax.text(0.2, 0.36, lay["title"], fontsize=17, weight="bold", color=INK, va="center")
    LBL = 1.3                       # lane-label strip width
    top0, gap, legend_h = 0.7, 0.32, 0.42
    tier_h = (H - top0 - legend_h - gap) / 2
    pos = {}
    for ti, tier in enumerate(lay["tiers"]):
        ty = top0 + ti * (tier_h + gap)
        exc_lanes = {T[n].lane if n in T else E[n][0] for n in tier["exc"]}
        used = set()
        for c in list(tier["cols"]) + list(tier["exc"]):
            if c in T: used.add(T[c].lane)
            elif c in G: used.add(G[c][0])
            elif c in E: used.add(E[c][0])
        used |= {T["B07"].lane if model == "baseline" else T["E07"].lane} if ti == 1 else set()
        units = [2.4 if l in exc_lanes else (1 if l in used else 0.72) for l in lanes]
        u = (tier_h - 0.28) / sum(units)
        ax.text(LBL + 0.05, ty + 0.12, tier["label"], fontsize=12.5, weight="bold", color="#0b3c49", va="center")
        y = ty + 0.28
        lane_y = {}
        for li, l in enumerate(lanes):
            h = units[li] * u
            ax.add_patch(Rectangle((0.15, y), W - 0.3, h, fc="#f8fafc" if li % 2 else "#ffffff", ec="#94a3b8", lw=1))
            ax.add_patch(Rectangle((0.15, y), LBL - 0.15, h, fc="#1d3557", ec="#1d3557"))
            thin = h < 0.7 * u
            ax.text(0.15 + (LBL - 0.15) / 2, y + h / 2, l.replace(" (", "\n(").replace(" contract & services", "\ncontract & services").replace(" / ", " /\n").replace(" contract & services", "\ncontract & services").replace(" / ", " /\n"), ha="center", va="center", color="white",
                    fontsize=7.8 if thin else 9, weight="bold", linespacing=0.95)
            lane_y[l] = (y, u, h)
            y += h
        x = LBL + 0.15
        for c in tier["cols"]:
            w = SMALL if (c in G or c in E or c.startswith("A_")) else TASK
            cx = x + w / 2
            if c in T: ln = T[c].lane
            elif c in G: ln = G[c][0]
            elif c in E: ln = E[c][0]
            else:  # connector sits in the lane of its neighbour flow
                ln = G["G1"][0] if (model == "baseline" and c == "A_out") else \
                     T["B07"].lane if c == "A_in" and model == "baseline" else \
                     T["E06"].lane if c == "A_out" else T["E07"].lane
            ly, lu, lh = lane_y[ln]
            pos[(ti, c)] = (cx, ly + (lu * 0.62 if lh > 1.5 * lu else lh / 2), lu)
            x += w
        for n, under in tier["exc"].items():
            cx, _, lu = pos[(ti, under)]
            ln = T[n].lane if n in T else E[n][0]
            ly, lu2, _ = lane_y[ln]
            pos[(ti, n)] = (cx, ly + lu2 * 1.84, lu2)
    # map node -> (tier, x, y, unit)
    where = {}
    for (ti, n), v in pos.items():
        where[(n if not n.startswith("A_") else f"{n}{ti}")] = (ti,) + v
    def box(n):
        ti, cx, cy, lu = where[n]
        if n in T: return cx, cy, TASK - 0.2, lu * (0.86 if T[n].path != "MAIN" else 0.8)
        if n in G: return cx, cy, 0.44, 0.44
        return cx, cy, 0.34, 0.34
    # edges
    def edge(a, b, label=None):
        ta, ax_, ay, _ = where[a]; tb, bx, by, _ = where[b]
        _, _, aw, ah = box(a); _, _, bw, bh = box(b)
        exc = label and any(k in label for k in ("FAIL", "ALERT", "discrepancy", "alert", "terminate"))
        col = "#b91c1c" if exc else "#334155"
        ls = (0, (4, 2)) if exc else "-"
        if abs(ax_ - bx) < 0.01:               # vertical (same column)
            sy = ay + (ah / 2 if by > ay else -ah / 2); ey = by - (bh / 2 if by > ay else -bh / 2)
            pts = [(ax_, sy), (bx, ey)]; lp = (ax_ + 0.06, (sy + ey) / 2)
        elif bx > ax_:
            sx, ex = ax_ + aw / 2, bx - bw / 2
            if abs(ay - by) < 0.01:
                pts = [(sx, ay), (ex, by)]; lp = ((sx + ex) / 2, ay - 0.07)
            elif by > ay and exc:               # drop down then right
                pts = [(ax_, ay + ah / 2), (ax_, by), (ex, by)]; lp = (ax_ + 0.05, (ay + by) / 2 + 0.05)
            else:
                mx = ex - 0.12
                pts = [(sx, ay), (mx, ay), (mx, by), (ex, by)]; lp = (sx + 0.03, ay - 0.06)
        elif ay > by:                           # loop back up-left into the target's right side
            xg = bx + bw / 2 + 0.13
            pts = [(ax_ - aw / 2, ay), (xg, ay), (xg, by + bh * 0.22), (bx + bw / 2, by + bh * 0.22)]
            lp = (ax_, ay + ah / 2 + 0.2)
        else:                                   # loop back left, routed below
            yy = max(ay + ah / 2, by + bh / 2) + 0.08
            pts = [(ax_, ay + ah / 2), (ax_, yy), (bx + 0.25, yy), (bx + 0.25, by + bh / 2)]
            lp = ((ax_ + bx) / 2, yy + 0.13)
        xs, ys = zip(*pts)
        ax.plot(xs[:-1], ys[:-1], color=col, lw=1.4, ls=ls, solid_capstyle="round")
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4, ls=ls, mutation_scale=14))
        if label:
            horiz = abs(ay - by) < 0.01
            txt = "\n".join(wrap(label, 13 if horiz else 13))
            va = "bottom"
            if not horiz and exc and bx > ax_:   # drop-down exception: narrow label above the lower leg
                lp = (ax_ + 0.04, by - 0.04); txt = "\n".join(wrap(label, 8))
            if abs(ax_ - bx) < 0.01:             # vertical edge: label beside the midpoint
                lp = (ax_ + 0.06, (ay + by) / 2); va = "center"
            if not horiz and ay > by and bx < ax_:
                txt = label
            if horiz and a in G:      # gateway branch label: one line, above-right of the diamond
                txt, lp = label, (ax_ + 0.24, ay - 0.17)
            ax.text(lp[0], lp[1], txt, fontsize=8.5, color=col, linespacing=0.95, style="italic", ha="left" if (horiz and a in G) or (not horiz and bx >= ax_) else "center", va=va,
                    bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    tier_of = {n: ti for (ti, n) in pos}
    for f in pm.FLOWS[model]:
        a, b = f[0], f[1]
        lab = f[2] if len(f) > 2 else None
        if tier_of.get(a) != tier_of.get(b):   # cross-tier via connector A
            edge(a, "A_out0", lab); edge("A_in1", b)
        else:
            edge(a, b, lab)
    # nodes
    for n, (ti, cx, cy, lu) in where.items():
        if n in T:
            t = T[n]; _, _, bw, bh = box(n)
            ax.add_patch(FancyBboxPatch((cx - bw / 2, cy - bh / 2), bw, bh, boxstyle="round,pad=0,rounding_size=0.07",
                                        fc=KC[t.kind], ec=KE[t.kind], lw=1.8, ls="-" if t.path == "MAIN" else (0, (4, 2))))
            for fs, nchar in ((10.5, 16), (10, 17), (9.5, 18), (9, 19), (8.5, 20), (8, 21), (7.5, 23)):
                lines = wrap(f"{t.id} {t.name}", nchar)
                if len(lines) * fs * 1.42 / 72 <= bh - 0.02: break
            txt = "\n".join(lines)
            ax.text(cx, cy, txt, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.05)
            # bold ID
        elif n in G:
            ax.add_patch(Polygon([(cx, cy - .22), (cx + .22, cy), (cx, cy + .22), (cx - .22, cy)], fc="#fef9c3", ec="#a16207", lw=1.6))
            ax.text(cx, cy, "×", ha="center", va="center", fontsize=15, color="#a16207")
            ax.text(cx - 0.2, cy - 0.17, G[n][1], ha="right", va="bottom", fontsize=9.5, weight="bold", color=INK)
        elif n.startswith("A_"):
            ax.add_patch(Circle((cx, cy), 0.17, fc="#0b3c49", ec="#0b3c49"))
            ax.text(cx, cy, "A", ha="center", va="center", fontsize=11, color="white", weight="bold")
        else:
            start = n == "start"
            ax.add_patch(Circle((cx, cy), 0.16, fc="white", ec="#15803d" if start else "#b91c1c", lw=1.8 if start else 3.2))
            if n in ("end_rej", "end_ref"):
                ax.text(cx + 0.21, cy, "\n".join(wrap(E[n][1], 12)), ha="left", va="center", fontsize=9.5, color="#b91c1c", linespacing=1.0)
            else:
                if n == "end":
                    ax.text(min(cx, W - 0.95), cy - 0.2, E[n][1], ha="center", va="bottom", fontsize=9.5, color=INK)
                else:
                    ax.text(cx, cy + 0.2, "\n".join(wrap(E[n][1], 14)), ha="center", va="top", fontsize=9.5, color=INK, linespacing=1.0)
    # legend
    ly = H - 0.24
    items = [("MANUAL", "Manual task"), ("AUTO", "Automated (simulated) task"), ("EXTERNAL_MANUAL", "Third-party manual (common to both)"), ("WAIT", "Waiting period")]
    x = 0.3
    for k, lab in items:
        ax.add_patch(Rectangle((x, ly - 0.09), 0.28, 0.18, fc=KC[k], ec=KE[k], lw=1.4)); ax.text(x + 0.36, ly, lab, va="center", fontsize=10.5)
        x += 0.5 + len(lab) * 0.085
    ax.plot([x, x + 0.4], [ly, ly], color="#b91c1c", ls=(0, (4, 2)), lw=1.4); ax.text(x + 0.5, ly, "Exception path (dashed)", va="center", fontsize=10.5, color="#b91c1c")
    fig.savefig(OUT / f"{model}_bpmn_slide.png", dpi=220)
    plt.close(fig)


def state_machine():
    from tradeescrow.model import TRANSITIONS, State
    color = {State.CREATED: "#64748b", State.PENDING: "#b7791f", State.UNDER_REVIEW: "#c2410c",
             State.FROZEN: "#1d4ed8", State.RELEASED: "#15803d", State.REFUNDED: "#7c3aed"}
    short = {(None, State.CREATED): "fund + creation\\nKYC/AML PASS", (State.CREATED, State.PENDING): "shipment attested",
             (State.CREATED, State.UNDER_REVIEW): "doc FAIL / dispute", (State.PENDING, State.UNDER_REVIEW): "doc FAIL / dispute",
             (State.CREATED, State.FROZEN): "AML alert / hold", (State.PENDING, State.FROZEN): "AML alert / hold",
             (State.UNDER_REVIEW, State.FROZEN): "AML alert / hold",
             (State.PENDING, State.RELEASED): "GUARD: shipment ∧ docs(current)\\n∧ KYC×2 (fresh) ∧ no hold",
             (State.UNDER_REVIEW, State.PENDING): "reviewer revalidates", (State.UNDER_REVIEW, State.CREATED): "revalidated,\\nnot shipped",
             (State.UNDER_REVIEW, State.REFUNDED): "reviewer terminates", (State.FROZEN, State.PENDING): "compliance clears",
             (State.FROZEN, State.CREATED): "clears\\n(not shipped)", (State.FROZEN, State.UNDER_REVIEW): "clears\\n(docs failing)",
             (State.FROZEN, State.REFUNDED): "compliance terminates"}
    nid = lambda s: "start" if s is None else s.replace(" ", "_").replace("/", "_")
    L = ['digraph G { rankdir=LR; size="13.33,7.5"; ratio=fill; bgcolor="white"; nodesep=0.6; ranksep=1.25; pad=0.25;',
         'node [shape=box style="rounded,filled" fontname="Helvetica-Bold" fontsize=24 fontcolor=white penwidth=0 margin="0.25,0.12"];',
         'edge [fontname="Helvetica" fontsize=17 color="#334155" fontcolor="#334155" penwidth=1.8 arrowsize=1.1];',
         'start [shape=circle label="" width=0.35 style=filled fillcolor="#14213d"];',
         'labelloc=t; fontname="Helvetica-Bold"; fontsize=24; label="Escrow state machine — 6 states, 15 permitted transitions (all others rejected)";']
    for s in State.ALL:
        L.append(f'{nid(s)} [label="{s}" fillcolor="{color[s]}"];')
    for (a, b) in TRANSITIONS:
        exc = b in (State.FROZEN, State.UNDER_REVIEW, State.REFUNDED)
        st = ' color="#b91c1c" fontcolor="#b91c1c" style=dashed' if exc else ""
        if b == State.RELEASED: st = ' penwidth=3.5 color="#15803d" fontcolor="#15803d" fontname="Helvetica-Bold"'
        L.append(f'{nid(a)} -> {nid(b)} [xlabel="{short[(a, b)]}"{st}];' if False else f'{nid(a)} -> {nid(b)} [label="{short[(a, b)]}"{st}];')
    L += ['{rank=same; Pending; Under_Review;}', '{rank=same; Released; Refunded_Terminated;}', '}']
    (OUT / "state_machine_slide.dot").write_text("\n".join(L))
    subprocess.run(["dot", "-Tpng", "-Gdpi=200", str(OUT / "state_machine_slide.dot"), "-o", str(OUT / "state_machine_slide.png")], check=True)


def architecture():
    dot = r'''digraph A { rankdir=TB; newrank=true; compound=true; size="13.33,7.5"; ratio=fill; pad=0.2;
fontname="Helvetica-Bold"; fontsize=20; nodesep=0.3; ranksep=0.45;
labelloc=t; label="Architecture and trust boundaries";
node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=17 fillcolor="#ffffff" color="#94a3b8" margin="0.15,0.06"];
edge [fontname="Helvetica" fontsize=14 color="#475569" fontcolor="#334155" penwidth=1.6];
subgraph cluster_users { label="Seven participants (role-selected; server-side RBAC)"; fontsize=18; style="rounded,filled"; fillcolor="#f1f5f9"; color="#94a3b8";
  imp [label="HK importer"]; exp [label="Thai exporter"]; bh [label="Bank H\n(ops + compliance)"]; bo [label="Thai Bank O\n(observer)"];
  log [label="Logistics provider"]; cus [label="Customs authority"]; reg [label="Regulator\n(read-only audit)"];
  {rank=same; imp; exp; bh; bo;} {rank=same; log; cus; reg;} imp -> log [style=invis]; exp -> cus [style=invis]; bh -> reg [style=invis]; }
subgraph cluster_ui { label="Presentation (same service layer)"; fontsize=18; style="rounded,filled"; fillcolor="#eef6ff"; color="#60a5fa";
  st [label="Streamlit app"]; fl [label="Flask console\n(verified, fallback demo)"]; }
subgraph cluster_core { label="Escrow service layer — simulated smart contract (Bank H)"; fontsize=18; style="rounded,filled"; fillcolor="#ecfdf5"; color="#10b981";
  rbac [label="Command authorisation\n(PERMISSIONS, party scope)"]; sm [label="Six-state machine\n+ release guard" penwidth=2.5 color="#0f766e"];
  tok [label="Token accounting\nTDEP-HKD@Bank H\n(integer cents, conservation)"]; jr [label="Append-only journal\nSHA-256 hash chain"];
  views [label="Role projections\n& audit export"]; }
subgraph cluster_off { label="Off-chain attestation modules\n(SIMULATED — trust boundary)"; fontsize=18; fontcolor="#c2410c"; style="rounded,filled,dashed"; fillcolor="#fff7ed"; color="#f97316"; penwidth=2;
  docm [label="Document matching\n(contract, invoice,\nB/L, customs)"]; kyc [label="KYC/AML screening\n(creation + pre-release,\n48h)"]; ship [label="Shipment attestation\n(logistics)"]; }
db [shape=cylinder label="SQLite mock\npermissioned ledger" fillcolor="#f8fafc"];
ext [label="e-HKD extension (conceptual)\n2-phase commit: tokenised deposits\n⇄ CeBM mock — all-or-nothing" style="rounded,filled,dashed" fillcolor="#eef2ff" color="#6366f1"];
nolive [label="NOT CONNECTED: real banks,\nHKMA e-HKD, EnsembleTX, mBridge,\nreal KYC/AML, customs, FX" shape=note fillcolor="#fef2f2" color="#ef4444" fontcolor="#991b1b"];
reg -> st [ltail=cluster_users lhead=cluster_ui]; st -> rbac [lhead=cluster_core ltail=cluster_ui label="commands / reads"];
rbac -> sm; sm -> tok [label="lock / release\n/ refund"]; sm -> jr [label="every accepted\n& rejected command"]; jr -> views;
ship -> sm [label="attestation\n(PASS/FAIL)"]; docm -> sm [label="attestation\n(digest-pinned)"]; kyc -> sm [label="PASS / ALERT\n→ hold"];
tok -> db; jr -> db; sm -> ext [style=dashed label="post-release\nillustration"]; {rank=same; db; ext; nolive;}
{rank=same; rbac; docm; kyc; ship;}
}'''
    (OUT / "architecture_slide.dot").write_text(dot)
    subprocess.run(["dot", "-Tpng", "-Gdpi=200", str(OUT / "architecture_slide.dot"), "-o", str(OUT / "architecture_slide.png")], check=True)


if __name__ == "__main__":
    bpmn("baseline"); bpmn("proposed"); state_machine(); architecture()
    print(sorted(p.name for p in OUT.glob("*.png")))


# ---------------------------------------------------------------- hand-placed versions (override)
from matplotlib.patches import FancyArrowPatch
import numpy as np


def _arrow(ax, p, q, rad=0.0, color="#334155", ls="-", lw=1.8, label=None, lfs=12.5, loff=0.0, lcol=None, bold=False, shrinkA=0, shrinkB=0, lpos=None):
    a = FancyArrowPatch(p, q, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>", mutation_scale=18, color=color,
                        lw=lw, linestyle=ls, shrinkA=shrinkA, shrinkB=shrinkB, zorder=2)
    ax.add_patch(a)
    if label:
        p, q = np.array(p), np.array(q)
        d = q - p
        perp = np.array([d[1], -d[0]])
        m = (p + q) / 2 + 0.5 * rad * perp
        n = perp / (np.linalg.norm(perp) + 1e-9)
        m = m + n * loff
        if lpos is not None:
            m = lpos
        ax.text(m[0], m[1], label, ha="center", va="center", fontsize=lfs, color=lcol or color, zorder=5,
                weight="bold" if bold else "normal", linespacing=1.05,
                bbox=dict(fc="white", ec="none", pad=1.2, alpha=0.95))


def state_machine():
    S = {"Created": ((2.3, 3.75), "#64748b"), "Under Review": ((6.0, 6.0), "#c2410c"), "Pending": ((6.0, 1.5), "#b7791f"),
         "Frozen": ((9.7, 3.75), "#1d4ed8"), "Refunded/Terminated": ((11.4, 6.25), "#7c3aed"), "Released": ((11.4, 1.0), "#15803d")}
    BW = {"Refunded/Terminated": 3.05, "Under Review": 2.3}
    fig = plt.figure(figsize=(W, H), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    ax.text(0.3, 7.15, "Escrow state machine — 6 states, 15 permitted transitions (all others rejected)", fontsize=17, weight="bold", color=INK, va="center")

    def edge_pt(name, toward):
        (x, y), _ = S[name]; w = BW.get(name, 1.9) / 2; h = 0.33
        dx, dy = toward[0] - x, toward[1] - y
        t = min(w / abs(dx) if dx else 9e9, h / abs(dy) if dy else 9e9)
        return (x + dx * t, y + dy * t)

    RED, OK, GRY = "#b91c1c", "#15803d", "#334155"

    def E(a, b, label, kind="n", rad=0.0, loff=0.0, dx=(0, 0, 0, 0), lp=None):
        pa, pb = S[a][0], S[b][0]
        p = edge_pt(a, pb); q = edge_pt(b, pa)
        p = (p[0] + dx[0], p[1] + dx[1]); q = (q[0] + dx[2], q[1] + dx[3])
        col = {"n": GRY, "x": RED, "g": OK}[kind]
        _arrow(ax, p, q, rad=rad, color=col, ls=(0, (5, 3)) if kind == "x" else "-", lw=3.4 if kind == "g" else 1.8,
               label=label, loff=loff, lcol=col, bold=kind == "g", lfs=13 if kind == "g" else 12, lpos=lp)

    # start
    ax.add_patch(Circle((0.55, 3.75), 0.16, fc=INK, ec=INK))
    _arrow(ax, (0.72, 3.75), (2.3 - 0.95, 3.75), label="fund + creation\nKYC/AML PASS", lfs=11.5, lpos=(0.95, 4.42))
    E("Created", "Pending", "shipment attested", rad=0.12, lp=(3.25, 2.25))
    E("Created", "Under Review", "doc FAIL / dispute", "x", rad=-0.12, lp=(3.15, 5.3))
    E("Under Review", "Created", "revalidated,\nnot shipped", rad=-0.12, lp=(4.55, 4.75))
    E("Pending", "Under Review", "doc FAIL /\ndispute", "x", dx=(-0.45, 0, -0.45, 0), lp=(4.85, 2.6))
    E("Under Review", "Pending", "reviewer\nrevalidates", dx=(0.45, 0, 0.45, 0), lp=(7.05, 2.95))
    E("Created", "Frozen", "AML alert / hold", "x", dx=(0, 0.13, 0, 0.13), lp=(4.15, 4.12))
    E("Frozen", "Created", "clears (not shipped)", dx=(0, -0.15, 0, -0.15), lp=(7.95, 3.35))
    E("Pending", "Frozen", "AML alert / hold", "x", rad=0.12, lp=(9.15, 2.25))
    E("Frozen", "Pending", "compliance\nclears", rad=0.12, lp=(7.45, 2.55))
    E("Under Review", "Frozen", "AML alert / hold", "x", rad=-0.12, lp=(8.85, 5.35))
    E("Frozen", "Under Review", "clears\n(docs failing)", "x", rad=-0.12, lp=(7.55, 4.45))
    E("Under Review", "Refunded/Terminated", "reviewer terminates", "x", rad=-0.08, lp=(8.55, 6.62))
    E("Frozen", "Refunded/Terminated", "compliance\nterminates", "x", lp=(11.55, 4.95))
    E("Pending", "Released", "GUARD: shipment ∧ docs (current)\n∧ KYC×2 (fresh) ∧ no hold", "g", lp=(8.55, 0.72))
    for name, ((x, y), col) in S.items():
        w = BW.get(name, 1.9)
        term = name in ("Released", "Refunded/Terminated")
        ax.add_patch(FancyBboxPatch((x - w / 2, y - 0.33), w, 0.66, boxstyle="round,pad=0,rounding_size=0.14", fc=col,
                                    ec="white" if not term else col, lw=0, zorder=4))
        if term:
            ax.add_patch(FancyBboxPatch((x - w / 2 - 0.07, y - 0.4), w + 0.14, 0.8, boxstyle="round,pad=0,rounding_size=0.18",
                                        fc="none", ec=col, lw=2, zorder=4))
        ax.text(x, y, name, ha="center", va="center", fontsize=18, color="white", weight="bold", zorder=6)
    ax.text(W - 0.3, 0.25, "Solid = normal path · dashed red = exception path · double border = terminal state",
            ha="right", fontsize=11, color="#4b5563")
    fig.savefig(OUT / "state_machine_slide.png", dpi=220)
    plt.close(fig)


def architecture():
    fig = plt.figure(figsize=(W, H), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    ax.text(0.3, 7.2, "Architecture and trust boundaries", fontsize=17, weight="bold", color=INK, va="center")

    def cluster(x0, y0, x1, y1, title, fc, ec, dashed=False, tcol=INK):
        ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.15", fc=fc, ec=ec,
                                    lw=2, ls=(0, (5, 3)) if dashed else "-", zorder=0))
        ax.text(x0 + 0.15, y1 - 0.2, title, fontsize=12.5, weight="bold", color=tcol, va="center")

    def node(x, y, w, h, text, fs=12, ec="#94a3b8", fc="white", lw=1.4, tcol=INK, style="round,pad=0,rounding_size=0.1"):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=style, fc=fc, ec=ec, lw=lw, zorder=3))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tcol, zorder=4, linespacing=1.1)
        return (x, y, w, h)

    # participants
    cluster(0.25, 5.65, 8.45, 6.85, "Seven participants (role-selected; server-side RBAC)", "#f1f5f9", "#94a3b8")
    parts = ["HK\nimporter", "Thai\nexporter", "Bank H\n(ops +\ncompliance)", "Thai Bank O\n(observer)", "Logistics\nprovider", "Customs\nauthority", "Regulator\n(read-only\naudit)"]
    for i, t in enumerate(parts):
        node(0.85 + i * 1.12, 6.08, 1.02, 0.72, t, fs=10.5)
    # presentation
    cluster(8.75, 5.65, 13.05, 6.85, "Presentation (same service layer)", "#eef6ff", "#60a5fa")
    node(9.75, 6.08, 1.6, 0.6, "Streamlit app", fs=12)
    node(11.85, 6.08, 2.2, 0.6, "Flask console\n(verified, fallback demo)", fs=11)
    _arrow(ax, (8.45, 6.25), (8.75, 6.25), lw=2)
    # core
    cluster(0.25, 0.3, 7.45, 5.35, "Escrow service layer — simulated smart contract (Bank H)", "#ecfdf5", "#10b981")
    _arrow(ax, (9.2, 5.65), (5.6, 4.92), lw=2, label="commands / reads", lfs=11.5, lpos=(7.55, 5.47))
    node(5.0, 4.55, 3.0, 0.7, "Command authorisation\n(PERMISSIONS, party scope)")
    node(5.0, 3.25, 2.6, 0.75, "Six-state machine\n+ release guard", fs=13, ec="#0f766e", lw=2.8)
    node(5.55, 1.6, 3.0, 0.9, "Token accounting\nTDEP-HKD@Bank H\n(integer cents, conservation)", fs=11.5)
    node(2.0, 1.6, 2.5, 0.7, "Append-only journal\nSHA-256 hash chain")
    node(2.0, 0.72, 2.3, 0.6, "Role projections\n& audit export", fs=11.5)
    _arrow(ax, (5.0, 4.2), (5.0, 3.63), lw=1.8)
    _arrow(ax, (5.15, 2.87), (5.45, 2.05), label="lock / release / refund", lfs=11, lpos=(6.35, 2.45))
    _arrow(ax, (3.9, 3.0), (2.4, 1.95), label="every accepted &\nrejected command", lfs=11, lpos=(2.35, 2.75))
    _arrow(ax, (2.0, 1.25), (2.0, 1.02))
    # off-chain
    cluster(8.0, 2.68, 13.05, 5.25, "Off-chain attestation modules\n(SIMULATED — trust boundary)", "#fff7ed", "#f97316", dashed=True, tcol="#c2410c")
    ax.texts[-1].set_position((8.15, 4.95))
    offs = [(8.85, "Document matching\n(contract, invoice,\nB/L, customs)", "→ attestation\n(digest-pinned)"),
            (10.5, "KYC/AML screening\n(creation +\npre-release, 48h)", "→ PASS / ALERT\n→ hold"),
            (12.15, "Shipment\nattestation\n(logistics)", "→ attestation\n(PASS/FAIL)")]
    for i, (x, t, lab) in enumerate(offs):
        node(x, 3.85, 1.55, 1.25, t + "\n", fs=10.5)
        ax.text(x, 3.4, lab, ha="center", va="center", fontsize=9.5, style="italic", color="#c2410c", zorder=5, linespacing=1.0)
        ax.plot([x, x], [3.225, 3.08 - 0.12 * i], color="#475569", lw=1.6, zorder=2); _arrow(ax, (x, 3.08 - 0.12 * i), (6.3, 3.08 - 0.12 * i), color="#475569", lw=1.6)
    # bottom right
    ax.add_patch(FancyBboxPatch((7.7, 0.4), 1.95, 1.0, boxstyle="round,pad=0,rounding_size=0.3", fc="#f8fafc", ec="#64748b", lw=1.6, zorder=3))
    ax.text(8.675, 0.9, "SQLite mock\npermissioned\nledger", ha="center", va="center", fontsize=12, color=INK, zorder=4)
    _arrow(ax, (7.05, 1.4), (7.7, 1.05))
    _arrow(ax, (3.25, 1.4), (7.7, 0.7))
    node(11.5, 2.0, 2.95, 0.95, "e-HKD extension (conceptual)\n2-phase commit: tokenised deposits\n⇄ CeBM mock — all-or-nothing", fs=11,
         ec="#6366f1", fc="#eef2ff")
    _arrow(ax, (6.3, 3.0), (10.02, 2.15), ls=(0, (5, 3)), label="post-release illustration", lfs=11, lpos=(8.35, 2.28))
    node(11.5, 0.78, 2.95, 0.9, "NOT CONNECTED:\nreal banks, HKMA e-HKD, EnsembleTX,\nmBridge, real KYC/AML, customs, FX", fs=10,
         ec="#ef4444", fc="#fef2f2", tcol="#991b1b", style="square,pad=0")
    fig.savefig(OUT / "architecture_slide.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    state_machine(); architecture()
