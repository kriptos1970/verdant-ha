# Status and known limits

Current release: **1.0.2**, published on [GitHub Releases](https://github.com/kriptos1970/verdant-ha/releases). The add-on runs on a real Home Assistant installation with a personal archive.

## Implemented

- **Collection**: plants, rooms, products, photos, growth diary, annotated health album, collection pagination.
- **Care**: guided care round, weekly/monthly calendar, paginated history, treatments, deferrals and reminders.
- **Planning**: adaptive planner with seasonal rules and optional Open-Meteo. New plants start in manual mode; the operational Care Engine can postpone watering on fresh, reliable wet-soil readings (default active) and never advances care. See [CARE_ENGINE.md](CARE_ENGINE.md).
- **Sensors**: temperature, humidity, light, soil moisture and conductivity from Home Assistant entities mapped to a plant or room.
- **AI (optional)**: Gemini or OpenAI structured advice with preview and selective application; disabled by default, automatic application off.
- **Knowledge**: Pl@ntNet identification, iNaturalist catalog, Perenual and Open Plantbook profiles, nine illustrated care guides, guided symptom check.
- **Labels**: QR/NFC labels using the stable Home Assistant panel URL.
- **Data**: native archive import v1–v3, ZIP backup with SHA256 checksums, photo deduplication and EXIF stripping, configurable measurement retention.
- **Web UI**: responsive and aligned with the iOS app at phone widths; works inside Ingress. List images use cached 480 px thumbnails instead of originals.
- **Languages**: Italian and English message catalogs, language selector, English guides and diagnosis, server-side language preference for notifications and AI.
- **Analytics**: native plant health index (20–100) in every plant view, read-only collection analytics for 30/90/365 days and a merged plant timeline. The Analytics page renders the 30-day charts (phase 2), the Home page shows a compact collection health and care-rhythm summary without loading Recharts (phase 3), the plant card adds a twelve-month care activity chart (phase 4) and a merged care-and-measurement timeline (phase 5), and the Analytics page has a 30/90/365 selector that buckets the activity series by day, week or month (phase 6).

## Verification

- **225 backend tests** pass.
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
- Plant detail, collection, care, products, measurements and settings were compared with the native sources. The collection now has a **30-day trash with restore** (soft delete, expiry, automatic purge, permanent delete, backup excludes trashed plants); products now have a category filter on phone and desktop, a “Record use” dialog (plant, date, dose, notes → fertilizing or treatment by category) and purchase/expiry dates. Plant detail now has a **Move plant** action (room, exposure, date, note; the smart plan is recalculated from the saved climate with no weather call and a move event records the route), a **Safety** section that refreshes the Perenual profile with source, date and link, and the care insights show the species light-profile reliability. Settings now include a **default location** with Open-Meteo search, coordinates, save and remove; the smart planner proposes it automatically for plants without a plan. The care calendar now groups the selected day by kind, offers a **Postpone** action on each row (form pre-set to postponement) and groups history by day with health and clearable filters. The care engine can now run in **operational** mode from Settings: it only postpones watering when a fresh, reliable moisture reading says the substrate is still wet, never advances or records care. The measurements table now shows each reading’s source and reliability, merging native measurements (with their original provenance) and manual entries without duplicates. On phones the plant detail **⋯** button now opens a native-style menu with **Edit** and **Move plant** (translucent card, icons, closes on outside tap or Esc); the old care selector was removed from that menu. Every collection card now has a quick-action menu (record watering, edit, move to trash), matching the native context menu and swipe actions. Visual tokens now live in `frontend/src/tokens.css` (colours, phone type scale, spacing, radii, icons, tap targets; see `docs/VISUAL_TOKENS.md`). The plant editor now has **Pl@ntNet identification inside the form** with consent and automatic filling of name (when empty), species, family and category. The native iOS app was built and launched in the iPhone 17 Pro / iOS 26.5 simulator and compared at 430 px with the web: filled icons, coloured metric tiles, plant rows, large care cards, “Complete” buttons and the ⋯ menu now match. The simulator had 4 plants and no due care, so conditional sections were compared with the native screenshots supplied by the user. The plant editor now follows the native section order (Photo, Identity, Position, Physical profile, Pot and substrate, Plan mode, Additional activities, Other information) with control-first fields and captions below; the desktop plant card now uses the same native card stack (hero, two-column summary, collapsible sections) instead of tabs. The editor exposes all three native plan modes — **Manual / Verdant / AI** — and choosing Verdant calculates the plan on save from the default location and Open-Meteo weather (or reports a clear error and leaves the plant unchanged). The C section is complete; what remains are the field checks with physical devices, real sensors, an isolated restore and a very large archive. See `docs/SCREENS_COMPARISON.md`.
- No Home Assistant backup was created during development; no real care or plan was changed by the automated checks.

## Known limits

- **Physical iPhone / Companion app** validation is still pending: browser responsive checks do not emulate real safe-area insets.
- A full **restore on an isolated Home Assistant instance** has not been rehearsed yet.
- **Live sensors and Open-Meteo** are covered by simulated transports, not by a long-running real installation.
- **Large real archives** beyond the synthetic benchmark (100 plants / 50,000 events) still need validation.
- The **Care Engine** can only postpone watering, and only with a fresh, reliable moisture reading; it never advances or records care. In shadow mode it is advisory. The full behaviour is in [CARE_ENGINE.md](CARE_ENGINE.md).
- **AI automatic application** remains disabled by default. Gemini is configured and reachable; the real-data daily trial is deferred and will be repeated on request.
- **Desktop layout** realignment with the macOS app is postponed; the phone layout was the priority.
- **MariaDB** and any external database are postponed; SQLite remains the store.
- Some long backend texts already stored in archives (care notes, AI history notes) may remain in Italian. About 30 common error messages are translated; unusual ones fall back to generic English.
- Photos are never deleted automatically; **Archive and backup** now has a cleanup tool that lists unreferenced files, protects uploads younger than one hour and deletes only the confirmed files. Trashed plants keep their photos until purged.
- The frontend bundle is split into React, icons, QR and application chunks; the main chunk is below the default warning threshold.

## Release 1.0.2 (22 November 2026)

- **Diary photos**: thumbnails on the plant page open a modal with the original (`growthPhoto` in
  `main.tsx`), with a localised failure state (`detail.growthPhotoUnavailable`); they used to be
  links to a new tab that stayed blank on phones. The control is a `<button>` with an
  `aria-label`, and the thumbnail is `alt=""`.
- **Cached `Intl`**: a new `intl-cache.ts` module caches `DateTimeFormat`, `NumberFormat` and
  `PluralRules` for the i18n helpers, the calendar, the trend chart and the guides. Micro-measure:
  0.95 → 0.01 ms per calendar render (35 cells).
- **i18n checks**: `scripts/check_i18n.mjs` now verifies the 24 plural keys used in the code, so a
  missing form fails the check instead of reaching the screen. The guard was proven with a fake key
  that was removed straight after.
- Checks: 225 backend tests, 1,195 aligned keys, frontend build. The photo modal was not exercised
  in the demo preview (the sample archive has no growth photos): the visual check is on your real
  archive.

## Release 1.0.1 (22 November 2026)

- **Measured visual check** with `scripts/preview_ios.py` and headless Chrome at 320/360/375/390 px: no horizontal overflow on Home, Plant detail and Products, and the tab bar never covers content at the end of a scroll.
- **Touch**: visible tap highlight (`rgba(25,67,48,.12)`), `touch-action: manipulation` and a pressed `filter: brightness(.94)`; before this release the cascade had no `:active` rule at all.
- **Products**: the duplicated "Category" select is hidden through `main[data-page=products] .collection-toolbar`; the desktop filter is unchanged at 1440 px.
- **Detail**: `ios-plan-button` and `ios-more-trigger` reach 44 px, the "At a glance" grid is no longer clickable, `autoFocus` is off on phones, `color-scheme: light`, `overscroll-behavior: contain` on modals and the product overlay.
- **i18n**: health album, QR/NFC labels, botanical library, identification, species library, AI assistant and model catalog move to `t()`; dates, numbers and doses use `formatDate`/`formatNumber`/the active locale. The `dueLabel` helper in `api.ts` that always returned Italian is gone.
- Checks: 225 backend tests, 1,193 aligned i18n keys, frontend build, `verify_product_dose.mjs` against the Swift function on 40 cases, screenshots in Italian and English.

## Release 1.0.0 (22 November 2026)

- **First stable release.** The code is unchanged from 0.11.28: presentation and distribution changed.
- **Add-on store**: `icon.png` and `logo.png` taken from the native `AppIcon-1024.png`, `plantcare_web/README.md` as the store introduction, `translations/en.yaml` and `translations/it.yaml` for every option.
- **Panel**: `panel_admin: false` (visible to non-admin users), `stage: stable`.
- **README**: `my.home-assistant.io` badge to add the repository in one click, five real English screenshots (390×844 at 2x, 1440×900), FAQ and privacy sections; `README.it.md` mirrors it.
- **Releases**: bilingual notes generated by `scripts/release_notes.py`, with the repository install as the first step.
- **Language**: fixed the `calendar.daySummary.other` plural, translated the desktop detail captions and the plan name in the English UI (`detail.yourPlant`, `detail.editPlant`, `detail.closePlant`).
- **Images**: `.github/workflows/publish.yml` publishes `ghcr.io/kriptos1970/verdant-ha-{arch}:<version>` for aarch64 and amd64; the image is enabled in `config.yaml` after the first publication.
- Checks: 225 backend tests, 1024 i18n keys aligned, frontend build, green CI on the presentation commit.

## Release 0.11.28 (21 November 2026)

- **Trash on phones**: the command lived inside `.page-heading`, which the phone layout hides (`main:not([data-page=today]) .page-heading{display:none}`), so after a swipe delete there was no way to restore. A round `.ios-title-action` button now sits next to `.ios-page-title` on the Plants page (`main.tsx`, `ios-layout.css`) and is shown only below 760 px.
- Desktop is unchanged: the command stays in `.collection-heading-actions`, next to the leaf icon.
- Checked at 320 and 375 px (44 × 44 px, no horizontal overflow, the trash modal opens) and at 813 px (mobile button `display:none`, title row 0 px high).

## Release 0.11.27 (21 November 2026)

- **Plant list on phones**: swipe a row to the left, the red **Delete** button is revealed and the plant moves to the trash (new `SwipeRow` component in `plantcare_web/frontend/src/main.tsx`, styles in `ios-layout.css`). No confirmation: restoring within 30 days is the safety net and the “Plant moved to the trash” notice confirms the outcome.
- The gesture uses `touch-action: pan-y`, only starts for touch pointer types, opens one row at a time and closes on a tap on the row or elsewhere; desktop keeps the ⋯ menu with its confirmation.
- **Trash**: the new **Empty trash** button asks for confirmation through `trash.emptyConfirm` (one or many plants) and reports “Trash emptied”. The generic confirm dialog now uses `common.confirmTitle`, `common.cancel` and `common.delete` instead of hard-coded Italian text.
- Checked at 320/375 px: swipe, tap to close, delete, restore, empty with confirmation and cancel; at 1000 px the button stays `display:none` and the grid is unchanged.

## Release 0.11.26 (21 November 2026)

- **Care calendar on phones**: the week view no longer uses arrows; the day strip scrolls horizontally and continuously (380 days, from 14 days before today to one year ahead) with `scroll-snap-type: x proximity` and a hidden scrollbar (`plantcare_web/frontend/src/care-calendar.tsx`, `ios-layout.css`).
- The selected day is centred on open, on tap and with **Today** only when it is not already fully visible; a tap selects the day and refreshes the list below.
- Desktop is unchanged (seven-day grid with arrows); month view keeps the arrows on phones too. Checked at 320, 375, 390 and 800 px, including the live switch between both layouts without a reload.

## Release 0.11.25 (21 November 2026)

- **Care calendar on phones**: the rules `main[data-page=care] .calendar-panel .section-heading{display:none}` and `main[data-page=care] .calendar-navigation{display:none}` added in 0.11.19 hid the month, the **Today** button, the arrows and the week/month switch; they are replaced by a compact header (`plantcare_web/frontend/src/ios-layout.css`).
- Below 430 px the “Month view” text stays only as the icon `aria-label`; buttons keep a 38 px height.
- The week strip is a seven-column grid instead of a horizontal carousel: `scrollWidth == clientWidth` at 320, 375 and 390 px, and the selected day is always visible.
- Checked in the browser at 320, 375, 390 and 500 px: arrows move 16–22 → 23–29 November, month view shows 42 cells (26 October – 6 December), **Today** restores the current selection and month. Room chips stay hidden on phones.

## Release 0.11.24 (21 November 2026)

- **Growth diary**: a chosen or shot photo is downscaled to 2400 px and re-encoded as JPEG in the browser before the request, so about a third of the bytes cross the network and the thumbnail appears sooner, including through Ingress or from a remote connection.
- The compression keeps the EXIF orientation and also covers the health album, plant photo and product photo; the server decodes and re-encodes in a worker thread and asks libjpeg for a smaller decode of very large images.
- 225 backend tests, 1,014 i18n keys, frontend build.

## Release 0.11.23 (21 November 2026)

- Care cards and history rows show a small action icon in the bottom-right corner of the plant image: watering, feeding, rotation, health check, growth diary and the other care kinds, in the category colour.
- The icon is decorative for accessibility; the action remains written in the card. 224 backend tests, 1,014 i18n keys, frontend build.

## Release 0.11.22 (21 November 2026)

- **Home on phones**: “Buongiorno 🌿” stays on one line; the weather/icon column now sizes to its content instead of taking half the heading.
- The compact phone weather shows the temperature only, with the location kept in the accessible label; below 360 px the greeting uses 26 px.
- Checked locally at 390, 375, 360 and 320 px with no wrapping or overlap. The fix is ready for the repository update.

## Release 0.11.21 (20 November 2026)

- **Settings → Care engine**: the active mode now has a dot and the caption “Mode active in the add-on”; both modes are listed separately and the current one is highlighted.
- The description no longer reads like the current value when the other mode is active; after changing the option, restart the add-on and the web UI updates within a minute.
- 224 backend tests, 1,014 i18n keys, frontend build.

## Release 0.11.20 (20 November 2026)

- The page canvas uses a soft green tint (`--vc-canvas`); panels, cards and sheets stay white, so sections separate as in the native app.
- On phones the detail header follows the page canvas while care cards stay white.
- Content, flows and data are unchanged. 224 backend tests, 1,013 i18n keys, frontend build.

## Release 0.11.19 (20 November 2026)

- The **Growth diary** activity keeps the previous confirmation layout (date, postponement, health, notes) and adds **Take a photo** / **Choose photos**.
- Photos are saved in the growth entry; the “Update progress” event stays in the history. Corrects the route introduced in 0.11.18.
- 224 backend tests, 1,013 i18n keys, frontend build.

## Release 0.11.18 (20 November 2026)

- **Growth diary activity** now opens the diary editor with **Take a photo** and **Choose photos**; photos are saved in the growth entry and the activity is recorded.
- **Pillow 13.0.0** and **python-multipart 0.0.31** security updates; `pip-audit` and `npm audit` report no known vulnerabilities.
- 223 backend tests, 1,013 i18n keys, frontend build.

## Release 0.11.17 (20 November 2026)

- The generic “Check the data and try again.” banner is no longer shown for errors without detail or while a modal form is open; validation messages name the field and reason and remain inline in the form.
- Added `maxLength` limits to long text fields to avoid avoidable validation errors.
- 223 backend tests, frontend build.

## Release 0.11.16 (20 November 2026)

- Care engine step 1.3: **beginner / intermediate / expert / professional** grower profile in Settings, with maximum step 1/2/3/4 days.
- Learning uses the number of honoured or early postponements, up to the profile maximum; late gaps without a postponement and insufficient data stay at 1 day.
- Daily AI and assistant receive `experienceLevel`; `contextVersion` 4.
- 222 backend tests, 1,012 i18n keys, frontend build.

## Release 0.11.15 (20 November 2026)

- Care engine step 1.2: adaptive learning from postponements. The step is 1 day by default and rises to 2 days with at least two honoured postponements (or two early postponements in the opposite direction).
- Late gaps without a postponement do not accelerate learning; the ±30% bound and target remain.
- `careLearning` exposes the step and the postponement/delay counts used.
- 220 backend tests, frontend build.

## Release 0.11.14 (20 November 2026)

- Care engine step 1.1: the daily AI analysis receives the **location** and `careTiming` (observed gaps, postponements with notes, late gaps without a postponement); the prompt separates intentional postponements from delays.
- The plant-card assistant receives location and recent postponements too; `contextVersion` updated to 3.
- 217 backend tests, frontend build.

## Release 0.11.13 (20 November 2026)

- Desktop care cards: the **Complete** button is 200 px wide (at most 100% of the card) and 44 px high, no longer full width.
- On phones it remains full width.
- 215 backend tests, frontend build.

## Release 0.11.12 (20 November 2026)

- The phone **Complete** sheet scrolls vertically only: horizontal overflow hidden, horizontal overscroll disabled and `touch-action: pan-y pinch-zoom`.
- Long plant names, guide steps and reasons wrap; fields and buttons stay within the panel width.
- Verified at 320/390 px with a very long plant name, with no horizontal overflow.
- 215 backend tests, frontend build.

## Release 0.11.11 (20 November 2026)

- The detail-panel handle is now available in the empty state too, not only with an open plant, so the right column can be resized immediately.
- Handle z-index raised to avoid overlap with the detail content.
- 215 backend tests, frontend build.

## Release 0.11.10 (20 November 2026)

- Desktop: the **left sidebar** and the **detail panel** are resizable by dragging their edge, with persistent width and double-click reset.
- Keyboard arrows, limits 190–420 px (sidebar) and 320–720 px (detail), at least 420 px for the content.
- Handles are available above 1000 px only; phone/tablet layout is unchanged.
- 215 backend tests, frontend build.

## Release 0.11.9 (19 November 2026)

- Visible add-on and web app name changed to **Verdant**: add-on name, sidebar panel, brand, page title, notifications and messages.
- The `plantcare_web` slug, `/data`, database, photos, backup format and internal identifiers are unchanged, preserving data and updates.
- 215 backend tests, frontend build.

## Release 0.11.8 (19 November 2026)

- AI answers are rendered as Markdown in the green box: headings, paragraphs, bold/italic, lists, quotes, code and tables.
- The renderer is loaded on demand in a separate chunk and does not interpret raw HTML.
- Gemini and OpenAI use the same `summaryMarkdown` field and the same rendering.
- 215 backend tests, frontend build.

## Release 0.11.7 (19 November 2026)

- QR/NFC labels use the current add-on slug (local or repository); already printed labels remain readable.
- Real repository add-on migration completed: `309d34f7_plantcare_web` 0.11.7 with the archive and options copied, 124 photos; the old `local_plantcare_web` stays stopped for rollback.
- Care engine documentation in all three modes: [CARE_ENGINE.md](CARE_ENGINE.md) and [Italian version](../CARE_ENGINE.md).
- 215 backend tests.

## Release 0.11.6 (19 November 2026)

- Assisted local → repository add-on migration: imports the database from `/share/plantcare/migrate/plantcare.sqlite` when `/data` is empty and `import-request` exists.
- SQLite header validation, atomic replacement, request consumed once; the snapshot stays in place for rollback.
- 215 backend tests.

## Release 0.11.5 (19 November 2026)

- The plant editor now associates fertilizer through a **visual list** with thumbnail, name, brand, category and form, plus “No fertilizer”.
- The free-text “Fertilizer type” field is gone; the type is derived from the selected product on the backend too.
- Only fertilizer products (Fertilizzante, Biostimolante, Ammendante, Radicante) plus the already linked product are listed; the dose appears only with a product.
- Verified: 213 backend tests, 1,001 i18n keys, frontend build, no overflow at 320/390 px.

## Release 0.11.4 (19 November 2026)

- The care engine now has a **single source of truth**: the `care_engine_mode` add-on option, defaulting to **Operational**. The web override that could diverge from the configuration is gone.
- **Settings → Care engine** shows the effective mode, explains shadow and operational, and says where to change it; there is no selector that can diverge.
- Verified: 212 backend tests, 1,000 i18n keys, frontend build.

## Release 0.11.3 (19 November 2026)

- **Web-first plant editor** with progressive disclosure: photo and Pl@ntNet recognition, identity, room, care plan, watering and last watering always visible.
- Five collapsible optional sections with a summary line (Position and profile, Pot and substrate, Schedule and feeding, Additional activities, Other information).
- A single sticky Cancel/Save bar at the bottom, safe area included; the duplicate top bar is gone.
- Two-column grids for short fields, one column below 360 px. Content at 390 px drops from about 4,038 px to about 1,392 px (2,975 px with every section open).
- Validation: required fields stay visible; an invalid control inside a closed section opens it and receives focus.
- Soft green panels (`--vc-mint-soft` / `--vc-mint-line`) for growth, care history, merged timeline, trend, editor sections and Pl@ntNet recognition.
- Verified: 320/390/430 px without overflow, 212 backend tests, 999 i18n keys, frontend build.

## Release 0.11.2 (19 November 2026)

- Functional and structural parity with Verdant across collection, products, plant detail, settings, care, measurements and growth diary.
- Visual tokens in `frontend/src/tokens.css`; filled icons, proportionate phone type, Home/Care/History realigned.
- Pl@ntNet recognition inside the plant editor: the button turns green after the photo, waits for the result and fills the fields without confirmation prompts.
- Operational care engine and unreferenced photo cleanup.
- 212 backend tests, 988 i18n keys, frontend build.

## Next release (0.11.20)

- Phone camera light meter, “Active” notification bell/web notifications if requested, in-place backup restore.
- Deferred field checks: physical iPhone/Companion, real QR/NFC, real Pl@ntNet, real Gemini, isolated HA restore, real sensors/weather, very large archive.

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
