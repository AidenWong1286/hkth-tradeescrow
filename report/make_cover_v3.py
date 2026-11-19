"""Report cover v3 (A4, 2480 x 3508 px at 300 dpi) in the colour deck style.

    python report/make_cover_v3.py            -> report/figs/cover_v3.png

Same information as the previous cover (university, department, course, group, title, members and
IDs, submission, case, run of record, evidence, synthetic-data disclaimer); every number is read
from results/. Rendered with Playwright + the installed Microsoft Edge (Segoe UI, offline).
Palette = project palette: navy structure, teal tested, gold money/modelled, red only for refusals.
"""
import csv
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figs" / "cover_v3.png"
PHOTO = (ROOT / "presentation" / "v4" / "photos_duo" / "ship_top.jpg").as_uri()

MET = {r["metric_id"]: r for r in csv.DictReader(open(ROOT / "results/metrics.csv", encoding="utf-8"))}
MAN = json.load(open(ROOT / "results/run_manifest.json", encoding="utf-8"))
v = lambda k: MET[k]["value"]
d = lambda k: MET[k]["denominator"]
num = lambda x: f"{int(float(x)):,}"

_IDS = json.load(open(ROOT / "team.local.json", encoding="utf-8"))["ids"] if (ROOT / "team.local.json").exists() else {}
TEAM = [(n, a, _IDS.get(n, "")) for n, a in (("Tang Yu Hin", "Alex"), ("Chow Ka Shing", "Marcus"),
                                             ("Wong Ho Ming", "Michael"), ("So Lai Chun", "Jeff"))]   # IDs: team.local.json (not in git)

RING = "".join(
    f'<circle cx="60" cy="60" r="50" pathLength="700" stroke-dasharray="84 616" stroke-dashoffset="{-(i * 100) - 8}" />'
    for i in range(7))
CHAIN = "".join(f'<i class="{"on" if i == 15 else ""}"></i>' for i in range(16))

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
:root{{--paper:#F6F5F1;--navy:#0B1730;--ink2:#3E4A5E;--mute:#6B7689;--hair:#D9DEE6;--teal:#1F8A82;--tealT:#E1F0ED;
--gold:#B07A22;--goldT:#F5ECDA}}
*{{box-sizing:border-box;margin:0}}
body{{width:1240px;height:1754px;background:var(--paper);color:var(--navy);font-family:"Segoe UI Variable Text","Segoe UI",sans-serif;
  position:relative;overflow:hidden}}
.top{{position:absolute;left:96px;right:96px;top:72px;display:flex;justify-content:space-between;align-items:flex-start}}
.top b{{display:block;font-family:"Segoe UI Semibold","Segoe UI";font-weight:600;font-size:19px;letter-spacing:.1px}}
.top span{{display:block;font-size:15px;color:var(--mute);margin-top:3px}}
.top .r{{text-align:right}}
.brand{{position:absolute;left:96px;top:150px;display:flex;align-items:center;gap:12px;font-size:16px}}
.mark{{display:grid;grid-template-columns:14px 14px;gap:4px}}
.mark i{{width:14px;height:14px;border-radius:3px;border:2px solid var(--navy)}}
.mark i:nth-child(1){{background:var(--navy)}} .mark i:nth-child(4){{background:var(--teal);border-color:var(--teal)}}
.brand b{{font-family:"Segoe UI Semibold","Segoe UI";font-weight:600}} .brand span{{color:var(--mute)}}
.hero{{position:absolute;left:96px;right:96px;top:205px;height:690px;border-radius:30px;overflow:hidden;
  background:url("{PHOTO}") center 55%/cover}}
.hero::after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,23,48,0) 45%,rgba(11,23,48,.55) 100%)}}
.route{{position:absolute;inset:0;z-index:2}}
.route .lbl{{position:absolute;color:#fff;font-family:"Segoe UI Semibold","Segoe UI";font-weight:600;font-size:18px}}
.route .lbl small{{display:block;font-family:"Segoe UI";font-weight:400;font-size:14px;opacity:.85}}
.ring{{position:absolute;right:40px;top:36px;width:120px;height:120px;z-index:2}}
.ring circle{{fill:none;stroke:#fff;stroke-width:9;stroke-linecap:round;transform:rotate(-90deg);transform-origin:60px 60px}}
.ringlbl{{position:absolute;right:40px;top:162px;width:120px;text-align:center;color:#fff;font-size:13px;z-index:2;opacity:.9}}
.kicker{{position:absolute;left:96px;top:950px;color:var(--teal);font-family:"Segoe UI Semibold","Segoe UI";font-weight:600;font-size:19px}}
h1{{position:absolute;left:92px;top:982px;font-family:"Segoe UI Semibold","Segoe UI";font-weight:600;font-size:104px;letter-spacing:-3.5px;line-height:1}}
.tag{{position:absolute;left:96px;top:1102px;font-family:"Segoe UI Light","Segoe UI";font-weight:300;font-size:46px;letter-spacing:-1px;color:var(--navy)}}
.sub{{position:absolute;left:98px;top:1170px;font-size:20px;color:var(--ink2);max-width:900px;line-height:1.45}}
.kpis{{position:absolute;left:96px;right:96px;top:1250px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
.kpi{{border-radius:18px;padding:20px 22px;background:var(--tealT)}}
.kpi.g{{background:var(--goldT)}}
.kpi b{{display:block;font-family:"Segoe UI Light","Segoe UI";font-weight:300;font-size:46px;letter-spacing:-1.5px;color:var(--teal);line-height:1.05}}
.kpi.g b{{color:var(--gold)}}
.kpi span{{display:block;font-size:15px;color:var(--ink2);margin-top:6px;line-height:1.3}}
.kpi em{{font-style:normal;font-family:"Segoe UI Semibold","Segoe UI";font-weight:600;font-size:12.5px;color:var(--teal);letter-spacing:.3px}}
.kpi.g em{{color:var(--gold)}}
.info{{position:absolute;left:96px;right:96px;top:1445px;display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:40px;
  border-top:2px solid var(--navy);padding-top:22px}}
.info h4{{font-family:"Segoe UI Semibold","Segoe UI";font-weight:600;font-size:14px;color:var(--teal);margin-bottom:10px}}
.info p{{font-size:17px;line-height:1.55}}
.info .m{{color:var(--mute);font-size:14px}}
.info .row{{display:flex;justify-content:space-between;font-size:17px;line-height:1.75}}
.info .row span{{color:var(--mute);font-family:Consolas,monospace;font-size:15px}}
.foot{{position:absolute;left:96px;right:96px;bottom:58px;display:flex;justify-content:space-between;align-items:center;
  font-size:12.5px;color:var(--mute);white-space:nowrap}}
.chain{{display:flex;align-items:center}}
.chain i{{width:10px;height:8px;border-radius:2px;background:#A9D3CD;display:block}}
.chain i+i{{margin-left:6px;position:relative}}
.chain i+i::before{{content:"";position:absolute;left:-6px;top:3px;width:6px;height:2px;background:#C7D0DB}}
.chain i.on{{background:var(--teal)}}
</style></head><body>
<div class="top"><div><b>The Chinese University of Hong Kong</b><span>Department of Systems Engineering and Engineering Management</span></div>
<div class="r"><b>FTEC3002</b><span>Introduction to Financial Infrastructure</span></div></div>
<div class="brand"><span class="mark"><i></i><i></i><i></i><i></i></span><b>TradeEscrow</b><span>Hong Kong → Thailand</span></div>
<div class="hero">
  <svg class="route" viewBox="0 0 1048 690" preserveAspectRatio="none">
    <path d="M 120 600 C 360 330, 700 300, 930 560" fill="none" stroke="#E2B35C" stroke-width="4" stroke-dasharray="2 0"/>
    <circle cx="120" cy="600" r="11" fill="#2BB3A8" stroke="#fff" stroke-width="3"/>
    <circle cx="930" cy="560" r="11" fill="#0B1730" stroke="#E2B35C" stroke-width="4"/>
  </svg>
  <div class="route"><div class="lbl" style="left:44px;top:622px">Hong Kong<small>importer · Bank H</small></div>
  <div class="lbl" style="right:48px;top:582px;text-align:right">Laem Chabang<small>exporter · Bank O</small></div></div>
  <svg class="ring" viewBox="0 0 120 120">{RING}</svg>
  <div class="ringlbl">7 release checks</div>
</div>
<div class="kicker">Final project report · Group 1</div>
<h1>HK–TH TradeEscrow</h1>
<div class="tag">Pay when the goods are proven.</div>
<div class="sub">A tokenised-deposit escrow prototype for Hong Kong–Thailand cross-border trade finance</div>
<div class="kpis">
  <div class="kpi"><em>Tested</em><b>{v('M-01')}/{d('M-01')}</b><span>automated tests pass</span></div>
  <div class="kpi"><em>Tested</em><b>{v('M-04')}/{d('M-04')}</b><span>unsafe release attempts refused, funds unchanged</span></div>
  <div class="kpi"><em>Tested</em><b>0 / {num(d('M-09'))}</b><span>invariant violations in randomised checks</span></div>
  <div class="kpi g"><em>Modelled</em><b>−{v('M-32')}%</b><span>manual settlement tasks, matched scope</span></div>
</div>
<div class="info">
  <div><h4>Prepared by</h4>
    {''.join(f'<div class="row">{n} ({a})<span>{i}</span></div>' for n, a, i in TEAM)}
  </div>
  <div><h4>Submitted</h4><p>19 November 2026</p><p class="m">Final report · v1.0</p>
       <h4 style="margin-top:18px">Case</h4><p>Trade TR-001 · ESC-001</p><p class="m">Synthetic fixture {MAN['fixture_version']}</p></div>
  <div><h4>Run of record</h4><p style="font-family:Consolas,monospace;font-size:16px">{MAN['code_sha256_16'][:8]}</p><p class="m">Code hash · results/ reproducible</p>
       <h4 style="margin-top:18px">Evidence</h4><p>{v('M-01')} tests · {v('M-04')} attacks · {d('M-11')} mutants</p><p class="m">Simulation on synthetic data</p></div>
</div>
<div class="foot"><span>All transaction data are synthetic. No live bank, tokenised deposit, e-HKD, EnsembleTX or mBridge system was used.</span>
<span class="chain">{CHAIN}</span></div>
</body></html>"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = OUT.with_suffix(".html")
    html.write_text(HTML, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge", headless=True)
        page = b.new_page(viewport={"width": 1240, "height": 1754}, device_scale_factor=2)
        page.goto(html.as_uri())
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT))
        b.close()
    html.unlink()
    print("saved", OUT)


if __name__ == "__main__":
    main()
