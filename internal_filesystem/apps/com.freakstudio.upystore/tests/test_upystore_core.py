import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "assets"


class TM:
    @staticmethod
    async def wait_for(coro, timeout):
        return await asyncio.wait_for(coro, timeout)

    @staticmethod
    async def sleep_ms(ms):
        await asyncio.sleep(ms / 1000)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.mpos = types.ModuleType("mpos")
        self.mpos.TaskManager = TM
        self.mpos.ConnectivityManager = types.SimpleNamespace(is_online=lambda: True)
        self.mpos.BuildInfo = types.SimpleNamespace(version=types.SimpleNamespace(release="0.21.2", api_level=0))
        self.mpos.AppManager = types.SimpleNamespace(refresh_apps=lambda: None)
        self.mpos.DownloadManager = types.SimpleNamespace()
        self.modules = patch.dict(sys.modules, {"mpos": self.mpos})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        spec = importlib.util.spec_from_file_location("upystore_core", APP / "upystore_core.py")
        self.core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.core)

    def test_relative_url_and_blocked_cross_origin(self):
        self.assertEqual(self.core.absolute_url("/api/v1/apps/a"), "https://upystore.io/api/v1/apps/a")
        for bad in ["http://upystore.io/a", "https://evil.example/a", "//evil.example/a", "https://upystore.io.evil/a"]:
            with self.assertRaises(ValueError):
                self.core.absolute_url(bad)

    def test_fullname_validation(self):
        for bad in ["../x", "a/b", "a..b", "a b", "x\\y", ""]:
            with self.assertRaises(ValueError):
                self.core.validate_fullname(bad)
        self.assertEqual(self.core.validate_fullname("com.example.cc_skill_smoke"), "com.example.cc_skill_smoke")

    def test_percent_encoding(self):
        self.assertEqual(self.core.quote_query("a &中"), "a%20%26%E4%B8%AD")

    def test_offline_does_not_start_request(self):
        self.mpos.ConnectivityManager.is_online = lambda: False
        with self.assertRaisesRegex(RuntimeError, "Offline"):
            asyncio.run(self.core.StoreClient().list_apps())

    def test_list_and_detail_contracts(self):
        client = self.core.StoreClient()

        async def request(path, **kwargs):
            if "/apps?" in path:
                return {
                    "apps": [{"fullname": "a.b", "slug": "a-b"}],
                    "pagination": {"page": 1, "total_pages": 2, "total": 7},
                }
            return {
                "app": {"fullname": "a.b", "slug": "a-b", "revision": 1},
                "versions": [{"revision": 1, "file_sha256": "a" * 64}],
            }

        client.json_request = request
        self.assertEqual(asyncio.run(client.list_apps())["pagination"]["total"], 7)
        self.assertEqual(asyncio.run(client.detail("a-b"))["app"]["fullname"], "a.b")

    def test_integrity_detects_corrupt_size_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x"
            p.write_bytes(b"PKxx")
            self.core.verify_package(str(p), 4, hashlib.sha256(b"PKxx").hexdigest())
            with self.assertRaises(ValueError):
                self.core.verify_package(str(p), 5, None)
            with self.assertRaises(ValueError):
                self.core.verify_package(str(p), 4, "a" * 64)

    def test_http_404_is_actionable(self):
        text = self.core.friendly_error(RuntimeError("HTTP 404"))
        self.assertIn("unavailable", text.lower())
        self.assertIn("Retry", text)

    def test_timeout_is_actionable(self):
        self.assertIn("Retry", self.core.friendly_error(TimeoutError()))

    def test_commit_rollback_preserves_existing_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            stage = tmp / "stage"
            dest = tmp / "dest"
            backup = tmp / "backup"
            stage.mkdir()
            dest.mkdir()
            (dest / "old").write_text("saved")
            rename = self.core.os.rename

            def fail(source, target):
                if source == str(stage):
                    raise OSError("promotion failed")
                return rename(source, target)

            with patch.object(self.core.os, "rename", side_effect=fail):
                with self.assertRaises(OSError):
                    self.core.commit_install(str(stage), str(dest), str(backup))
            self.assertEqual((dest / "old").read_text(), "saved")

    def test_json_invalid_and_size_limit(self):
        async def download(url, chunk_callback=None, **kwargs):
            await chunk_callback(b"x" * 150000)
            return True

        self.mpos.DownloadManager.download_url = download
        with self.assertRaisesRegex(ValueError, "large"):
            asyncio.run(self.core.StoreClient().json_request("/api/v1/apps"))


if __name__ == "__main__":
    unittest.main()
