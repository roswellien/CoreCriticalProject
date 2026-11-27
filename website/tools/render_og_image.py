"""Render the 1200x630 social preview image (og:image) from the homepage hero art.

Run from the website folder: python tools/render_og_image.py
The output, assets/plates/og-image.jpg, is committed so the build stays a plain copy.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PLATES = ROOT / "assets" / "plates"
FONTS = ROOT / "assets" / "fonts"
OUTPUT = PLATES / "og-image.jpg"

# 1200x630 is the size Facebook, Discord, X (summary_large_image), LinkedIn and Slack
# all crop to, so nothing important is lost on any of them.
WIDTH = 1200
HEIGHT = 630

# Colours from DESIGN.md.
GROUND = (20, 23, 23)
TITLE_INK = (238, 228, 215)
READING_INK = (212, 212, 205)
AMBER = (239, 163, 72)

LEFT_MARGIN = 64


def load_hero_cover():
    """Scale the hero art to cover the canvas, keeping the Mad Cat on the right."""
    hero = Image.open(PLATES / "hero-art.png").convert("RGB")
    scale = HEIGHT / hero.height
    scaled_width = round(hero.width * scale)
    hero = hero.resize((scaled_width, HEIGHT), Image.Resampling.LANCZOS)
    # The mech is nearly as wide as the canvas, so the wordmark has to sit over its
    # left missile rack. Cut mostly from the left so the whole cockpit stays in view,
    # right of the text; darken_behind_text keeps the rack from fighting the letters.
    spare_width = scaled_width - WIDTH
    crop_left = round(spare_width * 0.62)
    return hero.crop((crop_left, 0, crop_left + WIDTH, HEIGHT))


def darken_behind_text(image):
    """Fade the left side to the page ground so the wordmark reads on any screen."""
    shade = Image.new("L", (WIDTH, HEIGHT))
    shade_pixels = shade.load()
    solid_end = 470
    fade_end = 720
    for x in range(WIDTH):
        if x < solid_end:
            opacity = 215
        elif x < fade_end:
            # Ease out from under the text towards the mech.
            progress = (x - solid_end) / (fade_end - solid_end)
            opacity = round(215 * (1 - progress) ** 1.6)
        else:
            opacity = 0
        for y in range(HEIGHT):
            shade_pixels[x, y] = opacity
    ground = Image.new("RGB", (WIDTH, HEIGHT), GROUND)
    return Image.composite(ground, image, shade)


def display_font(size, weight):
    font = ImageFont.truetype(str(FONTS / "Orbitron.ttf"), size)
    font.set_variation_by_axes([weight])
    return font


def draw_spaced(draw, position, text, font, fill, tracking):
    """Draw text with extra letter spacing (CSS letter-spacing), returning the end x."""
    x, y = position
    for character in text:
        draw.text((x, y), character, font=font, fill=fill)
        x += draw.textlength(character, font=font) + tracking
    return x - tracking


def draw_wordmark(image):
    draw = ImageDraw.Draw(image)
    title_font = display_font(92, 900)
    title_tracking = 92 * 0.01
    line_height = round(92 * 0.94)
    top = 150
    draw_spaced(draw, (LEFT_MARGIN, top), "CORE", title_font, TITLE_INK, title_tracking)
    critical_right = draw_spaced(
        draw, (LEFT_MARGIN, top + line_height), "CRITICAL", title_font, TITLE_INK, title_tracking
    )

    # The site sets "MW3" in Russo One stretched sideways after an amber rule that
    # fills the rest of the wordmark's width; copy that lockup.
    edition_font = ImageFont.truetype(str(FONTS / "RussoOne-Regular.ttf"), 78)
    edition_text = "MW3"
    edition_tracking = 78 * 0.07
    edition_stretch = 1.36
    edition_box = draw.textbbox((0, 0), edition_text, font=edition_font)
    natural_width = round(
        draw.textlength(edition_text, font=edition_font) + edition_tracking * len(edition_text)
    )
    edition_layer = Image.new("RGBA", (natural_width, edition_box[3] + 4), (0, 0, 0, 0))
    draw_spaced(
        ImageDraw.Draw(edition_layer), (0, 0), edition_text, edition_font, AMBER, edition_tracking
    )
    stretched_width = round(natural_width * edition_stretch)
    edition_layer = edition_layer.resize(
        (stretched_width, edition_layer.height), Image.Resampling.LANCZOS
    )
    edition_top = top + line_height * 2 + 6
    edition_left = round(critical_right) - stretched_width
    image.paste(edition_layer, (edition_left, edition_top), edition_layer)

    glyph_middle = edition_top + (edition_box[1] + edition_box[3]) / 2
    rule_height = 6
    rule_top = round(glyph_middle - rule_height / 2)
    draw.rectangle(
        (LEFT_MARGIN, rule_top, edition_left - 20, rule_top + rule_height - 1), fill=AMBER
    )

    tagline_font = ImageFont.truetype(str(FONTS / "Barlow-Regular.ttf"), 34)
    tagline_top = edition_top + edition_box[3] + 26
    draw_spaced(
        draw,
        (LEFT_MARGIN, tagline_top),
        "Original gameplay. A modern core.",
        tagline_font,
        READING_INK,
        34 * 0.03,
    )

    footer_font = ImageFont.truetype(str(FONTS / "Barlow-SemiBold.ttf"), 22)
    draw_spaced(
        draw, (LEFT_MARGIN, HEIGHT - 70), "CORECRITICAL.DEV", footer_font, AMBER, 22 * 0.16
    )


def main():
    image = darken_behind_text(load_hero_cover())
    draw_wordmark(image)
    # JPEG keeps it small: some apps (WhatsApp, iMessage) skip previews over ~300 KB.
    image.save(OUTPUT, quality=86, optimize=True, progressive=True)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
