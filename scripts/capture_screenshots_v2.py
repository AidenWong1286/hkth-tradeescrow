"""Capture screenshots of the redesigned Flask console (2026-11-19 "Ink & Signal" UI).

Needs the console running (python -m ui_flask.app) and `pip install playwright`. Uses the Microsoft Edge
already installed on Windows (channel="msedge"), so no browser download is required.

Every state is reached through the console's own operator control /sim/step, i.e. the same autoplay
steps, principals and engine as the test suite; nothing is staged in the page.

Outputs (results/screenshots/v2/):
  {theme}_tc001_released.png   TC-001 finished, viewed by Bank H operations
  {theme}_tc002_review.png     TC-002 after the refused release (Under Review), Bank H operations
  {theme}_tc003_frozen.png     TC-003 after the refused release (Frozen), Bank H compliance
  {theme}_ledger_regulator.png Ledger page as the regulator after TC-001 (metadata only)
  {theme}_tc003_frozen_stage.png  cropped stage (state word + ring + guard) for report Figure 5
for theme in dark, light. Full-window shots are 1920 x 1089 (aspect 1.764 = the deck/report frames).
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "screenshots" / "v2"
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5050"
W, H = 1920, 1089  # 1920 / 1.764


def run(page, viewer: str, variant: str, upto: int | None):
    """Fresh ledger via step 0, then steps 1..upto (None = all), then view as `viewer`."""
    from tradeescrow.ui_actions import autoplay_steps
    n = len(autoplay_steps(variant)) if upto is None else upto + 1
    for i in range(n):
        r = page.request.post(f"{BASE}/sim/step", form={"variant": variant, "i": str(i)})
        assert r.ok, (variant, i, r.status)
    page.request.post(f"{BASE}/as", form={"principal": viewer})


def settle(page, url="/"):
    page.goto(BASE + url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2600)   # let the one-time entrance animation finish
    page.add_style_tag(content=".film,.toast{display:none!important}")   # player bar would cover the guard verdict


def main():
    sys.path.insert(0, str(ROOT))
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        for theme in ("dark", "light"):
            ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=2)
            ctx.add_init_script(f"try{{localStorage.setItem('te-theme','{theme}')}}catch(e){{}}")
            page = ctx.new_page()
            shots = [
                ("tc001_released", "u_bank_hk_ops", "clean", None),
                ("tc002_review", "u_bank_hk_ops", "mismatch", 6),       # step 6 = refused release
                ("tc003_frozen", "u_bank_hk_compliance", "aml", 8),      # step 8 = refused release
            ]
            for name, viewer, variant, upto in shots:
                run(page, viewer, variant, upto)
                settle(page)
                page.screenshot(path=str(OUT / f"{theme}_{name}.png"))
                if name == "tc003_frozen":
                    # Report Figure 5: cinema layout, crop stage + guard at the frame aspect 1.764
                    page.keyboard.press("c")
                    page.wait_for_timeout(700)
                    box = page.locator("#stage").bounding_box()
                    w = box["width"]
                    page.screenshot(path=str(OUT / f"{theme}_{name}_stage.png"),
                                    clip={"x": box["x"], "y": box["y"], "width": w, "height": w / 1.764})
                    page.keyboard.press("c")
            run(page, "u_regulator", "clean", None)
            settle(page, "/ledger")
            page.screenshot(path=str(OUT / f"{theme}_ledger_regulator.png"))
            # Deck slide 9: the laptop artwork's screen opening is 1708 x 1098 px (aspect 1.556)
            page.set_viewport_size({"width": 1920, "height": 1234})
            run(page, "u_bank_hk_ops", "clean", None)
            settle(page)
            page.screenshot(path=str(OUT / f"{theme}_tc001_released_laptop.png"))
            ctx.close()
        browser.close()
    print("saved to", OUT)


if __name__ == "__main__":
    main()
