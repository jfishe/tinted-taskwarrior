#!/usr/bin/env python3
"""Map "hex:RRGGBB" tokens in built themes to the nearest xterm-256 color.

Usage: quantize.py PATH [PATH ...]

Each PATH is a .theme file or a directory of them; files are rewritten in
place. Taskwarrior accepts at most 256 colors, so every token becomes the
closest (CIEDE2000) entry of the 6x6x6 cube ("rgbRGB") or the gray ramp
("grayN"), and the original hex values are kept in a trailing comment.

Cube entries 16-21 (rgb000-rgb005) are never chosen: tinted-shell redefines
those slots to extra scheme colors, so they would not show the expected color.

Also used as the tinty item hook (quantize.py %f): for schemes without a
prebuilt theme (schemes.extras, generated schemes) tinty renders the template
at apply time, leaving raw hex: tokens.

Standard library only.
"""

import math
import re
import sys
from functools import cache
from pathlib import Path

TOKEN = re.compile(r"hex:([0-9a-fA-F]{6})\b")
CUBE_LEVELS = (0, 95, 135, 175, 215, 255)
# xterm indices that tinted-shell reassigns (base09, base0F, base01..base06).
RESERVED = range(16, 22)

RGB = tuple[int, int, int]
Lab = tuple[float, float, float]


def _palette() -> list[tuple[str, int, RGB]]:
    """Return (name, xterm index, rgb) for every candidate color."""
    out = []
    for r in range(6):
        for g in range(6):
            for b in range(6):
                index = 16 + 36 * r + 6 * g + b
                if index in RESERVED:
                    continue
                rgb = (CUBE_LEVELS[r], CUBE_LEVELS[g], CUBE_LEVELS[b])
                out.append((f"rgb{r}{g}{b}", index, rgb))
    for n in range(24):
        v = 8 + 10 * n
        out.append((f"gray{n}", 232 + n, (v, v, v)))
    return out


def _srgb_to_linear(c: int) -> float:
    v = c / 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: RGB) -> Lab:
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    # sRGB -> XYZ (D65), normalised by the D65 white point.
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def ciede2000(lab1: Lab, lab2: Lab) -> float:
    """CIEDE2000 color difference (kL = kC = kH = 1)."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    c_bar = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = 0.5 * (1 - math.sqrt(c_bar**7 / (c_bar**7 + 25**7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if c1p else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if c2p else 0.0

    dLp = L2 - L1
    dCp = c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp / 2))

    Lp_bar = (L1 + L2) / 2
    Cp_bar = (c1p + c2p) / 2
    if c1p * c2p == 0:
        hp_bar = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hp_bar = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hp_bar = (h1p + h2p + 360) / 2
    else:
        hp_bar = (h1p + h2p - 360) / 2

    t = (
        1
        - 0.17 * math.cos(math.radians(hp_bar - 30))
        + 0.24 * math.cos(math.radians(2 * hp_bar))
        + 0.32 * math.cos(math.radians(3 * hp_bar + 6))
        - 0.20 * math.cos(math.radians(4 * hp_bar - 63))
    )
    d_theta = 30 * math.exp(-(((hp_bar - 275) / 25) ** 2))
    r_c = 2 * math.sqrt(Cp_bar**7 / (Cp_bar**7 + 25**7))
    s_l = 1 + 0.015 * (Lp_bar - 50) ** 2 / math.sqrt(20 + (Lp_bar - 50) ** 2)
    s_c = 1 + 0.045 * Cp_bar
    s_h = 1 + 0.015 * Cp_bar * t
    r_t = -math.sin(math.radians(2 * d_theta)) * r_c

    return math.sqrt(
        (dLp / s_l) ** 2
        + (dCp / s_c) ** 2
        + (dHp / s_h) ** 2
        + r_t * (dCp / s_c) * (dHp / s_h)
    )


PALETTE = [(name, index, rgb, rgb_to_lab(rgb)) for name, index, rgb in _palette()]


@cache
def nearest(hex_color: str) -> tuple[str, int]:
    """Return (taskwarrior color name, xterm index) closest to hex_color."""
    hex_color = hex_color.lstrip("#")
    rgb = (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    lab = rgb_to_lab(rgb)
    name, index, _, _ = min(PALETTE, key=lambda p: ciede2000(lab, p[3]))
    return name, index


def quantize_line(line: str) -> str:
    hexes = TOKEN.findall(line)
    if not hexes:
        return line
    body = TOKEN.sub(lambda m: nearest(m.group(1))[0], line)
    comment = " on ".join(f"#{h.lower()}" for h in hexes)
    return f"{body}  # {comment}"


def quantize_file(path: Path) -> None:
    lines = path.read_text().splitlines()
    new = [quantize_line(line) for line in lines]
    leftover = [i + 1 for i, line in enumerate(new) if "hex:" in line.split("#")[0]]
    if leftover:
        raise ValueError(f"{path}: malformed hex: token on line(s) {leftover}")
    path.write_text("\n".join(new) + "\n")


def iter_themes(paths: list[str]):
    for p in map(Path, paths):
        if p.is_dir():
            yield from sorted(p.glob("*.theme"))
        else:
            yield p


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    try:
        count = 0
        for path in iter_themes(argv):
            quantize_file(path)
            count += 1
    except (OSError, ValueError) as e:
        print(f"quantize.py: {e}", file=sys.stderr)
        return 1
    print(f"quantized {count} theme(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
