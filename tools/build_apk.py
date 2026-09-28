#!/usr/bin/env python3
"""Repack an extracted APK directory into a new, installable APK.

Rules applied (mirroring what aapt2/zipalign produce for a real APK):

* stale signature files from the previous APK are dropped
  (META-INF/MANIFEST.MF, *.SF, *.RSA, *.DSA, *.EC, INDEX.LIST)
* resources.arsc is stored (not deflated) and 4-byte aligned
* native libraries (lib/**/*.so) are deflated - exactly like the original
  source APK (they are extracted at install time: extractNativeLibs=true).
  Storing them uncompressed would additionally require surviving the
  apksigner zip rewrite with perfect 4096 alignment, which is fragile.
* everything else is deflated
* timestamps are fixed so builds are reproducible

Usage:
  python3 tools/build_apk.py <source-dir> <output.apk>
"""
import os
import struct
import sys
import zipfile

STORED_ARSC_ALIGN = 4

DROP_NAMES = {"META-INF/MANIFEST.MF", "META-INF/INDEX.LIST",
              "META-INF/code_transparency_signed.jwt"}
DROP_SUFFIXES = (".SF", ".RSA", ".DSA", ".EC")


def collect(src):
    entries = []
    for root, dirs, files in os.walk(src):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, src).replace(os.sep, "/")
            entries.append((rel, full))
    return entries


def sort_key(rel):
    """Android-friendly ordering: manifest, resources, libs, assets, res, rest."""
    if rel == "AndroidManifest.xml":
        return (0, rel)
    if rel == "resources.arsc":
        return (1, rel)
    if rel.startswith("lib/"):
        return (2, rel)
    if rel.startswith("assets/"):
        return (3, rel)
    if rel.startswith("res/"):
        return (4, rel)
    if rel.startswith("META-INF/"):
        return (5, rel)
    return (6, rel)


def align_extra(name_len, offset, align):
    """Extra field that pads a stored entry so its data starts aligned."""
    pad = (-(offset + 30 + name_len)) % align
    if pad == 0:
        return b""
    if pad < 4:            # an extra field needs at least an id + size
        pad += align
    return struct.pack("<HH", 0xD935, pad - 4) + b"\x00" * (pad - 4)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    if not os.path.isdir(src):
        raise SystemExit(f"not a directory: {src}")

    out_abs = os.path.abspath(out)
    entries = []
    dropped = []
    for rel, full in collect(src):
        if os.path.abspath(full) == out_abs:
            continue
        if rel in DROP_NAMES or rel.startswith("META-INF/") and rel.endswith(DROP_SUFFIXES):
            dropped.append(rel)
            continue
        entries.append((rel, full))

    entries.sort(key=lambda e: sort_key(e[0]))

    total = len(entries)
    print(f"packing {total} files from {src}")
    if dropped:
        print(f"dropping {len(dropped)} stale signature file(s): {', '.join(dropped)}")

    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with zipfile.ZipFile(out, "w") as zf:
        for i, (rel, full) in enumerate(entries, 1):
            with open(full, "rb") as fh:
                data = fh.read()

            stored = False
            align = 0
            if rel == "resources.arsc":
                stored, align = True, STORED_ARSC_ALIGN

            zi = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            zi.create_system = 3
            zi.external_attr = 0o644 << 16
            zi.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED

            if stored:
                pos = zf.fp.tell()
                zi.extra = align_extra(len(rel), pos, align)

            if stored:
                zf.writestr(zi, data, compress_type=zipfile.ZIP_STORED)
            else:
                zf.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

            if i % 500 == 0 or i == total:
                print(f"  {i}/{total}")

    size = os.path.getsize(out)
    print(f"wrote {out} ({size} bytes, {size / (1024 * 1024):.1f} MiB)")


if __name__ == "__main__":
    main()
