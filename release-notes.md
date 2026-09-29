# InstaLume v1.0.2

InstaLume is a customized Instagram client experience with additional
user-focused features and customization.

**Created by Umaiz Sufiyan**

- GitHub: https://github.com/sufiyan-sabeel/Insta-Lume
- Instagram: https://www.instagram.com/umaizsufiyan.78/

## What's in this release

- **Version 1.0.2** — `versionName 1.0.2`, `versionCode 2000000002`.
  The versionCode series was raised because v1.0.3/v1.0.4 already shipped
  as `1000000003`/`1000000004`; `2000000002` is strictly higher than all
  of them, so 1.0.2 installs as a normal **upgrade** instead of failing
  with `INSTALL_FAILED_VERSION_DOWNGRADE`.
- **New launcher icon** — InstaLume's own blue→cyan "IL" mark replaces the
  Instagram artwork at all five densities (adaptive background + foreground
  *and* the legacy `icon.png`). Image bytes are swapped in place, so every
  resource ID, the adaptive-icon XML and `resources.arsc` are untouched.
- **About/credits rebranded** — the creator credit row now reads
  *InstaLume (Tap to open)* / *Creator* and opens
  `https://instagram.com/umaizsufiyan.78`.
- **Carried over from earlier releases** — launcher label *InstaLume*,
  *InstaLume Settings* header, About screens, crash toast, donation
  links neutralised, and all structural patches that keep `libinstazen.so`
  byte-identical in size and layout.

## Login / "outdated client" — what we verified

This release does **not** claim to restore login, and nothing here spoofs
a client version, bypasses authentication or fakes a successful login.
What was actually checked:

- The client is **Instagram `438.0.0.28.88`** (released July 2026).
  Instagram's current Android build is **`449.0.0.48.84`** (29 Sep 2026),
  so the base is roughly eleven releases behind.
- The version Instagram's servers are told is a **compile-time constant
  inside `classes.dex`** — the literal `438.0.0.28.88` sits in the dex
  string pool. It is *not* read from `AndroidManifest.xml`.
  Consequences, both verified rather than assumed:
  - the manifest `versionName` in this release (`1.0.2`) is the *app's*
    display version only, and we do **not** claim it changes what
    Instagram's backend sees;
  - the client's reported version can only be raised by rebuilding against
    a newer Instagram build.
- **No authorized newer upstream exists to update from.** Checked:
  `SpoilerTech/InstaZen` contains six runtime JSON files and *no* source
  and *no* APK assets in its releases; no InstaZen source tree exists on
  this machine; upstream's newest changelog entry (`v8.50`, 2 Sep 2026)
  matches the base already in use (`V8.5`). Meta publishes no source and
  no authorized third-party build of Instagram.

So the blocker is **not** a patchable defect in InstaLume: an outdated,
closed-source client is being rejected server-side, and there is no
legitimate source to update it from. Fixing login for real requires a
current Instagram build distributed by Meta.

## Build verification

Runs in CI and **fails the job** on any error:

- source APK downloaded and checked against a pinned SHA-256
- branding/icon patches applied and their structural invariants checked
  (`.so` file size, string count/order and `.data` byte length unchanged)
- `zipalign -f -p 4` + `zipalign -c -p 4`
- `tools/validate_apk.py`: ZIP integrity, entry set, arsc alignment,
  `aapt2` parse, `apksigner` verification
- assertions on package name, label, versionName, versionCode, minSdk,
  targetSdk and arm64-v8a-only ABI, with every native library checked to
  be a complete AArch64 ELF
- signed with the InstaLume release key, then re-verified
  (`apksigner verify`, v2 for API 24–27 and v3 for API 28+)

## Installation

1. Download `InstaLume-v1.0.2-arm64.apk` from this release.
2. Install on an Android device (arm64-v8a, Android 9+/API 28+). Allow
   installation from unknown sources when prompted.
3. Signed with the stable InstaLume release key, so it upgrades earlier
   *InstaLume* releases in place.

> The package name stays `com.instazen.android`. A device that currently
> runs the **original** InstaZen build (signed with a different key) must
> uninstall it first — Android will not upgrade across different signing
> keys.

## Limitations

- **Login is not fixed and is not claimed to work.** See above.
- **Package name unchanged** (`com.instazen.android`): renaming it would
  break in-app features that bind to the original component names.
- **Internal identifiers, paths and file names** still carry upstream names
  (Dex2C symbols, `Downloads/InstaZen/`, preference keys, intent actions,
  JNI symbol `InstaZenPlus`). They are never shown to the user and
  renaming them would break the app — including downloads and backups that
  existing users already have on disk.
- **Upstream attribution and functional endpoints are preserved**: the
  changelog/update/backup/emoji-font URLs, the upstream team credits and
  the original mod by SpoilerTech all remain credited.

> This is an unofficial build. It is not affiliated with, endorsed by or
> connected to Meta/Instagram. Use at your own risk and review the
> permissions you grant.
