# Roadmap

Verdant HA is developed incrementally. This file gives the high-level direction; detailed verification notes and known limits live in [docs/STATUS.md](docs/STATUS.md) (currently in Italian), and released changes are listed in [plantcare_web/CHANGELOG.md](plantcare_web/CHANGELOG.md).

Current release: **0.10.3**. The project is usable on a real Home Assistant installation, but a few verification and parity items remain open.

## Now — close the consolidation step

These are verification and hardening tasks, not new features:

- [ ] Test the responsive layout on a **physical iPhone with the Home Assistant Companion app** (bottom bar, safe-area insets, not just Safari responsive mode).
- [ ] Scan a **QR/NFC label with a real phone** and verify the stable Home Assistant panel link.
- [ ] Perform a **backup and restore rehearsal on an isolated Home Assistant instance**.
- [ ] Verify **live Home Assistant sensors** and **Open-Meteo** with real entities and a real location.
- [ ] Validate a **much larger archive** than the synthetic benchmark (100 plants / 50,000 events).
- [ ] Record the results in `docs/STATUS.md` and close the open items of step 8.

## Next — iOS parity and internationalization

- [ ] Port the native **timeline chart and health index** calculation. Do not introduce estimated or invented health values.
- [ ] Compare the complete **growth entry and health album** flows with the native app, including photos.
- [ ] Evaluate a **camera-based lux meter** and decide whether the browser can provide a trustworthy measurement.
- [ ] **App localization (IT/EN)**: extract UI strings into message catalogs, add a `t()` helper and locale detection, localize dates/numbers with `Intl`.
- [ ] Introduce **canonical domain values** (`water`, `fertilize`, `good`, `excellent`, …) and keep Italian labels only for display; this is required before a real translation of events, guides and backend messages.
- [ ] Translate the **documentation** into English (`docs/en/`), starting from installation and status.
- [ ] Realign the **desktop layout** with the native macOS app, after the iOS work is closed.

## Later — activation and scale

- [ ] Move the **Care Engine** from shadow mode to operational recommendations, with explicit user opt-in and evidence from real measurements.
- [ ] Validate **OpenAI** and the **daily AI analysis** on real data; keep automatic application off by default.
- [ ] Add **pagination to the plant collection**.
- [ ] Add a **maintenance tool for unreferenced photo files** (no automatic deletion).
- [ ] Add a **relational index or local normalization** if archives grow beyond the current JSON-document approach.
- [ ] Automate **releases** (tag → source package → SHA256 → GitHub Release).
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
