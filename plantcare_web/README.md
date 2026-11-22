# Verdant

**Plant care for Home Assistant.** A self-hosted add-on for a houseplant collection: care
rounds, calendar, history, treatments, sensors and optional AI advice, all on your own
instance.

- **Collection**: plants, rooms, products, photos, growth diary, health album.
- **Care**: guided rounds by room, weekly and monthly calendar, history, deferrals,
  treatment cycles and reminders.
- **Scheduling**: manual intervals or an adaptive planner with seasonal rules and the
  Open-Meteo forecast. New plants start in manual mode; the planner only postpones
  watering, it never advances care.
- **Sensors**: map temperature, humidity, light, soil moisture and conductivity entities to
  a plant or a room.
- **Optional AI**: Gemini or OpenAI with a preview and selective apply. Off by default.
- **Data**: SQLite and photos on your instance, ZIP backup with SHA-256 checksums, import
  from the native Verdant archive.

## Install

1. Settings → Add-ons → Add-on store → ⋮ → **Repositories**
2. Add `https://github.com/kriptos1970/verdant-ha`
3. Install **Verdant**, start it and open the **Web UI** (Ingress, no port exposed)

## Privacy

No account and no telemetry. Weather lookups go to Open-Meteo; Pl@ntNet, Perenual,
Open Plantbook, Gemini and OpenAI are only called when you add a key.

## Links

- [Documentation](DOCS.md)
- [Changelog](CHANGELOG.md)
- [Project README](https://github.com/kriptos1970/verdant-ha#readme)
- [Issues](https://github.com/kriptos1970/verdant-ha/issues)

MIT licensed. Verdant is an independent project, not affiliated with Home Assistant,
Pl@ntNet, Perenual, Open Plantbook, iNaturalist, Google or OpenAI.
