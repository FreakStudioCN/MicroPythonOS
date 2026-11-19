import json

import lvgl as lv
from mpos import Activity, AppManager, InputActivity, Intent, TaskManager
from mpos.ui import add_focus_border
from upystore_core import StoreClient, friendly_error


class UpyStoreActivity(Activity):
    def onCreate(self):
        self.page = 1
        self.query = ""
        self.rows = []
        self.pagination = {}
        self.detail_data = None
        self.task = None
        self.busy = False
        self.closed = False
        self.view = "list"
        self.state = "idle"
        self.message = "Ready"
        self.install_result = None
        self.last_error = None
        self.client = StoreClient(self._notify)
        self.screen = lv.obj()
        self.screen.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.screen.set_style_pad_all(4, 0)
        self.screen.set_style_pad_row(3, 0)
        self.header = self._label(self.screen, "uPyStore")
        tools = self._row(self.screen)
        self.search_button = self._button(tools, "Search", self._search)
        self.refresh_button = self._button(tools, "Retry", lambda e: self.refresh())
        self.catalog_button = self._button(tools, "Catalog", lambda e: self.check_catalog())
        self.status = self._label(self.screen, "Ready")
        self.status.set_height(44)
        self.progress = lv.bar(self.screen)
        self.progress.set_size(lv.pct(100), 6)
        self.progress.set_range(0, 100)
        self.progress.set_value(0, False)
        self.body = lv.obj(self.screen)
        self.body.set_width(lv.pct(100))
        self.body.set_flex_grow(1)
        self.body.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.body.set_style_pad_all(3, 0)
        self.body.set_style_pad_row(4, 0)
        self.footer = self._row(self.screen)
        self.prev_button = self._button(self.footer, "Prev", lambda e: self.change_page(-1))
        self.page_label = self._label(self.footer, "1 / ?")
        self.page_label.set_width(60)
        self.next_button = self._button(self.footer, "Next", lambda e: self.change_page(1))
        self._render()
        self.setContentView(self.screen)

    def _label(self, parent, text):
        label = lv.label(parent)
        label.set_text(text)
        label.set_width(lv.pct(100))
        label.set_long_mode(lv.label.LONG_MODE.WRAP)
        return label

    def _row(self, parent):
        row = lv.obj(parent)
        row.set_size(lv.pct(100), 38)
        row.set_flex_flow(lv.FLEX_FLOW.ROW)
        row.set_style_pad_all(1, 0)
        row.set_style_pad_column(3, 0)
        row.remove_flag(lv.obj.FLAG.SCROLLABLE)
        return row

    def _button(self, parent, text, callback, grow=1):
        button = lv.button(parent)
        button.set_height(32)
        button.set_flex_grow(grow)
        if grow == 0:
            button.set_width(lv.pct(100))
        button.set_style_pad_all(4, 0)
        label = lv.label(button)
        label.set_text(text)
        label.center()
        button.add_event_cb(callback, lv.EVENT.CLICKED, None)
        lv.group_get_default().add_obj(button)
        add_focus_border(button)
        return button

    def onResume(self, screen):
        super().onResume(screen)
        self.closed = False
        if self.state == "idle":
            self.refresh()
        else:
            self._notify(self.state, self.message)
            self._render()

    def onPause(self, screen):
        super().onPause(screen)
        if self.task and self.busy:
            self.task.cancel()
        self.task = None
        self.busy = False

    def onStop(self, screen):
        self.onPause(screen)

    def onDestroy(self, screen):
        self.closed = True
        self.onPause(screen)

    def _notify(self, state, message, progress=0):
        self.state = state
        self.message = message
        self.if_foreground(self.status.set_text, message)
        self.if_foreground(self.progress.set_value, int(progress), False)

    def _run(self, operation):
        if self.busy:
            return
        self.busy = True
        self.last_error = None
        self.client.last_request = None
        self.task = TaskManager.create_task(self._execute(operation))

    async def _execute(self, operation):
        try:
            await operation()
        except Exception as error:
            self.last_error = {"url": self.client.last_request, "error": str(error)}
            print("UPYSTORE_ERROR", json.dumps(self.last_error))
            self._notify("error", friendly_error(error))
        finally:
            self.busy = False
            self.task = None

    def refresh(self):
        if self.view == "detail" and self.detail_data:
            self.open_app(self.detail_data["app"]["slug"])
        else:
            self._run(self._load_list)

    async def _load_list(self):
        self._notify("loading", "Loading apps...")
        value = await self.client.list_apps(self.page, self.query)
        self.rows = value["apps"]
        self.pagination = value["pagination"]
        self.view = "list"
        self._notify("ready", "%d apps | %s" % (self.pagination.get("total", len(self.rows)), self.query or "All"))
        self.if_foreground(self._render)

    def change_page(self, delta):
        if self.busy:
            return
        maximum = self.pagination.get("total_pages", 1)
        target = max(1, min(maximum, self.page + delta))
        if target != self.page:
            self.page = target
            self.view = "list"
            self.refresh()

    def _search(self, event):
        if self.busy:
            return
        self.startActivityForResult(Intent(activity_class=InputActivity, extras={"setting": {"title": "Search upystore", "ui": "text", "key": "query"}, "value": self.query}), self._search_result)

    def _search_result(self, result):
        data = result.get("data", result)
        if result.get("result_code"):
            self.query = str(data.get("value", ""))[:80]
            self.page = 1
            self.view = "list"
            self.refresh()

    def check_catalog(self):
        self._run(self._catalog)

    async def _catalog(self):
        self._notify("loading", "Checking compatibility catalog...")
        count = await self.client.catalog_count()
        self._notify("ready", "Compatibility catalog: %d apps" % count)

    def open_app(self, slug):
        async def load():
            self._notify("loading", "Loading app details...")
            self.detail_data = await self.client.detail(slug)
            self.view = "detail"
            self._notify("ready", "Details loaded")
            self.if_foreground(self._render)
        self._run(load)

    def _back(self, event=None):
        if self.busy:
            return
        self.view = "list"
        self._render()

    def _render(self):
        self.body.clean()
        self.page_label.set_text("%d / %d" % (self.page, self.pagination.get("total_pages", 1)))
        if self.view == "detail" and self.detail_data:
            app = self.detail_data["app"]
            self._button(self.body, "Back to list", self._back, grow=0)
            self._label(self.body, app.get("name", app["fullname"]))
            self._label(self.body, "v%s  r%s\n%s" % (app.get("version"), app.get("revision"), app.get("publisher", "")))
            self._label(self.body, app.get("long_description") or app.get("short_description") or "No description")
            self.install_button = self._button(self.body, "Install / update", lambda e: self.install_selected(), grow=0)
            self.launch_button = self._button(self.body, "Open installed app", lambda e: self.launch_selected(), grow=0)
        else:
            for app in self.rows:
                button = self._button(self.body, app.get("name", app.get("fullname", "?")), lambda e, slug=app["slug"]: self.open_app(slug))
                button.set_width(lv.pct(100))
                button.set_flex_grow(0)
            if not self.rows:
                self._label(self.body, "No apps. Check WiFi and Retry.")

    def install_selected(self):
        if not self.detail_data:
            return
        self._run(self._install)

    async def _install(self):
        self.install_result = await self.client.install(self.detail_data)
        self.if_foreground(self._render)

    def launch_selected(self):
        if self.busy or not self.detail_data:
            return
        fullname = self.detail_data["app"]["fullname"]
        AppManager.refresh_apps()
        if not AppManager.get(fullname):
            self._notify("error", "Install this app before opening it.")
            return
        print("UPYSTORE_LAUNCH", fullname)
        if not AppManager.start_app(fullname):
            self._notify("error", "App failed to start. Return here and Retry.")
