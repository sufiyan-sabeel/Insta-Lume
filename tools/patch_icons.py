#!/usr/bin/env python3
"""Replace the launcher icon images in an extracted APK tree with InstaLume art.

Only image *bytes* are replaced; every path, resource ID, the adaptive-icon
XML and resources.arsc stay untouched, so nothing else in the app can break.

Files replaced (all densities):

  res/mipmap-<density>/ig_launcher_background.png   adaptive-icon background
  res/mipmap-<density>/ig_launcher_foreground.png   adaptive-icon foreground
  res/mipmap-<density>/icon.png                     legacy (non-adaptive) icon

The replacement PNG must have exactly the same pixel dimensions as the file
it replaces - that is asserted here, so a wrong asset fails the build instead
of producing a stretched icon.

Usage:
  python3 tools/patch_icons.py <extracted-apk-dir> [<icons-dir>]
"""
import os
import struct
import sys

DENSITIES = {          # density -> (layer size, legacy icon size)
    "mdpi": (108, 48),
    "hdpi": (162, 72),
    "xhdpi": (216, 96),
    "xxhdpi": (324, 144),
    "xxxhdpi": (432, 192),
}


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path}: not a PNG")
    return struct.unpack(">II", head[16:24])


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    tree = sys.argv[1]
    icons = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "icons")

    replaced = 0
    for density, (layer, legacy) in DENSITIES.items():
        targets = (
            (f"ig_launcher_background.png", layer),
            (f"ig_launcher_foreground.png", layer),
            (f"icon.png", legacy),
        )
        for name, size in targets:
            rel = f"res/mipmap-{density}/{name}"
            dst = os.path.join(tree, rel)
            src = os.path.join(icons, f"{density}_{name}")
            if not os.path.isfile(dst):
                raise SystemExit(f"missing launcher icon entry: {rel} (source APK layout changed)")
            if not os.path.isfile(src):
                raise SystemExit(f"missing InstaLume asset: {src} (run tools/gen_icons.py)")
            old_size = png_size(dst)
            new_size = png_size(src)
            if old_size != (size, size):
                raise SystemExit(f"{rel}: source icon is {old_size}, expected {size}x{size}")
            if new_size != old_size:
                raise SystemExit(f"{rel}: asset is {new_size}, source is {old_size}")
            with open(src, "rb") as fh:
                data = fh.read()
            with open(dst, "wb") as fh:
                fh.write(data)
            replaced += 1
            print(f"  {rel:<52} {old_size[0]}x{old_size[1]} -> {len(data)}B")

    if replaced != 15:
        raise SystemExit(f"expected 15 icon files, replaced {replaced}")
    print(f"replaced {replaced} launcher icon files with InstaLume artwork")


if __name__ == "__main__":
    main()
