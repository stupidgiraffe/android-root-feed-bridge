"""Fail-closed contract validation for merged MMRL, KernelSU Next and discovery."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_INT = 2_147_483_647
COVER = "https://raw.githubusercontent.com/stupidgiraffe/rootatlas/main/assets/root-feed-banner.jpg"
TRACK_TYPES = {"GIT", "ONLINE_ZIP", "ONLINE_JSON", "UNKNOWN", "LOCAL_JSON", "LOCAL_ZIP"}


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def require(value, message):
    if not value:
        raise RuntimeError("Feed validation failed: " + message)


def https_url(value):
    return isinstance(value, str) and value.startswith("https://") and len(value) > 9


def validate():
    mmrl = load("json/modules.json")
    config = load("json/config.json")
    ksu = load("ksu/modules.json")
    discovery = load("discovery.json")
    state = load("state.json")
    report = load("report.json")
    federation_state = load("federation-state.json")
    provenance = load("federation-provenance.json")
    config_sources = load("sources/federation.json")
    try:
        from source_directory import render_sources
    except ModuleNotFoundError:
        from scripts.source_directory import render_sources
    require(
        (ROOT / "SOURCES.md").read_text(encoding="utf-8") ==
        render_sources(config_sources, load("source-discovery-state.json"), report),
        "published source directory is stale or incomplete",
    )
    search_state = load("source-discovery-state.json")
    require(search_state.get("version") == 1, "independent source-discovery state schema")
    search_repos = search_state.get("repositories")
    require(isinstance(search_repos, dict), "source-discovery repositories missing")
    for key, entry in search_repos.items():
        repo = entry.get("repository", "").casefold()
        require(repo != "stupidgiraffe/rootatlas",
                "source-discovery must not recursively import RootAtlas")
        require("template" not in repo.split("/")[-1],
                "demo/template repositories must never enter source index")
        if entry.get("status") == "found":
            require(https_url(entry.get("url")),
                    "discovered source must use HTTPS")
            require(entry.get("kind") in ("mmrl", "ksunext"),
                    "unrecognized discovered source type")

    require(mmrl.get("name") == config.get("name"), "MMRL config name mismatch")
    require(mmrl.get("cover") == COVER and config.get("cover") == COVER,
            "MMRL cover missing")
    require((ROOT / "assets/root-feed-banner.jpg").stat().st_size > 5000,
            "banner empty or missing")
    require(mmrl.get("metadata", {}).get("version") == 1, "metadata version")
    require(isinstance(mmrl["metadata"].get("timestamp"), (int, float)),
            "metadata timestamp")
    require(isinstance(mmrl.get("modules"), list) and mmrl["modules"],
            "MMRL missing modules")
    require(isinstance(ksu, list) and ksu, "KSU Next requires nonempty array")
    require(isinstance(federation_state.get("sources"), dict),
            "federation-state missing source cache")
    require(config_sources.get("schema_version") == 1, "federation source schema")
    require(isinstance(provenance.get("module_origins"), dict),
            "missing module provenance")
    require(isinstance(provenance.get("ksu_origins"), dict),
            "missing KSU provenance")

    # Authorization: only module records present in the current trusted
    # federation cache, or previously inspected in the catalog state.
    source_entries = {}
    ksu_entries = {}
    for entry in federation_state["sources"].values():
        if entry.get("kind") == "mmrl":
            base = entry.get("source")
            if not https_url(base):
                continue
            source_entries[base] = {(m["id"], m["versionCode"], m["versions"][0]["zipUrl"])
                                    for m in entry.get("entries", [])}
        elif entry.get("kind") == "ksunext":
            source = entry.get("source")
            ksu_entries[source] = {m["repoUrl"].casefold()
                                   for m in entry.get("entries", [])}

    seen, original = set(), 0
    for module in mmrl["modules"]:
        module_id = module.get("id")
        require(isinstance(module_id, str) and module_id and module_id not in seen,
                f"duplicate/invalid MMRL module {module_id}")
        seen.add(module_id)
        for key in ("id", "name", "author", "version", "versionCode", "track", "versions"):
            require(module.get(key) is not None, f"{module_id} missing {key}")
        require(all(isinstance(module[k], str) and bool(module[k])
                    for k in ("name", "author", "version")), f"{module_id}: name/author/version")
        code = module["versionCode"]
        require(type(code) is int and 0 <= code <= MAX_INT,
                f"{module_id}: invalid versionCode")
        track = module["track"]
        require(isinstance(track, dict) and track.get("type") in TRACK_TYPES,
                f"{module_id}: track type")
        require(isinstance(track.get("source"), str), f"{module_id}: track.source")
        versions = module["versions"]
        require(isinstance(versions, list) and len(versions) >= 1,
                f"{module_id}: no versions")
        for ver in versions:
            require(isinstance(ver, dict), f"{module_id}: invalid version entry")
            for key in ("version", "versionCode", "zipUrl", "timestamp"):
                require(key in ver and ver[key] is not None,
                        f"{module_id}: versions missing {key}")
            require(type(ver["versionCode"]) is int and 0 <= ver["versionCode"] <= MAX_INT,
                    f"{module_id}: version entry code")
            require(isinstance(ver["version"], str) and ver["version"],
                    f"{module_id}: version entry title")
            require(https_url(ver["zipUrl"]), f"{module_id}: insecure zipUrl")
            require(type(ver["timestamp"]) in (int, float) and
                    math.isfinite(ver["timestamp"]) and ver["timestamp"] >= 0,
                    f"{module_id}: invalid version timestamp")
        require(versions[0]["versionCode"] == code and
                versions[0]["version"] == module["version"],
                f"{module_id}: top-level version mismatch")

        origin = provenance["module_origins"].get(module_id)
        require(isinstance(origin, dict), f"{module_id}: missing provenance")
        zip_url = versions[0]["zipUrl"]
        if origin.get("kind") == "catalog":
            original += 1
            source = track["source"]
            require(source.startswith("https://github.com/"),
                    f"{module_id}: verified origin not GitHub")
            repo_key = source.removeprefix("https://github.com/").casefold()
            saved = state.get("repos", {}).get(repo_key, {})
            require(saved.get("valid") is True and saved.get("zip") == zip_url,
                    f"{module_id}: catalog provenance not backed by inspected ZIP")
        elif origin.get("kind") == "mmrl":
            source = origin.get("url")
            require(source in source_entries, f"{module_id}: unapproved federation source")
            require((module_id, code, zip_url) in source_entries[source],
                    f"{module_id}: origin absent from normalized source index")
        else:
            raise RuntimeError(f"{module_id}: unknown origin category")

    require(len(provenance["module_origins"]) == len(mmrl["modules"]),
            "MMRL provenance count mismatch")
    require(len(ksu) == len({m.get("repoUrl", "").casefold() for m in ksu}),
            "duplicate KernelSU GitHub repository")
    for module in ksu:
        repo = module.get("repoUrl")
        require(https_url(repo) and repo.startswith("https://github.com/"),
                "KSU source must be a GitHub repo")
        require(all(isinstance(module.get(key), str) and module[key].strip()
                    for key in ("name", "author", "description")),
                f"KSU entry incomplete: {repo}")
        require(module.get("visibility") == 1, f"KSU hidden item included: {repo}")
        key = repo.casefold()
        source = provenance["ksu_origins"].get(key)
        require(source is not None, f"KSU missing provenance: {repo}")
        if source == "catalog":
            state_key = repo.removeprefix("https://github.com/").casefold()
            entry = state.get("repos", {}).get(state_key, {})
            require(entry.get("valid") is True and entry.get("zip_count") == 1,
                    f"KSU catalog source not archive inspected: {repo}")
        else:
            require(key in ksu_entries.get(source, set()),
                    f"KSU source absent from official upstream list: {repo}")

    require(discovery.get("schema_version") == 2, "discovery schema")
    entries = discovery.get("entries")
    require(isinstance(entries, list) and len(entries) >= 1000,
            "original discovery catalog lost")
    require(len({e["id"] for e in entries}) == len(entries),
            "duplicate catalog ID")
    require(any(e["provider"] == "codeberg.org" for e in entries), "lost Codeberg projects")
    require(any(e["provider"] == "gitlab.com" for e in entries), "lost GitLab projects")
    require(any(e["kind"] == "patched_apk" for e in entries), "lost Morphe APKs")
    require(discovery["summary"]["total_entries"] == len(entries), "discovery count mismatch")
    require(report.get("catalog_entries") == len(entries), "reported discovery count mismatch")
    require(report.get("mmrl_modules") == len(mmrl["modules"]),
            "reported MMRL count mismatch")
    require(report.get("kernelsu_next_modules") == len(ksu),
            "reported KernelSU count mismatch")
    require(report.get("checked_repositories") <= report.get("github_repositories"),
            "catalog coverage mismatch")
    federation_report = report.get("federation", {})
    discovered_count = sum(entry.get("status") == "found" for entry in search_repos.values())
    require(federation_report.get("independent_discovery", {}).get("discovered_feeds")
            == discovered_count, "discovered source count mismatch")
    require(federation_report.get("unified_mmrl_modules") == len(mmrl["modules"]),
            "federation MMRL count mismatch")
    require(federation_report.get("unified_ksu_modules") == len(ksu),
            "federation KSU count mismatch")
    require(federation_report.get("base_mmrl_modules", 0) >= 200,
            "base catalog mysteriously shrank")
    require(federation_report.get("base_ksu_modules", 0) >= 100,
            "base KernelSU catalog mysteriously shrank")
    print(f"Validated federated feeds: {len(mmrl['modules'])} MMRL, "
          f"{len(ksu)} KernelSU Next, {len(entries)} discovery entries, "
          f"{len(federation_state['sources'])} cached upstream sources, "
          f"{original} MMRL entries from inspected catalog")


if __name__ == "__main__":
    validate()
