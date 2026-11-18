# Status and known limits

Current release: **0.11.1**, published on [GitHub Releases](https://github.com/kriptos1970/verdant-ha/releases). The add-on runs on a real Home Assistant installation with a personal archive.

## Implemented

- **Collection**: plants, rooms, products, photos, growth diary, annotated health album, collection pagination.
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
- The plant collection is now paginated at 12 plants per page with a filter-aware reset; 390 and 1280 px layouts, the Italian/English labels and the 12 + 2 split on a 14-plant synthetic archive were checked.
- On phones, the plant plan button now opens the smart plan configuration for manual plants too, so the Open-Meteo weather option is reachable; the separate pencil still edits manual intervals.
- The plant editor now covers the native fields: real placement, growing method, height, care rhythm with interval rescaling, last fertilizing, fertilizer type and dose, activity switches with defaults, new-plant defaults, and a “Pot and substrate” section (drainage quality, pot height and volume, cachepot, saucer, substrate name and properties). Values persist in `setup.container` and `setup.substrate`; the plant card shows the height when present. In-form Pl@ntNet identification remains the only missing editor field (the web keeps a separate tool).
- The native plant editor was compared field by field with the web form: 38 items, 17 present, 4 partial and 17 missing (placement, planting method, pot height/volume, drainage quality, cachepot, saucer, substrate and properties, care rhythm, last fertilizing, fertilizer type/dose, in-form identification). Most missing values already exist in the imported archive, so the gap is mainly UI; see `docs/PLANT_EDITOR_COMPARISON.md`.
- The Home page no longer repeats a six-plant preview of the collection, matching the native dashboard which has no plant list; indicators now read Plants / Due care / Rooms, a weather chip comes from the latest adaptive plan, and a metrics row shows 30-day care, active days, regularity and plants to watch. The comparison with `DashboardView.swift` is in `docs/HOME_COMPARISON.md`.
- Plant detail, collection, care, products, measurements and settings were compared with the native sources. The collection now has a **30-day trash with restore** (soft delete, expiry, automatic purge, permanent delete, backup excludes trashed plants); products now have a category filter on phone and desktop, a “Record use” dialog (plant, date, dose, notes → fertilizing or treatment by category) and purchase/expiry dates. Plant detail now has a **Move plant** action (room, exposure, date, note; the smart plan is recalculated from the saved climate with no weather call and a move event records the route), a **Safety** section that refreshes the Perenual profile with source, date and link, and the care insights show the species light-profile reliability. Settings now include a **default location** with Open-Meteo search, coordinates, save and remove; the smart planner proposes it automatically for plants without a plan. The care calendar now groups the selected day by kind, offers a **Postpone** action on each row (form pre-set to postponement) and groups history by day with health and clearable filters. The care engine can now run in **operational** mode from Settings: it only postpones watering when a fresh, reliable moisture reading says the substrate is still wet, never advances or records care. The measurements table now shows each reading’s source and reliability, merging native measurements (with their original provenance) and manual entries without duplicates. On phones the plant detail **⋯** button now opens a native-style menu with **Edit** and **Move plant** (translucent card, icons, closes on outside tap or Esc); the old care selector was removed from that menu. Every collection card now has a quick-action menu (record watering, edit, move to trash), matching the native context menu and swipe actions. The plant editor now follows the native section order (Photo, Identity, Position, Physical profile, Pot and substrate, Plan mode, Additional activities, Other information) with control-first fields and captions below; the desktop plant card now uses the same native card stack (hero, two-column summary, collapsible sections) instead of tabs. The editor exposes all three native plan modes — **Manual / Verdant / AI** — and choosing Verdant calculates the plan on save from the default location and Open-Meteo weather (or reports a clear error and leaves the plant unchanged). The C section is complete; what remains are the field checks with physical devices, real sensors, an isolated restore and a very large archive. See `docs/SCREENS_COMPARISON.md`.
- No Home Assistant backup was created during development; no real care or plan was changed by the automated checks.

## Known limits

- **Physical iPhone / Companion app** validation is still pending: browser responsive checks do not emulate real safe-area insets.
- A full **restore on an isolated Home Assistant instance** has not been rehearsed yet.
- **Live sensors and Open-Meteo** are covered by simulated transports, not by a long-running real installation.
- **Large real archives** beyond the synthetic benchmark (100 plants / 50,000 events) still need validation.
- The **Care Engine** is intentionally in shadow mode; measurements do not rewrite the schedule.
- **AI automatic application** remains disabled by default. The daily analysis runs with the configured provider; a manual real-data trial on Home Assistant was rejected by Gemini with `User location is not supported` (raw 400). The public IP is Italian (Telecom Italia, AS3269), no proxy/VPN is in use, IPv6 is unavailable and Cloudflare only fronts inbound `sicoli.ovh`; Google is misclassifying the public IP, as confirmed by the temporary fix after a router restart. An OpenAI key, a new/static IP or Google’s IP report is needed to complete the trial.
- **Desktop layout** realignment with the macOS app is postponed; the phone layout was the priority.
- **MariaDB** and any external database are postponed; SQLite remains the store.
- Some long backend texts already stored in archives (care notes, AI history notes) may remain in Italian. About 30 common error messages are translated; unusual ones fall back to generic English.
- Photos are never deleted automatically; **Archive and backup** now has a cleanup tool that lists unreferenced files, protects uploads younger than one hour and deletes only the confirmed files. Trashed plants keep their photos until purged.
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

## Field checks — status on 17 November 2026

- **#5 large archive (partial)** — the synthetic benchmark now also runs at **400 plants / 200,000 events** (four times the previous size): full response 49.5 MB in 2.05 s, compact collection 561 kB in 1.05 s (−98.87%), history page 18.5 kB in 0.68 s on the development Mac. Run with `scripts/benchmark_archive.py --plants 400 --events 500` (events per plant). It does not replace a real, much larger archive.
- **#4 sensors and weather (blocked on configuration)** — the add-on `exposed_entities` option is empty, `/api/sensors` returns 0 readings and no mappings exist. Home Assistant exposes 90 supported entities, including `sensor.dracena_moisture` (36%), `sensor.dracena_illuminance` (6 lx) and `sensor.dracena_conductivity` (74 µS/cm). All 18 adaptive plans have weather disabled (last plan computed on 20 September 2026).
- **#2 QR/NFC (link verified)** — the Ficus Elastica label carries the stable URL `https://sicoli.ovh/app/local_plantcare_web/plant/170F12A0-7D2E-489E-AF4A-116A108D6985` with no ingress token; without a session the page asks for Home Assistant access. The physical scan is still pending.
- **#1 physical iPhone** and **#3 isolated restore** need the device and a separate instance; the procedures are ready and their outcome is to be recorded.
