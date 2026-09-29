# InstaLume

**InstaLume is a customized Instagram client experience with additional
user-focused features and customization.**

Created by **Umaiz Sufiyan**

- GitHub: https://github.com/sufiyan-sabeel
- Instagram: https://www.instagram.com/umaizsufiyan.78

Version: **1.0.2** · base `438.0.0.28.88` · package `com.instazen.android`

> Unofficial build. Not affiliated with, endorsed by or connected to
> Meta/Instagram. InstaLume is a rebrand of the *InstaZen* mod by
> SpoilerTech — full credit for the original work.

---

## Login status (read this first)

**Login through this client is not currently working, and this repository
does not pretend otherwise.** No client version is spoofed, no
authentication path is bypassed and no login result is faked.

What was verified, not assumed:

| Fact | Evidence |
|------|----------|
| Base client is Instagram `438.0.0.28.88` (July 2026) | `versionName` in the source APK |
| Current Instagram is `449.0.0.48.84` (Sep 2026) | public release listings |
| The version sent to Instagram is a constant compiled into `classes.dex` | literal `438.0.0.28.88` found in the dex string pool |
| Therefore the manifest `versionName` cannot affect backend compatibility | it is never read to build the client's reported version |
| No authorized newer upstream exists | `SpoilerTech/InstaZen` holds six JSON files, no source, no APK assets; no InstaZen source tree exists locally; upstream's newest changelog (`v8.50`) matches the base already used |

Instagram is closed source and Meta distributes no authorized build for
third parties to rebrand, so an outdated base can only be fixed by moving
to a current Instagram build — which this project cannot obtain
legitimately. Everything else (branding, packaging, signing, integrity)
is built and verified normally.

---

## Releases

Releases are **built, signed and verified entirely by GitHub Actions** —
no APK is committed to this repository.

| Step | What happens |
|------|--------------|
| 1 | Download the unmodified original APK (SHA-256 pinned) |
| 2 | Apply InstaLume branding patches (content-based, length-safe) |
| 3 | Rebuild the APK (preserves `resources.arsc` / `.so` alignment) |
| 4 | Sign with the release key stored in Actions secrets |
| 5 | Verify the signature (`apksigner verify`) — the job **fails** if signing or verification fails |
| 6 | Publish **only the signed APK** to the GitHub Release |

The original (unmodified) source APK is attached to the [`source`
release](../../releases/tag/source) and is what CI downloads. To use a
different mirror, set the repository variable `SOURCE_APK_URL` **and**
update `SOURCE_APK_SHA256` in `.github/workflows/release.yml`.

### Cutting a release

```bash
git tag v1.0.2
git push origin v1.0.2
```

The workflow run ends with a release containing `InstaLume-v1.0.2-arm64.apk`,
its SHA-256, size, package name and build status in the notes.

`versionCode` is derived from the tag by
`2000000000 + (MAJOR-1)*1000000 + MINOR*1000 + PATCH`, so it always stays
strictly above every previously published build (`1000000004` was the
highest before this scheme) and an older-looking tag such as `v1.0.2`
still installs as an upgrade instead of failing with
`INSTALL_FAILED_VERSION_DOWNGRADE`.

---

## Repository layout

```
.github/workflows/release.yml   CI: build → sign → verify → release
tools/                          patchers, packer, validator (Python, stdlib only)
tools/icons/                    InstaLume launcher icon PNGs (all densities)
tools/gen_icons.py              regenerates tools/icons/ from SVG (needs rsvg-convert)
tools/patch_icons.py            swaps the launcher icon bytes into the APK tree
docs/branding-audit.md          full audit: what changed, what's preserved
release-notes.md                release notes template (workflow appends build info)
Donations-empty.json            empty donation config (neutralises upstream donation fetch)
signing/                        LOCAL ONLY — release keystore, never committed
InstaZen_*/ , dist/ , *.apk     LOCAL ONLY — extracted tree & outputs, never committed
```

## Security & signing

The release key never touches the repository. GitHub Actions uses four
**secrets** (names only — values are stored in the repository settings and
are never printed by the workflow):

| Secret name | Contents |
|-------------|----------|
| `INSTA_LUME_KEYSTORE_BASE64` | base64-encoded release keystore |
| `INSTA_LUME_KEYSTORE_PASSWORD` | keystore password |
| `INSTA_LUME_KEY_ALIAS` | key alias |
| `INSTA_LUME_KEY_PASSWORD` | key password |

- The keystore lives only in `signing/` locally, which `.gitignore`
  excludes (along with `*.keystore`, `*.apk`, `dist/`, `app/`, `InstaZen_*/`).
- The workflow decodes the keystore with `umask 077` during the release job
  only, signs with `apksigner`, verifies with `apksigner verify`, and
  deletes the unsigned artifact before publishing.
- Debug signing is never used for releases; every release is signed with
  the same key so upgrades install cleanly.

## Branding scope

See [docs/branding-audit.md](docs/branding-audit.md) for the complete list
of rebranded strings and the identifiers deliberately left untouched
(package name, JNI symbols, preferences, file paths, resource IDs).
