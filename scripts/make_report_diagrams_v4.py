"""Report versions of the team's two-tier BPMN maps, flow architecture and hand-laid state machine
(source: scripts/make_slide_diagrams.py), re-coloured to the report palette (navy/teal/gold, red = exception)
and rendered at 300 dpi into diagrams/report/. Layout and content are unchanged."""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "scripts" / "make_slide_diagrams.py").read_text()
src = src.replace('"Under Review": ((6.0, 6.0), "#c2410c")', '"Under Review": ((6.0, 6.0), "#B8342A")')
# report-only tweaks: drop in-image titles (the report's exhibit headline replaces them), keep task text to two lines,
# and move three crowded state-machine labels apart
src = src.replace('ax.text(0.3, 7.2, "Architecture and trust boundaries", fontsize=17, weight="bold", color=INK, va="center")', 'None')
src = src.replace('ax.text(0.2, 0.36, lay["title"], fontsize=17, weight="bold", color=INK, va="center")', 'None')
src = src.replace('ax.text(0.3, 7.15, "Escrow state machine — 6 states, 15 permitted transitions (all others rejected)", fontsize=17, weight="bold", color=INK, va="center")', 'None')
src = src.replace('for fs, nchar in ((10.5, 16), (10, 17), (9.5, 18), (9, 19), (8.5, 20), (8, 21), (7.5, 23)):', 'for fs, nchar in ((10.5, 16), (10, 17), (9.5, 18), (9, 19), (8.5, 20), (8, 21), (7.5, 23), (7.5, 26), (7, 28)):')
src = src.replace('if len(lines) * fs * 1.42 / 72 <= bh - 0.02: break', 'if len(lines) <= 2 and len(lines) * fs * 1.42 / 72 <= bh - 0.02: break')
src = src.replace('E("Frozen", "Created", "clears (not shipped)", dx=(0, -0.15, 0, -0.15), lp=(7.95, 3.35))', 'E("Frozen", "Created", "clears (not shipped)", dx=(0, -0.15, 0, -0.15), lp=(4.2, 3.35))')
src = src.replace('E("Frozen", "Pending", "compliance\\nclears", rad=0.12, lp=(7.45, 2.55))', 'E("Frozen", "Pending", "compliance\\nclears", rad=0.12, lp=(8.45, 3.1))')
src = src.replace('OUT = ROOT / "diagrams" / "slide"', 'OUT = ROOT / "diagrams" / "report"').replace("dpi=220", "dpi=300")
PAL = {"#fde2c4": "#F3E3C0", "#c2410c": "#B07A22", "#cdeee9": "#D3ECE8", "#0f766e": "#1F8A82", "#e5e7eb": "#E6EAF0", "#4b5563": "#5B6573",
       "#fff1a8": "#E6EAF2", "#a16207": "#0B1730", "#14213d": "#0B1730", "#0b3c49": "#0B1730", "#1d3557": "#0B1730", "#f8fafc": "#F6F7F9",
       "#94a3b8": "#C9D0DB", "#b91c1c": "#B8342A", "#15803d": "#1F8A82", "#334155": "#3E4A5E", "#64748b": "#7A8496", "#b7791f": "#B07A22",
       "#1d4ed8": "#0B1730", "#7c3aed": "#3E4A5E", "#eef6ff": "#EEF1F6", "#60a5fa": "#8FA3C4", "#ecfdf5": "#EEF7F5", "#10b981": "#1F8A82",
       "#fff7ed": "#F8F1E3", "#f97316": "#B07A22", "#475569": "#3E4A5E", "#6366f1": "#2B4570", "#eef2ff": "#EEF1F6", "#ef4444": "#B8342A",
       "#fef2f2": "#FBEDEB", "#991b1b": "#B8342A", "#f1f5f9": "#F6F7F9", "#fef9c3": "#FFFFFF"}
for a, b in PAL.items(): src = re.sub(re.escape(a), b, src, flags=re.I)
src = src.replace('matplotlib.use("Agg")', 'matplotlib.use("Agg")\nmatplotlib.rcParams["font.family"] = ["Inter", "DejaVu Sans"]')
src = src.replace('if __name__ == "__main__":', 'if False:')
ns = {"__name__": "report_diagrams", "__file__": str(ROOT / "scripts" / "make_slide_diagrams.py")}
exec(compile(src, "make_slide_diagrams(report)", "exec"), ns)
for m in ("baseline", "proposed"): ns["bpmn"](m)
ns["state_machine"](); ns["architecture"]()
from PIL import Image, ImageChops
for p in (ROOT / "diagrams" / "report").glob("*.png"):   # trim white margins, keep a small pad
    im = Image.open(p).convert("RGB"); bg = Image.new("RGB", im.size, "white")
    x0, y0, x1, y1 = ImageChops.difference(im, bg).getbbox(); pad = 30
    im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad))).save(p)
print(sorted(p.name for p in (ROOT / "diagrams" / "report").glob("*.png")))
