import asyncio
import sys
import unittest

sys.path.insert(0, 'apps/com.freakstudio.upystore')

from mpos import App, TaskManager
import upystore_app
import upystore_core
import upystore_source


class TestCoexist(unittest.TestCase):
    def test_store_object_is_separate_from_global_app(self):
        original = App(name='Installed', fullname='com.test.coexist', version='1.0.0', installed_path='apps/com.test.coexist', load_icons=False)
        copied = upystore_app.UPyStore._copy_installed_app(original)
        self.assertFalse(copied is original)
        upystore_source.attach(copied, {'version': '2.0.0', 'publisher': 'Remote', '_store_source': 'upystore'})
        self.assertEqual(original.version, '1.0.0')
        self.assertFalse(hasattr(original, '_store_source'))
        self.assertEqual(copied.installed_path, original.installed_path)

    def test_pending_deeplink_waits_while_paused(self):
        store = upystore_app.UPyStore()
        store._has_foreground = False
        store._pending_deeplink = 'com.test.coexist'
        app = type('App', (), {'fullname': 'com.test.coexist'})()
        store.apps = [app]
        store._wip_apps = []
        calls = []
        store.show_app_detail = calls.append
        store._resolve_pending_deeplink()
        self.assertEqual(calls, [])
        self.assertEqual(store._pending_deeplink, app.fullname)
        store._has_foreground = True
        store._resolve_pending_deeplink()
        self.assertEqual(calls, [app])
        self.assertIsNone(store._pending_deeplink)

    def test_destroy_discards_pending_navigation(self):
        store = upystore_app.UPyStore()
        store.apps = []
        store._pending_deeplink = 'com.test.coexist'
        store.onDestroy(None)
        self.assertIsNone(store._pending_deeplink)

    def test_service_start_is_idempotent(self):
        manager = upystore_core.UPyStoreUpdateManager()
        events = []
        class Connectivity:
            def register_callback(self, callback):
                events.append('register')
            def unregister_callback(self, callback):
                events.append('unregister')
        connectivity = Connectivity()
        original_get = upystore_core.ConnectivityManager.get
        original_task = TaskManager.create_task
        tasks = []
        upystore_core.ConnectivityManager.get = lambda: connectivity
        TaskManager.create_task = tasks.append
        try:
            manager.start()
            manager.start()
            self.assertEqual(events, ['register'])
            self.assertEqual(len(tasks), 1)
            manager.stop()
            self.assertEqual(events, ['register', 'unregister'])
        finally:
            manager.stop()
            upystore_core.ConnectivityManager.get = original_get
            TaskManager.create_task = original_task

    def test_notification_identity_is_separate(self):
        self.assertEqual(upystore_core.UPyStoreUpdateManager.NOTIFICATION_ID, 'upystore.updates_available')
        self.assertEqual(upystore_core.UPyStoreUpdateManager.ICON_PATH, 'M:apps/com.freakstudio.upystore/icon_64x64.png')


if __name__ == '__main__':
    unittest.main()
