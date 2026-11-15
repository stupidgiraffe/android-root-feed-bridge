"""Unit tests for federated source validation, caching and duplicate handling."""
import unittest

from scripts.federation import (
    canonical_base, canonical_github, gather_feeds, normalize_mmrl,
    normalize_ksu, fetch_all, merge,
)


def module(mid="sample", code=12, timestamp=123.0):
    return {
        "id": mid, "name": "Sample", "author": "Test", "version": "1",
        "versionCode": code,
        "track": {"type": "ONLINE_JSON", "added": timestamp, "source": ""},
        "versions": [{"version": "1", "versionCode": code, "timestamp": timestamp,
                      "zipUrl": "https://github.com/author/a/releases/download/1/m.zip"}],
    }


class FederationTests(unittest.TestCase):
    def test_source_dedup_and_self_exclusion(self):
        config = {
            "mmrl": ["https://example.org/repo", "https://example.org/repo//",
                     "https://raw.githubusercontent.com/stupidgiraffe/android-root-feed-bridge/main/"],
            "mmrl_directory": "https://example.org/list.json",
            "ksunext": [{"name": "official", "url": "https://example.org/ksu.json",
                         "enabled": True},
                        {"name": "nonfree", "url": "https://example.org/nonfree",
                         "enabled": False}],
        }
        m, k, warnings = gather_feeds(config, lambda url: ["https://other.org/r/"])
        self.assertEqual(m, ["https://example.org/repo/", "https://other.org/r/"])
        self.assertEqual(len(k), 1)
        self.assertEqual(warnings, [])

    def test_invalid_timestamp_does_not_break_index(self):
        bad = module()
        bad["versions"] = [{"version": "2", "versionCode": 2,
                            "zipUrl": "https://example.org/module.zip"}]
        self.assertIsNone(normalize_mmrl(bad))
        bad["versions"].append(module()["versions"][0])
        good = normalize_mmrl(bad)
        self.assertEqual(len(good["versions"]), 1)
        self.assertEqual(good["versionCode"], 12)

    def test_type_and_url_checks(self):
        self.assertIsNone(normalize_mmrl({**module(), "track": {"type": "WRONG"}}))
        self.assertIsNone(normalize_mmrl({**module(), "versions": [{"version":"1",
                           "versionCode":1,"timestamp":1,"zipUrl":"http://insecure"}]}))
        self.assertIsNone(normalize_ksu({"name":"x","author":"y","description":"z",
                                        "repoUrl":"https://example.org/malware"}))
        self.assertEqual(canonical_github("https://github.com/OWNER/repo/"),
                         "https://github.com/OWNER/repo")
        self.assertEqual(canonical_base("https://example.org/r////"), "https://example.org/r/")

    def test_cache_fallback(self):
        source = "https://example.org/repo/"
        url = source + "json/modules.json"
        previous = {"sources": {"mmrl:" + url: {
            "kind": "mmrl", "source": source, "url": url,
            "count": 1, "invalid": 0, "last_success": 100,
            "entries": [normalize_mmrl(module())]}}}
        def broken(_):
            raise OSError("Source temporarily unavailable")
        states, status = fetch_all([source], [], broken, previous, 200)
        self.assertEqual(status["failed"], 1)
        self.assertEqual(status["failures"][0]["status"], "stale")
        self.assertEqual(len(states["mmrl:" + url]["entries"]), 1)

    def test_merge_dedup_and_prioritize_newer(self):
        catalog = module("shared", 9, 100)
        catalog["track"]["source"] = "https://github.com/original/a"
        remote = normalize_mmrl(module("shared", 12, 200))
        extra = normalize_mmrl(module("only-remote", 1, 90))
        state = {"mmrl:https://remote.test/r/json/modules.json": {
            "kind":"mmrl", "source":"https://remote.test/r/",
            "entries":[remote, extra]}}
        base_ksu = [{"name": "One", "author": "A", "description": "b",
                     "repoUrl": "https://github.com/original/a", "visibility": 1}]
        state["ksunext:https://official.test/all.json"] = {
            "kind":"ksunext", "source":"Official", "entries":[
                {"name":"Same","author":"B","description":"c",
                 "repoUrl":"https://github.com/ORIGINAL/a","visibility":1,
                 "license":"GPL-3.0"},
                {"name":"More","author":"B","description":"c",
                 "repoUrl":"https://github.com/new/r","visibility":1},
            ]}
        m, k, audit = merge([catalog], base_ksu, state)
        self.assertEqual(len(m), 2)
        self.assertEqual(next(i for i in m if i["id"] == "shared")["versionCode"], 12)
        self.assertEqual(audit["module_origins"]["shared"]["kind"], "mmrl")
        self.assertEqual(audit["module_conflicts"]["shared"], 1)
        self.assertEqual(len(k), 2)
        self.assertEqual(next(i for i in k if i["repoUrl"].lower().endswith("/a"))["license"],
                         "GPL-3.0")

    def test_bad_index_refuses_empty_source(self):
        base = "https://example.org/"
        def fetch(_):
            return {"name":"Broken","modules":[{"id":"broken"}]}
        states, status = fetch_all([base], [], fetch, {}, 100)
        self.assertEqual(states, {})
        self.assertEqual(status["failures"][0]["status"], "excluded")


if __name__ == "__main__":
    unittest.main()
