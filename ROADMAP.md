# Roadmap

Verdant HA is a self-hosted Home Assistant add-on for a houseplant collection. This file lists what is actually still open; released changes are in [plantcare_web/CHANGELOG.md](plantcare_web/CHANGELOG.md), and verification notes are in [docs/STATUS.md](docs/STATUS.md).

Current version: **1.1.4** (27 November 2026).

## Done recently

- [x] **Plant photo viewer (1.1.4)**: removed the inaccessible original link while keeping full-screen viewing.
- [x] **Adjustable text size (1.1.3)**: five browser-local levels (90–150%) with preview and reset under Settings → Appearance; enlarged-text reflow on desktop and phone, unchanged icon/photo sizing and printed labels, 60 browser tests and visual checks at 320/360/375/390 and 1280 px. No archive migration; rollback checkpoint `checkpoint/before-font-scaling`.
- [x] **Bidirectional care learning and grower guardrails (1.1.2)**: repeated postponements can lengthen irrigation intervals and early watering can shorten them; recorded deadlines, historical estimates and distinct cycles are explicit. Daily AI bounds follow the experience profile (±15/25/35/50%) without relaxing botanical minimums or adding automatic plan application.
- [x] **Clearer API errors (1.1.1)**: distinguish server, session and network failures from invalid input; preserve structured field details and specific English errors instead of the generic validation banner.
- [x] **Feeding safety (1.1.1)**: preselect feeding for combined care while allowing opt-out; require at least two watering intervals between feeding dates, including manual saves, adaptive plans and AI suggestions, with explicit prompt constraints and output correction.
- [x] **Backup and restore**: a web ZIP/JSON backup can now be restored over the current archive, with a preview of both sides, a second confirmation, an atomic replacement and a `restore-snapshot.sqlite` copy of the previous database. Photos are never deleted; the export docs now name the add-on plus `/share` partial backup.
- [x] **Frontend quality baseline**: Chromium E2E and axe checks in CI, keyboard navigation and dialog fixes, and improved text contrast in the core views.
- [x] **Care and plant detail browser coverage**: verify that canceling a watering changes nothing, completion persists in both histories, and plant details show the correct diary on desktop and mobile.
- [x] **Archive scale baseline**: [repeatable synthetic workload](docs/ARCHIVE_SCALE.md) and a local SQLite index for paginated care history, without changing the backup format.
- [x] Growth diary photos open full size in a modal instead of a blank tab on phones.
- [x] `Intl` formatters cached once per language and option shape; plural keys used in code are checked in CI.
- [x] Phone polish: real tap feedback, 44 px detail buttons, contained modal scrolling and no keyboard stealing in the editors.
- [x] Complete English UI: health album, labels, botanical library, identification, species library, AI assistant and model catalog, with dates and doses following the active locale.

- [x] Care engine with three per-plant modes (Manual, Verdant, AI) and one global shadow/operational switch.
- [x] AI daily analysis and plant-card assistant, with preview and selective application; automatic application off by default.
- [x] AI answers rendered as Markdown in the green advice box.
- [x] Collection analytics, health index, merged timeline, Home insights, plant-card chart and 30/90/365 selector.
- [x] Italian and English catalogs, language selector and CI key/placeholder checks.
- [x] Products, treatments, measurements, photos, health album and growth diary.
- [x] GitHub add-on repository, assisted local → repository migration and backup/restore documentation.
- [x] Visible name changed to **Verdant**; internal slug, data paths and backup format preserved.
- [x] Desktop resizable sidebar and detail panel; phone care sheet scrolls vertically only; compact Complete button on desktop.
- [x] Validation errors now name the field and reason; the generic banner is hidden when there is no useful detail.
- [x] Growth diary activity keeps the previous care confirmation layout and adds camera/library photos; Pillow 13 and python-multipart 0.0.31 security updates applied.
- [x] Soft green page canvas; panels, cards and sheets stay white, matching the native section separation at phone and desktop widths.
- [x] Care engine mode in Settings shows the running add-on value explicitly, with both modes listed and the current one highlighted.
- [x] Care cards and history rows show the action icon in the bottom-right corner of the plant image, colour-coded by care kind.
- [x] At normal text size the Home greeting keeps “Buongiorno 🌿” on one line on phones; larger text can wrap. The weather/icon column sizes to its content and the compact phone weather shows the temperature only.
- [x] The phone care calendar keeps the month title, Today button, week/month switch and arrows; enlarged text allows horizontal scrolling in the Home weekly strip rather than squeezing day labels.
- [x] On phones the week arrows are replaced by a continuously swipeable day strip (14 days back, one year ahead); desktop keeps the seven-day grid and arrows.
- [x] Phone plant rows swipe left to reveal Delete and move the plant to the trash (30-day restore); the trash can be emptied on demand behind a confirmation.

## Care engine — requested steps complete

The three requested steps are released. The next work is field validation and the optional features below.

- [x] **1.1 — AI context**: the daily analysis now receives the location and a structured `careTiming` summary (observed gaps, intentional postponements with notes, late gaps without a postponement). The assistant receives the same context. Released in 0.11.14.
- [x] **1.2 — Adaptive learning**: the step is 1 day by default and 2 days with at least two honoured postponements (or two early postponements in the opposite direction); late gaps without a postponement stay at 1. The ±30% safety bound remains. Released in 0.11.15.
- [x] **1.3 — Grower experience**: beginner/intermediate/expert/professional profile in Settings; the learning step is capped at 1/2/3/4 days and the AI receives `experienceLevel`. Released in 0.11.16.

No automatic plan changes are introduced by these steps: proposals remain reviewable and the operational engine still only postpones watering.

## Step 8 — field validation complete

Field validation is complete for the home-use add-on. See the [closeout report](docs/STEP8.md#chiusura-dello-step-8) and the [GitHub milestone](https://github.com/kriptos1970/verdant-ha/milestone/1).

- [x] Responsive layout on a **physical iPhone with the Home Assistant Companion app**: confirmed by the maintainer in everyday use. [#1](https://github.com/kriptos1970/verdant-ha/issues/1)
- [x] **VoiceOver** on a physical iPhone in Home Assistant Companion: tested successfully by the maintainer.
- [x] **QR label scan**: a newly generated QR code opened the correct plant on a physical iPhone via the stable Home Assistant panel link. [#2](https://github.com/kriptos1970/verdant-ha/issues/2)
- [x] **Backup and restore rehearsal**: Verdant ZIP and Home Assistant partial backup (add-on plus `/share`) restored successfully in an isolated macOS VM, using synthetic plants, care history and photos. [#3](https://github.com/kriptos1970/verdant-ha/issues/3)
- [x] **Open-Meteo**: confirmed that the Today view shows the outdoor temperature for a real location. [#4](https://github.com/kriptos1970/verdant-ha/issues/4)
- [x] **Live Home Assistant sensors**: the maintainer confirmed that humidity, illuminance and soil moisture sensors work in Verdant. No temperature sensor was configured. [#4](https://github.com/kriptos1970/verdant-ha/issues/4)
- [x] **Large archive rehearsal**: tested up to 500,000 synthetic events through Home Assistant Ingress on an isolated Mac VM, not on production hardware or with a personal archive. This was a one-off stress test, not a requirement for the home-use add-on. [#5](https://github.com/kriptos1970/verdant-ha/issues/5)

- [x] **Pl@ntNet in the plant editor**: tested successfully by the maintainer.
- [x] **Gemini on live data**: tested successfully by the maintainer. OpenAI was not tested because no key is configured.
- [x] Results recorded in the [Italian](docs/STATUS.md#chiusura-dello-step-8) and [English](docs/en/STATUS.md#step-8-closeout) status docs. [#6](https://github.com/kriptos1970/verdant-ha/issues/6)

**Deferred:** A ZIP with `data.json` below the metadata limit can still be rejected because of internal base64 wrapping. Keep the [reproduction and measurements](docs/ARCHIVE_SCALE.md#home-assistant-os-rehearsal-mac-vm) for reference; no fix or repeat of the 500,000-event stress test is planned for now.

## On hold / non-goals

- Synchronization with the native Apple apps or the old Verdant server.
- Cloud accounts or mandatory external services; local SQLite and offline use remain requirements.
- Pump or actuator activation.
- Automatic deletion of care events or photos.
- External MariaDB: postponed by decision; SQLite remains the supported store.
- Provider credentials in the browser or in QR labels.

## How work is tracked

- **GitHub Issues** for concrete tasks and bug reports.
- **Milestones** per release when a set of issues belongs together.
- **`docs/STATUS.md`** for what has actually been verified, including limits.
- **`CHANGELOG.md`** for what shipped in each version.

This roadmap is intentionally short. If an item needs discussion, open an issue and link it here.
