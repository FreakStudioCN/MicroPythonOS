# Independent uPyStore on D-Shell — 2026-11-20

The independent uPyStore app preserves the official AppStore interface and
management features, with its own backend and application identity. Public
calculator downloads and a controlled helper-module upgrade were exercised on
physical D-Shell hardware. This is a scoped result, not acceptance of every
catalog application, public dual-revision upgrades or OTA.

## Device and release

| Item | Value |
| --- | --- |
| Hardware | D-Shell / ESP32-S3 N16R8, 16 MB Flash, 8 MB PSRAM |
| Display/input | ST7789V 240 × 320, 80 MHz SPI, GT911 touch |
| Firmware | Existing MicroPythonOS 0.21.2 / API 0; no firmware flashing or `/lib` overlay this round |
| Official store | Firmware-provided `com.micropythonos.appstore` 1.5.0 restored; its previous test overlay is backed up |
| Independent app | `com.freakstudio.upystore` 1.1.0, local unpublished revision 1 |
| Final MPK | 37,122 bytes, SHA256 `13e7e1a9777b7cbf949753590ab61cfe89b9d0b252f61ba6e28778d81cce278e` |
| Public test app | CC Skill Smoke 1.0.0 / revision 1, 3,872 bytes |
| Calculator MPK SHA256 | `44b63bb4af00613edea5ce01069aa58e3032a7dad81a7e350b263c35a75418b6` |

The firmware image SHA256 last read on November 19 was
`c72e27e795441c4ab2077e97cced514ea7ac825be0e29851a5ca790ea49fd0a9`.
It is historical image-identification evidence, not a newly repeated flash
read in this round.

## What is retained and repaired

- Official list/detail layout, icon pipeline and placeholders, categories,
  Installed/Updates, version display, Open/Uninstall/Update, Update All and
  settings remain available.
- The app has a boot update service and separate notification identity. Actual
  notification dispatch opens this app's Updates page. A regression also
  serializes/restores the notification before dispatch.
- Both foreground and background use uPyStore. Search only changes the visible
  catalog; it neither filters update checks nor clears their existing state.
- Modules, preferences and update-manager instances are isolated. Store-only
  metadata and widgets are attached to copies of system App objects.
- uPyStore receipts from the prior integration are copied without modifying the
  source store's files. Removal markers prevent unwanted re-import.
- Size/SHA256, archive-root/path checks, declared launcher validation, staged
  promotion/rollback and helper-cache eviction remain enabled. Paused/destroyed
  activities release timers/widgets and do not open a late deep-link page.
- Real LVGL timer callbacks can provide a different Python wrapper for the same
  timer; callback tokens prevent missed or stale icon dispatches.

## Physical results and version boundaries

The search-fix candidate `a9c05a5a` changes only
`UPyStore._store_source_changed()` from the preceding fully exercised 1.1.0
candidate `bba7259e`: searching now invalidates the visible catalog without
clearing updates/notifications or starting an unnecessary background full-list
query. Its other ten packaged files are byte-identical to `bba7259e`.

The final release then normalizes source line endings to LF and removes one
whitespace-only line. All seven runtime modules have identical Python ASTs to
`a9c05a5a`; manifest values, documentation content, license and icon are
equivalent. This comparison is saved as `release-equivalence.json`. The final
MPK is installed as a whole package, all eleven installed file hashes are
checked, and launch/catalog/return and official-store coexistence are checked
again. Packaging normalizes text so Windows/Linux checkouts reproduce the same
artifact.

| Physical check | Observed result | Evidence scope |
| --- | --- | --- |
| Full public catalog | All displayed 529 merged rows; Utilities displayed 384; no store App object shared with AppManager | Candidate `bba7259e` |
| Search/details | Real CC Skill Smoke query and details; owned list objects and installed/published versions | Search-fix candidate `a9c05a5a`, AST-equivalent final release, plus final launch/catalog check |
| Download/install/open/uninstall | Real HTTPS MPK; size/SHA256 checked; uninstall and reinstall; CalculatorActivity `2 + 3 = 5`; return and widget cleanup | `a9c05a5a` real main-chain retest; final source equivalence and installation identity recorded |
| Receipt migration/isolation | Previous uPyStore receipt copied; official receipt and settings unchanged; uninstall cannot resurrect the foreign receipt | Initial migration plus `a9c05a5a` compatibility retest |
| Controlled upgrades | Two fixture apps: 1.0.0/r1 helper `v1 / 5` → Update All → 1.1.0/r2 helper `v2 / 105`; both reopened, then uninstalled | Candidate `bba7259e`; unchanged installer/core/detail and batch code |
| Invalid launcher | Controlled r3 rejected before replacement; installed v1 and its helper retained | Candidate `bba7259e`; unchanged installer |
| Notifications | Actual notification posted and triggered; independent app opened with `category=Updates` | Candidate `bba7259e`; unchanged final manifest/core |
| Failure/recovery | Actual MPK with controlled wrong expected SHA rejected without changing old main.py; controlled timeout; real Wi-Fi disconnect/reconnect; successful reinstall clears old error | Candidate `bba7259e`; unchanged installer/detail/backend |
| Unavailable sample | Device detail request returned HTTP 404 with a retry/return message | Candidate `bba7259e` |
| Icon timer | Real LVGL callback ran the icon request exactly once; pause/stale-callback cases covered by native tests | Candidate `bba7259e`; unchanged detail module |
| Search and coexistence | Targeted search-fix verification retains update state during search and opens both stores with distinct managers | `a9c05a5a` targeted record plus final package coexistence check |

Candidate `bba7259e` was 37,356 bytes, SHA256
`bba7259e7435a2bb389dcb2c7dfb9fc54625ec9f3ec719bd7af6f6a0802ce117`.
Its raw logs and MPK remain alongside the final release. Per-case JSON records
retain the MPK hash actually running; intermediate evidence is not relabeled
as final-candidate footage. Original v1 fixture installs were reused and
reopened before the final notification/batch sequence.

The fixture transport replaces only this app's source/installer request
functions. It does not patch global DownloadManager or the official AppStore.
It is restored after testing; test apps are removed. This is not a download or
upgrade between two revisions published by the public store.

## Host/native validation and reproduction

- 46 CPython backend/install/coexistence regressions pass.
- 24 native MicroPython tests pass: 10 install/lifecycle, 5 coexistence and 9
  independent update-flow tests. Assertions are enabled. This is headless LVGL
  execution, not a full SDL desktop-preview claim.
- `make lint`, `make syntax-tests`, manifest/MPK validation, deterministic
  rebuild and hardware-access policy checks pass.
- The API checker emits the same 41 reference-summary gaps as the unmodified
  official AppStore, with no new entries. Its raw return status is retained as
  a warning, not converted into a passing gate.
- Original source comments/docstrings and MIT license are retained. No board,
  framework or built-in AppStore source is changed in this branch.

```text
python -m unittest discover -s tests -p "cpython_upystore_*.py"
python scripts/test_upystore_headless.py --binary /path/to/lvgl_micropy_unix
python scripts/package_upystore.py --output-dir tmp/upystore-release
python tests/fixtures/upystore/build_fixtures.py --output tmp/upystore-fixtures
```

Source/installation instructions:
https://github.com/FreakStudioCN/MicroPythonOS/blob/feature/upystore-app/internal_filesystem/apps/com.freakstudio.upystore/README.md

Controlled-upgrade instructions:
https://github.com/FreakStudioCN/MicroPythonOS/blob/feature/upystore-app/tests/fixtures/upystore/README.md

## Remaining issues and evidence limits

1. A trusted helper-containing app with two genuinely published revisions is
   still required from the publisher for a public-store upgrade test.
2. Background transport stability remains open. The November 20 logs reproduce
   an `IndexError` during the page-6 update-list request below; earlier evidence
   also contains TLS `-29312` and timeouts. Foreground retry success and one
   successful full catalog do not establish repeated background stability.
   OS/HTTP/TLS and store maintainers need to investigate together.

   https://upystore.io/api/v1/apps?limit=100&page=6&q=

   The independently observed OSUpdate endpoint is tracked separately:
   https://updates.micropythonos.org/osupdate_d_shell.json
3. Danke's missing root and Show Battery's outside-root `__MACOSX` files were
   rejected in the November 19 tests. No new repaired-package acceptance is
   claimed; publishers must supply corrected releases, with strict checks kept.
4. The obsolete sample still returns a device-observed 404. Earlier calculator
   single-file 404s remain a separate server follow-up; whole-package install
   succeeds. An empty firmware-release list in the prior checks does not
   establish OTA compatibility.

   https://upystore.io/api/v1/apps/io-kontinyu-upystore-sample

   https://upystore.io/api/v1/apps/com-example-cc-skill-smoke/rev/1/files/assets/main.py

   https://upystore.io/api/v1/apps/com-example-cc-skill-smoke/rev/1/files/MANIFEST.JSON
5. Rating submission has no agreed uPyStore contract; optional install/profile
   reporting is not enabled. D-Shell camera/QR, rollback UI, power-loss recovery,
   all-app compatibility and OTA are outside the accepted result.
6. The user confirmed all requested independent-app operations on November 20:
   touch, scrolling, buttons, uninstall, install, Open, `2 + 3 = 5` and return.
   A new physical video will be supplied later. The November 19 official-store
   video remains evidence for 1.5.1 only. Framebuffer PNGs are genuine device
   captures, not camera recordings.

The initial PC urllib User-Agent received HTTP 403/1010. A request using the
stock MicroPythonOS User-Agent subsequently returned 200 for the calculator
search, followed by a PC connection timeout. These probes are not substituted
for the successful physical-device main-chain checks.

Official PR submission is on hold. No official PR, merge, store publication or
email sending is part of this result.
