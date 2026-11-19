"""Navy -> teal duotone versions of the deck photos (presentation/v4/photos -> photos_duo), in the project palette."""
from pathlib import Path

from PIL import Image, ImageOps

V4 = Path(__file__).resolve().parent
SRC, OUT = V4 / "photos", V4 / "photos_duo"
OUT.mkdir(exist_ok=True)
for f in sorted(SRC.glob("*.jpg")):
    g = ImageOps.grayscale(Image.open(f))
    duo = ImageOps.colorize(g, black="#0B1730", mid="#1F6F78", white="#E9F3F0", blackpoint=8, whitepoint=250, midpoint=120)
    duo.save(OUT / f.name, quality=88, optimize=True, progressive=True)
    print(f.name)
