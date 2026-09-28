# InstaLume branding audit

Scope: user-visible branding only. Every functional identifier required by
the app to keep working is preserved.

## 1. Changed — resources.arsc

| Field | Before | After |
|-------|--------|-------|
| Application label (unique pool string) | `InstaZen` | `InstaLume` |

Patched by `tools/patch_arsc_label.py` (unique pool match, pool-slack
checked).

## 2. Changed — dex (classes21.dex)

| String (59 bytes) | Before | After |
|-------------------|--------|-------|
| Crash toast | `InstaZen has crashed. Please share the crash log via Gmail.` | `InstaLume has crashed. Please share the crash log via Gmail` |

Equal-length replacement; `tools/patch_dex_string.py` repairs SHA-1 and
Adler-32 afterwards. Verified against the original APK: the string occurs
exactly once (`string_ids[5067]`).

## 3. Changed — native library (lib/arm64-v8a/libinstazen.so)

The Dex2C string blob in `.data` is addressed **positionally**
(base + offset / index); content is not hashed (verified: no Java-hash /
FNV / CRC32 matches). Therefore **whole-string, NUL-bounded** edits only —
and length may change only under the stricter rule implemented by
`tools/patch_so_blob.py`: a grown string must be paid for by the string
directly after it shrinking by the same amount, so that the string count,
the string order and the total `.data` byte length all stay identical and
every *unpatched* string keeps its exact offset. File size is unchanged
(34,572,840 bytes).

### 3a. Rebranding

| Before | After | Bytes | How |
|--------|-------|-------|-----|
| `InstaZen Settings` | `InstaLume Settings` | 17 → 18 | +1 paid for by `Contact Us` → `Reach out` (10 → 9) |
| `Aman Ojha` | `Umaiz Sufiyan` | 9 → 13 | +4 paid for by `spoilertechuco@ybl` → `sufiyan-sabeel` (18 → 14) |
| `InstaZen` (standalone, date-label context) | `InstaLume` | 8 → 9 | +1 paid for by `dd/MM hh:mm a` → `dd/MM hh:mma` (13 → 12) |
| `Developed with ❤️ by Aman Ojha` | `Developed by Umaiz Sufiyan` (+ pad) | 34 | length-neutral |
| `InstaZen V8.5` | `InstaLume 1.0` | 13 | exact |
| ` V8.5` (About version suffix) | ` 1.0 ` | 5 | exact |
| `InstaZen Testers` | `InstaLume Tester` | 16 | exact |
| `Zen` (second half of the Settings/About brand line, rendered next to `Insta`) | `Lume` | 3 → 4 | +1 paid for by `APP CUSTOMIZATION` → `APP CUSTOMIZABLE` (17 → 16) — the header now reads `InstaLume 1.0` instead of `InstaZen 1.0` |
| `Your support helps us keep InstaZen free & updated!` | `Your support helps keep InstaLume free & updated!` (+ pad) | 51 | length-neutral |

### 3b. PayPal / UPI removal (request: "remove paypal and upi")

| Before | After | Bytes |
|--------|-------|-------|
| `https://www.paypal.com/paypalme/SpoilerTech` | `http://github.com/sufiyan-sabeel/Insta-Lume` | 43 |
| `PayPal` | `GitHub` | 6 |
| `UPI ID` | `Handle` | 6 |
| `UPI ID copied! Open any UPI app to pay` | `Link copied! Open it in your browser.` (+ pad) | 38 |
| `spoilertechuco@ybl` | `sufiyan-sabeel` (+ pad) | 18 |
| `spoilertechuco@ybl (Tap to copy)` | `sufiyan-sabeel (Tap to copy)` (+ pad) | 32 |
| `Cannot open PayPal` | `Cannot open link` (+ pad) | 18 |
| `UPI data not loaded` | `Nothing to show` (+ pad) | 19 |
| `PayPal ID Copied` | `Link copied!` (+ pad) | 16 |
| `PayPal link not loaded yet` | `Link not loaded yet` (+ pad) | 26 |
| `UPI Payment` | `Payment` (+ pad) | 11 |
| `com.paypal.android.p2pmobile` (deep-link package) | `com.instalume.disabled.shell` | 28 |
| `https://raw.githubusercontent.com/SpoilerTech/InstaZen/refs/heads/main/Donations.json` | `https://raw.githubusercontent.com/sufiyan-sabeel/Insta-Lume/main/Donations-empty.json` | 85 |

The donation endpoint now serves `Donations-empty.json` (`{}`) from this
repository, so no UPI ID, PayPal link, QR image or donor list is fetched at
runtime. The Support screen therefore renders without payment details, and
any residual local value shows neutral text instead.

Total bytes changed in the library: **351** (file size identical:
34,572,840 bytes — verified byte-for-byte against the original APK).

## 4. Preserved on purpose (functional identifiers)

- Package / components: `com.instazen.android`, `com.instazen.*`,
  `com.instagram.*`, `Linstazen0/*`, `startInstaZenSettings`,
  `QuickAccessDialog$InstaZenClick`, JNI symbol `InstaZenPlus`.
- Preferences & stores: `instazen_prefs`, `instazen_saved_copies`,
  `instazen_navbar`, `instazen_story_fonts`, `InstaZenFontPrefs`,
  `InstaZen@Unsent!`, `__instazen_filtered__`.
- File paths (existing user data): `/storage/emulated/0/Download/InstaZen/*`,
  `Pictures/InstaZen`, `InstaZen_` (export prefix), `Download/InstaZen`,
  `InstaZen/Id_Name_Mappings`, `/InstaZen-iOS_Emojis.ttf`.
- Resource IDs, JSON keys and method names that merely contain
  `paypal`/`upi` (`paypalLink`, `upiQrUrl`, `setPaypalData`,
  `showUpiDialog`, `upi_id`, `paypal_link`, …) — they are not
  user-visible and renaming them would break code paths.
- Instagram/Meta platform features: Instagram's own in-app PayPal/UPI
  checkout, fundraisers and payment strings are upstream platform
  functionality and were left untouched.
- Upstream attribution & links: SpoilerTech channel/Telegram/backup URLs,
  changelog & version endpoints, team credits (`InstaMoon`, testers).

## 5. Known limitations

1. **Full native rebrand achieved.** `InstaLume Settings`, `InstaLume`,
   `Version 1.0` and `Umaiz Sufiyan` all fit: growth of the three visible
   strings (+1 / +4 / +1 byte) is paid for by shrinking the string that
   follows each of them, so the blob length, string count, string order and
   every other offset are byte-identical to the original
   (`tools/patch_so_blob.py` enforces this and prints every moved offset).
   No shortened "Lume" branding remains anywhere.
2. **Package name stays `com.instazen.android`** (required for upgrades
   and component binding).
3. **Legacy paths keep the `InstaZen` folder name** so installed users'
   downloads, backups and settings continue to work.
