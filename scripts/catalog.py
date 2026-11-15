"""Read the exact catalog powering the upstream Best Root Apps website.

The upstream Pages generator parses bold Markdown table rows using APP_ROW.
Do not turn APKs, LSPosed entries, or other apps into root modules.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from urllib.parse import urlsplit

SOURCE = "https://github.com/krishna3163/best-root-apps-for-android"
APP_ROW = re.compile(
    r"^\| \*\*\[([^\]]+)\]\((https?://[^)]+)\)\*\* \| (.*?) \| (.*?) \| (.*?) \|\s*$"
)
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
FRAMEWORK_BADGE = re.compile(r"\[(M|K|A|LSP)\]")
HEADING = re.compile(r"^#{2,5}\s+(.+)")
GITHUB_REPO = re.compile(r"^[a-zA-Z0-9-]+/[a-zA-Z0-9_.-]+$")
AUTO_START = "<!-- AUTO-DISCOVERED-ROOT-APPS:START -->"
AUTO_END = "<!-- AUTO-DISCOVERED-ROOT-APPS:END -->"
CATEGORY_DEFAULT = "Root Apps"


def provider(url: str) -> str:
    try:
        host = (urlsplit(url).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host or "unknown"
    except ValueError:
        return "unknown"


def github_repository(url: str) -> str | None:
    """Return the exact GitHub owner/repo, never a guessed GitHub URL."""
    try:
        parts = urlsplit(url)
        if parts.scheme != "https" or (parts.hostname or "").lower() != "github.com":
            return None
        path = parts.path.strip("/").split("/")
        if len(path) < 2:
            return None
        full = path[0] + "/" + path[1].removesuffix(".git")
        return full if GITHUB_REPO.fullmatch(full) else None
    except ValueError:
        return None


def framework_badges(text: str) -> list[str]:
    mapping = {"M": "Magisk", "K": "KernelSU", "A": "APatch", "LSP": "LSPosed"}
    return [mapping[key] for key in FRAMEWORK_BADGE.findall(text)]


def clean_markdown(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def classify(description: str, category: str, frameworks: list[str], url: str) -> str:
    """Classification is descriptive; only archive inspection authorizes installation."""
    blob = (description + " " + category).lower()
    if "LSPosed" in frameworks and not any(x in frameworks for x in ("Magisk", "KernelSU", "APatch")):
        return "lsposed"
    if any(x in frameworks for x in ("Magisk", "KernelSU", "APatch")):
        return "root_module_candidate"
    if any(s in blob for s in ("shizuku", "rish", "wireless debugging")):
        return "shizuku"
    if any(s in blob for s in ("lsposed", "xposed", "zygisk")):
        return "lsposed_or_zygisk"
    if any(s in blob for s in ("magisk module", "kernelsu module", "apatch module", "root module")):
        return "root_module_candidate"
    if provider(url) == "play.google.com":
        return "android_app"
    return "android_tool"


def item_id(url: str, name: str) -> str:
    return hashlib.sha256((url.lower().rstrip("/") + "|" + name.casefold()).encode()).hexdigest()[:18]


def parse_readme(readme: str) -> list[dict]:
    """Follow the upstream APP_ROW contract, retaining each card and its labels."""
    entries: list[dict] = []
    current_category = CATEGORY_DEFAULT
    auto = False
    for line in readme.splitlines():
        if AUTO_START in line:
            auto = True
            current_category = "Auto-Discovered Root Projects"
            continue
        if AUTO_END in line:
            auto = False
            continue
        h = HEADING.match(line)
        if h and not auto:
            current_category = clean_markdown(h.group(1)).replace("**", "").strip()
        match = APP_ROW.match(line)
        if not match:
            continue
        name, url, description, badge_text, links_text = match.groups()
        category = "Auto-Discovered Root Projects" if auto else current_category
        repo = github_repository(url)
        frameworks = framework_badges(badge_text)
        links = [{"label": label, "url": dest} for label, dest in MARKDOWN_LINK.findall(links_text)]
        entry = {
            "id": item_id(url, name),
            "name": name, "url": url, "description": clean_markdown(description),
            "category": category, "provider": provider(url),
            "frameworks": frameworks, "license": badge_text, "links": links,
            "kind": classify(description, category, frameworks, url),
            "origin": "upstream_readme",
        }
        if repo:
            entry["repository"] = repo
        entries.append(entry)
    if len(entries) < 1000:
        raise RuntimeError(f"Upstream catalog unexpectedly small: {len(entries)}")
    if len({e["id"] for e in entries}) != len(entries):
        raise RuntimeError("Nonunique catalog identifiers; retain source consistency")
    return entries


def parse_morphe(data: dict) -> list[dict]:
    """Morphe releases are *APK discovery entries*, never flashable root modules."""
    entries = []
    for slug, record in sorted(data.items()):
        if not isinstance(record, dict):
            continue
        tag = record.get("release_tag") or ""
        if not tag or not re.fullmatch(r"[a-zA-Z0-9._-]+", tag):
            continue
        url = SOURCE + "/releases/tag/" + tag
        name = record.get("name") or slug
        entries.append({
            "id": item_id(url, str(name)), "name": str(name), "url": url,
            "description": "Morphe patch: " + ", ".join(record.get("patches", [])[:6]),
            "category": "Morphe Patched APKs", "provider": "github.com",
            "frameworks": [], "license": "See upstream", "links": [
                {"label": "Morphe release", "url": url},
            ], "kind": "patched_apk", "origin": "upstream_morphe",
            "version": str(record.get("version") or ""),
            "package": str(record.get("package_name") or ""),
            "channel": str(record.get("channel") or ""),
            "build_type": str(record.get("build_type") or ""),
        })
    return entries


def parse_trackers(config: dict, seen_repos: set[str]) -> list[dict]:
    """Capture the official tracked sources that aren't in the README tables."""
    entries = []
    for app in config.get("apps", []):
        if not app.get("enabled", True):
            continue
        repository = app.get("repository", "")
        if not GITHUB_REPO.fullmatch(repository) or repository.casefold() in seen_repos:
            continue
        url = "https://github.com/" + repository
        name = app.get("name") or repository
        entries.append({
            "id": item_id(url, name), "name": name, "url": url,
            "description": "Upstream release tracker", "category": "Release Trackers",
            "provider": "github.com", "frameworks": [], "license": "See upstream",
            "links": [], "kind": "tracked_project", "origin": "upstream_config",
            "repository": repository,
        })
        seen_repos.add(repository.casefold())
    return entries


def build_discovery(readme: str, morphe_data: dict, config: dict) -> dict:
    entries = parse_readme(readme)
    seen_repos = {e["repository"].casefold() for e in entries if e.get("repository")}
    entries += parse_morphe(morphe_data)
    entries += parse_trackers(config, seen_repos)
    by_kind = dict(sorted(Counter(e["kind"] for e in entries).items()))
    by_provider = dict(sorted(Counter(e["provider"] for e in entries).items()))
    return {
        "schema_version": 2,
        "source": SOURCE,
        "upstream_website": "https://krishna3163.github.io/best-root-apps-for-android/",
        "summary": {
            "total_entries": len(entries),
            "readme_entries": sum(e["origin"] == "upstream_readme" for e in entries),
            "morphe_entries": sum(e["origin"] == "upstream_morphe" for e in entries),
            "tracker_extras": sum(e["origin"] == "upstream_config" for e in entries),
            "unique_github_repositories": len(seen_repos),
            "by_kind": by_kind, "by_provider": by_provider,
        },
        "entries": entries,
    }
