#!/usr/bin/env python3
"""Generate the InstaLume launcher icon PNGs from SVG sources.

The launcher icon of the upstream client is Instagram artwork. InstaLume
ships its own icon instead, but only by *replacing image bytes at the same
resource paths* - the resource table, the adaptive-icon XML and every
resource ID stay untouched, so nothing else in the app has to change.

Outputs (written to tools/icons/, one file per entry that is replaced):

  ig_launcher_background.png   S x S   solid gradient layer (RGBA)
  ig_launcher_foreground.png   S x S   white "IL" monogram, transparent (RGBA)
  icon.png                     L x L   legacy (non-adaptive) icon: rounded
                                       gradient tile + monogram

Sizes are the exact pixel sizes of the files in the source APK:

  density     layer size   legacy icon size
  mdpi          108            48
  hdpi          162            72
  xhdpi         216            96
  xxhdpi        324           144
  xxxhdpi       432           192

Requires rsvg-convert (only for regeneration - the PNGs are committed, so
the release pipeline never needs an image tool).

Usage:
  python3 tools/gen_icons.py [output-dir]
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile

LAYERS = {  # density -> (layer size, legacy icon size)
    "mdpi": (108, 48),
    "hdpi": (162, 72),
    "xhdpi": (216, 96),
    "xxhdpi": (324, 144),
    "xxxhdpi": (432, 192),
}

GRADIENT_FROM = "#0B3CFF"   # InstaLume blue
GRADIENT_TO = "#22D3EE"     # InstaLume cyan


def background_svg(size):
    """Full-bleed diagonal gradient layer for the adaptive icon."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 108 108">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{GRADIENT_FROM}"/>
      <stop offset="1" stop-color="{GRADIENT_TO}"/>
    </linearGradient>
  </defs>
  <rect width="108" height="108" fill="url(#g)"/>
</svg>
"""


def monogram_paths():
    """White "IL" monogram, drawn inside the adaptive-icon safe zone.

    The adaptive-icon foreground safe zone is 66/108 of the canvas, i.e.
    x,y in [21, 87]; everything below stays inside it so no launcher can
    crop the mark.
    """
    return f"""
  <g fill="#FFFFFF">
    <!-- I: stem -->
    <rect x="36" y="32" width="10" height="44" rx="4"/>
    <!-- I: serifs -->
    <rect x="28" y="32" width="26" height="9" rx="4"/>
    <rect x="28" y="67" width="26" height="9" rx="4"/>
    <!-- L: stem + foot -->
    <rect x="62" y="32" width="10" height="44" rx="4"/>
    <rect x="62" y="67" width="24" height="9" rx="4"/>
  </g>
"""


def foreground_svg(size):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 108 108">{monogram_paths()}
</svg>
"""


def legacy_icon_svg(size):
    """Legacy (non-adaptive) icon: rounded gradient tile with the monogram."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 108 108">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{GRADIENT_FROM}"/>
      <stop offset="1" stop-color="{GRADIENT_TO}"/>
    </linearGradient>
    <clipPath id="tile"><rect width="108" height="108" rx="20" ry="20"/></clipPath>
  </defs>
  <g clip-path="url(#tile)">
    <rect width="108" height="108" fill="url(#g)"/>{monogram_paths()}
  </g>
</svg>
"""


def render(svg, size, out_path):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as fh:
        fh.write(svg)
        svg_path = fh.name
    try:
        subprocess.run(
            ["rsvg-convert", "-w", str(size), "-h", str(size), "-o", out_path, svg_path],
            check=True,
        )
    finally:
        os.unlink(svg_path)


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path}: not a PNG")
    return struct.unpack(">II", head[16:24])


def main():
    if not shutil.which("rsvg-convert"):
        raise SystemExit("rsvg-convert not found (icons are committed; regenerate only when needed)")
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "icons")
    os.makedirs(out_dir, exist_ok=True)

    for density, (layer, legacy) in LAYERS.items():
        bg = os.path.join(out_dir, f"{density}_ig_launcher_background.png")
        fg = os.path.join(out_dir, f"{density}_ig_launcher_foreground.png")
        icon = os.path.join(out_dir, f"{density}_icon.png")
        render(background_svg(layer), layer, bg)
        render(foreground_svg(layer), layer, fg)
        render(legacy_icon_svg(legacy), legacy, icon)
        for path, want in ((bg, layer), (fg, layer), (icon, legacy)):
            got = png_size(path)
            if got != (want, want):
                raise SystemExit(f"{path}: got {got}, want {want}x{want}")
            print(f"  {os.path.basename(path):<40} {got[0]}x{got[1]} {os.path.getsize(path)}B")
    print(f"wrote icon set to {out_dir}")


if __name__ == "__main__":
    main()
