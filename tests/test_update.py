import io
import importlib.util
import pathlib
import unittest
import zipfile

path = pathlib.Path(__file__).resolve().parents[1] / "scripts/update.py"
spec = importlib.util.spec_from_file_location("feed_update", path)
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedTests(unittest.TestCase):
    def test_prop(self):
        data = b"id=test.mod\nname=Test\nversion=v1\nversionCode=42\nauthor=A\n"
        self.assertEqual(feed.parse_prop(data)["versionCode"], "42")
        self.assertIsNone(feed.parse_prop(data.replace(b"42", b"broken")))
        self.assertIsNone(feed.parse_prop(data.replace(b"test.mod", b"bad id")))

    def test_zip_inspection(self):
        for inner, expected in [("module.prop", True), ("other/module.prop", False)]:
            out = io.BytesIO()
            with zipfile.ZipFile(out, "w") as archive:
                archive.writestr(inner, "id=example\nname=Example\nversion=1\nversionCode=1\n")
            original = feed.request
            feed.request = lambda *args, **kwargs: out.getvalue()
            try:
                result = feed.inspect_asset({
                    "name": "module.zip", "size": len(out.getvalue()),
                    "browser_download_url": "https://github.com/a/b/releases/download/v1/module.zip"
                })
                self.assertEqual(bool(result), expected)
            finally:
                feed.request = original

    def test_reject_nonmodules(self):
        self.assertIsNone(feed.inspect_asset({
            "name": "module.apk", "size": 2, "browser_download_url": "https://github.com/a/b"
        }))
        self.assertIsNone(feed.inspect_asset({
            "name": "module.zip", "size": 2, "browser_download_url": "https://untrusted.test/module.zip"
        }))
