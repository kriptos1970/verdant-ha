# Installation on Home Assistant

## Requirements

- Home Assistant OS or a supervised installation with local add-ons.
- Architectures: `aarch64` or `amd64`.
- Enough free space for SQLite, thumbnails and optional photos. Photos can live in `/share`.

## Install the add-on

1. Download the latest `plantcare-web-<version>.zip` from [GitHub Releases](https://github.com/kriptos1970/verdant-ha/releases) and extract it.
2. Copy the `plantcare_web` folder to `/addons/plantcare_web` on the Home Assistant host (Samba or Terminal & SSH). Do not copy `.venv`, `node_modules`, local databases or personal archives.
3. In the Home Assistant App store, refresh the local add-ons, install **PlantCare Web** and start it.
4. Open **Web UI**. The add-on uses Ingress; no port is exposed and no port forwarding is needed.
5. Configure the options, then restart only when Home Assistant asks for it.

## Options

| Option | Meaning |
|---|---|
| `language` | `auto`, `it` or `en`. The web UI also stores a per-browser preference and sends it back to the server for notifications and AI. |
| `timezone` | IANA timezone used for calendar days, reminders and formatting. |
| `photo_directory` | Default `/data/photos`. Use `/share/plantcare/photos` to share photos with other tools. |
| `max_photo_mb` | Upload limit per photo, 20 MB by default. |
| `measurement_retention_days` | Sensor measurement retention, 365 days by default. Care events and photos are never deleted automatically. |
| `exposed_entities` | Home Assistant entities the add-on may read: temperature, humidity, light, soil moisture and conductivity. |
| `ai_provider`, `ai_model`, API keys | Optional AI advice. Disabled by default; automatic application is off. |
| `plantnet_api_key`, `perenual_api_key` | Optional identification and botanical profiles. |
| `openplantbook_client_id`, `openplantbook_secret` | Optional Open Plantbook consultation. |

Credentials stay in the add-on options and are never sent to the browser.

## Data locations

- `/data/plantcare.sqlite`: database and application state.
- `/data/photos`: default photo directory.
- `/data/thumbnails`: rebuildable thumbnails.
- `/share/plantcare/photos`: optional shared photo directory.

Do not put SQLite on a network share. If you move photos, stop the add-on, copy the folder keeping the file names, change the option and restart. Verify the new path before deleting the old one.

## Backup and restore

- **Altro → Archivio e backup** exports a ZIP with `data.json`, separate photos and a SHA256 manifest.
- Import supports web ZIP archives and native JSON envelopes v1–v3. Import runs on an empty archive after a preview and validates checksums before writing.
- The ZIP export needs temporary disk space roughly equal to the photo collection.
- If photos live in `/share`, include that folder in the Home Assistant backup or run a dedicated backup on the NAS. Save the database at the same point in time.

## Upgrade

Copy the new `plantcare_web` folder over the old one, refresh the add-on in the App store and update it. Database schema and photo paths are preserved. Keep the previous source folder until the new version starts correctly.

## Security notes

- No public port is exposed; access goes through Home Assistant Ingress and requires the Home Assistant login.
- The Supervisor token stays in the container.
- Provider keys are server-side only.
- Report vulnerabilities privately as described in [`SECURITY.md`](../../SECURITY.md).
