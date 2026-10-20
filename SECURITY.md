# Security Policy

## Supported versions

InstaLume ships as a single, current build. Only the latest published
release is supported with security fixes.

| Version | Supported |
| ------- | --------- |
| Latest release | Yes |
| Older releases | No |

## Reporting a vulnerability

If you find a security issue in InstaLume — the app build, the release
pipeline, or the Python/shell patchers in `tools/` — please report it
privately rather than opening a public issue.

- **Email:** riyazo65ckm@gmail.com
- If enabled on this repository, you can also use GitHub's private
  vulnerability reporting (Security tab → Report a vulnerability).

Please include:

- a description of the issue and its impact,
- steps to reproduce (or a proof of concept),
- the affected version or commit, and
- any suggested fix.

## What to expect

- We aim to acknowledge reports within a few days.
- We will investigate and, where warranted, ship a fix in the next release
  and credit you if you wish.

## Scope

**In scope:** the InstaLume release pipeline, the build/patcher scripts in
`tools/`, and the packaging and signing process.

**Out of scope:** the upstream Instagram client and the InstaZen mod this
project rebrands — those are third-party, closed-source components that
this project does not control.

Please do not test against accounts or devices you do not own.
