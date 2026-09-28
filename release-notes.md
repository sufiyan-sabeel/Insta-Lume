# InstaLume v1.0.1

InstaLume is a customized Instagram client experience with additional
user-focused features and customization.

**Created by Umaiz Sufiyan**

- GitHub: https://github.com/sufiyan-sabeel/Insta-Lume
- Instagram: https://instagram.com/umaizsufiyan.78

## What's in this release

- **Complete visible rebrand:** Settings header now reads
  *InstaLume Settings*, the About/credits screens show *InstaLume*,
  *Version 1.0* and *Created by Umaiz Sufiyan* — no user-visible
  *InstaZen* / *Aman Ojha* text remains.
- **Settings redesign:** light background, dark text, rounded cards and a
  professional blue/cyan accent; follows the system light/dark theme.
- **Links:** About links open the InstaLume GitHub repository and the
  creator's Instagram profile.
- **Android 8–16 (API 26–36):** minSdk 28, targetSdk 36, compileSdk 37;
  `exported` flags, `PendingIntent` mutability, notification permission
  and foreground-service types audited — build, installation and runtime
  compatibility separated and documented in `docs/`.
- **Native branding patched safely:** `libinstazen.so` grows only where an
  adjacent string shrinks by the same amount, so every other offset in the
  string blob stays byte-identical (`tools/patch_so_blob.py`).
- **Pipeline:** CLEAN → BUILD → ZIPALIGN → SIGN → VERIFY runs in GitHub
  Actions; the job fails if signing or `apksigner verify` fails.

## Installation

1. Download `InstaLume-v1.0.1.apk` from this release.
2. Install it on an Android device (arm64-v8a). Allow installation from
   unknown sources when prompted.
3. Signed with the stable InstaLume release key — updates with the same
   key install over existing installs.

> This is an unofficial build. It is not affiliated with, endorsed by or
> connected to Meta/Instagram. Use at your own risk and review the
> permissions you grant.

## Limitations

- **Package name unchanged** (`com.instazen.android`): renaming it would
  break in-app features that bind to the original component names.
- **Internal identifiers, paths and file names** still carry the original
  upstream names (Dex2C symbol names, `Downloads/InstaZen/`, preference
  keys, intent actions). They are never shown to the user; renaming them
  would break the app.
- Upstream attribution and licensing are preserved: this is a rebrand of
  the *InstaZen* mod by SpoilerTech — full credit for the original work.
