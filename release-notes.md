# InstaLume v1.0.0

InstaLume is a customized Instagram client experience with additional
user-focused features and customization.

**Created by Umaiz Sufiyan**

- GitHub: https://github.com/sufiyan-sabeel
- Instagram: https://www.instagram.com/umaizsufiyan.78

## What's in this release

- **Rebrand:** the app now presents as *InstaLume* (launcher label, crash
  toast and all visible in-app branding text).
- **Creator:** About/credits text updated for InstaLume; upstream author
  attribution is preserved.
- **PayPal & UPI removed:** every user-visible donation link, UPI ID and
  PayPal deep-link in the mod's Support/About screens was replaced with
  neutral, equal-length text; the donation config endpoint was repointed to
  an empty JSON so no payment details are fetched at runtime.
- **Same app underneath:** package name, version and all functional
  identifiers are untouched (see *Limitations*).

## Installation

1. Download `InstaLume-v1.0.0.apk` from this release.
2. Install it on an Android device (arm64-v8a). Allow installation from
   unknown sources when prompted.
3. Signing: released with the project's stable release key — updates with
   the same key install over existing installs.

> This is an unofficial build. It is not affiliated with, endorsed by or
> connected to Meta/Instagram. Use at your own risk and review the
> permissions you grant.

## Limitations

- **Package name unchanged** (`com.instazen.android`): renaming it would
  break in-app features that bind to the original component names.
- **Native library branding:** `libinstazen.so` addresses its string blob by
  fixed offsets, so only *equal-length* replacements are safe. Visible
  strings were reworded (`Lume Settings`, `Lume V8.5`, `InstaLume Tester`),
  but the short name **"Lume"** is used where the full name would not fit.
- **Instagram's own payment features** (in-app PayPal/UPI checkout offered
  by Instagram itself) are platform functionality and remain intact.
- **File paths and preferences** such as `Download/InstaZen`,
  `Pictures/InstaZen`, `instazen_prefs` and `instazen_saved_copies` keep
  their original names so existing data and downloads keep working.
- **Updater endpoints** for changelog/version checks still point at the
  upstream project; the donation endpoint does not.

## Attribution

- Base project: **InstaZen** by *SpoilerTech* (https://github.com/SpoilerTech)
  — used under its upstream license; all credit for the original
  modification work goes to the upstream author and testers.
- InstaLume rebrand, packaging and releases: **Umaiz Sufiyan**.

_(Build size, SHA-256, package, commit and build status are appended
automatically by the release workflow.)_
