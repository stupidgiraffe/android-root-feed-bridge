"""Render the public source listing from current RootAtlas generated state."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

LABELS = {
 "https://gr.dergoogler.com/gmr": "Googlers Magisk Repository (GMR)",
 "https://magisk-modules-alt-repo.github.io/json-v2": "Magisk Modules Alt Repo",
 "https://apt.izzysoft.de/magisk": "IzzyOnDroid Magisk",
 "https://rikj000.github.io/Magisk-Modules-Rikj000-Repo": "Rikj000 Modules",
 "https://natsumerinchan.github.io/celica-magisk-modules-repo": "Celica Modules",
 "https://codeberg.org/fruitsnack/magisk-font-repo/raw/branch/main": "Fruitsnack Fonts",
 "https://leloubil.github.io/magisk-repo": "Leloubil Repo",
 "https://misak10.github.io/mmrl-repo": "Misak10 Repo",
 "https://zguation-projects.github.io/ZG-R": "ZGuation Projects (ZG-R)",
 "https://mrepo.rem01gaming.dev": "Rem01Gaming MRepo",
 "https://ssmg4.github.io/SSR": "SSMG4 Repo",
 "https://juliazero.github.io/mrbj": "JuliaZero MRBJ",
 "https://shamratrh-web.github.io/mmrl-repo": "ShamratRH",
 "https://cabiamdos.github.io/my-mmrl-repository": "Cabiamdos",
 "https://mystster.github.io/module-repo": "Mystster",
 "https://vc-teahouse.github.io/magisk-module-repo": "VC Teahouse",
 "https://zelect0r.github.io/zamr": "ZAMR (zelect0r)",
 "https://yukari0201.github.io/mmrl-repo": "Yukari",
 "https://privshell.github.io/privshell-repo": "PrivShell",
 "https://mmrl.dev/repo": "MMRL Repo",
 "https://mmrl.dev/repo/ksu": "MMRL KernelSU",
 "https://raw.githubusercontent.com/script-or-script/FlutterTap-mmrl/main": "FlutterTap",
}


def base(url):
    return url.rstrip("/").casefold()


def valid_url(url):
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    p = urlsplit(url)
    return bool(p.hostname) and not any(x in url for x in ("|", " ", "\n", "(", ")"))


def render_sources(config, search_state, report):
    stamp = datetime.fromtimestamp(report["updated"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    bad = {base(x["source"]) for x in report["federation"]["failures"] if x.get("kind") == "mmrl"}
    found = sorted((r for r in search_state.get("repositories", {}).values()
                    if r.get("status") == "found" and r.get("kind") in ("mmrl", "ksunext")),
                   key=lambda r: r["repository"].casefold())
    lines = [
        "# RootAtlas — all tracked source repositories",
        "",
        "Automatically generated from the actual source configuration and discovery state.",
        "Last successful feed update: **" + stamp + "**.",
        "",
        "## Live coverage",
        "",
        "- Best Root Apps catalog: **" + str(report["catalog_entries"]) + "** discovery entries, "
        + str(report["github_repositories"]) + " GitHub project candidates.",
        "- MMRL modules after deduplication: **" + str(report["mmrl_modules"]) + "**.",
        "- KernelSU Next entries after deduplication: **" + str(report["kernelsu_next_modules"]) + "**.",
        "- External feeds fetched: **" + str(report["federation"]["fetched"]) + " / "
        + str(report["federation"]["total"]) + "** (some failed sources may retain cached entries).",
        "",
        "## Original discovery catalog (1)",
        "",
        "- [Best Root Apps for Android](https://github.com/krishna3163/best-root-apps-for-android) "
        "— full project catalog, including qualifying root-module ZIPs, apps, and utilities.",
        "- [Browse each individual catalog entry](discovery.json). Not all catalog items are installable modules.",
        "",
        "## Curated MMRL feeds (" + str(len(config["mmrl"])) + ")",
        "",
        "| Upstream repository | Feed URL | Last update |",
        "|---|---|---|",
    ]
    for url in config["mmrl"]:
        if not valid_url(url):
            raise ValueError("Invalid configured feed URL")
        name = LABELS.get(url.rstrip("/"), urlsplit(url).hostname + urlsplit(url).path.rstrip("/"))
        status = "Failed (retrying)" if base(url) in bad else "Loaded"
        lines.append("| [" + name + "](" + url + ") | [Open feed](" + url + ") | " + status + " |")
    lines += [
        "",
        "The [MMRL official discovery directory]"
        "(https://github.com/MMRLApp/Discovery/blob/main/json/remotes.json) is also monitored. "
        "This directory is a registry of URLs, not another standalone module feed.",
        "",
        "## KernelSU Next manifests",
        "",
        "| Upstream manifest | Source URL | Status |",
        "|---|---|---|",
    ]
    for item in config["ksunext"]:
        if not valid_url(item["url"]):
            raise ValueError("Invalid KernelSU manifest")
        status = "Enabled" if item["enabled"] else "Not included (opt-in)"
        lines.append("| [" + item["name"] + "](" + item["url"] + ") | "
                     "[Open JSON](" + item["url"] + ") | " + status + " |")
    lines += [
        "",
        "## Independently discovered GitHub feeds (" + str(len(found)) + ")",
        "",
        "Repository names below come directly from the GitHub discovery state. "
        "Some are alternate URLs or mirrors of curated sources; do not add "
        "these counts to the curated total as if they were all unique.",
        "",
        "| GitHub repository | Type | Feed URL |",
        "|---|---|---|",
    ]
    for item in found:
        repo = item["repository"]
        url = item["url"]
        if not valid_url(url) or any(c in repo for c in ("|", " ", "\n", "(", ")")):
            raise ValueError("Invalid discovered source")
        kind = "MMRL" if item["kind"] == "mmrl" else "KernelSU Next"
        lines.append("| [" + repo + "](https://github.com/" + repo + ") | " + kind
                     + " | [Open JSON](" + url + ") |")
    lines += [
        "",
        "## Verification and limitations",
        "",
        "- [Live source-health report](report.json)",
        "- [Curated source configuration](sources/federation.json)",
        "- [Automatic discovery state](source-discovery-state.json)",
        "- [Per-module source provenance](federation-provenance.json)",
        "- [Scheduled update runs](https://github.com/stupidgiraffe/rootatlas/actions/workflows/update.yml)",
        "",
        "Entries from third-party feeds are schema-validated, not individually security-audited. "
        "Original catalog GitHub ZIPs are structurally inspected; this does not prove safety. "
        "Original module developers host their own downloads.",
        "",
        "This page is regenerated by scripts/source_directory.py on every successful update.",
        "",
    ]
    return "\n".join(lines)


def main():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "sources/federation.json").read_text())
    found = json.loads((root / "source-discovery-state.json").read_text())
    report = json.loads((root / "report.json").read_text())
    (root / "SOURCES.md").write_text(render_sources(config, found, report), encoding="utf-8")


if __name__ == "__main__":
    main()
