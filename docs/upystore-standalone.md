# Independent uPyStore client

uPyStore 1.1.0 (`com.freakstudio.upystore`) reuses the official MicroPythonOS
AppStore interface and management flows as an independently installed app.
The official `com.micropythonos.appstore` remains the BadgeHub client. No board,
firmware, framework or built-in AppStore source is changed by this branch.

The independent client retains lists, downloaded/fallback icons, categories,
Installed/Updates, descriptions, installed/published versions, Open, Uninstall,
individual updates, Update All, settings and boot-service notifications. Its
foreground and background requests use uPyStore; background update checks do
not inherit a foreground search query. Searching does not clear pending
updates or request another full background catalog.

App-local `upystore_` modules, preferences, receipts, request queue, update
manager and notification identity are separate from the official store.
Installed-app metadata is copied before it is enriched for this storefront.
Update notifications have a manifest-declared app-owned action/data route so
the Updates destination survives dispatch and notification persistence.

Whole-package installation requires published size/SHA256, safe archive paths,
matching identity/version and a declared launcher with a syntactically valid
Python entry or a compatible MPY header. Validated files are promoted from
staging with rollback. Old helper modules are invalidated before reopening.
Runtime dependencies and successful launch are verified separately.

Installation and reproduction:
https://github.com/FreakStudioCN/MicroPythonOS/blob/feature/upystore-app/internal_filesystem/apps/com.freakstudio.upystore/README.md

Hardware results and evidence boundaries:
https://github.com/FreakStudioCN/MicroPythonOS/blob/feature/upystore-app/docs/test-results/upystore-standalone-2026-11-20.md

The early simplified prototype and the November 19 built-in-store integration
remain historical branches. This branch replaces the prototype's application
identity with the fuller official-store-derived implementation. Tested source
snapshots, intermediate MPKs and original logs are retained in the evidence
archive; earlier videos retain their original version labels.

Upstream discussion:
https://github.com/MicroPythonOS/MicroPythonOS/issues/207

Official PR submission is explicitly on hold. Organization-branch commits,
public app-store publication, official PR submission and official merge are
separate states; this delivery does not publish an app or open/merge a PR.
