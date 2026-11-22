"""Build the add-on icon, logo and GitHub social preview from the native Verdant icon.

Maintainer helper: the source artwork lives in the native app project
(`PlantCare2.0/VerdantMultiplatform/AppResources/AppIcon-1024.png`), outside this
repository, so the generated PNGs are committed and this script is only run when
the brand artwork changes.

    .venv/bin/python scripts/make_brand_assets.py [path/to/AppIcon-1024.png]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "plantcare_web"
DOCS = ROOT / "docs"
SOURCE = Path(
    "/Volumes/Dati/Progetti/Maurizio/PlantCare2.0/VerdantMultiplatform/AppResources/AppIcon-1024.png"
)

FOREST = (25, 67, 48, 255)      # --vc-forest #194330
MOSS = (64, 110, 77, 255)       # --vc-moss #406e4d
CANVAS = (242, 246, 236, 255)   # --vc-canvas #f2f6ec
FONT = "/System/Library/Fonts/Avenir Next.ttc"


def native_tile(source: Path, size: int) -> Image.Image:
    """Crop the rounded square out of the native artwork and resize it."""
    img = Image.open(source).convert("RGBA")
    box = img.getbbox()  # the artwork sits on a transparent canvas
    if not box:
        raise SystemExit(f"No visible artwork in {source}")
    tile = img.crop(box)
    side = max(tile.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.alpha_composite(tile, ((side - tile.width) // 2, (side - tile.height) // 2))
    return square.resize((size, size), Image.LANCZOS)


def logo(tile: Image.Image, width: int = 250, height: int = 100) -> Image.Image:
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mark = tile.resize((84, 84), Image.LANCZOS)
    img.alpha_composite(mark, (0, (height - mark.height) // 2))

    draw = ImageDraw.Draw(img)
    x = mark.width + 12
    title = ImageFont.truetype(FONT, 36, index=1)  # Avenir Next Demi Bold
    draw.text((x, 20), "Verdant", font=title, fill=FOREST)
    small = ImageFont.truetype(FONT, 9, index=0)
    draw.text((x + 1, 64), "HOME ASSISTANT ADD-ON", font=small, fill=MOSS)
    return img


def social(tile: Image.Image, width: int = 1280, height: int = 640) -> Image.Image:
    img = Image.new("RGBA", (width, height), CANVAS)
    mark = tile.resize((280, 280), Image.LANCZOS)
    img.alpha_composite(mark, (96, (height - mark.height) // 2))

    draw = ImageDraw.Draw(img)
    title = ImageFont.truetype(FONT, 92, index=1)
    body = ImageFont.truetype(FONT, 32, index=0)
    mono = ImageFont.truetype(FONT, 24, index=0)
    draw.text((440, 165), "Verdant HA", font=title, fill=FOREST)
    draw.text((444, 285), "Plant care add-on for Home Assistant", font=body, fill=MOSS)
    draw.text((444, 338), "Care rounds · Calendar · Sensors · Optional AI", font=body, fill=MOSS)
    draw.text((444, 470), "github.com/kriptos1970/verdant-ha", font=mono, fill=MOSS)
    return img


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else SOURCE
    if not source.exists():
        raise SystemExit(f"Native artwork not found: {source}")
    tile = native_tile(source, 1024)
    tile.resize((128, 128), Image.LANCZOS).save(OUT / "icon.png")
    logo(tile).save(OUT / "logo.png")
    social(tile).save(DOCS / "social-preview.png")
    print("wrote", OUT / "icon.png", OUT / "logo.png", DOCS / "social-preview.png")


if __name__ == "__main__":
    main()
