# AppStore upstream synchronization and focused regression, 2026-11-25

The organization main and full integration branch retain the existing commits and
all historical evidence. They were synchronized with official main `311f9790ca51e2d15240c32563fb8bb5db4c482e`.
Only CHANGELOG conflicted; the future AppStore entry and official release notes
were retained. The latest upstream follow-up touches only Duke3D and does not
change the tested AppStore, framework or tests.

At original submission the upstream branch had **two focused commits, 22 changed files**: AppStore code,
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

Official PR submitted by yangcong-bit from the organization branch:
https://github.com/MicroPythonOS/MicroPythonOS/pull/415

The PR is open and has not been merged. The author-closed #410 remains closed.
PR submission and upstream merge are separate milestones; CI and maintainer
review continue on the PR page.


## CI follow-up: install-button regression

The original full CI run exposed a missed graphical suite:
`test_graphical_appstore_install_button.py`, specifically
`test_no_download_url_ignores_click`. Linux x64/arm64 and macOS Intel/arm64 all
reported the same missing `MockDetail.fetch_and_set_app_details` error; each
failed 1 of 227 test files. This was an implementation/test-contract mismatch
in this integration, not a completed full-CI result.

Fix on the organization PR branch:
https://github.com/FreakStudioCN/MicroPythonOS/commit/30a269018b9300db82a28378620859edfc3ba5a5

Missing URLs keep the original no-op behavior unless a detail request has
actually failed. Failed details remain retryable, while an in-progress detail
request is not queued again. The original assertion is preserved. Two cases
cover retry-after-failure and no duplicate request while loading, and the
graphical install-button suite is now part of the default focused native runner.

Red-before/green-after verification reproduced the original error and the new
loading-state failure before the fix. Afterwards **28 graphical install-button
cases**, **160 native cases in total**, **45 CPython cases**, project lint,
MicroPython syntax and PR-scope whitespace checks passed.

[Red/green and host regression logs](assets/appstore-upstream-20261125/ci-fix-evidence.zip)

The updated PR now has three commits and 23 changed files. New official CI has
started; lint passed, and the remaining jobs were still running when checked.
The earlier 21 physical-device checks and MPK hash describe the pre-fix payload.
No new physical deployment or manual confirmation is claimed for this follow-up.
