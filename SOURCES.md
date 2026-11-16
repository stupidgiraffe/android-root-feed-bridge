# RootAtlas — upstream sources

RootAtlas combines multiple public root-module sources into **one subscription for MMRL** and **one subscription for KernelSU Next**. The files contain different schemas, so the manager URLs are separate.

**Status snapshot:** November 16, 2026 (JST). This page names sources; see the **[live report](report.json)** for today's counts, outages, and scan progress. A ✅ means the source JSON was readable and passed schema validation, **not** that every module is safe or compatible.

## Discovery catalog — 1 source

| Catalog | What RootAtlas imports |
|---|---|
| [Best Root Apps for Android](https://github.com/krishna3163/best-root-apps-for-android) | Complete upstream directory across root modules, APK apps, LSPosed/Shizuku tools and third-party hosts; qualified GitHub release ZIPs are inspected for `module.prop` before inclusion as installable root modules |

## Curated MMRL sources — 22 feeds

| Feed | Type | Last checked |
|---|---|---|
| [Googlers Magisk Repository (GMR)](https://gr.dergoogler.com/gmr/) | Googlers / degoogler | ✅ Responding |
| [Magisk Modules Alt Repo](https://magisk-modules-alt-repo.github.io/json-v2/) | Community | ✅ Responding |
| [IzzyOnDroid Magisk repository](https://apt.izzysoft.de/magisk/) | Community | ✅ Responding |
| [Rikj000's Magisk modules](https://rikj000.github.io/Magisk-Modules-Rikj000-Repo/) | Independent | ✅ Responding |
| [Celica Magisk modules](https://natsumerinchan.github.io/celica-magisk-modules-repo/) | Independent | ✅ Responding |
| [Fruitsnack Magisk fonts (Codeberg)](https://codeberg.org/fruitsnack/magisk-font-repo/raw/branch/main/) | Fonts | ✅ Responding |
| [Leloubil Magisk repository](https://leloubil.github.io/magisk-repo/) | Independent | ⚠️ Unreachable |
| [Misak10 MMRL repository](https://misak10.github.io/mmrl-repo/) | Independent | ⚠️ Unreachable |
| [ZG-R (ZGuation Projects)](https://zguation-projects.github.io/ZG-R/) | Independent | ✅ Responding |
| [Rem01Gaming MRepo](https://mrepo.rem01gaming.dev/) | Independent | ✅ Responding |
| [SSMG4 repository](https://ssmg4.github.io/SSR/) | Independent | ⚠️ Unreachable |
| [JuliaZero MRBJ](https://juliazero.github.io/mrbj/) | Independent | ✅ Responding |
| [ShamratRH MMRL](https://shamratrh-web.github.io/mmrl-repo/) | Independent | ✅ Responding |
| [Cabiamdos MMRL](https://cabiamdos.github.io/my-mmrl-repository/) | Independent | ✅ Responding |
| [Mystster module repository](https://mystster.github.io/module-repo/) | Independent | ✅ Responding |
| [VC Teahouse Magisk repository](https://vc-teahouse.github.io/magisk-module-repo/) | Independent | ✅ Responding |
| [ZAMR (zelect0r)](https://zelect0r.github.io/zamr/) | Independent | ✅ Responding |
| [Yukari's MMRL repository](https://yukari0201.github.io/mmrl-repo/) | Independent | ✅ Responding |
| [PrivShell repository](https://privshell.github.io/privshell-repo/) | Independent | ✅ Responding |
| [MMRL module repository](https://mmrl.dev/repo/) | MMRL | ✅ Responding |
| [MMRL KernelSU-focused repository](https://mmrl.dev/repo/ksu/) | MMRL | ✅ Responding |
| [FlutterTap MMRL](https://raw.githubusercontent.com/script-or-script/FlutterTap-mmrl/main/) | Independent | ✅ Responding |

The **[official MMRL Discovery directory](https://github.com/MMRLApp/Discovery/blob/main/json/remotes.json)** is also checked automatically. This is a registry of source URLs, **not** a separate module repository, so it is not counted as another module feed. RootAtlas excludes its own URL from imports to avoid recursion.

## KernelSU Next — 2 enabled feeds

| Feed | Current configuration |
|---|---|
| [KernelSU Next official open-source modules](https://github.com/KernelSU-Next/KernelSU-Next-Modules-Repo/blob/main/modules.json) | ✅ Enabled |
| [KernelSU Next official metamodules](https://github.com/KernelSU-Next/KernelSU-Next-Modules-Repo/blob/main/meta_modules.json) | ✅ Enabled |
| [KernelSU Next non-free modules](https://github.com/KernelSU-Next/KernelSU-Next-Modules-Repo/blob/main/non_free_modules.json) | **Not enabled** — available only as an opt-in source in the configuration |

## Independent GitHub feed discovery

RootAtlas also searches public GitHub repositories for real MMRL and KernelSU Next JSON indexes. These repositories passed the discovery checks in the latest search snapshot:

| GitHub repository | Coverage |
|---|---|
| [brz0x100/mmrl-repo](https://github.com/brz0x100/mmrl-repo) | Additional discovery |
| [cabiamdos/my-mmrl-repository](https://github.com/cabiamdos/my-mmrl-repository) | Also curated |
| [hiighbob/MmrlRepo](https://github.com/hiighbob/MmrlRepo) | Additional discovery |
| [JasonALorance/INTJLo-MMRL-Repo](https://github.com/JasonALorance/INTJLo-MMRL-Repo) | Additional discovery |
| [mystster/module-repo](https://github.com/mystster/module-repo) | Also curated |
| [natsumerinchan/celica-magisk-modules-repo](https://github.com/natsumerinchan/celica-magisk-modules-repo) | Also curated |
| [privshell/privshell-repo](https://github.com/privshell/privshell-repo) | Also curated |
| [RavenWolf1998/MMRL-Magisk-Module-Repo](https://github.com/RavenWolf1998/MMRL-Magisk-Module-Repo) | Additional discovery |
| [Rikj000/Magisk-Modules-Rikj000-Repo](https://github.com/Rikj000/Magisk-Modules-Rikj000-Repo) | Also curated |
| [script-or-script/FlutterTap-mmrl](https://github.com/script-or-script/FlutterTap-mmrl) | Also curated |
| [shamratrh-web/mmrl-repo](https://github.com/shamratrh-web/mmrl-repo) | Also curated |
| [uonou/mmrl-repo](https://github.com/uonou/mmrl-repo) | Additional discovery |
| [vc-teahouse/magisk-module-repo](https://github.com/vc-teahouse/magisk-module-repo) | Also curated |
| [VD171/VD-Modules](https://github.com/VD171/VD-Modules) | Additional discovery |
| [Yukari0201/mmrl-repo](https://github.com/Yukari0201/mmrl-repo) | Also curated |

Some independently discovered repositories are already in the curated list. **These are not extra unique repository counts.** New discoveries appear in the automatically generated [discovery state](source-discovery-state.json). Valid records are deduplicated; automatically discovered sources cannot replace established module IDs.

## How to verify it yourself

- [Public source configuration](sources/federation.json)
- [Current import health, exclusions and counts](report.json)
- [Per-module provider provenance](federation-provenance.json)
- [Discovered source state and checks](source-discovery-state.json)
- [GitHub Actions — successful scheduled runs](https://github.com/stupidgiraffe/rootatlas/actions/workflows/update.yml)
- [Module import/validation rules](docs/ARCHITECTURE.md)

**Compatibility and security:** Best Root Apps GitHub release ZIPs receive a static archive/module.prop structure check. Third-party MMRL feeds and KernelSU Next manifests receive metadata/schema validation only; RootAtlas does **not** independently security-audit every remote ZIP. APK-based LSPosed/Xposed modules are outside the flashable-module feeds. RootAtlas never rehosts or silently installs developers' releases.
