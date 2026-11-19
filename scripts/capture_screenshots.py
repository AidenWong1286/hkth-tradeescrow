"""Drive the running Flask console with real browser clicks and capture screenshots.

Usage: python -m ui_flask.app &   then   python scripts/capture_screenshots.py [outdir]
Each screenshot is taken from the live app state produced by the clicks
(UI-level end-to-end check of TC-001/002/003 and RBAC).
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "results/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
log = []


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--disable-gpu", "--disable-background-networking", "--disable-component-update"])
        pg = b.new_page(viewport={"width": 1500, "height": 1000}, device_scale_factor=1.5)

        def act_as(pid):
            pg.goto(BASE + "/")
            with pg.expect_navigation():          # onchange submits the form; wait for that round trip
                pg.select_option("select[name=principal]", pid)
            pg.wait_for_load_state()

        def click(label):
            pg.get_by_role("button", name=label, exact=True).click()
            pg.wait_for_load_state()
            flash = pg.locator(".flash").first.inner_text() if pg.locator(".flash").count() else ""
            log.append({"click": label, "flash": flash})
            return flash

        def shot(name, full=True):
            pg.screenshot(path=str(OUT / f"{name}.png"), full_page=full, timeout=90000)
            log.append({"screenshot": name})

        def reset(variant):
            pg.goto(BASE + "/")
            pg.select_option("select[name=variant]", variant)
            click("Reset ledger with this fixture")

        # ---------------- TC-001 normal settlement, step by step via role switching
        reset("clean")
        act_as("u_importer_02"); click("Create & fund escrow"); shot("TC-017b-importer2-create-rejected", False)
        act_as("u_importer_01"); shot("TC-001-0-importer-before", False)
        click("Create & fund escrow"); shot("TC-001-1-created-importer")
        act_as("u_customs"); click("Submit export customs declaration")
        act_as("u_logistics"); click("Attest shipped on board (SH-001)"); shot("TC-001-2-pending-logistics-view")
        act_as("u_exporter_01"); click("Submit commercial invoice"); click("Submit bill of lading")
        act_as("u_bank_hk_ops"); click("Run document matching"); shot("TC-001-3-bank-guard-before-kyc")
        act_as("u_bank_hk_compliance"); click("Run pre-release KYC/AML screening")
        act_as("u_bank_hk_ops"); click("Trigger contract release"); shot("TC-001-4-released-bank-view")
        act_as("u_bank_th"); click("Acknowledge receipt (observation)")
        act_as("u_exporter_01"); shot("TC-001-5-exporter-credited")
        act_as("u_regulator"); shot("TC-001-6-regulator-audit-view")
        click("Try to release funds (forbidden)"); shot("TC-001-7-regulator-denied", False)
        act_as("u_importer_02"); shot("TC-017-other-importer-denied", False)
        act_as("u_bank_hk_ops"); pg.goto(BASE + "/ledger", wait_until="domcontentloaded"); shot("TC-001-8-ledger-journal")
        act_as("u_importer_02"); pg.goto(BASE + "/ledger", wait_until="domcontentloaded"); shot("LEDGER-importer2-own-only", False)
        act_as("u_regulator"); pg.goto(BASE + "/ledger", wait_until="domcontentloaded"); shot("LEDGER-regulator-metadata", False)
        act_as("u_logistics"); pg.goto(BASE + "/ledger", wait_until="domcontentloaded"); shot("LEDGER-logistics-denied", False)

        # ---------------- TC-002 mismatch
        reset("mismatch")
        pg.goto(BASE + "/"); pg.get_by_role("button", name="▶ Auto-play selected scenario").click(); pg.wait_for_load_state()
        # replay stops after release; rebuild manually to capture the review moment
        reset("mismatch")
        act_as("u_importer_01"); click("Create & fund escrow")
        act_as("u_customs"); click("Submit export customs declaration")
        act_as("u_logistics"); click("Attest shipped on board (SH-001)")
        act_as("u_exporter_01"); click("Submit commercial invoice"); click("Submit bill of lading")
        act_as("u_bank_hk_ops"); click("Run document matching")
        click("Trigger contract release"); shot("TC-002-1-under-review-release-blocked")
        act_as("u_exporter_01"); click("Submit corrected invoice")
        act_as("u_bank_hk_ops"); click("Run document matching"); click("Reviewer: revalidate documents")
        act_as("u_bank_hk_compliance"); click("Run pre-release KYC/AML screening")
        act_as("u_bank_hk_ops"); click("Trigger contract release"); shot("TC-002-2-corrected-released")

        # ---------------- TC-003 AML alert
        reset("aml")
        act_as("u_importer_01"); click("Create & fund escrow")
        act_as("u_customs"); click("Submit export customs declaration")
        act_as("u_logistics"); click("Attest shipped on board (SH-001)")
        act_as("u_exporter_01"); click("Submit commercial invoice"); click("Submit bill of lading")
        act_as("u_bank_hk_ops"); click("Run document matching")
        click("Inject AML watchlist hit")
        act_as("u_bank_hk_compliance"); click("Run pre-release KYC/AML screening"); shot("TC-003-1-frozen-compliance-view")
        act_as("u_bank_hk_ops"); click("Trigger contract release"); shot("TC-003-2-release-denied-frozen")
        click("Reviewer: terminate & refund"); shot("TC-014-refund-denied-active-hold", False)
        act_as("u_exporter_01"); click("Try to clear AML hold (forbidden)"); shot("TC-015-exporter-denied", False)
        act_as("u_regulator"); shot("TC-003-3-regulator-sees-freeze")
        act_as("u_bank_hk_compliance"); click("Clear hold (false positive)"); click("Run pre-release KYC/AML screening")
        act_as("u_bank_hk_ops"); click("Trigger contract release"); shot("TC-003-4-cleared-released")

        # ---------------- e-HKD concept
        pg.goto(BASE + "/ehkd"); pg.check("input[value=success]"); pg.get_by_role("button", name="Execute two-leg settlement").click()
        pg.wait_for_load_state(); shot("EHKD-1-success")
        pg.check("input[value=cebm_insufficient]"); pg.get_by_role("button", name="Execute two-leg settlement").click()
        pg.wait_for_load_state(); shot("EHKD-2-rollback")
        b.close()
    (OUT / "capture_log.json").write_text(json.dumps(log, indent=1, ensure_ascii=False))
    print(f"{sum(1 for l in log if 'screenshot' in l)} screenshots -> {OUT}")


if __name__ == "__main__":
    main()
