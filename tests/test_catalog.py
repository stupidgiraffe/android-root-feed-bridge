"""Regression tests for complete catalog and conservative dual-feed generation."""
import importlib.util
import pathlib
import unittest

from scripts.catalog import build_discovery, parse_readme, provider, github_repository

PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts/update.py"
SPEC = importlib.util.spec_from_file_location("bridge_update", PATH)
feed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(feed)


def row(name, url, desc="", badges="See project"):
    return f"| **[{name}]({url})** | {desc} | {badges} | [Source]({url}) |"


class CatalogTests(unittest.TestCase):
    def test_upstream_row_contract_categorization_and_non_github(self):
        from scripts.catalog import classify, framework_badges
        self.assertEqual(classify("Works with Shizuku", "Tools", [], "https://github.com/a/b"), "shizuku")
        self.assertEqual(classify("An LSPosed module", "Tools", ["LSPosed"], "https://codeberg.org/a/b"), "lsposed")
        self.assertEqual(classify("KernelSU module", "Tools", ["KernelSU"], "https://github.com/a/b"), "root_module_candidate")
        self.assertEqual(framework_badges("FOSS [M] [K] [LSP]"), ["Magisk", "KernelSU", "LSPosed"])

    def test_all_entries_preserved(self):
        text = "\n".join([
            "<!-- AUTO-DISCOVERED-ROOT-APPS:START -->",
            row(f"App {i}", f"https://github.com/user/repo{i}", "Shizuku app")
            for i in range(1002)
        ]) + "\n<!-- AUTO-DISCOVERED-ROOT-APPS:END -->\n" + row(
            "Non-GitHub", "https://codeberg.org/owner/app", "standalone application")
        result = build_discovery(text, {
            "patched": {"name": "Patched APK", "release_tag": "patched-v1",
                        "version": "v1", "patches": ["Feature"]}
        }, {"apps": [
            {"name": "Tracker", "repository": "example/upstream-new", "enabled": True}
        ]})
        self.assertEqual(result["summary"]["readme_entries"], 1003)
        self.assertEqual(result["summary"]["morphe_entries"], 1)
        self.assertEqual(result["summary"]["tracker_extras"], 1)
        self.assertEqual(len(result["entries"]), 1005)
        self.assertTrue(any(x["provider"] == "codeberg.org" for x in result["entries"]))
        self.assertTrue(any(x["kind"] == "patched_apk" for x in result["entries"]))

    def test_repo_url_canonicalization(self):
        self.assertEqual(github_repository("https://github.com/Owner/repo/releases/latest"), "Owner/repo")
        self.assertEqual(github_repository("https://github.com/Owner/repo.git"), "Owner/repo")
        self.assertIsNone(github_repository("https://gitlab.com/Owner/repo"))
        self.assertEqual(provider("https://codeberg.org/o/r"), "codeberg.org")

    def test_kernel_su_feed_cannot_select_multiple_zip_releases(self):
        data = {"entries": [
            {"repository": "a/b", "name": "Example", "description": "",
             "frameworks": ["KernelSU"]},
            {"repository": "c/d", "name": "APK", "description": "", "frameworks": []},
        ]}
        entry = {"valid": True, "prop": {"id": "module", "name": "Example",
                    "version": "v1", "versionCode": "1", "author": "Author",
                    "description": ""}, "size": 1024, "zip": "https://github.com/a/b/releases/download/v1/abc.zip",
                 "zip_count": 2, "valid_zip_count": 1, "timestamp": 1000}
        modules, ksu = feed.create_indexes(data, {"a/b": entry}, 1000)
        self.assertEqual(len(modules), 1)
        self.assertEqual(ksu, [])
        entry["zip_count"] = 1
        modules, ksu = feed.create_indexes(data, {"a/b": entry}, 1000)
        self.assertEqual(len(ksu), 1)

    def test_cached_release_checked_timestamp_is_updated(self):
        saved = {"valid": True, "release_id": 55, "checked": 1, "prop": {"id": "t"}}
        original = feed.release
        feed.release = lambda repo: {"id": 55}
        try:
            result = feed.inspect({"repository": "a/b"}, saved)
        finally:
            feed.release = original
        self.assertTrue(result["checked"] > 1)
        self.assertTrue(result["valid"])
        self.assertEqual(result["prop"]["id"], "t")


if __name__ == "__main__":
    unittest.main()
