"""Fail closed if the published indexes violate either Android manager's schema."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise RuntimeError("Feed validation failed: " + message)


def validate():
    mmrl = load("json/modules.json")
    config = load("json/config.json")
    ksu = load("ksu/modules.json")
    discovery = load("discovery.json")
    state = load("state.json")
    report = load("report.json")

    require(mmrl.get("name") == config.get("name"), "MMRL config name mismatch")
    require(isinstance(mmrl.get("metadata", {}).get("timestamp"), (float, int)),
            "MMRL metadata timestamp missing")
    require(mmrl.get("metadata", {}).get("version") == 1, "MMRL metadata version")
    require(isinstance(mmrl.get("modules"), list) and mmrl["modules"],
            "MMRL modules array is empty")
    require(isinstance(ksu, list), "KernelSU Next root must be an array")
    ids, sources = set(), set()
    for module in mmrl["modules"]:
        for field in ("id", "name", "version", "versionCode", "author", "track", "versions"):
            require(field in module and module[field] is not None,
                    f"{module.get('id', '?')}: missing {field}")
        identifier = module["id"]
        require(identifier not in ids, f"duplicate MMRL module id: {identifier}")
        ids.add(identifier)
        require(isinstance(module["versionCode"], int), f"bad versionCode: {identifier}")
        require(module["track"].get("type") == "GIT", f"bad track type: {identifier}")
        source = module["track"].get("source")
        require(isinstance(source, str) and source.startswith("https://github.com/"),
                f"invalid source repository: {identifier}")
        sources.add(source)
        versions = module["versions"]
        require(isinstance(versions, list) and len(versions) == 1,
                f"ambiguous module versions: {identifier}")
        for version in versions:
            for field in ("version", "versionCode", "timestamp", "zipUrl"):
                require(field in version and version[field] is not None,
                        f"{identifier}: missing versions.{field}")
            require(version["versionCode"] == module["versionCode"],
                    f"version codes inconsistent: {identifier}")
            require(isinstance(version["timestamp"], (int, float)),
                    f"timestamp invalid: {identifier}")
            require(isinstance(version.get("size"), int) and version["size"] > 0,
                    f"missing ZIP size: {identifier}")
            uri = version["zipUrl"]
            require(isinstance(uri, str) and
                    uri.startswith(source + "/releases/download/") and
                    uri.lower().endswith(".zip"),
                    f"download does not belong to source release: {identifier}")
    ksu_repos = set()
    for entry in ksu:
        require(all(isinstance(entry.get(field), str) and entry[field]
                    for field in ("name", "description", "author", "repoUrl")),
                "malformed KernelSU Next item")
        require(entry.get("visibility") == 1, "KSU visibility")
        source = entry["repoUrl"]
        require(source in sources, f"KSU source not validated by MMRL feed: {source}")
        require(source not in ksu_repos, f"duplicate KSU repository: {source}")
        ksu_repos.add(source)

    require(discovery.get("schema_version") == 2, "discovery schema_version")
    entries = discovery.get("entries")
    require(isinstance(entries, list) and len(entries) >= 1000,
            "missing comprehensive discovery catalog")
    require(len({e["id"] for e in entries}) == len(entries),
            "duplicate discovery identifiers")
    require(any(e["provider"] == "codeberg.org" for e in entries),
            "Codeberg upstream entries were lost")
    require(any(e["provider"] == "gitlab.com" for e in entries),
            "GitLab upstream entries were lost")
    require(any(e["kind"] == "patched_apk" for e in entries),
            "Morphe patched APK entries were lost")
    require(discovery["summary"]["total_entries"] == len(entries),
            "catalog total count inconsistent")
    for entry in entries:
        require(entry.get("url", "").startswith("https://"), "unsafe discovery source URL")
        require(entry.get("kind") != "flashable", "discovery is not an install approval")
    require(isinstance(state.get("repos"), dict), "missing release state")
    require(report["catalog_entries"] == len(entries), "report catalog count mismatch")
    require(report["mmrl_modules"] == len(mmrl["modules"]), "report MMRL count mismatch")
    require(report["kernelsu_next_modules"] == len(ksu), "report KSU count mismatch")
    require(report["checked_repositories"] <= report["github_repositories"],
            "checked counts inconsistent")
    print(f"Validated: {len(entries)} discovery entries; "
          f"{len(mmrl['modules'])} MMRL ZIPs; {len(ksu)} KernelSU Next modules; "
          f"{report['checked_repositories']}/{report['github_repositories']} repos checked")


if __name__ == "__main__":
    validate()
