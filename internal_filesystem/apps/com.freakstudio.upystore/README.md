# uPyStore for MicroPythonOS

Independent application derived from the official MicroPythonOS AppStore.
It preserves the official list/detail interface, icon pipeline, categories,
installed-app management, version display, uninstall, Update All, settings and
background update notifications while connecting to `https://upystore.io/`.
It does not replace `com.micropythonos.appstore` or change its BadgeHub backend.

Application: `com.freakstudio.upystore` version **1.1.0**. This supersedes the
early simplified 1.0.0 prototype using the same application identity.

## Installation

Build a deterministic local MPK from the repository root:

```text
python scripts/package_upystore.py --output-dir tmp/upystore-release
```

Install `com.freakstudio.upystore_r1.mpk` using MicroPythonOS's package installer
or copy it to the device and run:

```python
from mpos import AppManager
AppManager.install_mpk('/data/com.freakstudio.upystore_r1.mpk', '/apps/com.freakstudio.upystore')
AppManager.refresh_apps()
```

When replacing the 1.0.0 prototype, close its activities and restart the device
after installation to release its old modules. No firmware rebuild or `/lib`
overlay is required. The deferred boot service starts update checks after boot;
the UI also allows foreground checks through the existing update flows.

Open **uPyStore**, select **All**, or use **Settings → Search Store**. Open an
application row for description, installed/store versions, Install/Update,
Open and Uninstall. The **Updates** category and **Update N Apps** action use
the same uPyStore source as the foreground catalog.

## Isolation and installation protection

- Application modules use `upystore_` names. Official AppStore modules,
  preferences, service singleton and notification are not replaced.
- Update notifications use an app-owned Intent action and data route so the
  Updates category survives notification dispatch and persistence. No global
  notification or navigation framework change is required.
- Preferences: `prefs/com.freakstudio.upystore`; receipts are below its
  `receipts` directory. Temporary downloads/staging/backups are under
  `cache/com.freakstudio.upystore/install`.
- Existing uPyStore receipts from the earlier AppStore integration are copied
  read-only from its old locations. BadgeHub receipts are not imported. Removal
  records prevent an old foreign receipt from being imported again after an
  uninstall; source receipts are preserved.
- Whole MPKs require published size and SHA256, a matching single application
  root, safe paths, compatible metadata and a `main`/`launcher` entrypoint.
  Python entries are compiled for syntax checks; compiled entries are checked
  for an appropriate MPY header. Validation does not execute downloaded code.
- Validated files are promoted from staging with rollback; helper-module
  caches are cleared before relaunch. Installation success and launch success
  must be checked separately. This is not a package-signature implementation
  or a claim of sudden-power-loss atomicity.

## Validation and remaining limits

```text
python -m unittest discover -s tests -p "cpython_upystore_*.py"
python scripts/test_upystore_headless.py --binary /path/to/lvgl_micropy_unix
python tests/fixtures/upystore/build_fixtures.py
```

See `docs/test-results/upystore-standalone-2026-11-20.md` for the versioned
hardware results and the distinction between real public downloads and
controlled helper-module upgrades.

uPyStore has no agreed rating-submission contract, so BadgeHub rating controls
are not exposed. Optional install/device-profile reporting is not enabled.
Camera scanning is retained from the official UI, with no new global URL
handler or host allowlist; D-Shell has no camera and scanning is not accepted
as tested. Firmware OTA, app rollback UI, all-app compatibility, and repeated
background TLS stability are not included in the accepted result.

The known malformed Danke/Show Battery packages must be fixed by their
publishers; path checks remain strict. Public dual-revision helper upgrade
testing requires a trusted application with both revisions actually published.

## Provenance and license

Based on the official `com.micropythonos.appstore` at MicroPythonOS commit
`8484908a5ceade80a7a5854925b85d662a3b480b`, with the tested integration and
installation fixes developed on `feature/appstore-upystore`.
MicroPythonOS source: https://github.com/MicroPythonOS/MicroPythonOS

The original MIT license and copyright notice are included in `LICENSE`.
The official upstream PR is on hold; neither this app nor the backend
integration is represented as approved or merged upstream.
