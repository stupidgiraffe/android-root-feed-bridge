"""Bounded, reproducible discovery of independent Android root-module feeds.

Searches GitHub *repository* metadata only, then probes exact public MMRL
and KernelSU Next JSON contracts. No scraping arbitrary web pages, no
installation, and no wholesale trust of GitHub search results.
"""
from __future__ import annotations

import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

SEARCH_QUERIES = (
    "mmrl-repo in:name archived:false fork:false",
    "magisk-module-repo in:name archived:false fork:false",
    "MMRL modules repository in:description archived:false fork:false",
    "magisk modules repository in:description archived:false fork:false",
    "kernelsu modules repo in:description archived:false fork:false",
    "magisk modules mmrl in:readme archived:false fork:false",
)
PROBE_LIMIT = 96  # new repository candidates per run
NEGATIVE_RETRY = 14 * 86400
QUERY_PER_PAGE = 45
MAX_INDEX = 4 * 1024 * 1024
REPOSITORY = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$")
VERSION = 1
SELF_REPO = "stupidgiraffe/android-root-feed-bridge"
SKIP_NAME_TOKENS = ("template", "example", "demo", "installer_api_test", "gh-repo-clone")



def eligible_repository(full: str) -> bool:
    if not REPOSITORY.fullmatch(full) or full.casefold() == SELF_REPO:
        return False
    name = full.split("/")[-1].lower()
    return not any(token in name for token in SKIP_NAME_TOKENS)


def candidate_urls(repo: dict) -> list[tuple[str, str]]:
    """Prefer raw GitHub URLs: they work even when Pages is disabled."""
    full = repo.get("full_name") or ""
    branch = repo.get("default_branch") or "main"
    if not eligible_repository(full) or not re.fullmatch(r"[A-Za-z0-9_.\-/]+", branch):
        return []
    owner, name = full.split("/")
    raw = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/"
    pages = f"https://{owner.lower()}.github.io/{name}/"
    return [
        ("mmrl", raw + "json/modules.json"),
        ("mmrl", pages + "json/modules.json"),
        ("ksunext", raw + "modules.json"),
        ("ksunext", pages + "modules.json"),
    ]


def inspect_candidate(repo: dict, get_json) -> dict:
    """Accept a candidate only if a real valid module is present."""
    try:
        from federation import normalize_ksu, normalize_mmrl
    except ModuleNotFoundError:
        from scripts.federation import normalize_ksu, normalize_mmrl
    last_error = "no_module_index"
    for kind, url in candidate_urls(repo):
        try:
            data = get_json(url, MAX_INDEX, 16)
        except (OSError, ValueError, TypeError, TimeoutError, RuntimeError) as exc:
            last_error = type(exc).__name__
            continue
        if kind == "mmrl":
            if not isinstance(data, dict) or not isinstance(data.get("modules"), list):
                continue
            if len(data["modules"]) > 10000:
                continue
            valid = sum(normalize_mmrl(item) is not None for item in data["modules"])
        else:
            if not isinstance(data, list) or len(data) > 10000:
                continue
            valid = sum(normalize_ksu(item) is not None for item in data)
        if valid:
            return {"kind": kind, "url": url, "modules": valid,
                    "status": "found", "repository": repo["full_name"]}
    return {"kind": "none", "status": "unmatched", "repository": repo["full_name"],
            "last_error": last_error}


def search_github(get_json, now: int):
    """GitHub search is discovery, not authority; a failed query is non-fatal."""
    repos, errors = {}, []
    # One stable search for exact repo names; rotate broad searches to spread
    # coverage without exhausting GitHub's search-rate quota.
    queries = [SEARCH_QUERIES[0], SEARCH_QUERIES[1]]
    others = SEARCH_QUERIES[2:]
    index = (now // 86400) % len(others)
    queries += [others[index], others[(index + 1) % len(others)]]
    for query in queries:
        # Alternate page 1 and page 2 on successive days.
        for page in (1, 2):
            params = urllib.parse.urlencode({
                "q": query, "sort": "updated", "order": "desc",
                "per_page": QUERY_PER_PAGE, "page": page,
            })
            try:
                response = get_json("https://api.github.com/search/repositories?" + params,
                                    3 * 1024 * 1024, 25)
                if not isinstance(response, dict) or not isinstance(response.get("items"), list):
                    raise ValueError("Unexpected GitHub search result")
                for item in response["items"]:
                    full = item.get("full_name") or ""
                    if (not eligible_repository(full) or item.get("archived") or
                            item.get("fork") or not item.get("default_branch") or
                            item.get("size", 0) == 0):
                        continue
                    repos[full.casefold()] = {
                        "full_name": full, "default_branch": item["default_branch"],
                    }
            except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
                errors.append({"query": query, "page": page,
                               "error": type(exc).__name__})
    return repos, errors


def discover(previous: dict, get_json, now: int):
    """Return working new feeds and compact persistent candidate-search state."""
    prior = previous.get("repositories", {}) if previous.get("version") == VERSION else {}
    found, errors = search_github(get_json, now)
    known = {}
    for key, saved in prior.items():
        if not isinstance(saved, dict):
            continue
        repo = saved.get("repository")
        if isinstance(repo, str) and eligible_repository(repo):
            known[key] = saved.copy()
    todo = []
    for key, item in found.items():
        old = known.get(key, {})
        if old.get("status") == "found":
            continue
        if old.get("checked", 0) and now - old["checked"] < NEGATIVE_RETRY:
            continue
        todo.append((key, item))
    todo.sort(key=lambda x: (known.get(x[0], {}).get("checked", 0), x[0]))
    to_check = todo[:PROBE_LIMIT]
    checked = 0
    if to_check:
        with ThreadPoolExecutor(max_workers=8) as pool:
            pending = {pool.submit(inspect_candidate, item, get_json): key
                       for key, item in to_check}
            for future in as_completed(pending):
                key = pending[future]
                try:
                    result = future.result()
                except Exception as exc:  # Never let one candidate block publishing.
                    result = {"status": "error", "kind": "none",
                              "repository": found[key]["full_name"],
                              "last_error": type(exc).__name__}
                result["checked"] = now
                known[key] = result
                checked += 1
    sources = [
        item for item in known.values()
        if item.get("status") == "found" and
        item.get("kind") in ("mmrl", "ksunext") and
        isinstance(item.get("url"), str) and item["url"].startswith("https://")
    ]
    sources.sort(key=lambda x: (x["kind"], x["url"]))
    report = {
        "github_queries": 8, "github_search_errors": errors,
        "github_search_candidates_this_run": len(found),
        "new_candidates_inspected": checked,
        "remaining_unchecked_candidates": len(todo) - checked,
        "candidates_ever_checked": sum("checked" in x for x in known.values()),
        "discovered_feeds": len(sources),
        "discovered_mmrl_feeds": sum(x["kind"] == "mmrl" for x in sources),
        "discovered_ksu_feeds": sum(x["kind"] == "ksunext" for x in sources),
    }
    return sources, {"version": VERSION, "generated": now, "repositories": known}, report
