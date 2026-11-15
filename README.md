<div align="center">

<img src="assets/root-feed-banner.jpg" alt="RootAtlas — a luminous modular cube linking Android root module repositories" width="100%" />

<h1>RootAtlas</h1>

<h3>The federated index for Android root modules.</h3>

<p>Find more Android modules without adding dozens of repos. RootAtlas combines MMRL feeds, KernelSU Next manifests, independently discovered GitHub repositories, and the complete <strong><a href="https://krishna3163.github.io/best-root-apps-for-android/">Best Root Apps for Android</a></strong> discovery catalog, with automatic daily updates.</p>

<p>
  <a href="https://github.com/stupidgiraffe/rootatlas/actions/workflows/update.yml"><img alt="Daily feed build" src="https://github.com/stupidgiraffe/rootatlas/actions/workflows/update.yml/badge.svg" /></a>
  <img alt="Free and open catalog" src="https://img.shields.io/badge/Free-to%20use-00bfa5?style=flat-square" />
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

> [!IMPORTANT]
> **Repository renamed to RootAtlas.** Old raw-file subscriptions may not redirect after the rename. Replace them with the new URLs below.

## 📦 Add to MMRL

In **MMRL → Repos → +**, paste this **base URL** (including the trailing slash):

```text
https://raw.githubusercontent.com/stupidgiraffe/rootatlas/main/
```

MMRL reads our [unified module index](json/modules.json) and displays both inspected Best Root Apps releases and modules from other curated MMRL repositories. The banner above also appears in MMRL's repository card.

## ⚡ Add to KernelSU Next

In **KernelSU Next → Module Repository → Manage Repositories → Add**, paste this **JSON file URL**:

```text
https://raw.githubusercontent.com/stupidgiraffe/rootatlas/main/ksu/modules.json
```

KernelSU Next uses a different format. This feed merges our inspected single-ZIP sources with the official KernelSU Next open-source and metamodule manifests. The manager fetches each upstream repository's release when you select a module.

> [!IMPORTANT]
> The **MMRL URL is a folder**, while the **KernelSU Next URL is a JSON file**. The two are not interchangeable.

## ✨ What's inside?

| | Collection | What you'll find |
|:--:|---|---|
| 🧭 | **[Best Root Apps catalog](discovery.json)** | Original upstream entries, including root apps, Shizuku tools, LSPosed utilities, GitLab, Codeberg, Play Store links, and Morphe patched APKs |
| 📦 | **[MMRL modules](json/modules.json)** | Combined index from our inspected catalog and other MMRL repository feeds; duplicates resolved by module ID |
| ⚡ | **[KernelSU Next modules](ksu/modules.json)** | Our inspected sources plus official KernelSU Next open-source and metamodule manifests, deduped by repository |
| 📈 | **[Live coverage report](report.json)** | Exact discovery counts, successful module inspections, exclusions, and scan progress |

<div align="center">

<a href="report.json"><img alt="MMRL module count" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fstupidgiraffe%2Frootatlas%2Fmain%2Freport.json&query=%24.mmrl_modules&label=MMRL%20modules&color=0891b2&style=for-the-badge" /></a>
<a href="report.json"><img alt="KernelSU Next module count" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fstupidgiraffe%2Frootatlas%2Fmain%2Freport.json&query=%24.kernelsu_next_modules&label=KernelSU%20Next&color=7c3aed&style=for-the-badge" /></a>
<a href="report.json"><img alt="Total discovery entries" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fstupidgiraffe%2Frootatlas%2Fmain%2Freport.json&query=%24.catalog_entries&label=Catalog%20entries&color=0f766e&style=for-the-badge" /></a>

<sub>These counts come from the live generated report, not hardcoded values.</sub>

</div>

## 🔄 How it works

```text
Best Root Apps ──────┐
MMRL directory ──────┤
Curated MMRL feeds ──┤
GitHub repo discovery┤ → validate → merge → deduplicate
KernelSU manifests ──┘                   |
                           ┌─────────────┴───────────┐
                           |                         |
                       MMRL JSON             KernelSU Next JSON
                           |                         |
                           └── daily GitHub Actions ─┘
```

- **Daily updates:** GitHub Actions refreshes around **18:17 JST**, including newly registered MMRL sources and previously discovered repositories.
- **Independent GitHub discovery:** bounded repository searches check public `modules.json` and `json/modules.json` for valid manager-specific entries; candidates that fail validation are excluded.
- **Different safety tiers:** upstream feeds supply module metadata; RootAtlas does not audit every external ZIP or guarantee compatibility.
- **Your existing sources:** We started with the repository URLs recovered from your MMRL app, plus official discovery feeds. Your phone does **not** need to remain connected.
- **One source, one record:** MMRL deduplicates by module ID; KernelSU Next deduplicates by GitHub source repository.
- **Failure protection:** Broken JSON, missing required timestamps and failed feeds cannot invalidate the combined repository. Previously successful upstream data is cached.
- **No rehosting or automatic flashing:** Developer downloads stay upstream and nothing is installed on your phone.

**Different verification levels:** Best Root Apps ZIPs are downloaded and structurally inspected for `module.prop`. Other MMRL repositories are checked for valid JSON and required fields, **not** independently audited ZIP-by-ZIP. The official KernelSU Next manifests are sourced from their maintainers. No feed entry guarantees security, compatibility or successful installation.

### 📡 Upstream sources and transparency

- **[Configured repositories](sources/federation.json):** the curated starting sources, MMRL directory, and KernelSU Next manifests.
- **[Discovered repositories](source-discovery-state.json):** independent GitHub feeds found through scheduled searches, with public source URLs and inspection timestamps.
- **[Coverage and source-health report](report.json):** live counts, successful feeds, failed feeds, and filtered entries.
- **[Module provenance](federation-provenance.json):** records which catalog or repository supplied each displayed module.
- **[Processing architecture](docs/ARCHITECTURE.md):** merge rules, caching, validation and limitations.

The MMRL app and KernelSU Next require **different JSON schemas**. The two import URLs above remain separate, but each is a unified repository for its manager.

<details>
<summary><strong>🔧 Maintainer information, validation and troubleshooting</strong></summary>

The repository is intentionally small and serverless.

- [Current automation status](https://github.com/stupidgiraffe/rootatlas/actions/workflows/update.yml)
- [Coverage and exclusion reasons](report.json)
- [Architecture, data boundaries and update policy](docs/ARCHITECTURE.md)
- [MMRL JSON output](json/modules.json) · [KernelSU Next JSON output](ksu/modules.json)
- [Updater source](scripts/update.py) · [Validation source](scripts/validate.py)
- [Original source catalog](https://github.com/krishna3163/best-root-apps-for-android)

To refresh manually, open **Actions → Update Root Module Feeds → Run workflow**. If MMRL shows an older count or banner, tap **Update** on the repository card. GitHub may occasionally delay scheduled actions; the repository is intended to be hands-off, not guaranteed to require zero maintenance forever.

</details>

## 🧩 Xposed and LSPosed

RootAtlas deliberately does **not** turn Xposed/LSPosed APKs into
Magisk/KernelSU flashable modules. That ecosystem already has a dedicated
and actively updated [official Xposed Module Repository](https://modules.lsposed.org/)
and a separate [community Xposed directory](https://github.com/rushiranpise/xposed-modules).
Use those for APK-based modules; the two RootAtlas feeds remain for root ZIPs.

## 🤝 Open-source and contributions

RootAtlas's original indexer code is [MIT licensed](LICENSE). Original
module authors retain ownership and licensing of their binaries and metadata.
To propose missing sources, report a broken feed or improve the pipeline, see
[Contributing](CONTRIBUTING.md) and the
[technical architecture](docs/ARCHITECTURE.md).

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

<sub>Catalog data belongs to its respective authors. This independent index is not affiliated with or endorsed by source maintainers, MMRL, KernelSU Next, or module developers. Inspect what you flash.</sub>

</div>
