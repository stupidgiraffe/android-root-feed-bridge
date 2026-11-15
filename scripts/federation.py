"""Federate curated MMRL and KernelSU Next upstream feeds.

Original ZIPs/URLs remain upstream. Never invent timestamps or hide invalid
payloads behind synthetic defaults. Bad modules or failing sources are skipped
without blanking the previously published catalogue.
"""
from __future__ import annotations

import copy
import json
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SCHEMA_VERSION = 1
MAX_INDEX_BYTES = 16 * 1024 * 1024
ALLOWED_TRACK = {"UNKNOWN", "ONLINE_JSON", "ONLINE_ZIP", "GIT", "LOCAL_JSON", "LOCAL_ZIP"}
REPO = re.compile(r"^https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/?$", re.I)
MODULE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,180}$")
INT32 = 2_147_483_647
STR_FIELDS = ("description", "homepage", "icon", "cover", "donate", "support", "license", "readme")
LIST_FIELDS = ("categories", "arch", "devices", "screenshots", "require", "permissions")


def https_url(value) -> bool:
    if not isinstance(value, str) or not value.startswith("https://"):
        return False
    try:
        parsed = urlsplit(value)
        return bool(parsed.hostname and not parsed.username and not parsed.password)
    except ValueError:
        return False


def canonical_base(url: str) -> str:
    if not https_url(url):
        raise ValueError("repository must be a public HTTPS URL")
    parsed = urlsplit(url)
    if parsed.query or parsed.fragment:
        raise ValueError("repository base cannot include query or fragment")
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", parsed.netloc.lower(), path, "", "")) + "/"


def canonical_github(url: str) -> str | None:
    if not https_url(url):
        return None
    parsed = urlsplit(url)
    if parsed.hostname.casefold() != "github.com" or parsed.query or parsed.fragment:
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or not re.fullmatch(r"[A-Za-z0-9-]+", parts[0]):
        return None
    repo = parts[1].removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        return None
    return f"https://github.com/{parts[0]}/{repo}"


def finite_number(x):
    return type(x) in (float, int) and math.isfinite(x) and x >= 0


def parse_code(value):
    if type(value) is int and 0 <= value <= INT32:
        return value
    return None


def normalize_mmrl(item: dict) -> dict | None:
    if not isinstance(item, dict):
        return None
    identifier, name, author = item.get("id"), item.get("name"), item.get("author")
    if not (isinstance(identifier, str) and MODULE_ID.fullmatch(identifier) and
            isinstance(name, str) and 0 < len(name.strip()) <= 220 and
            isinstance(author, str) and 0 < len(author.strip()) <= 220):
        return None
    track = item.get("track")
    if not isinstance(track, dict) or track.get("type") not in ALLOWED_TRACK:
        return None
    added = track.get("added")
    if not finite_number(added):
        added = 0.0
    src = track.get("source")
    trk = {"type": track["type"], "added": float(added),
           "source": src if https_url(src) else ""}
    versions = []
    seen_codes = set()
    for v in item.get("versions") or []:
        if not isinstance(v, dict):
            continue
        code = parse_code(v.get("versionCode"))
        ts = v.get("timestamp")
        url = v.get("zipUrl")
        version = v.get("version")
        if (code is None or not finite_number(ts) or not https_url(url) or
                not isinstance(version, str) or not version.strip()):
            continue
        if code in seen_codes:
            continue
        seen_codes.add(code)
        result = {"versionCode": code, "version": version[:150],
                  "timestamp": float(ts), "zipUrl": url}
        if type(v.get("size")) is int and 0 < v["size"] <= INT32:
            result["size"] = v["size"]
        if isinstance(v.get("changelog"), str):
            result["changelog"] = v["changelog"][:25000]
        versions.append(result)
    if not versions:
        return None
    versions.sort(key=lambda z: (z["versionCode"], z["timestamp"]), reverse=True)
    latest = versions[0]
    mod = {"id": identifier, "name": name.strip()[:220],
           "author": author.strip()[:220], "version": latest["version"],
           "versionCode": latest["versionCode"], "track": trk,
           "versions": versions[:5], "verified": False}
    for field in STR_FIELDS:
        value = item.get(field)
        if isinstance(value, str) and len(value) <= 15000:
            if field in ("homepage", "icon", "cover", "donate", "support", "readme"):
                if not https_url(value):
                    continue
            mod[field] = value
    for field in LIST_FIELDS:
        value = item.get(field)
        if (isinstance(value, list) and len(value) <= 30
                and all(isinstance(s, str) and len(s) <= 512 for s in value)):
            mod[field] = value
    for field in ("minApi", "maxApi", "size", "stars"):
        value = item.get(field)
        if type(value) is int and 0 <= value <= INT32:
            mod[field] = value
    return mod


def normalize_ksu(item) -> dict | None:
    if not isinstance(item, dict):
        return None
    repo = canonical_github(item.get("repoUrl", ""))
    if not repo:
        return None
    name = item.get("name")
    author = item.get("author")
    description = item.get("description")
    if not all(isinstance(v, str) and 0 < len(v.strip()) <= 1500
               for v in (name, author, description)):
        return None
    if item.get("visibility", 1) != 1:
        return None
    mod = {"name": name.strip()[:250], "description": description.strip()[:1000],
           "author": author.strip()[:250], "repoUrl": repo, "visibility": 1}
    for field in ("bannerUrl", "license"):
        val = item.get(field)
        if field == "bannerUrl" and https_url(val):
            mod[field] = val
        elif field == "license" and isinstance(val, str) and len(val) < 150:
            mod[field] = val
    return mod


def load_curated(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("Unexpected federation source format")
    return data


def gather_feeds(config: dict, get_json):
    """Get all curated and official-discovery sources; directory failure is soft."""
    mmrl = {canonical_base(url) for url in config["mmrl"]}
    notes = []
    directory = config.get("mmrl_directory")
    if directory:
        try:
            remote = get_json(directory)
            if not isinstance(remote, list):
                raise ValueError("MMRL directory is not an array")
            if len(remote) > 1000:
                raise ValueError("Unexpectedly large public directory")
            mmrl.update(canonical_base(url) for url in remote)
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            notes.append(f"Official MMRL directory unavailable: {type(exc).__name__}")
    self_base = canonical_base("https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/")
    mmrl.discard(self_base)
    ksu = [entry for entry in config["ksunext"] if entry.get("enabled", False)]
    return sorted(mmrl), ksu, notes


def fetch_all(mmrl_urls, ksu_sources, fetch_json, previous, now):
    """Parallel source ingestion; last-good cache is used on fetch/schema failures."""
    tasks = [("mmrl", url, url.rstrip("/") + "/json/modules.json")
             for url in mmrl_urls]
    tasks += [("ksunext", source["name"], source["url"])
              for source in ksu_sources]
    states, failures, fresh, malformed = {}, [], 0, 0

    def job(kind, label, url):
        nonlocal malformed
        data = fetch_json(url)
        if kind == "mmrl":
            if not isinstance(data, dict) or not isinstance(data.get("modules"), list):
                raise ValueError("Not an MMRL modules index")
            if len(data["modules"]) > 20000:
                raise ValueError("MMRL index exceeds module limit")
            normalized = [v for item in data["modules"]
                          if (v := normalize_mmrl(item)) is not None]
            invalid = len(data["modules"]) - len(normalized)
        else:
            if not isinstance(data, list) or len(data) > 10000:
                raise ValueError("Not a KernelSU Next module array")
            normalized = [v for item in data if (v := normalize_ksu(item)) is not None]
            invalid = len(data) - len(normalized)
        if not normalized:
            raise ValueError("No valid entries; retaining previous source")
        return {"kind": kind, "source": label, "url": url, "count": len(normalized),
                "invalid": invalid, "last_success": now, "entries": normalized}

    with ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(job, *task): task for task in tasks}
        for fut in as_completed(future_map):
            kind, label, url = future_map[fut]
            key = kind + ":" + url
            try:
                value = fut.result()
                fresh += 1
                malformed += value["invalid"]
                states[key] = value
            except (OSError, ValueError, TimeoutError, RuntimeError, TypeError) as exc:
                old = previous.get("sources", {}).get(key)
                if isinstance(old, dict) and old.get("entries") and old.get("kind") == kind:
                    states[key] = old
                    status = "stale"
                else:
                    status = "excluded"
                failures.append({"kind": kind, "source": label, "status": status,
                                 "error": type(exc).__name__})
    return states, {"fetched": fresh, "failed": len(failures),
                    "malformed_modules": malformed, "failures": failures,
                    "total": len(tasks)}


def merge(base_mmrl: list, base_ksu: list, states: dict):
    """Deduplicate MMRL by ID, KSU Next by GitHub repository URL."""
    chosen = {}
    origins = {}
    conflict_counts = {}
    for base in base_mmrl:
        chosen[base["id"]] = copy.deepcopy(base)
        origins[base["id"]] = {"kind": "catalog", "url": base.get("homepage", "")}
    external = []
    # Curated sources are evaluated before uncurated GitHub discoveries.
    # Automatically discovered repositories must NEVER shadow an existing
    # module ID, even with a forged higher versionCode.
    for key, state in sorted(states.items(), key=lambda pair: (
        1 if pair[1].get("tier") == "discovered" else 0, pair[0])):
        if state.get("kind") != "mmrl":
            continue
        for item in state.get("entries", []):
            external.append((item, state["source"], state.get("tier", "curated")))
    for item, origin, tier in external:
        identifier = item["id"]
        incumbent = chosen.get(identifier)
        if incumbent is None:
            chosen[identifier] = item
            origins[identifier] = {"kind": "mmrl", "url": origin}
            continue
        conflict_counts[identifier] = conflict_counts.get(identifier, 0) + 1
        if tier == "discovered":
            # Do not let a random search result usurp known publishers.
            continue
        # VersionCode is the primary ordering for Android modules; stable
        # ordering means exact ties continue using existing/catalog source.
        if (item["versionCode"], item["versions"][0]["timestamp"]) > (
            incumbent["versionCode"], incumbent["versions"][0]["timestamp"]):
            chosen[identifier] = item
            origins[identifier] = {"kind": "mmrl", "url": origin}
    mmrl = sorted(chosen.values(), key=lambda m: (m["name"].casefold(), m["id"]))
    ksu_map = {canonical_github(m.get("repoUrl", "")) .casefold(): copy.deepcopy(m)
               for m in base_ksu if canonical_github(m.get("repoUrl", ""))}
    ksu_origins = {k: "catalog" for k in ksu_map}
    for key, state in sorted(states.items()):
        if state.get("kind") != "ksunext":
            continue
        for item in state.get("entries", []):
            key_repo = item["repoUrl"].casefold()
            if key_repo not in ksu_map:
                ksu_map[key_repo] = item
                ksu_origins[key_repo] = state["source"]
            else:
                # The official manifest can supply richer nonfunctional metadata.
                for field in ("bannerUrl", "license"):
                    if field in item and field not in ksu_map[key_repo]:
                        ksu_map[key_repo][field] = item[field]
    ksu = sorted(ksu_map.values(), key=lambda m: (m["name"].casefold(), m["repoUrl"]))
    audit = {"module_origins": origins, "module_conflicts": conflict_counts,
             "ksu_origins": ksu_origins}
    return mmrl, ksu, audit


def federate(root: Path, base_mmrl: list, base_ksu: list, request_json, now: int):
    config = load_curated(root / "sources/federation.json")
    old = {}
    state_path = root / "federation-state.json"
    try:
        old = json.loads(state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        pass
    mmrl_urls, ksu_sources, notes = gather_feeds(config, request_json)
    curated_mmrl = set(mmrl_urls)
    curated_ksu = {entry["url"] for entry in ksu_sources}

    try:
        from source_discovery import discover
    except ModuleNotFoundError:
        from scripts.source_discovery import discover
    search_state_path = root / "source-discovery-state.json"
    try:
        previous_search = json.loads(search_state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        previous_search = {}
    new_sources, search_state, search_report = discover(
        previous_search,
        lambda url, limit, timeout: request_json(url),
        now,
    )
    for source in new_sources:
        if source["kind"] == "mmrl" and source["url"].endswith("/json/modules.json"):
            mmrl_urls.append(source["url"][:-len("json/modules.json")])
        elif source["kind"] == "ksunext" and source["url"].endswith("/modules.json"):
            ksu_sources.append({"name": source["repository"], "url": source["url"]})
    mmrl_urls = sorted(set(canonical_base(url) for url in mmrl_urls))
    ksu_sources = list({s["url"]: s for s in ksu_sources}.values())

    states, report = fetch_all(mmrl_urls, ksu_sources, request_json, old, now)
    for value in states.values():
        if value["kind"] == "mmrl":
            base = value["url"][:-len("json/modules.json")] if value["url"].endswith("json/modules.json") else ""
            value["tier"] = "curated" if base in curated_mmrl else "discovered"
        elif value["kind"] == "ksunext":
            value["tier"] = "curated" if value["url"] in curated_ksu else "discovered"
    if not states:
        raise RuntimeError("No usable federation sources; preserving existing outputs")
    mmrl, ksu, audit = merge(base_mmrl, base_ksu, states)
    report.update({
        "mmrl_upstream_sources": len(mmrl_urls),
        "ksu_upstream_sources": len(ksu_sources),
        "base_mmrl_modules": len(base_mmrl),
        "base_ksu_modules": len(base_ksu),
        "unified_mmrl_modules": len(mmrl),
        "unified_ksu_modules": len(ksu),
        "mmrl_external_selected": sum(o["kind"] == "mmrl" for o in audit["module_origins"].values()),
        "ksu_external_selected": sum(o != "catalog" for o in audit["ksu_origins"].values()),
        "duplicate_ids_resolved": len(audit["module_conflicts"]),
        "directory_notes": notes,
        "independent_discovery": search_report,
    })
    return (mmrl, ksu, {"schema_version": 1, "generated": now, "sources": states},
            audit, report, search_state)
