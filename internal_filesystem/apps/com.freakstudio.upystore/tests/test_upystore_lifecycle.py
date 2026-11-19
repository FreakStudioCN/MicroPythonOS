import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class BaseActivity:
    def onResume(self, screen):
        self._has_foreground = True

    def onPause(self, screen):
        self._has_foreground = False

    def if_foreground(self, func, *args):
        if self._has_foreground:
            func(*args)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        mpos = types.ModuleType("mpos")
        for key in ["AppManager", "InputActivity", "Intent"]:
            setattr(mpos, key, object())
        mpos.TaskManager = types.SimpleNamespace(create_task=lambda coroutine: coroutine.close())
        mpos.Activity = BaseActivity
        ui = types.ModuleType("mpos.ui")
        ui.add_focus_border = lambda *a: None
        core = types.ModuleType("upystore_core")
        core.StoreClient = object
        core.friendly_error = str
        with patch.dict(
            sys.modules, {"mpos": mpos, "mpos.ui": ui, "lvgl": types.ModuleType("lvgl"), "upystore_core": core}
        ):
            path = Path(__file__).resolve().parents[1] / "assets/main.py"
            spec = importlib.util.spec_from_file_location("store_main", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        self.activity = mod.UpyStoreActivity()
        a = self.activity
        a._has_foreground = None
        a.state = "ready"
        a.message = "Loaded"
        a.closed = False
        a.busy = False
        a.task = None
        self.rendered = []
        a._render = lambda: self.rendered.append(True)
        a._notify = lambda *args: None

    def test_resume_restores_foreground_and_renders_loaded_state(self):
        self.activity.onResume(None)
        self.assertTrue(self.activity._has_foreground)
        self.assertEqual(self.rendered, [True])

    def test_pause_removes_foreground(self):
        self.activity._has_foreground = True
        self.activity.onPause(None)
        self.assertFalse(self.activity._has_foreground)

    def test_new_operation_does_not_report_previous_request_url(self):
        async def operation():
            pass

        self.activity.client = types.SimpleNamespace(last_request="https://upystore.io/previous")
        self.activity._run(operation)
        self.assertIsNone(self.activity.client.last_request)


if __name__ == "__main__":
    unittest.main()
