# Verdant HA

**English** | [Italiano](README.it.md)

[![CI](https://github.com/kriptos1970/verdant-ha/actions/workflows/ci.yml/badge.svg)](https://github.com/kriptos1970/verdant-ha/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/kriptos1970/verdant-ha?label=release)](https://github.com/kriptos1970/verdant-ha/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Verdant HA** (internally *PlantCare Web*) is a self-hosted **Home Assistant add-on** for looking after a houseplant collection: care scheduling, guided care rounds, history, treatments, sensors and optional AI advice.

Everything runs on your own Home Assistant instance, with SQLite and photos stored locally. There is no cloud account and no synchronization with the native Apple apps.

<p align="center">
  <img src="docs/screenshots/0.10.2/home-assistant-avocado-mobile.jpg" alt="Plant detail on mobile" width="300">
</p>

## Highlights

- **Collection**: plants, rooms, products, photos, growth diary and annotated health album.
- **Care**: guided care rounds by room, weekly and monthly calendar, paginated history, treatment cycles, deferrals and reminders.
- **Scheduling**: adaptive planner with seasonal rules and optional Open-Meteo weather. New plants start in manual mode; the advanced Care Engine runs in shadow mode and never rewrites the calendar on its own.
- **Sensors**: temperature, humidity, light, soil moisture and conductivity from Home Assistant entities, mapped to a plant or a room.
- **AI advice (optional)**: Gemini or OpenAI with structured output, explicit preview and selective application. Disabled by default; automatic application is off.
- **Knowledge**: Pl@ntNet plant identification, iNaturalist species catalog, Perenual and Open Plantbook profiles, nine care guides and a guided symptom check.
- **Labels**: QR/NFC labels that open the plant through the stable Home Assistant panel URL.
- **Data**: native archive import (envelope v1–v3), ZIP backup with SHA256 checksums, photo deduplication and EXIF stripping, configurable measurement retention.
- **Web UI**: responsive, aligned with the iOS app at phone widths; works inside Home Assistant Ingress without exposing ports.

## Stack

- Backend: Python 3.13, FastAPI, Pydantic, SQLite.
- Frontend: React 19, TypeScript, Vite.
- Packaging: Home Assistant add-on built from a local Dockerfile (aarch64 and amd64).
- Tests: 149 pytest tests; frontend type-check and build in CI.

## Status

Current version: **0.10.3**, published on [GitHub Releases](https://github.com/kriptos1970/verdant-ha/releases). The project is usable and runs on a real Home Assistant installation with a personal archive, but it is still under active development. The interface now has Italian and English message catalogs with a language selector; the core shell is translated and the remaining screens are being migrated.

Known limits and the remaining roadmap are tracked in the Italian documentation, starting from [docs/STATUS.md](docs/STATUS.md) and [docs/IOS_LAYOUT.md](docs/IOS_LAYOUT.md). The high-level plan is in [ROADMAP.md](ROADMAP.md).

## Installation

1. Download the latest `plantcare-web-<version>.zip` from [Releases](https://github.com/kriptos1970/verdant-ha/releases) and extract it.
2. Copy the `plantcare_web` folder to `/addons/plantcare_web` on your Home Assistant host.
3. Refresh the local add-ons in the Home Assistant App store, install **PlantCare Web** and start it.
4. Open **Web UI**: the add-on uses Ingress and does not expose a port.
5. Optionally configure timezone, exposed sensor entities, photo directory and AI provider in the add-on options.
6. To migrate from the native app, use **Altro → Archivio e backup** and import the exported backup.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the detailed procedure and [docs/IMPORT.md](docs/IMPORT.md) for the import notes.

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -r plantcare_web/backend/requirements.lock pytest
npm ci --prefix plantcare_web/frontend
npm run build --prefix plantcare_web/frontend
PLANTCARE_DATA=.data .venv/bin/uvicorn plantcare_web.backend.main:app --host 127.0.0.1 --port 8099 --no-proxy-headers
```

Open `http://127.0.0.1:8099/`. For frontend hot reload, run `npm run dev --prefix plantcare_web/frontend` while the backend listens on port 8099.

Run the test suite with:

```sh
.venv/bin/python -m pytest plantcare_web/tests -q
```

The CI workflow runs the same backend tests and the frontend build on every push and pull request.

## Documentation

- [Reference matrix and design decisions](docs/REFERENCE.md)
- [Current status, verification and known limits](docs/STATUS.md)
- [Deployment on Home Assistant](docs/DEPLOYMENT.md)
- [iOS layout comparison](docs/IOS_LAYOUT.md)
- [Archive consolidation and performance](docs/STEP8.md)

The detailed documentation is currently written in Italian. An English translation is planned; the README above is the English entry point. Start from the [documentation index](docs/README.md).

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request, run the backend tests and the frontend build, and never commit credentials, personal archives or photos from a real collection. Report security problems privately as described in [SECURITY.md](SECURITY.md).

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Maurizio Antonio Sicoli.

Verdant HA is an independent project and is not affiliated with Home Assistant, Pl@ntNet, Perenual, Open Plantbook, iNaturalist, Google or OpenAI. All trademarks belong to their respective owners.
