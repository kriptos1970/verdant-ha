# Status and known limits

Current release: **0.11.1**, published on [GitHub Releases](https://github.com/kriptos1970/verdant-ha/releases). The add-on runs on a real Home Assistant installation with a personal archive.

## Implemented

- **Collection**: plants, rooms, products, photos, growth diary, annotated health album.
- **Care**: guided care round, weekly/monthly calendar, paginated history, treatments, deferrals and reminders.
- **Planning**: adaptive planner with seasonal rules and optional Open-Meteo. New plants start in manual mode; the advanced Care Engine runs in shadow mode and never rewrites the calendar by itself.
- **Sensors**: temperature, humidity, light, soil moisture and conductivity from Home Assistant entities mapped to a plant or room.
- **AI (optional)**: Gemini or OpenAI structured advice with preview and selective application; disabled by default, automatic application off.
- **Knowledge**: Pl@ntNet identification, iNaturalist catalog, Perenual and Open Plantbook profiles, nine illustrated care guides, guided symptom check.
- **Labels**: QR/NFC labels using the stable Home Assistant panel URL.
- **Data**: native archive import v1–v3, ZIP backup with SHA256 checksums, photo deduplication and EXIF stripping, configurable measurement retention.
- **Web UI**: responsive and aligned with the iOS app at phone widths; works inside Ingress. List images use cached 480 px thumbnails instead of originals.
- **Languages**: Italian and English message catalogs, language selector, English guides and diagnosis, server-side language preference for notifications and AI.
- **Analytics**: native plant health index (20–100) in every plant view, read-only collection analytics for 30/90/365 days and a merged plant timeline. The Analytics page renders the 30-day charts (phase 2), the Home page shows a compact collection health and care-rhythm summary without loading Recharts (phase 3), the plant card adds a twelve-month care activity chart (phase 4) and a merged care-and-measurement timeline (phase 5), and the Analytics page has a 30/90/365 selector that buckets the activity series by day, week or month (phase 6).

## Verification

- **180 backend tests** pass.
- Frontend type-check and production build pass; CI runs both plus translation key/placeholder checks.
- 7.160 Care Engine recommendations, 4.096 adaptive plans, 162 native scheduling cases and 1.536 AI selection combinations were compared with the original Swift code.
- Real Home Assistant checks: Ingress in Safari, imported 18 plants, 7 products and 124 photos, care round, calendar, history, products and iOS layout at phone widths.
- Analytics were checked read-only on the real archive (18 plants, 732 events): 103 events and 71% regularity for 30 days, 495/83% for 90 days, 677/85% for 365 days. Water and feeding due dates matched 0.11.1 for every plant.
- Phase 2 charts were checked on a synthetic 6-plant/28-care archive at 320, 390, 430 and 1280 px with no horizontal overflow. The `charts-*.js` chunk (about 130 kB gzip) is not requested on the plant list and only loads when the Analytics panel approaches the viewport. Reduced-motion and table alternatives are wired into the shared chart shell.
- Phase 3 was checked on the same synthetic archive: Home shows 60% collection health, 22 care entries over 12 active days and two plants needing a health check. The analytics request is deferred until the block nears the viewport, `charts-*.js` stays off the Home page, and empty, error/retry and English states were exercised. Lighthouse accessibility is 0.96 with only the pre-existing contrast and calendar-label findings.
- Phase 4 adds a twelve-month care chart to the plant card, built from the history already loaded: 320, 390 and 1280 px were checked with no horizontal overflow, including the accessible data table and the empty state in both languages. No chart chunk is loaded on the plant card.
- Phase 6 adds the 30/90/365 selector: the API now returns the whole period day by day and the chart folds it into days, weeks or months. Switching refetches `days=30`, `days=90` or `days=365` while keeping the previous data visible, and the 320/390/1280 px layouts and English labels were checked. Lighthouse accessibility is 0.96 with only the pre-existing footer contrast finding.
- Phase 5 adds a merged care-and-measurement timeline to the plant diary, fed by `/api/plants/{id}/timeline`: 320/390/1280 px were checked with no horizontal overflow, and loading, empty, error/retry and English states were exercised. The plant card still loads no chart chunk.
- The add-on was rebuilt from these sources on the real Home Assistant installation on 17 November 2026, keeping version 0.11.1: 99 files verified by SHA256, Ingress checks confirmed 18 plants at 100% health, 495 care events and 83% regularity over 90 days, and a 12-entry plant timeline. No real care was recorded, no archive data changed and no backup was created.
- No Home Assistant backup was created during development; no real care or plan was changed by the automated checks.

## Known limits

- **Physical iPhone / Companion app** validation is still pending: browser responsive checks do not emulate real safe-area insets.
- A full **restore on an isolated Home Assistant instance** has not been rehearsed yet.
- **Live sensors and Open-Meteo** are covered by simulated transports, not by a long-running real installation.
- **Large real archives** beyond the synthetic benchmark (100 plants / 50,000 events) still need validation.
- The **Care Engine** is intentionally in shadow mode; measurements do not rewrite the schedule.
- **AI automatic application** and the daily analysis remain disabled by default and need a real-data trial.
- **Desktop layout** realignment with the macOS app is postponed; the phone layout was the priority.
- **MariaDB** and any external database are postponed; SQLite remains the store.
- Some long backend texts already stored in archives (care notes, AI history notes) may remain in Italian. About 30 common error messages are translated; unusual ones fall back to generic English.
- Photos are never deleted automatically; a maintenance tool for unreferenced files is not available yet.
- The frontend bundle is split into React, icons, QR and application chunks; the main chunk is below the default warning threshold.

## Remaining roadmap

- Physical iPhone and Companion app verification.
- Real QR/NFC scan on a phone.
- Backup/restore rehearsal on an isolated instance.
- Live sensors and weather verification.
- Larger archive benchmark.
- Optional Care Engine activation and AI real-data trial.
- Desktop layout realignment.
- English documentation expansion and editorial review of long translations.
