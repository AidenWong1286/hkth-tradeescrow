"""Crop the REAL browser screenshots (results/screenshots, captured by capture_screenshots.py)
into slide-sized panels. Pixel data is unchanged apart from cropping and JPEG encoding;
nothing is drawn onto the screenshots. Boxes are in screenshot pixels (1500x1000 viewport at 1.5x).

Usage: python scripts/make_slide_assets.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "results" / "screenshots", ROOT / "presentation" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

# name -> (source screenshot, box)
CROPS = {
    "S_TC001_panel": ("TC-001-4-released-bank-view", (555, 255, 2222, 1200)),
    "S_TC001_flash": ("TC-001-4-released-bank-view", (30, 172, 2222, 240)),
    "S_TC001_audit": ("TC-001-4-released-bank-view", (555, 1500, 2222, 2160)),
    "S_TC002_panel": ("TC-002-1-under-review-release-blocked", (555, 255, 2222, 1200)),
    "S_TC002_flash": ("TC-002-1-under-review-release-blocked", (30, 172, 2222, 240)),
    "S_TC003_panel": ("TC-003-1-frozen-compliance-view", (555, 255, 2222, 1200)),
    "S_TC003_flash": ("TC-003-1-frozen-compliance-view", (30, 172, 2222, 240)),
    # state strip and release-guard panel only (for side-by-side slides, larger type)
    "S_TC001_state": ("TC-001-4-released-bank-view", (555, 255, 1650, 470)),
    "S_TC002_state": ("TC-002-1-under-review-release-blocked", (555, 255, 1650, 470)),
    "S_TC003_state": ("TC-003-1-frozen-compliance-view", (555, 255, 1650, 470)),
    "S_TC001_guard": ("TC-001-4-released-bank-view", (1725, 495, 2222, 930)),
    "S_TC002_guard": ("TC-002-1-under-review-release-blocked", (1725, 495, 2222, 1010)),
    "S_TC003_guard": ("TC-003-1-frozen-compliance-view", (1725, 495, 2222, 1100)),
    "S_TC017b_flash": ("TC-017b-importer2-create-rejected", (30, 172, 2222, 240)),
    "S_LEDGER_regulator": ("LEDGER-regulator-metadata", (30, 160, 1330, 760)),
    "S_LEDGER_logistics": ("LEDGER-logistics-denied", (30, 160, 2222, 330)),
    "S_LEDGER_importer2": ("LEDGER-importer2-own-only", (30, 160, 2222, 600)),
    "S_EHKD_success": ("EHKD-1-success", None),
}


def main():
    for name, (src, box) in CROPS.items():
        if not (SRC / f"{src}.png").exists():
            print("skip (no screenshot):", src); continue
        im = Image.open(SRC / f"{src}.png").convert("RGB")
        if box:
            im = im.crop(box)
        im.save(OUT / f"{name}.jpg", quality=90)
        print(f"{name}.jpg  <- {src}.png {box or 'full'}  {im.size}")


if __name__ == "__main__":
    main()
