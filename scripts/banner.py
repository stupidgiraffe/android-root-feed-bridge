#!/usr/bin/env python3
"""Render the Root Feed Bridge's GitHub-hosted 2:1 MMRL banner.

This is a deterministic image asset, not an application dependency.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 1280, 625
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "root-feed-banner.jpg"
SEED = 310283


def bounded(x: float) -> int:
    return max(0, min(255, round(x)))


def polygon(draw, coords, color, outline=None, width=1):
    draw.polygon(coords, fill=color)
    if outline:
        draw.line(list(coords) + [coords[0]], fill=outline, width=width, joint="curve")


def main():
    rng = random.Random(SEED)
    img = Image.new("RGB", (WIDTH, HEIGHT), (3, 10, 23))
    p = img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dist = ((x - WIDTH * .51) ** 2 / (WIDTH * .58) ** 2 +
                    (y - HEIGHT * .46) ** 2 / (HEIGHT * .64) ** 2)
            central = math.exp(-dist * 2.9)
            teal = math.exp(-((x - 360) / 720) ** 2 - ((y - 420) / 540) ** 2)
            indigo = math.exp(-((x - 1030) / 550) ** 2 - ((y - 270) / 510) ** 2)
            grain = rng.randrange(-3, 4)
            p[x, y] = (
                bounded(5 + 9 * central + 6 * indigo + grain),
                bounded(11 + 19 * central + 14 * teal + grain),
                bounded(27 + 31 * central + 21 * indigo + grain),
            )

    # The large soft halo gives the modular core depth without flattening it.
    bloom = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom, "RGBA")
    for r in range(270, 10, -6):
        strength = int((1 - r / 280) * 5 + 1)
        bd.ellipse((650 - r * 1.1, 269 - r * .73,
                    650 + r * 1.1, 269 + r * .73),
                   fill=(20, 210, 240, strength))
    img = Image.alpha_composite(img.convert("RGBA"), bloom.filter(ImageFilter.GaussianBlur(27)))

    # Perspective grid, tracks, and flecks of light.
    bg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(bg, "RGBA")
    for i in range(30):
        shift = (i - 15) * 105
        d.line([(630, 380), (630 + shift, HEIGHT)], fill=(29, 132, 178, 29), width=1)
    for y in range(415, HEIGHT, 25):
        d.line([(0, y), (WIDTH, y)], fill=(15, 132, 154, 24), width=1)
    for _ in range(125):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        strength = rng.randrange(15, 78)
        d.ellipse([x, y, x + 1.5, y + 1.5], fill=(76, 211, 242, strength))
    img = Image.alpha_composite(img, bg)

    # Energy waves crossing behind the central cube.
    wave = Image.new("RGBA", img.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(wave, "RGBA")
    for track in range(9):
        yy = 275 + track * 13
        pts = [
            (x, yy + math.sin(x * .013 + track * .14) * (41 + track * 2)
             + (x - WIDTH / 2) ** 2 / 7500 * math.sin(track + .3))
            for x in range(-15, WIDTH + 25, 6)
        ]
        tone = (40, 236, 243, 150) if track % 3 else (158, 69, 249, 133)
        wd.line(pts, fill=tone, width=2, joint="curve")
    img = Image.alpha_composite(img, wave.filter(ImageFilter.GaussianBlur(15)))
    img = Image.alpha_composite(img, wave)

    # Embossed motherboard platforms in the foreground.
    platform = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(platform, "RGBA")
    for i in range(26):
        x = rng.randrange(-80, WIDTH + 10)
        y = rng.randrange(390, HEIGHT + 60)
        size = rng.randrange(70, 210)
        corners = [(x - size, y), (x - size * .32, y - 36),
                   (x + size * .87, y - 25), (x + size * .22, y + 22)]
        polygon(pd, corners, (11, 22, 39, 160), (65, 111, 140, 52), 2)
    for _ in range(90):
        x, y = rng.randrange(WIDTH), rng.randrange(420, HEIGHT)
        dx, dy = rng.randrange(15, 135), rng.choice((-28, 0, 28))
        col = (26, 236, 242, rng.randrange(30, 120))
        pd.line([(x, y), (x + dx * .45, y + dy),
                 (x + dx, y + dy)], fill=col, width=rng.choice([1, 2]))
        pd.ellipse((x + dx - 2, y + dy - 2, x + dx + 2, y + dy + 2), fill=col)
    img = Image.alpha_composite(img, platform)

    # A floating isometric cube: metallic shell, luminous inner chamber,
    # and negative space in its front faces.
    cube = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(cube, "RGBA")
    cx, cy, rx, ry = 635, 275, 185, 109
    top = [(cx, cy - ry - 100), (cx + rx, cy - ry),
           (cx, cy - 15), (cx - rx, cy - ry)]
    left = [(cx - rx, cy - ry), (cx, cy - 15),
            (cx, cy + ry + 105), (cx - rx, cy + 16)]
    right = [(cx, cy - 15), (cx + rx, cy - ry),
             (cx + rx, cy + 16), (cx, cy + ry + 105)]
    polygon(cd, top, (44, 57, 79, 253), (112, 170, 193, 230), 4)
    polygon(cd, left, (18, 30, 51, 245), (28, 227, 230, 233), 4)
    polygon(cd, right, (27, 37, 63, 248), (124, 118, 244, 206), 4)
    # Hollow windows convey modularity.
    polygon(cd, [(cx - 152, cy - 64), (cx - 21, cy + 7),
                 (cx - 21, cy + 168), (cx - 152, cy + 91)],
            (3, 33, 54, 242), (47, 242, 243, 240), 5)
    polygon(cd, [(cx + 21, cy + 7), (cx + 152, cy - 64),
                 (cx + 152, cy + 91), (cx + 21, cy + 168)],
            (4, 34, 64, 239), (59, 222, 246, 232), 5)
    polygon(cd, [(cx - 125, cy - ry - 7), (cx, cy - ry - 80),
                 (cx + 125, cy - ry - 7), (cx, cy - 38)],
            (10, 36, 65, 250), (50, 238, 250, 235), 5)
    # Glowing inner power core, with extruded 3D faces.
    polygon(cd, [(cx, cy - 48), (cx + 75, cy - 10),
                 (cx, cy + 30), (cx - 75, cy - 10)],
            (31, 235, 251, 195), (144, 255, 254, 235), 3)
    polygon(cd, [(cx - 75, cy - 10), (cx, cy + 30),
                 (cx, cy + 119), (cx - 75, cy + 77)],
            (9, 138, 206, 200), (109, 251, 247, 235), 3)
    polygon(cd, [(cx, cy + 30), (cx + 75, cy - 10),
                 (cx + 75, cy + 77), (cx, cy + 119)],
            (29, 225, 226, 205), (114, 255, 250, 245), 3)
    # Glossy segmented cube corners.
    for x, y in [(cx-rx, cy-ry), (cx+rx, cy-ry),
                 (cx-rx, cy+16), (cx+rx, cy+16)]:
        cd.line([(x-7, y-7), (x+9, y+9)], fill=(187, 241, 246, 200), width=3)
    img = Image.alpha_composite(img, cube.filter(ImageFilter.GaussianBlur(16)))
    img = Image.alpha_composite(img, cube)

    # The levitating pedestal and underglow.
    podium = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pod = ImageDraw.Draw(podium, "RGBA")
    polygon(pod, [(455, 496), (630, 452), (840, 490), (653, 552)],
            (26, 41, 66, 243), (61, 234, 242, 236), 5)
    polygon(pod, [(455, 496), (653, 552), (653, 565), (455, 510)],
            (19, 34, 54, 245), (62, 160, 218, 105), 2)
    polygon(pod, [(653, 552), (840, 490), (840, 505), (653, 565)],
            (14, 30, 55, 249), (96, 108, 240, 112), 2)
    pod.ellipse((589, 463, 707, 505), fill=(44, 250, 246, 127))
    img = Image.alpha_composite(img, podium.filter(ImageFilter.GaussianBlur(17)))
    img = Image.alpha_composite(img, podium)

    # Dark vignette keeps the art legible inside the MMRL card.
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")
    for n in range(80):
        a = round(2.0 * (n / 80))
        od.rectangle((n, n, WIDTH - n, HEIGHT - n), outline=(0, 0, 6, a), width=2)
    img = Image.alpha_composite(img, overlay).convert("RGB")

    # Quiet, legible project identity in the safe bottom-left edge.
    logo = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 43)
        subtitle_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    logo.line([(44, 485), (166, 485)], fill=(45, 221, 240), width=3)
    logo.text((43, 507), "ROOTATLAS", font=title_font,
              fill=(211, 250, 255), stroke_width=1, stroke_fill=(4, 32, 47))
    logo.text((45, 569), "FEDERATED ANDROID ROOT MODULES",
              font=subtitle_font, fill=(113, 209, 232))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT, format="JPEG", quality=85, optimize=True, progressive=True,
             subsampling=0)
    print(f"Banner: {OUTPUT}, {WIDTH}x{HEIGHT}, {OUTPUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
