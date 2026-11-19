import gc
import hashlib
import json
import os
import shutil
import struct

from mpos import AppManager, BuildInfo, ConnectivityManager, DownloadManager, TaskManager


BASE_URL = "https://upystore.io"
SELF = "com.freakstudio.upystore"
MAX_PACKAGE_BYTES = 2097152


def absolute_url(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Missing URL")
    if value.startswith("/") and not value.startswith("//"):
        return BASE_URL + value
    if value.startswith(BASE_URL + "/"):
        return value
    raise ValueError("Only HTTPS upystore.io URLs are accepted")


def validate_fullname(value):
    if not isinstance(value, str) or not value or len(value) > 120:
        raise ValueError("Invalid app identity")
    if any(not part for part in value.split(".")):
        raise ValueError("Invalid app identity")
    if any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in value):
        raise ValueError("Invalid app identity")
    return value


def quote_query(text):
    output = ""
    for value in text.encode("utf-8"):
        char = chr(value)
        output += char if char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~" else "%%%02X" % value
    return output


def friendly_error(error):
    text = str(error)
    if "Offline" in text:
        return "Offline. Connect WiFi, then Retry."
    if "HTTP 404" in text or "HTTP 410" in text:
        return "App or package unavailable (404/410). Retry later or choose another app."
    if "HTTP 403" in text:
        return "Service blocked this request (403). Retry later; contact store support."
    if "HTTP" in text:
        return "Request failed: %s. Retry." % text[:80]
    if "hash" in text.lower() or "size mismatch" in text:
        return "Package verification failed. Existing app preserved. Retry."
    if not text or "timeout" in text.lower() or "-110" in text:
        return "Request timed out. Check WiFi, then Retry."
    return "%s. Retry." % text[:110]


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def mkdirs(path):
    current = ""
    for part in path.split("/"):
        if not part:
            continue
        current += "/" + part
        if not exists(current):
            os.mkdir(current)


def remove_tree(path):
    if exists(path):
        if os.stat(path)[0] & 0x4000:
            shutil.rmtree(path)
        else:
            os.remove(path)


def verify_package(path, expected_size, expected_sha):
    actual_size = os.stat(path)[6]
    if expected_size and actual_size != expected_size:
        raise ValueError("Package size mismatch")
    if actual_size < 4 or actual_size > MAX_PACKAGE_BYTES:
        raise ValueError("Package size is unsupported")
    sha = hashlib.sha256()
    with open(path, "rb") as source:
        if source.read(2) != b"PK":
            raise ValueError("Not an MPK ZIP package")
        source.seek(0)
        while True:
            chunk = source.read(4096)
            if not chunk:
                break
            sha.update(chunk)
    digest = "".join("%02x" % value for value in sha.digest())
    if not expected_sha or digest.lower() != expected_sha.lower():
        raise ValueError("Package SHA256 hash missing or mismatched")
    return digest


def check_archive_limits(path, fullname, free_bytes):
    total = 0
    count = 0
    with open(path, "rb") as source:
        while True:
            header = source.read(30)
            if header[:4] in (b"PK\x01\x02", b"PK\x05\x06"):
                break
            if len(header) != 30 or header[:4] != b"PK\x03\x04":
                raise ValueError("Invalid MPK header")
            values = struct.unpack("<IHHHHHIIIHH", header)
            flags, method, compressed, expanded, name_size, extra_size = values[2], values[3], values[7], values[8], values[9], values[10]
            name = source.read(name_size).decode("utf-8")
            if count == 0 and name != fullname + "/":
                raise ValueError("MPK root does not match app identity")
            if not name.startswith(fullname + "/") or ".." in name.split("/") or "\\" in name:
                raise ValueError("Unsafe MPK path")
            if flags & 9 or method not in (0, 8):
                raise ValueError("Unsupported MPK compression or flags")
            count += 1
            total += expanded
            if count > 256 or total > min(4194304, free_bytes - 65536):
                raise ValueError("Not enough free Flash or package too large")
            source.seek(extra_size + compressed, 1)
    if count == 0:
        raise ValueError("Empty MPK")
    return total


def validate_installed(path, expected):
    manifest_path = path + "/MANIFEST.JSON"
    if not exists(manifest_path):
        manifest_path = path + "/META-INF/MANIFEST.JSON"
    with open(manifest_path) as source:
        manifest = json.load(source)
    if manifest.get("fullname") != expected["fullname"] or manifest.get("version") != expected["version"]:
        raise ValueError("Installed manifest identity/version mismatch")
    activities = manifest.get("activities", [])
    if not activities:
        raise ValueError("No application Activity in package")
    for activity in activities + manifest.get("services", []):
        entry = activity.get("entrypoint", "")
        if entry.startswith("/") or ".." in entry.split("/") or "\\" in entry or not entry.endswith(".py"):
            raise ValueError("Invalid application entrypoint")
        if not exists(path + "/" + entry) or not activity.get("classname"):
            raise ValueError("Application entrypoint is missing")
    return manifest


def commit_install(stage, destination, backup):
    had_old = exists(destination)
    if exists(backup):
        raise RuntimeError("Previous install backup exists; recovery required")
    if had_old:
        os.rename(destination, backup)
    try:
        os.rename(stage, destination)
    except Exception:
        if had_old:
            os.rename(backup, destination)
        raise
    return had_old


class StoreClient:
    def __init__(self, notify=None, base_url=BASE_URL):
        self.notify = notify or (lambda state, message, progress: None)
        self.base_url = base_url
        self.last_request = None

    def emit(self, state, message, progress=0):
        print("UPYSTORE_STATE", state, message, progress)
        self.notify(state, message, progress)

    async def json_request(self, path, limit=131072):
        if not ConnectivityManager.is_online():
            raise RuntimeError("Offline")
        url = absolute_url(path)
        self.last_request = url
        print("UPYSTORE_REQUEST", url)
        data = bytearray()

        async def collect(chunk):
            if len(data) + len(chunk) > limit:
                raise ValueError("Response too large")
            data.extend(chunk)

        result = await TaskManager.wait_for(DownloadManager.download_url(url, chunk_callback=collect), 35)
        if not result:
            raise RuntimeError("Request failed")
        value = json.loads(data)
        data = None
        gc.collect()
        return value

    async def list_apps(self, page=1, query=""):
        value = await self.json_request("/api/v1/apps?limit=6&page=%d&q=%s" % (page, quote_query(query)))
        if not isinstance(value, dict) or not isinstance(value.get("apps"), list) or not isinstance(value.get("pagination"), dict):
            raise ValueError("Invalid app list response")
        return value

    async def catalog_count(self):
        value = await self.json_request("/app_index.json", 700000)
        if not isinstance(value, list):
            raise ValueError("Invalid compatibility catalog")
        count = len(value)
        del value
        gc.collect()
        return count

    async def detail(self, slug):
        validate_fullname(slug)
        value = await self.json_request("/api/v1/apps/" + slug)
        if not isinstance(value, dict) or not isinstance(value.get("app"), dict) or not isinstance(value.get("versions"), list):
            raise ValueError("Invalid application detail response")
        return value

    async def install(self, detail):
        app = detail["app"]
        fullname = validate_fullname(app["fullname"])
        if fullname == SELF or exists("/builtin/apps/" + fullname):
            raise ValueError("Built-in apps and this store cannot be replaced here")
        revision = app.get("revision")
        version = next((v for v in detail["versions"] if v.get("revision") == revision), None)
        if not version:
            raise ValueError("Published package revision unavailable")
        minimum = app.get("min_os_version")
        if minimum and AppManager.compare_versions(minimum, BuildInfo.version.release):
            raise ValueError("Requires OS " + minimum)
        if (app.get("min_api_level") or 0) > BuildInfo.version.api_level:
            raise ValueError("Requires a newer OS API level")
        size = version.get("file_size_bytes")
        if not isinstance(size, int) or size < 4 or size > MAX_PACKAGE_BYTES:
            raise ValueError("Published package size unavailable or too large")
        digest = version.get("file_sha256")
        if not digest or len(digest) != 64:
            raise ValueError("Published package SHA256 hash unavailable")
        if not ConnectivityManager.is_online():
            raise RuntimeError("Offline")
        url = absolute_url(version.get("download_url") or app.get("download_url"))
        work = "/data/upystore"
        mkdirs(work + "/stage")
        mkdirs(work + "/backup")
        stage = work + "/stage/" + fullname
        backup = work + "/backup/" + fullname
        destination = "/apps/" + fullname
        archive = work + "/download.mpk"
        if exists(backup):
            raise RuntimeError("Previous install backup exists; recovery required")
        remove_tree(stage)
        remove_tree(archive)
        received = 0
        self.last_request = url
        self.emit("downloading", "Downloading MPK", 0)
        print("UPYSTORE_REQUEST", url)
        try:
            with open(archive, "wb") as output:
                async def consume(chunk):
                    nonlocal received
                    received += len(chunk)
                    if received > size:
                        raise ValueError("Package size mismatch")
                    output.write(chunk)
                    self.emit("downloading", "Downloading %d / %d B" % (received, size), min(95, received * 95 // size))
                ok = await TaskManager.wait_for(DownloadManager.download_url(url, chunk_callback=consume), 90)
            if not ok:
                raise RuntimeError("Package download failed")
            self.emit("verifying", "Verifying size and SHA256", 96)
            actual_hash = verify_package(archive, size, digest)
            stats = os.statvfs("/")
            check_archive_limits(archive, fullname, stats[0] * stats[3])
            self.emit("installing", "Checking package in staging", 98)
            await TaskManager.sleep_ms(5)
            AppManager.install_mpk(archive, stage)
            validate_installed(stage, app)
            had_old = commit_install(stage, destination, backup)
            AppManager.refresh_apps()
            if had_old:
                remove_tree(backup)
            result = {"fullname": fullname, "version": app["version"], "revision": revision, "bytes": size, "sha256": actual_hash}
            print("UPYSTORE_INSTALLED", json.dumps(result))
            self.emit("installed", "Installed " + app["version"], 100)
            return result
        finally:
            remove_tree(archive)
            remove_tree(stage)
