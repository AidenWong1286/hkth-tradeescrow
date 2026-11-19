"""Render the console's wave mesh (ui_flask/static/mesh.js) as transparent PNGs for the v4 deck.
Ink hairlines on a transparent background, so they sit on the #F5F5F2 slide colour.
Uses Playwright with the installed Microsoft Edge (channel="msedge")."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "mesh"
MESH_JS = (ROOT / "ui_flask" / "static" / "mesh.js").as_uri()
HTML = """<!doctype html><html data-theme="light"><head><style>
html,body{margin:0;background:transparent}
.mesh{position:fixed;inset:0;width:100vw;height:100vh}
.mesh path{fill:none;vector-effect:non-scaling-stroke;stroke-width:%(w)s}
.mesh .ln{stroke:rgba(%(rgb)s,%(a)s)} .mesh .xl{stroke:rgba(%(rgb)s,%(x)s)}
</style></head><body><svg class="mesh" id="mesh"></svg>
<script>window.matchMedia=()=>({matches:true,addEventListener(){}});</script>
<script src="%(js)s"></script></body></html>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    variants = {"mesh_full": dict(w=1.6, a=0.20, x=0.07, rgb="17,17,17"),        # ink (monochrome v4)
                "mesh_teal": dict(w=1.6, a=0.42, x=0.12, rgb="31,138,130")}      # teal (colour deck)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge", headless=True)
        for name, v in variants.items():
            page = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
            html = OUT / f"_{name}.html"
            html.write_text(HTML % dict(v, js=MESH_JS), encoding="utf-8")
            page.goto(html.as_uri())
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT / f"{name}.png"), omit_background=True)
            html.unlink()
        b.close()
    print("saved", OUT)


if __name__ == "__main__":
    main()
