# InstaLume v1.1.0

InstaLume is a customized Instagram client experience with additional
user-focused features and customization.

**Created by Umaiz Sufiyan**

- GitHub: https://github.com/sufiyan-sabeel/Insta-Lume
- Instagram: https://www.instagram.com/umaizsufiyan.78/

## What's in this release

- **Version 1.1.0** — `versionName 1.1.0`, `versionCode 2000001000`.
  Monotonic versioning ensures clean upgrades over all previous builds
  (v1.0.0, v1.0.1, v1.0.2, v1.0.3, v1.0.4) without downgrade conflicts.
- **Full InstaLume Branding in Settings & App**:
  - Settings/About header properly displays **InstaLume** (split string
    brand patch for `Insta` + `Lume`).
  - Settings screen rebrand: *InstaLume Settings*, clean cards and theme styling.
  - Creator and About credits rebrand: *InstaLume (Tap to open)* / *Creator*
    pointing directly to `https://instagram.com/umaizsufiyan.78`.
  - Launcher label: *InstaLume*.
  - Launcher icon: InstaLume blue→cyan "IL" mark across all densities
    (adaptive background + foreground and legacy `icon.png`).
  - Crash toast: *InstaLume has crashed. Please share the crash log via Gmail.*
  - Upstream donation links (PayPal / UPI) neutralized and redirected.
- **Android 9–16 (API 28–36)**: ARM64-v8a architecture, validated AArch64 ELFs,
  deflated native libraries, and 4-byte aligned resources.
- **Reproducible CI Build**: downloaded from pinned SHA-256 source, patched,
  aligned, signed with the official InstaLume key, and validated via `apksigner`.

## Login / "outdated client" notice

This release does **not** claim to bypass Meta server-side login checks.
The base client is Instagram `438.0.0.28.88`, which is compiled into `classes.dex`.
All branding, packaging, signing, and local mod features are fully operational.

## Installation

1. Download `InstaLume-v1.1.0-arm64.apk` from this release.
2. Install on an Android device (arm64-v8a, Android 9+/API 28+). Allow
   installation from unknown sources when prompted.
3. Signed with the stable InstaLume release key, upgrading earlier
   *InstaLume* releases in place.

> The package name stays `com.instazen.android`. A device that currently
> runs the **original** InstaZen build (signed with a different key) must
> uninstall it first — Android will not upgrade across different signing
> keys.

## Limitations

- **Package name unchanged** (`com.instazen.android`): renaming it would
  break in-app features that bind to the original component names.
- **Internal identifiers, paths and file names** still carry upstream names
  (Dex2C symbols, `Downloads/InstaZen/`, preference keys, intent actions,
  JNI symbol `InstaZenPlus`). They are never shown to the user and
  renaming them would break the app.
- **Upstream attribution and functional endpoints are preserved**: the
  changelog/update/backup/emoji-font URLs, the upstream team credits and
  the original mod by SpoilerTech all remain credited.

> This is an unofficial build. It is not affiliated with, endorsed by or
> connected to Meta/Instagram. Use at your own risk and review the
> permissions you grant.
