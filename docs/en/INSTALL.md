# Installation on Home Assistant

## Requirements

- Home Assistant OS or a supervised installation with local add-ons.
- Architectures: `aarch64` or `amd64`.
- Enough free space for SQLite, thumbnails and optional photos. Photos can live in `/share`.

## Install the add-on

### From the GitHub add-on repository (recommended)

1. In Home Assistant open **Settings → Add-ons → Add-on store**.
2. Open the **⋮** menu → **Repositories** and add `https://github.com/kriptos1970/verdant-ha`.
3. Refresh the store, open **Verdant** and install it.
4. Start it and open **Web UI**. The add-on uses Ingress; no port is exposed and no port forwarding is needed.
5. Configure the options, then restart only when Home Assistant asks for it.

Home Assistant reads `plantcare_web/config.yaml`; a higher `version` in the repository is offered as an update in the store.

### From a local folder (offline or development)

1. Download the latest `plantcare-web-<version>.zip` from [GitHub Releases](https://github.com/kriptos1970/verdant-ha/releases) and extract it.
2. Copy the `plantcare_web` folder to `/addons/plantcare_web` on the Home Assistant host (Samba or Terminal & SSH). Do not copy `.venv`, `node_modules`, local databases or personal archives.
3. In the Home Assistant App store, refresh the local add-ons, install **Verdant** and start it.

> A repository install is registered with a repository-prefixed slug (for example `309d34f7_plantcare_web`); a local install uses `local_plantcare_web`. Their data volumes are separate. To move a local install to the repository add-on, export the ZIP backup, install the repository add-on, re-enter its options and import the ZIP on the empty archive.

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

### Repository add-on

When a new version is published in the repository, the App store shows **Update**. Updating rebuilds the add-on and preserves `/data` (database, application state) and the options. Photos in `/share/plantcare/photos` are outside the container and are preserved. Create a partial backup of the add-on and the `share` folder first.

### Local add-on

Copy the new `plantcare_web` folder over the old one, refresh the add-on in the App store and update it. Database schema and photo paths are preserved. Keep the previous source folder until the new version starts correctly.

### Moving from the local add-on to the repository add-on

The slug changes from `local_plantcare_web` to a repository-prefixed slug (for example `309d34f7_plantcare_web`), so the data volume and the Ingress/panel URL change. Export the ZIP from **Altro → Archivio e backup**, install the repository add-on, copy the options, then import the ZIP on the empty archive. QR/NFC labels that used the old panel URL must be regenerated.

## Security notes

- No public port is exposed; access goes through Home Assistant Ingress and requires the Home Assistant login.
- The Supervisor token stays in the container.
- Provider keys are server-side only.
- Report vulnerabilities privately as described in [`SECURITY.md`](../../SECURITY.md).
