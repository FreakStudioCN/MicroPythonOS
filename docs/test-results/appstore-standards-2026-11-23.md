# Built-in AppStore standards review, 2026-11-23

The task is to extend the official builtin AppStore with uPyStore while keeping
its existing user flow, and verify browsing, download, install, launch,
update/uninstall on D-Shell. Every-app compatibility, OTA and a public two-revision
example are not submission gates for this scoped client change.

PR #410 was closed by its author on November 20, before this standards review.
Its source branch was deleted. No maintainer review or rejection was recorded.
It remains closed; this review does not reopen it or create another PR.
The previous code and full history are preserved locally and in Git bundles.

## Review findings and corrections

| Official requirement / source | Check and resulting implementation | Evidence |
| --- | --- | --- |
| Default/backend compatibility: https://docs.micropythonos.com/apps/appstore/ | Corrected the unpublished project default from uPyStore to BadgeHub. uPyStore remains selectable; explicit saved choices are retained. Invalid choices fall back to BadgeHub. | Default, invalid preference and both explicit-source regressions. |
| Lifecycle: https://docs.micropythonos.com/apps/app-lifecycle/ | Retained base resume/pause calls, foreground guards, timer cancellation and owned-widget cleanup. Storage progress now also ignores a paused/destroyed page. | Existing owner/lifecycle regressions plus a new paused storage-progress case. |
| App/module layout: https://docs.micropythonos.com/apps/creating-apps/ | Retained original fullname, icon, root MANIFEST.JSON and flat Python modules. No alternate storefront or copied framework module. | Manifest/package validators and source-scope review. |
| MPK contract: https://docs.micropythonos.com/apps/bundling-apps/ | Exact first root directory, only one top-level root, safe entry paths, categories list, declared main/launcher, deterministic sorted package and fixed timestamps remain. | Strict malformed-path/launcher/hash/staging cases. Deflate is supported; the documentation's stored-entry preference is not a mandatory restriction. |
| Storage ownership: https://docs.micropythonos.com/architecture/filesystem/ | Temporary work stays under this app's cache namespace; receipts under preferences with legacy migration. Stage and backup directories represent distinct replacement/rollback states. | Receipt migration/removal and replacement/rollback tests. |
| Current upstream installation behavior | Merged official main fbfa13a4. Resolved the AppDetail conflict by retaining verified staged installs and the new asynchronous storage-reservation callback. The archive closes around defragmentation, then resumes from its saved position. Older firmware uses its existing installer. | New byte-preservation, closed-handle/progress, legacy fallback and failure-cleanup tests. |
| Contribution: https://docs.micropythonos.com/other/merge-checklist/ | App version 1.5.4, factual CHANGELOG, focused regressions, updated reproduction instructions. Code changes and evidence/document reorganization are committed separately. No new board or framework requires MAINTAINERS changes. | Commit history, project lint, syntax and targeted native/host tests. |

Source comments/docstrings are retained; the storage-progress method is inherited
from upstream rather than an app-local copy of a framework. The custom reference
index checker is not substituted for actual framework source or runtime tests.
Upstream architectural acceptance remains a maintainer decision.

## Current artifact and target

| Item | Value |
| --- | --- |
| AppStore | 1.5.4, original com.micropythonos.appstore identity |
| Local package | revision 4, 34,617 bytes; unpublished |
| Package SHA256 | b6a42d68ca5852ad3dee6b5093b91e2bcdd594373e57807fb65c9d865149f41e |
| Target | D-Shell ESP32-S3 N16R8, ST7789V 240x320, GT911, display SPI 80 MHz |
| Firmware | Existing MicroPythonOS 0.21.2 / API 0; full latest OS not reflashed |
| Deployment | Same-fullname app update; earlier 1.5.3 directory backed up; all nine new file hashes verified |

The native-extent path is exercised with current framework source and focused
reservation tests. This board's older firmware exercises the compatibility
fallback. These are distinct observations, not a claim of new native-extent
firmware acceptance on D-Shell.

## Test execution

Before the fixes, the new/updated host cases failed (three assertions and three
missing-helper errors). After fixes: **45 CPython tests** and **132 native
MicroPython cases** passed, plus project lint and MicroPython syntax checks.
The isolated native run uses the latest merged Python source and the available
MicroPython interpreter, not a newly compiled complete OS image.

**25 physical-device checks passed on AppStore 1.5.4.** The user also confirmed
saved uPyStore selection, touch/scroll/buttons, uninstall, reinstall, Open,
2 + 3 = 5 and return with the reply “没问题”. This is new 1.5.4 feedback;
November 19/20 recordings and earlier application versions remain historical.

The live CC Skill Smoke 1.0.0/r1 MPK was 3,872 bytes, SHA256
`44b63bb4af00613edea5ce01069aa58e3032a7dad81a7e350b263c35a75418b6`.
All shows 529 merged entries and Utilities 384. Actual install, separate launch,
uninstall, controlled two-app Update All, renamed/removed helpers without reset,
invalid launcher rejection, notification navigation, wrong-hash protection,
actual Wi-Fi interruption/recovery, controlled timeout, real obsolete-sample
404 and final cleanup all passed. These counts do not mean every app was tested.

New evidence:

- [25 device records](assets/appstore-standards-20261123/device-results.json)
- [Catalog framebuffer](assets/appstore-standards-20261123/builtin-full-catalog.png)
- [Installed calculator framebuffer](assets/appstore-standards-20261123/builtin-calculator.png)
- [New helper framebuffer](assets/appstore-standards-20261123/builtin-renamed-helper-v2.png)

These PNGs are genuine device RGB565 framebuffers, not camera photographs.
No new physical video was supplied. Native tests also exercised the real current
StreamingUnzip asynchronous path with a valid MPK, separately from the focused
extent-reservation and old-runtime-fallback cases.

The auxiliary API index checker reports 44 unresolved index entries: 41 inherited,
one timer type-inference case, and two imports of the new official extent module
not present in the older index. Its raw result remains failed; new interfaces
were checked against current upstream source and runtime regressions instead.

## Organization review delivery

Code and test commit: https://github.com/FreakStudioCN/MicroPythonOS/commit/f1ec22737455123e6b8e7f3ebd86f71be027adae

Review branch: https://github.com/FreakStudioCN/MicroPythonOS/tree/review/appstore-upystore-standards

Closed PR (kept closed): https://github.com/MicroPythonOS/MicroPythonOS/pull/410


## Network and publisher issues: actual impact

- During the new calculator chain, a background request to
  `https://upystore.io/api/v1/apps?limit=100&page=4&q=` timed out; the foreground
  calculator install and launch succeeded. Background discovery can therefore
  be delayed or fail for that cycle. Prior page 3/6 TLS/header/timeout failures
  are historical observations, not a diagnosed server-side cause.
- A metadata/MPK timeout can also fail the current foreground operation. The
  client must display a retry path and preserve the old app. Device error and
  reconnection checks verify recovery; they do not prove the root cause fixed.
  Reproduction context is connected Wi-Fi plus a paginated 100-item background
  scan; the external failure is intermittent, not guaranteed every run. OS HTTP/
  TLS and store/network maintainers need to compare request and server logs.
- Previously malformed Danke/Show Battery revisions affect those packages;
  rejecting them is the intended safety result. Obsolete-sample and calculator
  single-file 404s do not affect a healthy whole-MPK installation. Their earlier
  dates are retained until a new response/package has been checked.
- The controlled helper upgrade proves the changed replacement/cache logic.
  A public two-revision example is useful additional coverage, not a uniform
  prerequisite for proposing this integration.

No new PR is submitted by this review. No email is sent by the tooling.
