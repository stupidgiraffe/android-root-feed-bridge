#!/usr/bin/env python3
"""Maintain conservative MMRL and KernelSU Next indexes for Best Root Apps.

The complete catalog is discovery-only. Installation entries are emitted only
after inspecting official GitHub release ZIPs for a valid root module.prop.
No downloaded code is executed, and no binaries are mirrored.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

try:
    from catalog import build_discovery
except ModuleNotFoundError:  # when imported from the repository root in unit tests
    from scripts.catalog import build_discovery

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "krishna3163/best-root-apps-for-android"
UPSTREAM = "https://raw.githubusercontent.com/" + SOURCE + "/main/"
API = "https://api.github.com/"
MAX_MODULE_BYTES = 96 * 1024 * 1024
MAX_SOURCE_BYTES = 4 * 1024 * 1024
NEW_CHECKS_PER_RUN = 2000
NEGATIVE_RETRY_SECS = 48 * 3600
MAX_WORKERS = 8
BLOCKED_ASSETS = (
    "source", "debug", "symbols", "uninstaller", "uninstall",
    "magisk-manager", "manager-only", "boot.img", "vendor_boot",
)
HEADERS = {
    "User-Agent": "android-root-feed-bridge/2.0 (+https://github.com/stupidgiraffe/rootatlas)",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def request(url: str, *, limit: int = MAX_SOURCE_BYTES, timeout: int = 25) -> bytes:
    """Read a bounded response (including content-length check before buffering)."""
    if not url.startswith("https://"):
        raise ValueError("Refusing non-HTTPS URL: " + url)
    headers = HEADERS.copy()
    if url.startswith(API) and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > limit:
            raise ValueError("Response too large: " + url)
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ValueError("Response exceeds maximum allowed size: " + url)
        return body


def read_json(url: str, *, optional: bool = False, limit: int = MAX_SOURCE_BYTES):
    try:
        return json.loads(request(url, limit=limit).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if optional and exc.code in (404, 410, 422):
            return None
        raise


def json_file(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_catalog() -> dict:
    """Use the same README row contract as the upstream website generator."""
    readme = request(UPSTREAM + "README.md", limit=MAX_SOURCE_BYTES).decode("utf-8-sig")
    config = read_json(UPSTREAM + "config/apps.json")
    morphe = read_json(UPSTREAM + "data/morphe-releases.json", optional=True) or {}
    if not isinstance(config, dict) or not isinstance(morphe, dict):
        raise RuntimeError("Unexpected source JSON, refusing to publish")
    return build_discovery(readme, morphe, config)


def release(repo: str):
    return read_json(API + "repos/" + repo + "/releases/latest", optional=True)


def parse_prop(blob: bytes):
    props = {}
    for line in blob.decode("utf-8-sig", "replace").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            props[key.strip()] = value.strip()
    code = props.get("versionCode", "")
    if not re.fullmatch(r"[0-9]{1,10}", code) or int(code) > 2_147_483_647:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", props.get("id", "")):
        return None
    if not props.get("name") or not props.get("version"):
        return None
    return props


def inspect_asset(asset):
    """Statically examine a ZIP. module.prop at ZIP root is mandatory."""
    size = asset.get("size") or 0
    name = (asset.get("name") or "").lower()
    if not (0 < size <= MAX_MODULE_BYTES and name.endswith(".zip")):
        return None
    if any(word in name for word in BLOCKED_ASSETS):
        return None
    url = asset.get("browser_download_url", "")
    if not url.startswith("https://github.com/"):
        return None
    blob = request(url, limit=MAX_MODULE_BYTES, timeout=85)
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            if len(archive.infolist()) > 50_000:
                return None
            path = next((name for name in ("module.prop", "./module.prop")
                         if name in archive.namelist()), None)
            if not path or archive.getinfo(path).file_size > 16_384:
                return None
            return parse_prop(archive.read(path))
    except (zipfile.BadZipFile, RuntimeError, ValueError, OSError):
        return None


def timestamp(date: str) -> int:
    if not date:
        return int(time.time())
    try:
        return int(datetime.fromisoformat(date.replace("Z", "+00:00"))
                   .astimezone(timezone.utc).timestamp())
    except (ValueError, TypeError, OverflowError):
        return int(time.time())


def inspect(item: dict, previous: dict):
    """Get current release and inspect ZIP. Don't erase good state on fetch errors."""
    repo = item["repository"]
    now = int(time.time())
    before = previous.copy()
    try:
        rel = release(repo)
        if rel is None:
            return {"checked": now, "release_id": None, "valid": False,
                    "reason": "no_latest_release"}
        rid = rel.get("id")
        if rid is None:
            raise ValueError("release ID missing")
        if before.get("release_id") == rid and "valid" in before:
            before["checked"] = now
            return before
        assets = [a for a in rel.get("assets", []) if
                  (a.get("name") or "").lower().endswith(".zip")]
        found = []
        fetch_errors = 0
        for asset in assets:
            try:
                prop = inspect_asset(asset)
            except (TimeoutError, OSError, ValueError, urllib.error.HTTPError) as exc:
                fetch_errors += 1
                print(f"WARN {repo}/{asset.get('name')}: {exc}", file=sys.stderr)
                continue
            if prop:
                found.append((asset, prop))
        if not found:
            if fetch_errors:
                before["last_error"] = "asset_download_failed"
                return before
            return {"checked": now, "release_id": rid, "valid": False,
                    "reason": "no_valid_module_zip"}
        # One repo's release can carry different device/arch-specific ZIPs.
        # MMRL can present only one unambiguous module candidate for now.
        # Never arbitrarily pick among multiple different module.prop IDs.
        ids = {props["id"] for _, props in found}
        if len(ids) > 1:
            return {"checked": now, "release_id": rid, "valid": False,
                    "reason": "ambiguous_multiple_module_ids"}
        # Prefer archive explicitly described as universal when multiple valid.
        found.sort(key=lambda pair: (
            0 if "universal" in (pair[0].get("name") or "").lower() else 1,
            pair[0].get("name") or ""))
        asset, prop = found[0]
        date = rel.get("published_at") or rel.get("created_at") or ""
        return {
            "checked": now, "release_id": rid, "valid": True,
            "prop": {k: prop.get(k, "") for k in (
                "id", "name", "version", "versionCode", "author", "description")},
            "zip": asset["browser_download_url"], "zip_count": len(assets),
            "valid_zip_count": len(found), "timestamp": timestamp(date),
            "size": asset.get("size", 0), "asset_name": asset.get("name") or "",
            "reason": "verified_zip_metadata",
        }
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        print(f"WARN keeping previous state for {repo}: {exc}", file=sys.stderr)
        before["last_error"] = type(exc).__name__
        return before


def collect_repositories(entries: list[dict]):
    """Exactly the unique GitHub repos from catalog and official trackers."""
    repos = {}
    for entry in entries:
        repo = entry.get("repository", "")
        if repo:
            repos.setdefault(repo.casefold(), {
                "repository": repo, "name": entry["name"],
                "description": entry.get("description", ""),
                "frameworks": entry.get("frameworks", []),
            })
    return repos


def create_indexes(discovery: dict, state: dict, now: int):
    repos = collect_repositories(discovery["entries"])
    modules, ksu, seen_ids = [], [], set()
    # Prefer the newest inspected release when forks publish the same
    # module.prop id. MMRL supports one ID per feed; alternative repositories
    # remain individually discoverable in KernelSU Next.
    for key in sorted(repos, key=lambda k: (-state.get(k, {}).get("timestamp", 0), k)):
        item, entry = repos[key], state.get(key, {})
        if not entry.get("valid"):
            continue
        prop = entry.get("prop") or {}
        identifier = prop.get("id")
        if not identifier:
            continue
        code = int(prop["versionCode"])
        url = "https://github.com/" + item["repository"]
        description = (prop.get("description") or item["description"])[:500]
        if not description:
            description = "Root module; inspect upstream source for compatibility."
        # KernelSU Next dedupes by name + repoUrl, not module.prop ID.
        if entry.get("zip_count") == 1 and entry.get("valid_zip_count", 1) == 1:
            ksu.append({
                "name": prop["name"], "description": description[:350],
                "author": prop.get("author") or item["repository"].split("/")[0],
                "repoUrl": url, "visibility": 1,
            })
        if identifier in seen_ids:
            continue
        seen_ids.add(identifier)
        modules.append({
            "id": identifier, "name": prop["name"], "version": prop["version"],
            "versionCode": code,
            "author": prop.get("author") or item["repository"].split("/")[0],
            "description": description, "homepage": url,
            "size": int(entry["size"]), "verified": False,
            "track": {"type": "GIT", "added": float(entry["timestamp"]), "source": url},
            "versions": [{
                "version": prop["version"], "versionCode": code,
                "zipUrl": entry["zip"], "timestamp": float(entry["timestamp"]),
                "size": int(entry["size"]),
            }],
        })
    modules.sort(key=lambda m: (m["name"].casefold(), m["id"]))
    ksu.sort(key=lambda m: (m["name"].casefold(), m["repoUrl"]))
    return modules, ksu


def main():
    discovery = source_catalog()
    now = int(time.time())
    previous_discovery = json_file(ROOT / "discovery.json", {"entries": []})
    old_total = len(previous_discovery.get("entries", []))
    if old_total and len(discovery["entries"]) < old_total * 0.75:
        raise RuntimeError("Upstream catalog shrank >25%; retaining last published files")
    repositories = collect_repositories(discovery["entries"])
    old = json_file(ROOT / "state.json", {"repos": {}}).get("repos", {})
    state = {key: old.get(key, {}) for key in repositories}

    due = []
    for key, item in repositories.items():
        prior = state[key]
        if prior.get("valid") or now - prior.get("checked", 0) >= NEGATIVE_RETRY_SECS:
            due.append((key, item, prior))
    # Check every formerly valid module; then never-before-seen candidates;
    # then oldest negative results. New candidates are never starved.
    due.sort(key=lambda x: (
        0 if x[2].get("valid") else 1 if not x[2] else 2,
        x[2].get("checked", 0),
        x[0],
    ))
    checked_now = due[:NEW_CHECKS_PER_RUN]
    if checked_now:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(inspect, item, previous): key
                       for key, item, previous in checked_now}
            for future in as_completed(futures):
                state[futures[future]] = future.result()

    base_modules, base_ksu = create_indexes(discovery, state, now)
    try:
        from federation import federate
    except ModuleNotFoundError:  # test/import path from the repository root
        from scripts.federation import federate
    modules, ksu, federation_state, federation_audit, federation_report, search_state = federate(
        ROOT, base_modules, base_ksu,
        lambda url: read_json(url, limit=16 * 1024 * 1024), now
    )
    previous_modules = json_file(ROOT / "json/modules.json", {"modules": []}).get("modules", [])
    if not modules:
        raise RuntimeError("Zero valid modules; refusing to publish empty feeds")
    if len(previous_modules) >= 30 and len(modules) < len(previous_modules) * 0.75:
        raise RuntimeError("Verified module count dropped >25%; refusing destructive feed update")
    checked = sum("checked" in state[key] for key in repositories)
    valid = sum(bool(state[key].get("valid")) for key in repositories)
    discovery["updated"] = now
    discovery["summary"].update({
        "repository_candidates": len(repositories),
        "checked_repositories": checked,
        "pending_repositories": len(repositories) - checked,
        "valid_module_repositories": valid,
        "mmrl_modules": len(modules),
        "kernelsu_next_modules": len(ksu),
        "catalog_mmrl_modules": len(base_modules),
        "catalog_kernelsu_next_modules": len(base_ksu),
        "federated_mmrl_sources": federation_report["mmrl_upstream_sources"],
        "federated_ksu_sources": federation_report["ksu_upstream_sources"],
    })
    report = {
        "updated": now, "source": SOURCE,
        "catalog_entries": len(discovery["entries"]),
        "catalog_readme_entries": discovery["summary"]["readme_entries"],
        "morphe_apks": discovery["summary"]["morphe_entries"],
        "tracked_extras": discovery["summary"]["tracker_extras"],
        "github_repositories": len(repositories),
        "checked_repositories": checked,
        "pending_repositories": len(repositories) - checked,
        "checked_this_run": len(checked_now),
        "verified_module_repositories": valid,
        "mmrl_modules": len(modules),
        "kernelsu_next_modules": len(ksu),
        "catalog_mmrl_modules": len(base_modules),
        "catalog_ksu_modules": len(base_ksu),
        "federation": federation_report,
        "exclusions_by_reason": {
            reason: sum(v.get("reason") == reason for v in state.values())
            for reason in sorted({v.get("reason") for v in state.values() if v.get("reason")})
            if reason != "verified_zip_metadata"
        },
    }

    # Stage all serializable outputs in memory before touching disk.
    cover = ("https://raw.githubusercontent.com/stupidgiraffe/"
             "android-root-feed-bridge/main/assets/root-feed-banner.jpg")
    mmrl = {
        "name": "RootAtlas — Android Module Index",
        "website": "https://github.com/stupidgiraffe/rootatlas",
        "cover": cover,
        "description": "RootAtlas unifies independent Android module repositories with transparent provenance and daily sync.",
        "metadata": {"version": 1, "timestamp": float(now)},
        "modules": modules,
    }
    config = {
        "name": mmrl["name"], "website": mmrl["website"],
        "cover": cover, "description": mmrl["description"],
    }
    write_json(ROOT / "json/modules.json", mmrl)
    write_json(ROOT / "json/config.json", config)
    write_json(ROOT / "ksu/modules.json", ksu)
    write_json(ROOT / "discovery.json", discovery)
    write_json(ROOT / "report.json", report)
    write_json(ROOT / "federation-state.json", federation_state)
    write_json(ROOT / "federation-provenance.json", federation_audit)
    write_json(ROOT / "source-discovery-state.json", search_state)
    write_json(ROOT / "state.json", {"schema_version": 2, "generated": now, "repos": state})
    print("RESULT " + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
