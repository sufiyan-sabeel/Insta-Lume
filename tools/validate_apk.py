#!/usr/bin/env python3
"""Validate a rebuilt APK.

Checks performed:
  1. file exists and is non-empty
  2. ZIP integrity (testzip)
  3. required entries present (manifest, resources.arsc, dex, native libs)
  4. stale signature entries from the previous signing are gone
  5. entry set matches the source directory (optional, when a source dir is given)
  6. stored entries are aligned (resources.arsc -> 4, *.so -> 4096)
  7. manifest parses via aapt2 (when available): package, launchable activity, label
  8. signature verifies via apksigner (when available)
  9. SHA-256 and size recorded

Usage:
  python3 tools/validate_apk.py <apk> [<source-dir>]
"""
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import zipfile


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def aligned_data_offset(zf, info):
    """Offset of an entry's payload inside the archive."""
    with open(zf.filename, "rb") as fh:
        fh.seek(info.header_offset)
        head = fh.read(30)
        if len(head) != 30:
            raise ValueError("truncated local header")
        name_len, extra_len = struct.unpack("<HH", head[26:30])
        return info.header_offset + 30 + name_len + extra_len


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    apk = sys.argv[1]
    src = sys.argv[2] if len(sys.argv) > 2 else None
    errors = []

    if not os.path.isfile(apk):
        fail(f"APK not found: {apk}")
    size = os.path.getsize(apk)
    if size <= 0:
        fail("APK is empty")
    print(f"[ok] APK exists, {size} bytes ({size / (1024 * 1024):.1f} MiB)")

    sha = hashlib.sha256()
    with open(apk, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    sha256 = sha.hexdigest()
    print(f"[ok] SHA-256: {sha256}")

    with zipfile.ZipFile(apk) as zf:
        bad = zf.testzip()
        if bad is not None:
            fail(f"ZIP integrity: first bad entry {bad}")
        print("[ok] ZIP integrity (testzip)")

        names = zf.namelist()
        required = ["AndroidManifest.xml", "resources.arsc", "classes.dex",
                    "lib/arm64-v8a/libinstazen.so"]
        for r in required:
            if r not in names:
                errors.append(f"missing required entry: {r}")
        dex_count = sum(1 for n in names if n.startswith("classes") and n.endswith(".dex"))
        print(f"[ok] {len(names)} entries, {dex_count} dex files")

        stale = [n for n in names
                 if n == "META-INF/MANIFEST.MF" or n.startswith("META-INF/")
                 and n.endswith((".SF", ".RSA", ".DSA", ".EC"))]
        signed = any(n.startswith("META-INF/")
                     and n.endswith((".SF", ".RSA", ".DSA", ".EC")) for n in names)
        if signed:
            # apksigner's own v1 entries are expected on a signed artifact;
            # their validity is enforced by the apksigner verify below.
            if "META-INF/MANIFEST.MF" not in names:
                errors.append("signature entries present but META-INF/MANIFEST.MF missing")
            else:
                print("[ok] signed artifact (v1 entries present, verified below)")
        elif stale:
            errors.append("stale signature entries present: " + ", ".join(stale))
        else:
            print("[ok] no stale signature entries")

        # alignment of stored entries
        for info in zf.infolist():
            if info.compress_type != zipfile.ZIP_STORED:
                continue
            off = aligned_data_offset(zf, info)
            want = 0
            if info.filename == "resources.arsc":
                want = 4
            elif info.filename.startswith("lib/") and info.filename.endswith(".so"):
                want = 4096
            if want and off % want:
                errors.append(f"{info.filename} data at {off} not {want}-byte aligned")
        print("[ok] stored-entry alignment checked")

        if src:
            disk = set()
            for root, _, files in os.walk(src):
                for f in files:
                    disk.add(os.path.relpath(os.path.join(root, f), src).replace(os.sep, "/"))
            drop = {"META-INF/MANIFEST.MF", "META-INF/INDEX.LIST",
                    "META-INF/code_transparency_signed.jwt"}
            disk = {d for d in disk if d not in drop and not
                    (d.startswith("META-INF/") and d.endswith((".SF", ".RSA", ".DSA", ".EC")))}
            # apksigner adds v1 (JAR) entries when signing; they exist only in
            # the archive, so the same filter must be applied to BOTH sides.
            archive = {n for n in names if n not in drop and not
                       (n.startswith("META-INF/") and n.endswith((".SF", ".RSA", ".DSA", ".EC")))}
            missing = sorted(disk - archive)
            extra = sorted(archive - disk)
            if missing:
                errors.append(f"{len(missing)} file(s) from source not in APK: {missing[:5]}")
            if extra:
                errors.append(f"{len(extra)} unexpected entry(ies) in APK: {extra[:5]}")
            if not missing and not extra:
                print(f"[ok] APK entry set matches source ({len(disk)} files)")

    # aapt2: manifest / resources parse + badging
    aapt2 = shutil.which("aapt2")
    if aapt2:
        try:
            out = subprocess.run([aapt2, "dump", "badging", apk],
                                 capture_output=True, text=True, timeout=300)
            text = out.stdout
            if out.returncode != 0:
                errors.append("aapt2 dump badging failed: " + (out.stderr or "")[:400])
            else:
                pkg = next((l for l in text.splitlines() if l.startswith("package:")), "?")
                label = next((l for l in text.splitlines() if l.startswith("application-label:")), "?")
                launch = next((l for l in text.splitlines() if l.startswith("launchable-activity:")), "?")
                print(f"[ok] aapt2 parsed manifest: {pkg}")
                print(f"[ok] {label}")
                print(f"[ok] {launch}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"aapt2 validation error: {exc}")
    else:
        print("[skip] aapt2 not available")

    apksigner = shutil.which("apksigner")
    if apksigner and not signed:
        print("[skip] apksigner: unsigned artifact (signature is verified "
              "after the signing step instead)")
    elif apksigner:
        try:
            out = subprocess.run([apksigner, "verify", "--verbose", apk],
                                 capture_output=True, text=True, timeout=600)
            if out.returncode != 0:
                errors.append("apksigner verify failed: " + (out.stderr or out.stdout)[:400])
            else:
                lines = [l for l in out.stdout.splitlines() if "Verified using" in l or l.startswith("Verifies")]
                print("[ok] apksigner verify: " + ("; ".join(lines) or "passed"))
                if not any("Verified using v3 scheme" in l and l.rstrip().endswith("true")
                           for l in out.stdout.splitlines()):
                    errors.append("apksigner verify: v3 scheme not verified (required for minSdk 28)")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"apksigner validation error: {exc}")
    elif signed:
        errors.append("signed artifact but apksigner is not available to verify it")
    else:
        print("[skip] apksigner not available")

    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("\nVALIDATION PASSED")


if __name__ == "__main__":
    main()
