# Architecture and reference matrix

This page summarizes the technical reference. The full Italian notes, including the functional matrix against the original Swift code, are in [`docs/REFERENCE.md`](../REFERENCE.md).

## Stack

- Backend: Python 3.13, FastAPI, Pydantic, SQLite.
- Frontend: React 19, TypeScript, Vite.
- Packaging: Home Assistant add-on built from a local Dockerfile; `aarch64` and `amd64`.
- Data: SQLite documents plus filesystem photos; no external database.

## Source of truth

The original Swift project (`PlantCare2.0`, adjacent folder) is the functional reference, not the historical README. The web implementation ports scheduling, learning, adaptive planning, Care Engine, AI rules and backup envelopes, and compares results by executing the original Swift code in verification scripts.

## Main areas

| Area | Reference | Web destination |
|---|---|---|
| Navigation | `ContentView.swift` | Desktop columns; mobile Today/Plants/Care/Products/More |
| Theme | `Theme.swift` | Forest, moss, mint and cream palette |
| Archive and care | `Models.swift`, `PlantStore.swift` | Central SQLite; tombstones for correct projections |
| Scheduling | `PlantCareStateReducer`, `PlantCareScheduleProjector` | Local dates, fertilizer alignment, authoritative postponements |
| Learning | `CarePlanLearner.swift` | At least 3 care events, last 7, median, ±1 day, ±30% baseline |
| AI | `LocalPlantAIService.swift` | Gemini/OpenAI, stable baseline, water limits ±25%, stale proposals rejected |
| Backup | `MacCollectionTools.swift` | Envelope v1–v3, SHA256, base64 payloads and photos |
| Sensors | `HomeAssistantSensors.swift` | Allowed classes, plant/room mapping, freshness and units |
| Advanced engine | `CareEngine/*` | Separate port, kept in shadow mode until equivalence |
| Photos | Growth and knowledge views, iOS care tools | Diary, health album, upload, QR |

## Design decisions

- Separate add-on; no synchronization with the native apps or the old server.
- Atomic import only on an empty archive; the original backup remains the user's responsibility.
- New plants start in manual mode until the adaptive planner is explicitly applied.
- AI disabled without credentials; automatic application disabled by default.
- No pump or actuator activation. The Supervisor token never reaches the browser.
- Native screenshots and verification on real Home Assistant/hardware are required before calling a release stable.
- An endpoint does not prove parity with the native app; limits stay documented.

## Canonical care values

Storage and the engine use stable English codes (`water`, `fertilize`, `repot`, `inspect`, `good`, `excellent`, …). The API and backups keep the native Italian values for compatibility with imported archives and the current frontend. Conversion lives in `backend/care_kinds.py`; the web backup remains importable by older releases.

## Verification scripts

- `scripts/verify_native.py`: scheduling, learning and projections against Swift.
- `scripts/verify_adaptive.py`: 4.096 adaptive plans against Swift.
- `scripts/verify_care_engine.py`: Care Engine decisions and dry-down against Swift.
- `scripts/verify_ai.py`: selective AI application combinations against Swift.
- `scripts/verify_health_guides.py`: diagnosis and seasonal guide values against Swift.
- `scripts/verify_ios_summary.mjs` and `scripts/verify_product_dose.mjs`: frontend summary and dosage rules.
- `scripts/check_lock.py` and `scripts/check_i18n.mjs`: dependency lock and translation catalogs.

These scripts read the adjacent Swift project and never modify it. Some require Swift and the native sources; the UI checks need Node and installed frontend dependencies.
