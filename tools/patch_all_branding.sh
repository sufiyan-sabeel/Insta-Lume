#!/usr/bin/env bash
# Apply the complete InstaLume branding patch set to an extracted APK tree.
# Usage: tools/patch_all_branding.sh <extracted-apk-dir>
set -euo pipefail

W="${1:?usage: patch_all_branding.sh <extracted-apk-dir>}"
SO="$W/lib/arm64-v8a/libinstazen.so"

# 1. Launcher label (unique resources.arsc pool string)
python3 tools/patch_arsc_label.py "$W/resources.arsc" InstaZen InstaLume

# 2. Crash toast (dex string, equal length)
python3 tools/patch_dex_string.py "$W/classes21.dex" \
  'InstaZen has crashed. Please share the crash log via Gmail.' \
  'InstaLume has crashed. Please share the crash log via Gmail'

# 3. Links: whole-string, exact same length, content-based (unique in .so)
python3 tools/patch_so_strings.py "$SO" \
  --replace 'https://www.paypal.com/paypalme/SpoilerTech' \
            'http://github.com/sufiyan-sabeel/Insta-Lume' \
  --replace 'https://raw.githubusercontent.com/SpoilerTech/InstaZen/refs/heads/main/Donations.json' \
            'https://raw.githubusercontent.com/sufiyan-sabeel/Insta-Lume/main/Donations-empty.json'

# 4. Structural patches: growth allowed ONLY when the immediately following
#    string shrinks by the same amount, so every other offset stays identical.
#    patch_so_blob.py enforces count/order/total-length invariants.
python3 tools/patch_so_blob.py "$SO" \
  --replace 'InstaZen Settings' 'InstaLume Settings' --replace 'Contact Us' 'Reach out' \
  --replace 'Aman Ojha' 'Umaiz Sufiyan' --replace 'spoilertechuco@ybl' 'sufiyan-sabeel' \
  --replace 'InstaZen' 'InstaLume' --replace 'dd/MM hh:mm a' 'dd/MM hh:mma'

# 4b. Settings/About header: the brand name is stored as TWO separate strings
#     ('Insta' + 'Zen') that the screen joins, so the header still rendered
#     "InstaZen 1.0" after step 4 (which only rewrites the standalone
#     'InstaZen' used by the date label).  Make the second half read 'Lume';
#     the +1 byte is paid for by the section header that directly follows
#     'Zen' losing one byte - they are one contiguous run, so every other
#     offset stays identical (enforced by patch_so_blob.py).
python3 tools/patch_so_blob.py "$SO" \
  --replace 'Zen' 'Lume' \
  --replace 'APP CUSTOMIZATION' 'APP CUSTOMIZABLE'

# 5. Cosmetic swaps: strictly same length (padded where shorter) -> no movement.
python3 tools/patch_so_strings.py "$SO" --pad \
  --replace 'PayPal' 'GitHub' \
  --replace 'UPI ID' 'Handle' \
  --replace 'UPI ID copied! Open any UPI app to pay' 'Link copied! Open it in your browser.' \
  --replace 'spoilertechuco@ybl (Tap to copy)' 'sufiyan-sabeel (Tap to copy)' \
  --replace 'Cannot open PayPal' 'Cannot open link' \
  --replace 'UPI data not loaded' 'Nothing to show' \
  --replace 'PayPal ID Copied' 'Link copied!' \
  --replace 'PayPal link not loaded yet' 'Link not loaded yet' \
  --replace 'UPI Payment' 'Payment' \
  --replace 'com.paypal.android.p2pmobile' 'com.instalume.disabled.shell' \
  --replace 'InstaZen Testers' 'InstaLume Tester' \
  --replace 'InstaZen V8.5' 'InstaLume 1.0' \
  --replace ' V8.5' ' 1.0 ' \
  --replace 'Your support helps us keep InstaZen free & updated!' 'Your support helps keep InstaLume free & updated!'

# 6. About credit line (string stores a supplementary emoji as CESU-8 surrogate
#    pairs, so it is patched byte-wise rather than through argv).
python3 - "$SO" <<'PY'
import sys
path = sys.argv[1]
buf = bytearray(open(path, 'rb').read())
old = b'Developed with \xed\xa0\xbe\xed\xb9\xb5 by Aman Ojha'   # 34 bytes
new = b'Developed by Umaiz Sufiyan'
assert len(old) == 34, len(old)
assert len(new) <= len(old)
new = new + b' ' * (len(old) - len(new))
assert len(new) == len(old)
# whole-string (NUL bounded) match only
needle = b'\x00' + old + b'\x00'
hits = []
st = 0
while True:
    i = buf.find(needle, st)
    if i < 0:
        break
    hits.append(i + 1)
    st = i + 1
assert len(hits) == 1, [hex(h) for h in hits]
buf[hits[0]:hits[0] + len(old)] = new
open(path, 'wb').write(bytes(buf))
print(f"  {old!r} -> {new!r} at 0x{hits[0]:x}")
PY

# 7. Code-transparency JWT was signed over the ORIGINAL app content and no
#    longer matches this build (never required for installation).
rm -f "$W/META-INF/code_transparency_signed.jwt"

echo "branding patches applied to $W"
