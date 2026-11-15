# Android Root Feed Bridge

[![Update Root Module Feeds](https://github.com/stupidgiraffe/android-root-feed-bridge/actions/workflows/update.yml/badge.svg)](https://github.com/stupidgiraffe/android-root-feed-bridge/actions/workflows/update.yml)

**A free, automatically updated MMRL + KernelSU Next companion to [Best Root Apps for Android](https://krishna3163.github.io/best-root-apps-for-android/).** It preserves the entire discovery catalog, inspects official module release ZIPs, and publishes two manager-native formats without mirroring any binaries.

## Add the feeds

**MMRL** → Repositories → Add. Paste the **base URL**, including the trailing slash:

```text
https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/
```

**KernelSU Next** → Module repository → Manage repositories → Add. Paste the **full JSON URL**:

```text
https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/ksu/modules.json
```

These formats are intentionally different: KernelSU Next will **not** import the MMRL JSON format, and MMRL expects the base URL rather than a `modules.json` file.

## What it includes

| Output | Description | View |
| --- | --- | --- |
| Complete discovery | Every upstream README entry, plus Morphe patched APKs and extra configured trackers | [Browse JSON](discovery.json) |
| MMRL repository | Inspected GitHub release ZIPs with root-level `module.prop` | [MMRL modules](json/modules.json) |
| KernelSU Next repository | Single-ZIP official GitHub releases the manager can consume reliably | [KernelSU modules](ksu/modules.json) |
| Live audit | Counts, scan coverage and exclusion reasons | [Coverage report](report.json) |

**Why aren't the module counts equal to the full catalog?** The original website includes regular APKs, LSPosed apps, Shizuku utilities, documentation, and device-specific projects. Those are discoverable but are not automatically installable root modules. KernelSU Next is also more restrictive because its app picks the first ZIP in a GitHub release. Alternative forks of the same module can appear individually there; MMRL can represent only one per module ID.

Everything in `discovery.json` retains its original upstream link and classification. Non-GitHub projects (Codeberg, GitLab, Google Play, etc.) remain discoverable even if their binaries aren't eligible for the installation feeds.

## Automatic updates

GitHub Actions refreshes the catalog **daily around 18:17 JST**, prioritizing newly discovered projects, then checking current release versions. Previous inspection results are cached and reused. Upstream ZIPs are inspected without installing or executing them. Validation prevents empty or unexpectedly shrunken indexes from overwriting known-good data.

- [Latest builds and their logs](https://github.com/stupidgiraffe/android-root-feed-bridge/actions/workflows/update.yml)
- [Pipeline architecture, source contracts and limits](docs/ARCHITECTURE.md)
- [Original upstream catalog repository](https://github.com/krishna3163/best-root-apps-for-android)

**Safety:** `module.prop` confirms a package's structure, **not** whether it is trustworthy, compatible with your phone, or safe to flash. Check the project before installing. No root module is installed automatically. Proprietary packages are not republished; downloads come from developers' own GitHub releases.

This independent bridge is not affiliated with or endorsed by the original catalog maintainer, MMRL, KernelSU, or module authors.
