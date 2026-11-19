# PlantCare Web

Open the web interface from Home Assistant. Start with a plant or import a native PlantCare backup from **More → Archive and backup**.

The full documentation is in the repository: [English index](https://github.com/kriptos1970/verdant-ha/blob/main/docs/en/README.md) and [Italian documentation](https://github.com/kriptos1970/verdant-ha/blob/main/docs/README.md). The Italian add-on README is at [README.it.md](https://github.com/kriptos1970/verdant-ha/blob/main/README.it.md).

## Options

- `language`: `auto`, `it` or `en`. The web interface also stores a per-browser preference and sends it to the server for notifications and AI.
- `timezone`: timezone used by the calendar.
- `photo_directory`: `/data/photos` by default; `/share/plantcare/photos` for a shared folder. Changing it does not move existing photos automatically.
- `max_photo_mb`: maximum size of new photos, 20 MB by default.
- `measurement_retention_days`: measurement retention, 365 days by default.
- `exposed_entities`: list of allowed Home Assistant sensor entities. All other entities are ignored.
- `poll_interval_minutes`: sampling interval, 15 minutes by default.
- `ai_provider`: `none`, `gemini` or `openai`.
- `ai_model`: explicit model; empty keeps the native default.
- `gemini_api_key`, `openai_api_key`: server-side keys only.
- `ai_update_time`: local time of the daily analysis.
- `auto_apply_ai`: automatic application, off by default.
- `plantnet_api_key`, `perenual_api_key`: optional plant identification and botanical profiles.
- `openplantbook_client_id`, `openplantbook_secret`: optional Open Plantbook consultation.

## Backup

With photos in `/data`, the add-on backup must include data and photos. With photos in `/share`, back up the shared folder too. The app ZIP export includes both with checksums and needs temporary space on the add-on volume.

Import supports web ZIP archives and native JSON envelopes v1–v3. Import runs on an empty archive after a preview and validates checksums before writing.

## Care engine

Each plant uses one of three plan modes:

- **Manual**: the intervals you set are used as they are; no weather, season or learning.
- **Verdant (Intelligent)**: the plan is calculated from species, real position, the default location, the Open-Meteo forecast and the season, then refreshed once a day. Completed waterings allow cautious learning (currently ±1 day). Manual and AI revisions stay protected.
- **AI**: only plants in AI mode are analysed; the provider proposes new intervals with a reason and a preview. Automatic application is off by default.

Separately, the `care_engine_mode` add-on option controls the operational engine:

- **shadow**: recommendations are advisory and do not change the calendar;
- **operational** (default): it may postpone watering when a fresh, reliable moisture reading says the substrate is still wet. It never advances care, never records care and applies at most one postponement per watering cycle.

Postponements are not delays: a postponement moves only that occurrence and is not used for learning. Full explanation, thresholds and recalculation times: [Care engine — Manual, Verdant and AI](https://github.com/kriptos1970/verdant-ha/blob/main/docs/CARE_ENGINE.md).

## Smart plan

Open **Configure smart plan** from the plant card. Choose exposure, location and coordinates; use a manual climate or enable Open-Meteo weather. Coordinates are sent to Open-Meteo only when this option is selected. The preview shows intervals and reasons; **Apply plan** applies exactly that preview, which expires after 30 minutes or after the plant changes.

Enabled weather recalculates the plan once a day at the first available sample. On error the previous intervals are kept. Imported plans do not start weather requests automatically. You can return to Manual from the plant editor.

Completed waterings allow cautious learning. Manual and AI revisions stay protected. In shadow mode the Care Engine observations are advisory; in operational mode they can only postpone watering as described above. They do not activate pumps and are not a diagnosis. Advanced botanical profiles are read from the imported native archive; without reliable profiles the engine asks for more data.

## Sensors

For the entities allowed in the options, map each sensor to a plant or room in **More → Sensors**. A Home Assistant measurement keeps its original observation date: repeated sampling does not make it fresher or increase confidence.

## AI assistant

Configure `ai_provider` and the matching key in the add-on options. From **More → AI plan → Assistant model** you can load the models available to your account and select one. The web choice applies to the current provider and is overridden when `ai_model` changes in the add-on options.

Open **AI** on the plant card, write a question and choose **Ask for advice**. The question and text context are sent to the configured provider, possibly consuming API credit. Photos are not sent. An identical request with the same context, provider and model reuses the result.

Select the activities to apply and review **The plan after applying**. Text indications are added to the notes. If the plant changes after the analysis, a new advice is required. Repeating the same confirmation does not create a second event.

Daily analyses cover plants in AI mode. Automatic application is off by default; proposals create a persistent Home Assistant notification. A notification error appears in the AI status and does not lose the proposals.

Live provider tests require your own keys; development checks use simulated responses. Do not paste keys into chats or issues.
