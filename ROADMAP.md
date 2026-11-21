# Roadmap

Verdant HA is a self-hosted Home Assistant add-on for a houseplant collection. This file lists what is actually still open; released changes are in [plantcare_web/CHANGELOG.md](plantcare_web/CHANGELOG.md), and verification notes are in [docs/STATUS.md](docs/STATUS.md).

Current release: **0.11.25** (21 November 2026).

## Done recently

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
- [x] The Home greeting keeps “Buongiorno 🌿” on one line on phones; the weather/icon column sizes to its content and the compact phone weather shows the temperature only.
- [x] The phone care calendar keeps the month title, Today button, week/month switch and arrows, and its seven-day strip fits the width without horizontal scrolling.

## Care engine — requested steps complete

The three requested steps are released. The next work is field validation and the optional features below.

- [x] **1.1 — AI context**: the daily analysis now receives the location and a structured `careTiming` summary (observed gaps, intentional postponements with notes, late gaps without a postponement). The assistant receives the same context. Released in 0.11.14.
- [x] **1.2 — Adaptive learning**: the step is 1 day by default and 2 days with at least two honoured postponements (or two early postponements in the opposite direction); late gaps without a postponement stay at 1. The ±30% safety bound remains. Released in 0.11.15.
- [x] **1.3 — Grower experience**: beginner/intermediate/expert/professional profile in Settings; the learning step is capped at 1/2/3/4 days and the AI receives `experienceLevel`. Released in 0.11.16.

No automatic plan changes are introduced by these steps: proposals remain reviewable and the operational engine still only postpones watering.

## Field validation (deferred)

These are verification tasks, not missing features. They are tracked in the [Step 8 milestone](https://github.com/kriptos1970/verdant-ha/milestone/1).

- [ ] Responsive layout on a **physical iPhone with the Home Assistant Companion app** (bottom bar, safe-area insets). [#1](https://github.com/kriptos1970/verdant-ha/issues/1)
- [ ] **QR/NFC label scan** with a real phone and the stable Home Assistant panel link. [#2](https://github.com/kriptos1970/verdant-ha/issues/2)
- [ ] **Backup and restore rehearsal on an isolated Home Assistant instance**. [#3](https://github.com/kriptos1970/verdant-ha/issues/3)
- [ ] **Live Home Assistant sensors** and **Open-Meteo** with real entities and a real location. [#4](https://github.com/kriptos1970/verdant-ha/issues/4)
- [ ] **Much larger archive** than the synthetic benchmark (100 plants / 50,000 events). [#5](https://github.com/kriptos1970/verdant-ha/issues/5)
- [ ] **Real Pl@ntNet trial** inside the plant editor (consent and quota).
- [ ] **Real Gemini daily analysis/advice** on live data; OpenAI remains untested because no key is configured.
- [ ] Record the results in `docs/STATUS.md` and close the open step 8 items. [#6](https://github.com/kriptos1970/verdant-ha/issues/6)

## Next features

- [ ] **Phone camera light meter**: evaluate whether the browser can provide a trustworthy measurement before implementing it.
- [ ] **Notification bell “Active” / web push**, if requested; today only AI proposals create a persistent Home Assistant notification.
- [ ] **Backup/restore improvements**: an in-place restore of the app ZIP (today import runs on an empty archive) and clearer scheduling guidance for Home Assistant backups. Photos in `/share` must be included explicitly.
- [ ] **Frontend tests and accessibility**: add component/E2E coverage and a broader accessibility pass; backend tests are at 217, frontend checks are build and i18n only.
- [ ] **Housekeeping**: add an add-on icon/logo, remove the old `local_plantcare_web` add-on after final verification, and clean the migration snapshot when no longer needed.
- [ ] **Scale**: evaluate a relational/local index if real archives grow well beyond the JSON-document approach.

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
