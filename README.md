<div align="center">

<img src="assets/root-feed-banner.jpg" alt="Root Feed Bridge — a luminous modular cube linking Android root module repositories" width="100%" />

<h1>Root Feed Bridge</h1>

<h3>One catalog. Two module managers. Automatic updates.</h3>

<p>Discover Android root tools from <strong><a href="https://krishna3163.github.io/best-root-apps-for-android/">Best Root Apps for Android</a></strong>, with ready-to-add repositories for <strong><a href="https://github.com/MMRLApp/MMRL">MMRL</a></strong> and <strong><a href="https://github.com/KernelSU-Next/KernelSU-Next">KernelSU Next</a></strong>.</p>

<p>
  <a href="https://github.com/stupidgiraffe/android-root-feed-bridge/actions/workflows/update.yml"><img alt="Daily feed build" src="https://github.com/stupidgiraffe/android-root-feed-bridge/actions/workflows/update.yml/badge.svg" /></a>
  <img alt="Free and open catalog" src="https://img.shields.io/badge/Free-forever-00bfa5?style=flat-square" />
  <img alt="Automatic daily refresh" src="https://img.shields.io/badge/Auto--sync-daily-64748b?style=flat-square" />
  <a href="https://buymeacoffee.com/stupidgiraffe"><img alt="Support development on Buy Me a Coffee" src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Support-FFDD00?logo=buymeacoffee&logoColor=000000&style=flat-square" /></a>
</p>

<p>
  <a href="#-add-to-mmrl"><strong>📦 Add to MMRL</strong></a>
  &nbsp; · &nbsp;
  <a href="#-add-to-kernelsu-next"><strong>⚡ Add to KernelSU Next</strong></a>
  &nbsp; · &nbsp;
  <a href="report.json"><strong>📊 Live coverage</strong></a>
  &nbsp; · &nbsp;
  <a href="#-support-development"><strong>☕ Support</strong></a>
</p>

</div>

---

## 📦 Add to MMRL

In **MMRL → Repos → +**, paste this **base URL** (including the trailing slash):

```text
https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/
```

MMRL reads our [module index](json/modules.json) and displays each qualifying module's version, metadata, and original developer-hosted ZIP. The banner at the top of this README also appears in MMRL's repository card.

## ⚡ Add to KernelSU Next

In **KernelSU Next → Module Repository → Manage Repositories → Add**, paste this **JSON file URL**:

```text
https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/ksu/modules.json
```

KernelSU Next uses a different format. This feed includes only validated repositories whose latest GitHub release contains a single ZIP, because its manager selects that ZIP itself.

> [!IMPORTANT]
> The **MMRL URL is a folder**, while the **KernelSU Next URL is a JSON file**. The two are not interchangeable.

## ✨ What's inside?

| | Collection | What you'll find |
|:--:|---|---|
| 🧭 | **[Complete catalog](discovery.json)** | Original upstream entries, including root apps, Shizuku tools, LSPosed utilities, GitLab, Codeberg, Play Store links, and Morphe patched APKs |
| 📦 | **[MMRL modules](json/modules.json)** | GitHub release ZIPs inspected for a valid root-level `module.prop`; one listing per module ID |
| ⚡ | **[KernelSU Next modules](ksu/modules.json)** | Eligible single-ZIP release repositories, including separate forks when applicable |
| 📈 | **[Live coverage report](report.json)** | Exact discovery counts, successful module inspections, exclusions, and scan progress |

<div align="center">

<a href="report.json"><img alt="MMRL module count" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fstupidgiraffe%2Fandroid-root-feed-bridge%2Fmain%2Freport.json&query=%24.mmrl_modules&label=MMRL%20modules&color=0891b2&style=for-the-badge" /></a>
<a href="report.json"><img alt="KernelSU Next module count" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fstupidgiraffe%2Fandroid-root-feed-bridge%2Fmain%2Freport.json&query=%24.kernelsu_next_modules&label=KernelSU%20Next&color=7c3aed&style=for-the-badge" /></a>
<a href="report.json"><img alt="Total discovery entries" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fstupidgiraffe%2Fandroid-root-feed-bridge%2Fmain%2Freport.json&query=%24.catalog_entries&label=Catalog%20entries&color=0f766e&style=for-the-badge" /></a>

<sub>These counts come from the live generated report, not hardcoded values.</sub>

</div>

## 🔄 How it works

```text
 Best Root Apps for Android
           │
  Read original catalog + release trackers
           │
   Check original GitHub releases
           │
  Inspect ZIP structure and module.prop
           │
     ┌─────┴───────────┐
     │                 │
  MMRL feed      KernelSU Next feed
     │                 │
     └──────┬──────────┘
            │
   Publish only after validation
```

- **Daily updates:** GitHub Actions refreshes around **18:17 JST** with no server or account required on your phone.
- **New discoveries:** New upstream catalog projects become discoverable automatically. Compatible module ZIP releases are added after inspection.
- **No rehosting:** ZIPs remain on the developers' original GitHub releases.
- **Failure protection:** Tests and schema checks run before publication. Suspiciously large drops preserve the last published feed.
- **No automatic flashing:** Adding this repo does not install or enable modules.

Regular APKs, LSPosed apps, Shizuku tools and projects with no valid release ZIP belong in **discovery**, not a flashable-module feed. Package structure checks are **not** security audits or device compatibility guarantees.

<details>
<summary><strong>🔧 Maintainer information, validation and troubleshooting</strong></summary>

The repository is intentionally small and serverless.

- [Current automation status](https://github.com/stupidgiraffe/android-root-feed-bridge/actions/workflows/update.yml)
- [Coverage and exclusion reasons](report.json)
- [Architecture, data boundaries and update policy](docs/ARCHITECTURE.md)
- [MMRL JSON output](json/modules.json) · [KernelSU Next JSON output](ksu/modules.json)
- [Updater source](scripts/update.py) · [Validation source](scripts/validate.py)
- [Original source catalog](https://github.com/krishna3163/best-root-apps-for-android)

To refresh manually, open **Actions → Update Root Module Feeds → Run workflow**. If MMRL shows an older count or banner, tap **Update** on the repository card. GitHub may occasionally delay scheduled actions; the repository is intended to be hands-off, not guaranteed to require zero maintenance forever.

</details>

## ☕ Support development

<div align="center">

<p>If this bridge saves you from hunting down module downloads and checking repositories by hand, a coffee helps support future improvements and upkeep.</p>

<a href="https://buymeacoffee.com/stupidgiraffe"><img src="https://raw.githubusercontent.com/stupidgiraffe/Kizuku/main/docs/media/buy-me-a-coffee-qr.png" alt="QR code for Buy Me a Coffee: stupidgiraffe" width="152" height="152" /></a>

<br />

<a href="https://buymeacoffee.com/stupidgiraffe"><img alt="Buy me a coffee" src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Support%20this%20project-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" /></a>

<sub>Completely optional. The feeds remain free.</sub>

</div>

---

<div align="center">

<strong>Made for the Android rooting community</strong> · Maintained by <a href="https://github.com/stupidgiraffe">stupidgiraffe</a>

<sub>Catalog data belongs to its respective authors. This independent project is not affiliated with or endorsed by the source maintainer, MMRL, KernelSU Next, or module developers. Inspect what you flash.</sub>

</div>
