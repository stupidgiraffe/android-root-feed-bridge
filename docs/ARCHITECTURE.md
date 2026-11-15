# Architecture and operating plan

## Goal and completion criteria

Mirror **all catalog metadata** published by [Best Root Apps for Android](https://krishna3163.github.io/best-root-apps-for-android/) while publishing only **inspected, installable root module ZIPs** to MMRL and KernelSU Next. The original author owns all source entries, downloads and licenses. We maintain indexes only.

Acceptance conditions:

1. Include every upstream README app row, its original link, labels, category, and description. Include upstream Morphe release metadata (discovery only) and any configured release trackers not already listed.
2. Maintain independent, correctly shaped MMRL and KernelSU Next feeds.
3. Query every distinct GitHub source repository and eventually reach zero unchecked GitHub repositories without requiring manual curation.
4. Update on a daily schedule, checking previously valid releases first and newly discovered sources before rescanning old negative results.
5. Block publication if sources disappear unexpectedly, the valid module count collapses, outputs are malformed, or unit/contract tests fail.
6. Never mirror, execute, repack, install, or auto-flash downloaded releases.

## Source-of-truth boundaries

- **Upstream README**: canonical list of projects, parsed with the exact bold-table-row pattern used in the upstream `scripts/readme.py`. It can be fresher than the GitHub Pages website.
- **Upstream `data/morphe-releases.json`**: additional patched APK entries, never root modules.
- **Upstream `config/apps.json`**: explicitly tracked release projects.
- **GitHub REST /repos/OWNER/REPO/releases/latest**: authoritative current release assets for a discovered GitHub project.
- **Release ZIP**: inspected statically; a root-level `module.prop` with valid ID, version and numeric versionCode is required.
- **Local `state.json`**: cached last-good module metadata and release ID, not a source of ownership or trust.

Providers outside GitHub (GitLab, Codeberg, Play Store, official sites) are included in discovery. They are *not* silently converted into GitHub repos or flashable modules.

## Outputs

| Path | Consumer | Contract |
| --- | --- | --- |
| `discovery.json` | General browsing, tooling | Complete item array with original URLs, provider, category, framework badges, provenance, and Morphe metadata |
| `report.json` | Audit / diagnostics | Coverage totals, scan progress, exclusions and module counts |
| `state.json` | Updater only | Cached release inspections keyed by canonical GitHub owner/repo |
| `json/modules.json` | MMRL | Object with name, metadata (version 1, epoch float), modules array, version metadata, selected ZIP |
| `json/config.json` | Repository compatibility | Name and website metadata |
| `ksu/modules.json` | KernelSU Next | Array with name, author, description, repoUrl and visibility |

Paste into MMRL (base directory):
`https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/`

Paste into KernelSU Next (JSON file):
`https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/ksu/modules.json`

## Installation boundary

The release ZIP must be HTTPS from GitHub's official releases and have `module.prop` at the ZIP root. The archive has a 96 MiB cap; the metadata file is limited to 16 KiB. No archive member is extracted or executed. A ZIP with invalid module.prop, no release, too many entries, or ambiguous multiple module IDs is **not** listed as installable. This is a packaging check **not** a safety, compatibility, authenticity, or root-hiding guarantee.

MMRL displays only one version per distinct module ID, selecting the most recently published inspected release if forks collide. KernelSU Next works differently: its manager fetches a repository's latest GitHub release and blindly selects the first ZIP asset. The KernelSU feed therefore includes only inspected releases with **exactly one ZIP**, but it can include multiple distinct source repos sharing a module ID.

Downloaded release assets can be linked to a different GitHub repository than the catalog source if that's the location returned by the source repository's GitHub Releases API. Cross-repository assets remain original developer-hosted assets; these should be individually reviewed before flashing.

**Nothing is installed on your Android device automatically.** Root and Zygisk compatibility must be checked by the user before flashing. Device-specific modules can be dangerous.

## Update and failure policy

The [GitHub Actions updater](../.github/workflows/update.yml) runs every day at 09:17 UTC (18:17 JST), and on source/test/workflow changes. New sources and all previously validated sources are checked first. Rejected sources are retried after 48 hours. Checks are bounded and run in parallel with a limit of eight workers. GitHub API errors preserve previous inspected data; no successful scan means no blank publication. Failure of any test, 25%+ source shrink, 25%+ verified module collapse, or malformed JSON aborts before commit. Generated data commits to `main` only after tests and validation pass.

GitHub may delay or suspend scheduled workflows and provider formats or rate limits may change. No upkeep is normally required, but permanent maintenance-free operation cannot be guaranteed.

## Operational verification

View [workflow runs](https://github.com/stupidgiraffe/android-root-feed-bridge/actions/workflows/update.yml) and [live coverage report](../report.json). Both installation indexes are validated in CI, but **real-device import and installation remain separate acceptance tests**.

Manual rerun: GitHub → Actions → Update Root Module Feeds → Run workflow.
