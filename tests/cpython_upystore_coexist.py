import asyncio
import json
from pathlib import Path
import unittest

import cpython_upystore_install as previous


class CoexistTests(previous.EnvironmentMixin, unittest.TestCase):
    def test_only_upystore_is_selected_even_if_old_preference_names_badgehub(self):
        self.prefs['store_source'] = 'badgehub'
        self.assertEqual(self.source.current_source(), 'upystore')
        self.assertEqual(self.source.index_url(), 'https://upystore.io/app_index.json')

    def test_cross_origin_request_is_rejected_before_network(self):
        async def unexpected(*args, **kwargs):
            self.fail('Another store must not receive requests')
        self.mpos.DownloadManager.download_url = unexpected
        with self.assertRaises(ValueError):
            asyncio.run(self.source.request('https://badgehub.eu/api/v3/projects/example'))

    def test_other_backend_cannot_bypass_sha_checks(self):
        app = previous.InstallationTests.prepare_archive(self)
        app._store_source = 'badgehub'
        with self.assertRaisesRegex(ValueError, 'source'):
            asyncio.run(self.install.install_package(app))

    def test_receipt_import_copies_only_upystore_and_preserves_official_file(self):
        directory = Path('prefs/com.micropythonos.appstore/receipts')
        directory.mkdir(parents=True)
        value = {'version': '1.0.0', 'revision': 3, 'source': 'upystore'}
        path = directory / 'com.example.upgrade.json'
        path.write_text(json.dumps(value))
        self.assertEqual(self.install.read_receipt('com.example.upgrade'), value)
        self.assertTrue(Path(self.install.RECEIPTS_DIR, path.name).exists())
        self.install.forget_receipt('com.example.upgrade')
        self.assertTrue(path.exists())
        self.assertIsNone(self.install.read_receipt('com.example.upgrade'))

    def test_other_store_receipt_is_not_imported(self):
        directory = Path('prefs/com.micropythonos.appstore/receipts')
        directory.mkdir(parents=True)
        (directory / 'com.example.upgrade.json').write_text('{"source":"badgehub","revision":9}')
        self.assertIsNone(self.install.read_receipt('com.example.upgrade'))

    def test_installation_state_belongs_to_independent_app(self):
        self.assertEqual(self.install.WORK_DIR, 'cache/com.freakstudio.upystore/install')
        self.assertEqual(self.install.RECEIPTS_DIR, 'prefs/com.freakstudio.upystore/receipts')
        manifest = json.loads((previous.STORE / 'MANIFEST.JSON').read_text())
        self.assertEqual(manifest['fullname'], 'com.freakstudio.upystore')
        self.assertEqual(manifest['activities'][0]['classname'], 'UPyStore')
        self.assertEqual(manifest['services'][0]['classname'], 'UPyStoreService')
        names = {p.stem for p in previous.STORE.glob('*.py')}
        self.assertTrue(all(name.startswith('upystore_') for name in names))


if __name__ == '__main__':
    unittest.main()
