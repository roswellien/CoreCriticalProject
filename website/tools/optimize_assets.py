"""Build the web-sized images and fonts the pages load from the original assets.

The original PNG plates and TTF fonts stay in the repository as the source files
(they carry the artwork provenance and match assets/fonts/provenance.json). Pages
load the smaller files this script writes next to them. Re-run it from the
repository root after replacing or adding an original, then commit the results:

    pip install pillow fonttools brotli
    python website/tools/optimize_assets.py

Fonts are converted to WOFF2 without subsetting or any other change. Orbitron and
Russo One have OFL Reserved Font Names; a plain format conversion is not a Modified
Version under the OFL, whereas subsetting would be, so subsetting is deliberately
not done here.
"""

from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

WEBSITE = Path(__file__).resolve().parent.parent
PLATES = WEBSITE / "assets" / "plates"
STUDIO = PLATES / "studio"
FONTS = WEBSITE / "assets" / "fonts"

# Quality 78 keeps painted artwork and game captures free of visible blocking.
ARTWORK_QUALITY = 78
# Mod Studio screenshots are mostly small interface text, which needs a higher quality.
INTERFACE_QUALITY = 90
# The surface texture is fine noise under translucent panels, so it tolerates more.
TEXTURE_QUALITY = 70

# Each plate gets a full-size WebP plus these smaller widths for srcset. The hero
# fills the viewport; the others appear at most about half the viewport wide.
ARTWORK_SMALLER_WIDTHS = {
    "hero-art": [1280],
    "native-art": [1024],
    "vulkan-art": [1024],
    "vulkan-c1m1-beach": [1280],
    "launcher-dashboard": [],
    # The before/after pair keeps identical sizes so the two frames line up.
    "compare-stock": [1280],
    "compare-core-critical": [1280],
}

# Only the current Mod Studio tour screenshots; the older numbered copies are unused.
STUDIO_SCREENSHOT_PATTERN = "mod-studio-*-v2.png"

# The brand mark is drawn at 20-32 CSS pixels; 128px covers 4x displays.
BRAND_MARK_IMAGE_SIZE = 128
BRAND_MARK_FAVICON_SIZE = 64


def report(path):
    print(f"{path.relative_to(WEBSITE)}  {path.stat().st_size:,} bytes")


def save_webp(image, destination, quality):
    image.save(destination, "WEBP", quality=quality, method=6)
    report(destination)


def resized_to_width(image, width):
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def open_rgb(path):
    with Image.open(path) as original:
        return original.convert("RGB")


def build_artwork():
    for name, smaller_widths in ARTWORK_SMALLER_WIDTHS.items():
        image = open_rgb(PLATES / f"{name}.png")
        save_webp(image, PLATES / f"{name}.webp", ARTWORK_QUALITY)
        for width in smaller_widths:
            smaller = resized_to_width(image, width)
            save_webp(smaller, PLATES / f"{name}-{width}.webp", ARTWORK_QUALITY)


def build_studio_screenshots():
    for source in sorted(STUDIO.glob(STUDIO_SCREENSHOT_PATTERN)):
        save_webp(open_rgb(source), source.with_suffix(".webp"), INTERFACE_QUALITY)


def build_texture():
    texture = open_rgb(PLATES / "surface-texture.png")
    save_webp(texture, PLATES / "surface-texture.webp", TEXTURE_QUALITY)


def build_brand_mark():
    image = open_rgb(PLATES / "brand-mark.png")
    size = BRAND_MARK_IMAGE_SIZE
    mark = image.resize((size, size), Image.Resampling.LANCZOS)
    save_webp(mark, PLATES / f"brand-mark-{size}.webp", 90)

    # Favicons stay PNG because not every browser accepts a WebP icon.
    size = BRAND_MARK_FAVICON_SIZE
    favicon_path = PLATES / f"brand-mark-{size}.png"
    image.resize((size, size), Image.Resampling.LANCZOS).save(favicon_path, optimize=True)
    report(favicon_path)


def build_fonts():
    for source in sorted(FONTS.glob("*.ttf")):
        font = TTFont(source)
        font.flavor = "woff2"
        destination = source.with_suffix(".woff2")
        font.save(destination)
        report(destination)


if __name__ == "__main__":
    build_artwork()
    build_studio_screenshots()
    build_texture()
    build_brand_mark()
    build_fonts()
