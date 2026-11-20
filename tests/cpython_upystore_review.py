import asyncio
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import cpython_upystore_install as previous


class ReviewTests(previous.EnvironmentMixin, unittest.TestCase):
    def prepare_archive(self, **kwargs):
        return previous.InstallationTests.prepare_archive(self, **kwargs)

    def test_default_is_independent_upystore(self):
        self.assertEqual(self.source.current_source(), 'upystore')

    def test_invalid_saved_source_falls_back_to_official_default(self):
        self.prefs['upystore_source'] = 'removed-provider'
        self.assertEqual(self.source.current_source(), 'upystore')

    def test_explicit_upystore_choice_is_preserved(self):
        self.prefs['upystore_source'] = 'upystore'
        self.assertEqual(self.source.current_source(), 'upystore')

    def test_builtin_manifest_uses_categories_list(self):
        manifest = json.loads((previous.STORE / 'MANIFEST.JSON').read_text())
        self.assertNotIn('category', manifest)
        self.assertEqual(manifest['categories'], ['Appstore'])

    def test_installer_uses_app_cache_and_preferences(self):
        app = self.prepare_archive()
        asyncio.run(self.install.install_package(app))
        base = Path('cache/com.freakstudio.upystore/install')
        self.assertEqual(list((base / 'stage').iterdir()), [])
        self.assertEqual(list((base / 'backup').iterdir()), [])
        self.assertTrue(Path('prefs/com.freakstudio.upystore/receipts/' + app.fullname + '.json').is_file())
        self.assertFalse(Path('data/appstore').exists())

    def test_legacy_receipt_migrates_without_losing_revision(self):
        directory = Path('data/appstore/receipts')
        directory.mkdir(parents=True)
        value = {'version': '1.0.0', 'revision': 3, 'source': 'upystore'}
        (directory / 'com.example.upgrade.json').write_text(json.dumps(value))
        self.assertEqual(self.install.read_receipt('com.example.upgrade'), value)
        self.assertTrue(Path('prefs/com.freakstudio.upystore/receipts/com.example.upgrade.json').is_file())
        self.manager.is_update_available = lambda *args: False
        self.assertTrue(self.install.update_available('com.example.upgrade', '1.0.0', 4, 'upystore'))

    def test_forgetting_receipt_cannot_resurrect_legacy_copy(self):
        directory = Path('data/appstore/receipts')
        directory.mkdir(parents=True)
        (directory / 'com.example.upgrade.json').write_text('{"revision": 1, "source": "upystore"}')
        self.install.read_receipt('com.example.upgrade')
        self.install.forget_receipt('com.example.upgrade')
        self.assertIsNone(self.install.read_receipt('com.example.upgrade'))

    def test_legacy_backup_requires_recovery_before_new_install(self):
        app = self.prepare_archive()
        backup = Path('data/appstore/install/backup') / app.fullname
        backup.mkdir(parents=True)
        (backup / 'saved').write_text('old')
        with self.assertRaisesRegex(RuntimeError, 'recovery'):
            asyncio.run(self.install.install_package(app))
        self.assertEqual((backup / 'saved').read_text(), 'old')

    def test_compiled_entrypoint_remains_supported(self):
        self.manifest(Path('stage'))
        Path('stage/main.py').unlink()
        Path('stage/main.mpy').write_bytes(b"M\x06\x00\x1f")
        value = self.install.validate_manifest('stage', 'com.example.upgrade', '1.0.0')
        self.assertEqual(value['activities'][0]['entrypoint'], 'main.py')

    def test_explicit_mpy_entrypoint_is_supported(self):
        self.manifest(Path('stage'))
        manifest = json.loads(Path('stage/MANIFEST.JSON').read_text())
        manifest['activities'][0]['entrypoint'] = 'main.mpy'
        Path('stage/MANIFEST.JSON').write_text(json.dumps(manifest))
        Path('stage/main.py').unlink()
        Path('stage/main.mpy').write_bytes(b"M\x06\x00\x1f")
        self.install.validate_manifest('stage', 'com.example.upgrade', '1.0.0')

    def test_invalid_compiled_header_is_rejected(self):
        self.manifest(Path('stage'))
        Path('stage/main.py').unlink()
        Path('stage/main.mpy').write_bytes(b"not-mpy")
        with self.assertRaises(ValueError):
            self.install.validate_manifest('stage', 'com.example.upgrade', '1.0.0')

    def test_unknown_provider_cannot_bypass_integrity_checks(self):
        app = self.prepare_archive()
        app._store_source = 'unknown'
        with self.assertRaisesRegex(ValueError, 'source'):
            asyncio.run(self.install.install_package(app))
        self.assertFalse(Path('apps/com.example.upgrade').exists())

    def test_cleanup_failure_does_not_turn_committed_install_into_failure(self):
        app = self.prepare_archive()
        original = self.install.remove_tree

        def cleanup(path):
            if path.endswith('/stage/' + app.fullname) and self.install.read_receipt(app.fullname):
                raise OSError('cleanup temporarily unavailable')
            return original(path)

        with patch.object(self.install, 'remove_tree', side_effect=cleanup):
            result = asyncio.run(self.install.install_package(app))
        self.assertEqual(result['version'], '1.1.0')
        self.assertTrue(Path('apps/com.example.upgrade/main.py').is_file())


if __name__ == '__main__':
    unittest.main()
