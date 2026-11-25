# AppStore upstream synchronization and focused regression, 2026-11-25

The organization main and full integration branch retain the existing commits and
all historical evidence. They were synchronized with official main `311f9790ca51e2d15240c32563fb8bb5db4c482e`.
Only CHANGELOG conflicted; the future AppStore entry and official release notes
were retained. The latest upstream follow-up touches only Duke3D and does not
change the tested AppStore, framework or tests.

The upstream branch has **two focused commits, 22 changed files**: AppStore code,
regressions, reproducible test/package tools, fixtures and one usage document.
Historical reports, duplicate screenshots, logs and internal delivery notes are
not in that diff. They remain on the organization integration branch.

## Commits and artifact

- Organization PR source: https://github.com/FreakStudioCN/MicroPythonOS/tree/feature/appstore-upystore-upstream
- Functional commit: https://github.com/FreakStudioCN/MicroPythonOS/commit/0270111f025370e9e222475704613c9e5af3af7e
- Usage documentation commit: https://github.com/FreakStudioCN/MicroPythonOS/commit/d12b1d01a7d4fb8a42d2db191db32362a113029a
- Full history: https://github.com/FreakStudioCN/MicroPythonOS/tree/review/appstore-upystore-standards
- AppStore 1.5.4, unpublished local revision 4; 34617 bytes.
- SHA256: `b6a42d68ca5852ad3dee6b5093b91e2bcdd594373e57807fb65c9d865149f41e`.

All nine packaged files match the device and both branches. The package hash is
identical to the November 23 standards-reviewed artifact; synchronizing upstream
and removing report-only files did not change the app payload.

## Verification after synchronization

- 45 CPython cases passed (27 backend and 18 review regressions).
- 132 native MicroPython cases passed using current merged Python framework
  source and the available native interpreter, not a rebuilt complete OS image.
- Project lint, MicroPython syntax and `git diff --check` passed.
- 21 focused physical-device records passed; detailed results below.

The isolated native export initially lacked the normal `apps/` directory. Its
three uninstall-refresh tests errored before their assertions. Creating that
standard directory and rerunning only the affected suite passed all three; the
initial runner result and final per-suite logs remain in the evidence archive.
The first online lint invocation could not fetch its tool; the project command
passed using the cached tool offline, and host lint passed separately.

Target: D-Shell ESP32-S3 N16R8, ST7789V 240x320, GT911, display SPI 80 MHz.
Firmware remains MicroPythonOS 0.21.2/API 0. No complete latest OS image was
flashed. Current extent extraction has native regression coverage; this older
device firmware exercises the compatibility install path.

Physical checks include real browsing/search/details, download, SHA256/size,
uninstall, install, CalculatorActivity launch with 2+3=5 and return. Controlled
two-app Update All, notification navigation, same-name and renamed/deleted helper
updates without reset, invalid launcher rejection and rollback protection passed.
The test transport was removed and real catalog/category/search restored.

These are programmatic UI operations on the real board. November 23 manual
confirmation remains separately dated; it is not a new November 25 manual run.
The three PNGs below are new device framebuffers, not photographs or camera video.
No new physical video was supplied.

## Evidence

- [Focused device records](assets/appstore-upstream-20261125/device-results.json)
- [Native summary](assets/appstore-upstream-20261125/native-summary.json)
- [Catalog framebuffer](assets/appstore-upstream-20261125/builtin-full-catalog.png)
- [Calculator framebuffer](assets/appstore-upstream-20261125/builtin-calculator.png)
- [Updated helper framebuffer](assets/appstore-upstream-20261125/builtin-renamed-helper-v2.png)
- [MPK, serial logs and reproduction evidence](assets/appstore-upstream-20261125/evidence.zip)

## Remaining limits

While the real foreground install/launch succeeded, a background request to
`https://upystore.io/api/v1/apps?limit=100&page=3&q=` timed out. Intermittent
network/TLS failures remain undiagnosed and can fail a foreground request or
delay background discovery. Recovery is tested; root-cause resolution is not
claimed. OS networking and store/network maintainers need correlated logs.

Malformed third-party packages remain rejected. A public dual-revision upgrade
is additional coverage, not a substitute for or prerequisite to the controlled
helper-upgrade result. Every-app compatibility and OTA are outside this task.

The auxiliary stale API index findings remain documented in the November 23
record; they are not represented as a passing gate. Official interfaces were
checked against current source and actual native runtime regressions.

PR submission and upstream merge are separate milestones. No upstream merge is
claimed by this report; the new PR URL will be recorded after submission.
