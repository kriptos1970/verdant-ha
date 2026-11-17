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
- **Analytics**: native plant health index (20–100) in every plant view, read-only collection analytics for 30/90/365 days and a merged plant timeline. Charts use this data in the following phase.

## Verification

- **180 backend tests** pass.
- Frontend type-check and production build pass; CI runs both plus translation key/placeholder checks.
- 7.160 Care Engine recommendations, 4.096 adaptive plans, 162 native scheduling cases and 1.536 AI selection combinations were compared with the original Swift code.
- Real Home Assistant checks: Ingress in Safari, imported 18 plants, 7 products and 124 photos, care round, calendar, history, products and iOS layout at phone widths.
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
