"""Report charts v3 — same data as results/*.csv, redesigned for readability (direct labels, no legend hunting).
Writes results/charts/v3/{manual_tasks,latency,financing}.{svg,png}. Run: python scripts/make_report_charts_v3.py"""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "charts" / "v3"
OUT.mkdir(parents=True, exist_ok=True)
fam = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": fam, "font.size": 10.5, "axes.edgecolor": "#CBD5E1", "axes.labelcolor": "#334155",
                     "xtick.color": "#475569", "ytick.color": "#334155", "svg.fonttype": "path", "axes.titleweight": "bold"})
INK, MUTE, GRID = "#0B1730", "#64748B", "#E8EDF3"
SKY, TEAL, ORANGE, AMBER, SLATE, GREEN = "#0B1730", "#1F8A82", "#B07A22", "#D9B26A", "#A3ABB8", "#5FA89F"

rd = lambda f: list(csv.DictReader(open(ROOT / "results" / f)))
counts, tl = rd("process_counts.csv"), rd("timelines.csv")
cnt = lambda s, m: int(next(c for c in counts if c["scenario"] == s and c["model"] == m)["manual_settlement_tasks"])
def T(m, field, term="0", s="normal", lv="base"):
    return float(next(r for r in tl if r["scenario"] == s and r["model"] == m and r["assumption_level"] == lv and r["payment_term_days"] == term)[field])

def save(fig, name):
    for ext, kw in (("svg", {}), ("png", {"dpi": 300})):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.08, **kw)
    plt.close(fig)

def header(fig, title, sub, tag, tagcol):
    fig.text(0.012, 0.985, title, fontsize=13, weight="bold", color=INK, va="top")
    fig.text(0.012, 0.915, sub, fontsize=9.5, color=MUTE, va="top")
    fig.text(0.988, 0.985, f"  {tag}  ", fontsize=8.5, weight="bold", color="white", va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.6", fc=tagcol, ec="none"))

# ── Fig 6: manual settlement tasks — dumbbell ─────────────────────────────
fig, ax = plt.subplots(figsize=(8.2, 3.7))
fig.subplots_adjust(top=0.74, left=0.16, right=0.97, bottom=0.14)
header(fig, "Manual settlement tasks per transaction", "BPMN task inventory · goods, customs, carriage and FX tasks excluded in all models",
       "TEAM PROCESS MODEL · not measured savings", ORANGE)
scen = [("normal", "Normal trade"), ("mismatch", "Document mismatch"), ("aml", "AML alert")]
for i, (k, lab) in enumerate(scen):
    y = 2 - i
    b, p, e = cnt(k, "baseline"), cnt(k, "proposed"), cnt(k, "proposed_e2e")
    ax.plot([p, b], [y, y], color="#CBD5E1", lw=5, solid_capstyle="round", zorder=1)
    for v, col, mk, fc in ((b, SKY, "o", SKY), (e, ORANGE, "o", "white"), (p, TEAL, "o", TEAL)):
        ax.scatter([v], [y], s=230, color=fc, edgecolor=col, linewidth=2.4, zorder=3, marker=mk)
        ax.text(v, y + 0.27, str(v), ha="center", va="bottom", fontsize=10.5, weight="bold", color=col)
    ax.text(b + 0.45, y, f"−{round((b - p) / b * 100)}% model\n−{round((b - e) / b * 100)}% matched scope", va="center", fontsize=8.8, color=MUTE)
ax.set_yticks([2, 1, 0], [s[1] for s in scen], fontsize=10.5, weight="bold")
ax.set_xlim(0, 11.2); ax.set_ylim(-0.6, 2.75)
ax.set_xticks(range(0, 11, 2)); ax.set_xlabel("manual settlement tasks (count)", fontsize=9.5, color=MUTE)
ax.grid(axis="x", color=GRID, lw=1); ax.set_axisbelow(True)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.tick_params(axis="y", length=0)
h = [plt.Line2D([], [], marker="o", ls="", ms=9, color=SKY, label="Open account (baseline)"),
     plt.Line2D([], [], marker="o", ls="", ms=9, color=TEAL, label="Escrow, prototype scope (ends at Bank H release)"),
     plt.Line2D([], [], marker="o", ls="", ms=9, mfc="white", mec=ORANGE, mew=2, color=ORANGE, label="Escrow + hypothetical cross-bank leg (matched scope)")]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.005, 0.86), ncol=3, frameon=False, fontsize=8.6, handletextpad=0.3, columnspacing=1.2)
save(fig, "manual_tasks")

# ── Fig 7: post-shipment latency — range dot plot (low–base–high) ────────
fig, ax = plt.subplots(figsize=(8.2, 4.3))
fig.subplots_adjust(top=0.76, left=0.25, right=0.97, bottom=0.12)
header(fig, "Post-shipment latency to exporter credit", "Dot = base assumption · bar = low–high range · escrow is unaffected by the payment term",
       "ASSUMED TIMINGS · simulated days", "#B07A22")
rows = [("baseline", "0", "Open account · pay at once", SKY), ("baseline", "30", "Open account · 30-day term", "#8FA3C4"),
        ("proposed", "0", "Escrow (prototype)", TEAL)]
labels, yy = [], []
y = 0
for gi, (k, lab) in enumerate(scen):
    for m, term, rl, col in rows:
        lo, ba, hi = (T(m, "post_shipment_latency_d", term, k, lv) for lv in ("low", "base", "high"))
        ax.plot([lo, hi], [y, y], color=col, lw=6, alpha=0.35, solid_capstyle="round")
        ax.scatter([ba], [y], s=70, color=col, edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(hi + 0.8, y, f"{ba:g} d", va="center", fontsize=9, weight="bold", color=col)
        labels.append(rl); yy.append(y); y -= 1
    ax.text(-0.5, y + 3.55, lab.upper(), fontsize=8.5, weight="bold", color=INK, ha="left", va="bottom", transform=ax.transData)
    y -= 0.9
ax.set_yticks(yy, labels, fontsize=9)
ax.set_xlim(-0.5, 50); ax.set_xlabel("simulated days after shipment", fontsize=9.5, color=MUTE)
ax.grid(axis="x", color=GRID, lw=1); ax.set_axisbelow(True)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.tick_params(axis="y", length=0)
save(fig, "latency")

# ── Fig 8: who carries the wait — timeline (Gantt) ───────────────────────
fig, ax = plt.subplots(figsize=(8.2, 3.9))
fig.subplots_adjust(top=0.72, left=0.25, right=0.97, bottom=0.13)
header(fig, "Who carries the financing burden — and for how long", "Normal trade, base assumptions · bars show who is waiting between funding, shipment and credit",
       "ASSUMED TIMINGS · simulated days", "#B07A22")
cats = [("Open account · pay at once", "baseline", "0"), ("Open account · 30-day term", "baseline", "30"),
        ("Escrow (prototype)", "proposed", "0"), ("Escrow + cross-bank leg (hyp.)", "proposed_e2e", "0")]
for i, (lab, m, term) in enumerate(cats):
    y = 3 - i
    tf, ts, tc = T(m, "t_funded_d", term), T(m, "t_shipment_d", term), T(m, "t_credited_d", term)
    imp, unsec = T(m, "importer_funds_committed_d", term), T(m, "exporter_unsecured_receivable_d", term)
    ax.barh(y + 0.17, tc - tf, left=tf, height=0.28, color=TEAL)
    if unsec > 0:
        ax.barh(y - 0.17, tc - ts, left=ts, height=0.28, color=ORANGE)
    else:
        ax.barh(y - 0.17, max(tc - ts, 0.15), left=ts, height=0.28, color="#CBD5E1", hatch="////", edgecolor="#94A3B8", lw=0)
    ax.plot([ts, ts], [y - 0.38, y + 0.38], color=INK, lw=1.6)
    ax.scatter([tc], [y], s=46, color=GREEN, zorder=4, edgecolor="white", linewidth=1.2)
    txt = f"importer {imp:g} d" + (f"  ·  exporter at risk {unsec:g} d" if unsec > 0 else "  ·  exporter secured")
    if tc + 17 < 52:
        ax.text(tc + 0.9, y, txt, va="center", fontsize=8.8, color=INK)
    else:
        ax.text(tc - 0.8, y - 0.17, txt, va="center", ha="right", fontsize=8.6, color="white", weight="bold")
ax.set_yticks([3, 2, 1, 0], [c[0] for c in cats], fontsize=9.2)
ax.set_xlim(0, 52); ax.set_ylim(-0.6, 3.75); ax.set_xlabel("days from contract (simulated)", fontsize=9.5, color=MUTE)
ax.grid(axis="x", color=GRID, lw=1); ax.set_axisbelow(True)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.tick_params(axis="y", length=0)
from matplotlib.patches import Patch
h = [Patch(color=TEAL, label="Importer cash committed"), Patch(color=ORANGE, label="Exporter shipped, unpaid & unsecured"),
     Patch(facecolor="#CBD5E1", hatch="////", edgecolor="#94A3B8", label="Exporter waiting, secured by escrow"),
     plt.Line2D([], [], color=INK, lw=1.6, label="shipment"), plt.Line2D([], [], marker="o", ls="", color=GREEN, label="exporter credited")]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.005, 0.84), ncol=5, frameon=False, fontsize=8.2, handlelength=1.4, columnspacing=1.0, handletextpad=0.4)
save(fig, "financing")
print("wrote", OUT)
