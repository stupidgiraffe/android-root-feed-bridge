"""Keep the published RootAtlas feed directory up to date automatically."""
import unittest
from scripts.source_directory import render_sources


class SourceDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "mmrl": ["https://gr.dergoogler.com/gmr/", "https://leloubil.github.io/magisk-repo/"],
            "ksunext": [{"name": "Official OSS", "url": "https://example.org/modules.json", "enabled": True},
                        {"name": "Non-free", "url": "https://example.org/non_free_modules.json", "enabled": False}],
        }
        self.report = {
            "updated": 1794907477, "catalog_entries": 1904, "github_repositories": 1794,
            "mmrl_modules": 879, "kernelsu_next_modules": 393,
            "federation": {"total": 4, "fetched": 3, "failures": [{
                "kind": "mmrl", "source": "https://leloubil.github.io/magisk-repo/",
            }]},
        }
        self.search = {"repositories": {
            "owner/other": {"status": "found", "repository": "owner/other",
                            "kind": "mmrl", "url": "https://example.org/json/modules.json"},
            "owner/old": {"status": "unmatched", "repository": "owner/old",
                          "kind": "none", "url": "https://example.org/missing"},
        }}

    def test_lists_every_configured_and_validated_source(self):
        doc = render_sources(self.config, self.search, self.report)
        self.assertIn("Googlers Magisk Repository", doc)
        self.assertIn("Leloubil Repo", doc)
        self.assertIn("Failed (retrying)", doc)
        self.assertIn("owner/other", doc)
        self.assertNotIn("owner/old", doc)
        self.assertIn("Non-free", doc)
        self.assertIn("Not included (opt-in)", doc)
        self.assertIn("879", doc)
        self.assertIn("393", doc)

    def test_new_discovery_appears_without_editing_document(self):
        doc1 = render_sources(self.config, self.search, self.report)
        self.search["repositories"]["owner/new"] = {
            "status": "found", "repository": "owner/new", "kind": "mmrl",
            "url": "https://raw.githubusercontent.com/owner/new/main/json/modules.json"}
        doc2 = render_sources(self.config, self.search, self.report)
        self.assertNotIn("owner/new", doc1)
        self.assertIn("owner/new", doc2)
        self.assertIn("Independently discovered GitHub feeds (2)", doc2)

    def test_insecure_source_url_rejected(self):
        self.config["mmrl"].append("http://example.com/")
        with self.assertRaises(ValueError):
            render_sources(self.config, self.search, self.report)


if __name__ == "__main__":
    unittest.main()
