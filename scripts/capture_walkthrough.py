"""Full screenshot walkthrough of the Flask console for the report appendix (Appendix I).

    python -m ui_flask.app            # in another terminal
    python scripts/capture_walkthrough.py [http://127.0.0.1:5050]

Every state is reached through the console's own controls: /sim/step replays the scripted scenario
steps as their real principals, /act/<action> runs a role's button, /as switches the viewer.
Nothing is staged in the page. Output: results/screenshots/walkthrough/NN_name.png (+ index.csv).
Uses Playwright with the installed Microsoft Edge (channel="msedge").
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradeescrow.ui_actions import autoplay_steps  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5050"
OUT = ROOT / "results" / "screenshots" / "walkthrough"
VW, VH = 1366, 900
HIDE = ".film,.toast{display:none!important}"

SHOTS = []   # (file, caption)


def steps(page, variant, upto=None):
    n = len(autoplay_steps(variant)) if upto is None else upto + 1
    for i in range(n):
        assert page.request.post(f"{BASE}/sim/step", form={"variant": variant, "i": str(i)}).ok


def view(page, pid):
    page.request.post(f"{BASE}/as", form={"principal": pid})


def go(page, url="/", cinema=True, keep_film=False, scroll_to=None):
    page.goto(BASE + url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2400)                        # one-time entrance animation
    if not keep_film:
        page.add_style_tag(content=HIDE)
    if cinema and url == "/":
        page.keyboard.press("c")
        page.wait_for_timeout(500)
    if scroll_to:
        page.locator(scroll_to).scroll_into_view_if_needed()
        page.wait_for_timeout(500)


def snap(page, name, caption, full=False):
    f = OUT / f"{len(SHOTS) + 1:02d}_{name}.png"
    page.screenshot(path=str(f), full_page=full)
    SHOTS.append((f.name, caption))
    print(f.name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge", headless=True)
        ctx = b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=2)
        ctx.add_init_script("try{localStorage.setItem('te-theme','light')}catch(e){}")
        page = ctx.new_page()

        go(page, "/intro", cinema=False)
        snap(page, "intro", "Opening page: the problem in one line and the prototype's scope (figures read from the code).")

        page.request.post(f"{BASE}/sim/reset", form={"variant": "clean"})
        view(page, "u_importer_01"); go(page)
        snap(page, "console_empty", "Console before any escrow exists, viewed by the Hong Kong importer: only the importer's own balance is visible.")

        steps(page, "clean", 0); view(page, "u_bank_hk_ops"); go(page)
        snap(page, "created", "TC-001 step 1: the importer creates and funds the escrow (creation KYC/AML passed); HKD 250,000 is locked.")

        steps(page, "clean", 2); view(page, "u_bank_hk_ops"); go(page)
        snap(page, "pending", "Customs declaration and shipment attestation recorded: Created → Pending. The live release guard shows which checks are still waiting.")

        steps(page, "clean"); view(page, "u_bank_hk_ops"); go(page)
        snap(page, "released", "TC-001 complete: all seven checks pass, the contract releases HKD 250,000 to the exporter exactly once.")

        steps(page, "mismatch", 6); view(page, "u_bank_hk_ops"); go(page)
        snap(page, "under_review", "TC-002: invoice HKD 245,000 vs contract 250,000. Documents fail, the escrow moves to Under Review and the release attempt is refused.")

        steps(page, "mismatch"); view(page, "u_bank_hk_ops"); go(page)
        snap(page, "mismatch_resolved", "TC-002 resolved: corrected invoice, fresh document PASS, reviewer revalidation and new screening, then a single release.")

        steps(page, "aml", 8); view(page, "u_bank_hk_compliance"); go(page)
        snap(page, "frozen", "TC-003: a synthetic watchlist hit freezes the escrow. Release is refused with ESCROW_FROZEN and ACTIVE_HOLD; funds stay locked.")

        steps(page, "aml"); view(page, "u_bank_hk_compliance"); go(page)
        snap(page, "aml_cleared", "TC-003 resolved: compliance clears a false positive, re-screening is required, and only then is the escrow released.")

        steps(page, "clean")
        view(page, "u_importer_01"); go(page, scroll_to="#lens")
        snap(page, "lens_importer", "Role lens, Hong Kong importer: full commercial view of its own trade; hatched fields are outside the projection.")
        view(page, "u_regulator"); go(page, scroll_to="#lens")
        snap(page, "lens_regulator", "Role lens, regulator: identity and amounts only; commercial terms and logistics references are hidden.")
        view(page, "u_importer_02"); go(page)
        snap(page, "lens_denied", "A participant outside the trade (importer #2) is refused (ACCESS_DENIED) and the refused read is written to the journal.")

        view(page, "u_bank_hk_ops"); go(page, "/ledger")
        snap(page, "ledger_bank", "Ledger page, Bank H operations: every token account, conservation check and the full hash-chained journal.")
        view(page, "u_importer_01"); go(page, "/ledger")
        snap(page, "ledger_importer", "Ledger page, importer: only its own token account and its own trade's events.")
        view(page, "u_regulator"); go(page, "/ledger")
        snap(page, "ledger_regulator", "Ledger page, regulator: integrity flags and event metadata only, no balances.")
        view(page, "u_customs"); go(page, "/ledger")
        snap(page, "ledger_denied", "Ledger page, customs: access denied (HTTP 403) and logged as a refused read.")

        view(page, "u_bank_hk_ops")
        page.request.post(f"{BASE}/sim/tamper")
        go(page, scroll_to="#chainpanel")
        snap(page, "tamper", "Tamper demonstration: one stored journal event is edited without re-hashing; verification fails and every later link is marked broken.")

        for case, cap in (("success", "e-HKD concept: both legs prepare and commit together (COMMITTED_BOTH)."),
                          ("cebm_insufficient", "e-HKD concept: insufficient central-bank money, so both legs roll back (all-or-nothing holds).")):
            go(page, "/ehkd", cinema=False)
            page.check(f"input[value='{case}']")
            page.click(".cases button")
            page.wait_for_load_state("networkidle"); page.wait_for_timeout(1200)
            snap(page, f"ehkd_{case}", cap)

        page.request.post(f"{BASE}/sim/reset", form={"variant": "clean"})
        steps(page, "clean", 4); view(page, "u_bank_hk_ops")
        go(page, keep_film=True)
        snap(page, "film_mode", "Cinema / film mode used for the demo video: the bottom player replays a scenario step by step, each step run by its real participant.")

        ctx.add_init_script("try{localStorage.setItem('te-theme','dark')}catch(e){}")
        page2 = ctx.new_page()
        steps(page2, "clean"); view(page2, "u_bank_hk_ops")
        go(page2)
        snap(page2, "dark_theme", "The same released escrow in the dark theme (theme switch in the top bar).")
        b.close()

    with open(OUT / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["file", "caption"]); w.writerows(SHOTS)
    print(len(SHOTS), "screenshots ->", OUT)


if __name__ == "__main__":
    main()
