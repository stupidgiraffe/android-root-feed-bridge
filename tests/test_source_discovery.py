"""Bounded discovery tests: no unverified feeds or unsafe URLs enter RootAtlas."""
import unittest

from scripts.source_discovery import candidate_urls, inspect_candidate, discover, PROBE_LIMIT


class DiscoveryTests(unittest.TestCase):
    def test_candidate_paths_and_identity(self):
        good = {"full_name": "Example/MMRL-Repo", "default_branch": "main"}
        links = candidate_urls(good)
        self.assertEqual(len(links), 4)
        self.assertEqual(links[0], ("mmrl", "https://raw.githubusercontent.com/Example/MMRL-Repo/main/json/modules.json"))
        self.assertTrue(all(u.startswith("https://") for _, u in links))
        self.assertEqual(candidate_urls({"full_name": "../../bad", "default_branch": "main"}), [])

    def test_only_valid_mmrl_indices_are_accepted(self):
        item = {"full_name": "Example/MMRL-Repo", "default_branch": "main"}
        good = {
            "name": "Example Feed",
            "modules": [{
                "id": "example", "name": "Example", "author": "Author",
                "version": "1", "versionCode": 1,
                "track": {"type": "GIT", "source": "https://github.com/Example/Module"},
                "versions": [{
                    "version": "1", "versionCode": 1, "timestamp": 1.0,
                    "zipUrl": "https://github.com/Example/Module/releases/download/v1/m.zip",
                }],
            }]
        }
        def fetch(url, limit, timeout):
            if url.endswith("/json/modules.json"):
                return good
            raise OSError("unexpected")
        result = inspect_candidate(item, fetch)
        self.assertEqual(result["kind"], "mmrl")
        self.assertEqual(result["modules"], 1)

    def test_empty_or_malformed_repo_is_not_accepted(self):
        item = {"full_name": "Example/MMRL-Repo", "default_branch": "main"}
        def fetch(url, limit, timeout):
            return {"name": "Looks valid", "modules": [{"id": "bad"}]}
        result = inspect_candidate(item, fetch)
        self.assertEqual(result["status"], "unmatched")

    def test_search_no_results_preserves_previous_discoveries(self):
        now = 1_800_000_000
        previous = {"version": 1, "repositories": {
            "author/repo": {
                "status": "found", "repository": "author/repo",
                "kind": "mmrl", "url": "https://author.github.io/repo/json/modules.json",
                "checked": now - 86400,
            },
        }}
        def fetch(url, limit, timeout):
            self.assertIn("/search/repositories", url)
            return {"items": []}
        sources, state, report = discover(previous, fetch, now)
        self.assertEqual(len(sources), 1)
        self.assertEqual(state["version"], 1)
        self.assertEqual(report["new_candidates_inspected"], 0)
        self.assertEqual(report["discovered_mmrl_feeds"], 1)

    def test_github_search_errors_are_nonfatal(self):
        def broken(url, limit, timeout):
            raise OSError("GitHub unavailable")
        sources, state, report = discover({}, broken, 1_800_000_000)
        self.assertEqual(sources, [])
        self.assertEqual(len(report["github_search_errors"]), 8)


if __name__ == "__main__":
    unittest.main()
