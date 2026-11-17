# Roadmap

Verdant HA is developed incrementally. This file gives the high-level direction; detailed verification notes and known limits live in [docs/STATUS.md](docs/STATUS.md) (currently in Italian), and released changes are listed in [plantcare_web/CHANGELOG.md](plantcare_web/CHANGELOG.md).

Current release: **0.11.1**. The project is usable on a real Home Assistant installation, but a few verification and parity items remain open.

## Done recently

- [x] English landing README with an Italian documentation entry point.
- [x] CI on every push and pull request; protected `main` (no force pushes or deletions).
- [x] Tag-driven releases with tests, source package and SHA256 checksum.
- [x] Contributor guide, security policy and issue/PR templates.
- [x] Canonical care kinds and health values in the backend, with the legacy Italian API contract preserved.
- [x] Italian/English message catalogs, language selector, `Intl` formatting and CI key/placeholder parity; navigation, tools and settings migrated.
- [x] Care round, calendar and history localized, including due labels and plural forms.
- [x] Care forms, plant detail header, products, product editor and treatments localized; API errors expose stable codes.
- [x] Home, plant list and server-side language preference localized; AI and notifications follow the selected language.
- [x] iOS detail, nine care guides, practical guide, diagnosis, care insights and adaptive plan localized.
- [x] English documentation, specific common error messages and frontend code-splitting.
- [x] Plant taxonomies, plant editor, add-on metadata and generated plan explanations localized.

## Now — close the consolidation step

These are verification and hardening tasks, not new features. They are tracked in the [Step 8 milestone](https://github.com/kriptos1970/verdant-ha/milestone/1).

- [ ] Test the responsive layout on a **physical iPhone with the Home Assistant Companion app** (bottom bar, safe-area insets, not just Safari responsive mode). [#1](https://github.com/kriptos1970/verdant-ha/issues/1)
- [ ] Scan a **QR/NFC label with a real phone** and verify the stable Home Assistant panel link. [#2](https://github.com/kriptos1970/verdant-ha/issues/2)
- [ ] Perform a **backup and restore rehearsal on an isolated Home Assistant instance**. [#3](https://github.com/kriptos1970/verdant-ha/issues/3)
- [ ] Verify **live Home Assistant sensors** and **Open-Meteo** with real entities and a real location. [#4](https://github.com/kriptos1970/verdant-ha/issues/4)
- [ ] Validate a **much larger archive** than the synthetic benchmark (100 plants / 50,000 events). [#5](https://github.com/kriptos1970/verdant-ha/issues/5)
- [ ] Record the results in `docs/STATUS.md` and close the open items of step 8. [#6](https://github.com/kriptos1970/verdant-ha/issues/6)

## Next — iOS parity and internationalization

- [ ] Port the native **timeline chart and health index** calculation. Do not introduce estimated or invented health values.
- [ ] Compare the complete **growth entry and health album** flows with the native app, including photos.
- [ ] Evaluate a **camera-based lux meter** and decide whether the browser can provide a trustworthy measurement.
- [ ] **App localization (IT/EN)**: the catalogs and language selector are in place; migrate care flows, products and guides next. See [docs/I18N.md](docs/I18N.md).
- [ ] Keep Italian labels only for display once the frontend catalogs exist; the backend now uses canonical values.
- [ ] Translate the **documentation** into English (`docs/en/`), starting from installation and status.
- [ ] Realign the **desktop layout** with the native macOS app, after the iOS work is closed.

## Later — activation and scale

- [ ] Move the **Care Engine** from shadow mode to operational recommendations, with explicit user opt-in and evidence from real measurements.
- [ ] Validate **OpenAI** and the **daily AI analysis** on real data; keep automatic application off by default.
- [ ] Add **pagination to the plant collection**.
- [ ] Add a **maintenance tool for unreferenced photo files** (no automatic deletion).
- [ ] Add a **relational index or local normalization** if archives grow beyond the current JSON-document approach.
- [ ] Expand accessibility and automated browser checks.

## On hold / non-goals

- Synchronization with the native Apple apps or the old Verdant server.
- Cloud accounts or mandatory external services; the app must keep working offline with local SQLite.
- Pump or actuator activation.
- Automatic deletion of care events or photos.
- External MariaDB: postponed by decision, SQLite remains the supported store.
- Storing provider credentials in the browser or in the QR label.

## How work is tracked

- **GitHub Issues** for concrete tasks and bug reports.
- **Milestones** per release when a set of issues belongs together.
- **`docs/STATUS.md`** for what has actually been verified, including limits.
- **`CHANGELOG.md`** for what shipped in each version.

This roadmap is intentionally short. If an item needs discussion, open an issue and link it here.
