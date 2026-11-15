#!/usr/bin/env python3
"""Build conservative MMRL and KernelSU Next indexes from a root-app catalog.

Only publish releases with an inspectable module.prop at the ZIP root.
Untrusted downloads are never executed.
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

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "krishna3163/best-root-apps-for-android"
UPSTREAM = "https://raw.githubusercontent.com/" + SOURCE + "/main/"
API = "https://api.github.com/"
MODULE_LIMIT = 35 * 1024 * 1024
NEW_CHECKS_PER_RUN = 240
NEGATIVE_RETRY_SECS = 7 * 86400
NAME_URL = re.compile(r"\[([^\]]{2,100})\]\(https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)(?:[^)]*)\)", re.I)
REPO_RE = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$")
DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"
BLOCKED_ASSETS = ("source", "debug", "symbols", "uninstaller", "uninstall", "magisk-manager", "manager-only")
HEADERS = {
    "User-Agent": "android-root-feed-bridge/1.0 (+https://github.com/stupidgiraffe/android-root-feed-bridge)",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def request(url: str, *, limit: int = 8 * 1024 * 1024, timeout: int = 25) -> bytes:
    headers = HEADERS.copy()
    if url.startswith(API) and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > limit:
            raise ValueError("Response too large: " + url)
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ValueError("Response exceeds byte limit: " + url)
        return body


def read_json(url: str, *, optional: bool = False):
    try:
        return json.loads(request(url).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if optional and exc.code in (404, 410, 422):
            return None
        raise


def json_file(path: Path, default):
    try:
        return json.loads(path.read_text("utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sources():
    catalog = request(UPSTREAM + "README.md", limit=3 * 1024 * 1024).decode("utf-8")
    config = read_json(UPSTREAM + "config/apps.json")
    entries = {}
    heading = "Root Apps"
    for line in catalog.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            heading = re.sub(r"[*#]", "", line).strip()
        if not line.lstrip().startswith("|"):
            continue
        match = NAME_URL.search(line)
        if not match:
            continue
        name, owner, repo = match.groups()
        repo = repo.removesuffix(".git")
        full = owner + "/" + repo
        if not REPO_RE.fullmatch(full):
            continue
        parts = [re.sub(r"<[^>]+>|\*", "", part).strip()
                 for part in line.strip().strip("|").split("|")]
        description = " ".join(parts[1:3])[:450] if len(parts) >= 2 else ""
        item = {"name": name.strip(), "repository": full,
                "description": description, "category": heading}
        entries.setdefault(full.lower(), item)
    for item in config.get("apps", []):
        full = item.get("repository", "")
        if REPO_RE.fullmatch(full) and item.get("enabled", True):
            entries.setdefault(full.lower(), {
                "name": item.get("name", full), "repository": full,
                "description": "Upstream release tracker", "category": "Tracked root apps"
            })
    if len(entries) < 60:
        raise RuntimeError(f"Upstream catalog unexpectedly small ({len(entries)}); keeping previous feeds")
    return list(entries.values())


def release(repo: str):
    return read_json(API + "repos/" + repo + "/releases/latest", optional=True)


def parse_prop(blob: bytes):
    prop = {}
    for line in blob.decode("utf-8-sig", "replace").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            prop[key.strip()] = value.strip()
    code = prop.get("versionCode", "")
    if not re.fullmatch(r"[0-9]{1,10}", code) or int(code) > 2147483647:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", prop.get("id", "")):
        return None
    if not prop.get("name") or not prop.get("version"):
        return None
    return prop


def inspect_asset(asset):
    size = asset.get("size") or 0
    name = (asset.get("name") or "").lower()
    if not (0 < size <= MODULE_LIMIT and name.endswith(".zip")):
        return None
    if any(bad in name for bad in BLOCKED_ASSETS):
        return None
    url = asset.get("browser_download_url", "")
    if not url.startswith("https://github.com/"):
        return None
    blob = request(url, limit=MODULE_LIMIT, timeout=65)
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            files = set(archive.namelist())
            if "module.prop" not in files and "./module.prop" not in files:
                return None
            path = "module.prop" if "module.prop" in files else "./module.prop"
            if archive.getinfo(path).file_size > 16384:
                return None
            return parse_prop(archive.read(path))
    except (zipfile.BadZipFile, RuntimeError, ValueError):
        return None


def inspect(item, previous):
    repo = item["repository"]
    updated = dict(previous)
    try:
        rel = release(repo)
        if rel is None:
            return {"checked": int(time.time()), "release_id": None, "valid": False}
        rid = rel.get("id")
        if previous.get("release_id") == rid:
            return updated
        assets = [a for a in rel.get("assets", [])
                  if (a.get("name") or "").lower().endswith(".zip")]
        prop = None
        chosen = None
        for asset in assets:
            try:
                prop = inspect_asset(asset)
            except (TimeoutError, OSError, ValueError) as exc:
                print(f"Could not inspect {repo} asset {asset.get('name')}: {exc}", file=sys.stderr)
            if prop:
                chosen = asset
                break
        if not prop or not chosen:
            return {"checked": int(time.time()), "release_id": rid, "valid": False}
        date = rel.get("published_at") or rel.get("created_at") or ""
        ts = (int(datetime.strptime(date[:19] + "Z", DATE_FMT)
                  .replace(tzinfo=timezone.utc).timestamp())
              if len(date) >= 19 else int(time.time()))
        return {
            "checked": int(time.time()), "release_id": rid, "valid": True,
            "prop": {key: prop.get(key, "") for key in
                     ("id", "name", "version", "versionCode", "author", "description")},
            "zip": chosen["browser_download_url"], "zip_count": len(assets),
            "timestamp": ts, "size": chosen.get("size", 0),
        }
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Keeping last-known state for {repo}: {exc}", file=sys.stderr)
        return updated


def main():
    items = sources()
    now = int(time.time())
    old = json_file(ROOT / "state.json", {"repos": {}}).get("repos", {})
    candidates = {item["repository"].lower(): item for item in items}
    state = {}
    pending = []
    for key, item in candidates.items():
        prev = old.get(key, {})
        state[key] = prev
        if prev.get("valid") or now - prev.get("checked", 0) > NEGATIVE_RETRY_SECS:
            pending.append((key, item, prev))
    pending.sort(key=lambda x: (
        0 if not x[2] else 1 if x[2].get("valid") else 2,
        x[2].get("checked", 0), x[0]))
    active = [x for x in pending if x[2].get("valid")]
    inactive = [x for x in pending if not x[2].get("valid")]
    selected = active + inactive[:NEW_CHECKS_PER_RUN]
    if selected:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(inspect, item, prev): key
                       for key, item, prev in selected}
            for future in as_completed(futures):
                state[futures[future]] = future.result()

    modules = []
    ksu = []
    ids = set()
    for key in sorted(candidates):
        item, entry = candidates[key], state.get(key, {})
        if not entry.get("valid"):
            continue
        prop = entry["prop"]
        if prop["id"] in ids:
            continue
        ids.add(prop["id"])
        code = int(prop["versionCode"])
        url = "https://github.com/" + item["repository"]
        description = (prop.get("description") or item["description"])[:500]
        modules.append({
            "id": prop["id"], "name": prop["name"],
            "version": prop["version"], "versionCode": code,
            "author": prop.get("author") or item["repository"].split("/")[0],
            "description": description, "homepage": url, "size": entry["size"],
            "verified": False,
            "track": {"type": "GIT", "added": float(entry["timestamp"]), "source": url},
            "versions": [{"version": prop["version"], "versionCode": code,
                          "zipUrl": entry["zip"], "timestamp": float(entry["timestamp"])}],
        })
        # KSU Next selects the *first* ZIP on the latest GitHub release,
        # so do not include ambiguous releases with multiple ZIP assets.
        if entry.get("zip_count") == 1:
            ksu.append({
                "name": prop["name"], "description": description[:350],
                "author": prop.get("author") or item["repository"].split("/")[0],
                "repoUrl": url, "visibility": 1,
            })
    if not modules:
        raise RuntimeError("Zero verified installable modules; preserving previous published feeds")
    modules.sort(key=lambda x: x["name"].casefold())
    ksu.sort(key=lambda x: x["name"].casefold())
    write_json(ROOT / "json/modules.json", {
        "name": "Root Feed Bridge (Best Root Apps)",
        "website": "https://github.com/stupidgiraffe/android-root-feed-bridge",
        "description": "Verified root module ZIPs discovered in Best Root Apps for Android.",
        "metadata": {"version": 1, "timestamp": float(now)},
        "modules": modules,
    })
    write_json(ROOT / "ksu/modules.json", ksu)
    write_json(ROOT / "discovery.json", {
        "source": "https://github.com/" + SOURCE,
        "updated": now, "total": len(items), "entries": items,
    })
    write_json(ROOT / "state.json", {"generated": now, "repos": state})
    print(f"Source entries: {len(items)}; checked: {len(selected)}; "
          f"MMRL: {len(modules)}; KernelSU Next: {len(ksu)}")


if __name__ == "__main__":
    main()
