# Care engine — Manual, Verdant and AI

Last updated: 19 November 2026 · version 0.11.7

The “care engine” has **two independent layers**:

1. **The plant plan** (`carePlanMode`): **Manual**, **Intelligent / Verdant**, or **AI**. It decides how watering and feeding intervals are created and updated.
2. **The global operational engine** (`care_engine_mode`, add-on option): **Observation only (shadow)** or **Operational**. It decides whether a sensor-driven recommendation may move a due date.

They are not the same thing. A Manual plant can be postponed by the operational engine when it is active; a Verdant plant is not postponed automatically when the engine is in shadow.

## Quick comparison

| | **Manual** | **Verdant (Intelligent)** | **AI** |
|---|---|---|---|
| Intervals | set by the user | calculated by the planner | proposed by the provider |
| Weather and season | no | yes, daily refresh | as context for the proposal |
| Learning from care | no | yes, adaptive 1–4 day step by experience | no, the model decides |
| Default location | not required | required | not required |
| When it changes | only when intervals are edited | creation, recalculation, move, daily refresh, completed watering | daily or manual analysis, then proposal approval |
| Control | full | automatic but cautious | proposal with preview |
| Manual postponements | yes | yes | yes |
| Operational engine | yes, when active | yes, when active | yes, when active |

---

## Manual

- Intervals are **exactly** the ones set: `wateringInterval` and `fertilizingInterval` are used by the calendar without weather, season or learning.
- **Care rhythm** (Very frequent → Very spaced) is not self-regulation: the editor rescales the current intervals immediately (×0.7–1.3) when the value changes. It is a user shortcut, not a planner recalculation.
- The displayed reason is “Manual interval chosen by you”.
- A **postponement** moves only that occurrence and does not change the interval.
- In operational mode, a Manual plant can still receive the **automatic wet-soil postponement**. For fully manual control, keep the operational engine in shadow in the add-on configuration.

## Verdant (Intelligent)

### How the plan is built

On creation, when switching to Verdant, or on recalculation:

1. the **default location** is required (latitude and longitude);
2. Open-Meteo provides the 7-day average temperature, relative humidity and expected rain;
3. the planner starts from species, family and, if available, the saved botanical profile;
4. it applies the **real position** (Full sun, Sheltered balcony, Shade, Half shade, Patio, Landing, Bright indoors, Low-light indoors);
5. it corrects for temperature, humidity and rain (outdoors only);
6. it applies the **season** from the month and hemisphere (latitude);
7. it applies safety thresholds, especially for succulents and high-water-reserve plants;
8. it aligns feeding to a multiple of the watering interval.

Main factors:

| Factor | Effect |
|---|---|
| Position | from ×0.75 (full sun) to ×1.55 (shade for succulents) |
| Temperature ≥ 30 °C | ×0.80 |
| Temperature ≥ 25 °C | ×0.90 |
| Temperature < 12 °C | ×1.25 |
| Humidity < 40% | ×0.95 |
| Humidity > 75% | ×1.10 |
| Rain > 15 mm, outdoors only | ×1.15 |
| Active growth | ×0.95 |
| Resting season | ×1.20 and reduced feeding |
| Transition | ×1.00 |

Watering is clamped between 2 and 35 days (12–60 for succulents, with a position-dependent minimum); feeding is always a multiple of the watering interval.

### Learning from care

After at least **3 completed waterings** and **2 intervals**:

- the last 7 days with completed watering are considered; multiple entries on one day do not simulate additional drying cycles;
- the median gap in days is calculated;
- the value is kept within ±30% of the Verdant baseline;
- the current interval moves towards that value by **1 day**;
- honoured postponements across at least **2 distinct cycles** can increase the step, up to the profile maximum: they may suggest slower drying but are not moisture measurements;
- at least **2 early waterings**, even without a previous postponement, can increase the step towards a shorter interval. Postponements followed by early completions work in the same direction. Conflicting signals prevent accelerated learning;
- new watering events store `wateringDueDate`, the due date before the care command, so later plan changes cannot rewrite that comparison. Shorter historical gaps without a saved due date are labelled separately as **inferred**. Changing an event's date, kind or status invalidates its old schedule snapshot;
- **late gaps without a postponement** never increase the step: they remain weak evidence and the step stays 1;
- the value stays within ±30% and never overshoots the target;
- confidence grows with the number of observed intervals.

### Grower experience

In **Settings → Grower experience** you choose the global level:

| Level | Maximum step |
|---|---:|
| Beginner | 1 day |
| Intermediate | 2 days |
| Expert | 3 days |
| Professional | 4 days |

The profile is a **guardrail against human error**, not proof that every intervention is correct. Repeated signals allow larger steps up to the profile maximum; late gaps without postponement and conflicting signals do not accelerate learning. Several postponements in one cycle are not independent confirmations. Species safety minimums always take priority; Verdant learning retains its ±30% baseline bound (rounded to whole days), distinct from the AI percentages below.

Learning applies:

- when a completed watering is recorded, if the plant is in Verdant and the plan has not been locked by a manual edit or an AI revision;
- during the daily refresh.

It does **not** apply to feeding: that is only realigned to the watering interval. Postponements never count as completed waterings; the gap calculation uses completed waterings only, while honoured and consistent postponements can increase the learning step.

### When it is recalculated

| Moment | Behaviour |
|---|---|
| Creation or switch to Verdant | Immediate calculation with location and weather |
| “Recalculate plan” | Preview, then apply |
| Moving the plant | Immediate recalculation with the last saved climate |
| Once a day | First scheduler cycle after local midnight, at most once per plant per day |
| Completed watering | Immediate learning update |

The automatic daily refresh runs only if the plant is in **Verdant** or **AI**, already has a plan and the plan has **weather enabled**. If “Use weather” is turned off in the Verdant editor, the plan is no longer recalculated automatically.

If intervals are edited by hand, the plan becomes `Manual edit`: the refresh still updates season and climate metadata, but **no longer changes the chosen numbers**. An AI revision on a Verdant plan is preserved while its reason has evidence; for plants in AI mode the refresh always preserves the AI intervals.

### What it does not use

The planner uses the **real position**, not the **Exposure** field (low/indirect/strong light, direct sun). Exposure is only a fallback for the succulent minimum. Two plants with the same position but different exposure therefore get the same plan.

## AI

- The daily analysis considers **only plants in AI mode**.
- It runs once a day at `ai_update_time` (default **03:00**) or on demand with “Analyse now”.
- The provider receives: current intervals, Verdant baseline, care rhythm, room, light, saved season and climate, **location**, **experience level**, recent care, the linked fertilizer product and pot data.
- `careTiming` summarises, for water and feeding, observed gaps, intentional postponements with date, new date and note, and late gaps without a postponement. Each postponement includes the subsequent completion, if any, and its gap from the previous care event. `recentCare` preserves postponement status and target dates instead of making deferred events look completed. The prompt requires the reason to explain how honoured postponements affected the decision, including when no change is proposed.
- `careTiming.water` also includes watering completed before recorded due dates, separately inferred early waterings in old history, and their dates, deadlines, notes and days early. The model must consider postponements as possible slower-drying signals and repeated early care as possible faster-drying signals, never as soil readings. Experience and consistency across cycles control prudence; experience alone is not evidence.
- Proposals are validated:
  - they must declare sufficient evidence and a concrete reason;
  - watering stays within the profile allowance around the Verdant baseline: **beginner ±15%, intermediate ±25%, expert ±35%, professional ±50%**. Species minimums always take priority. Integer bounds round inward and are sent in `wateringLimits`; the same bounds normalize output and are rechecked before applying proposals. Experience alone is not evidence;
  - when a proposed interval is clamped, the reason includes the requested and accepted values and the profile limit;
  - feeding is aligned to a multiple of watering, with at least two cycles;
  - a proposal identical to the current intervals is discarded.
- With `auto_apply_ai` off (the default), proposals **wait for approval** in “AI plan”. Applying them updates intervals and plan with an AI revision and a history entry.
- For plants in AI mode the daily refresh **preserves** the AI intervals. An AI revision on a Verdant plan is preserved while its reason has evidence; without evidence the plan can return to the Verdant/learning baseline.

The AI assistant in the plant card is separate: it answers a question and does not recalculate the plan.

These percentages apply to daily AI analysis. They do not change the ±30% Verdant learning bound or unlock the fixed watering interval in the plant-card assistant.

## Operational engine (shadow / operational)

It is independent of the three modes and is configured **only** by the add-on option `care_engine_mode`:

- **shadow**: computes and shows advice but does not change due dates;
- **operational**: may **only postpone** watering, never advance it and never record care.

The automatic postponement runs after a manual measurement or a sensor poll when:

- the soil-moisture reading is fresh (at most 12 hours) and reliable (≥ 65%);
- the substrate is still wet above the threshold;
- recommendation confidence is sufficient (≥ 35% for moisture ≥ 70%, ≥ 55% otherwise);
- the new time is at least 12 hours after the current due date;
- no postponement has already been applied in the same cycle.

The postponement is capped at **14 days**, written to `nextWateringOverride` and recorded as a “Plan update” entry in the history. The same reading cannot apply it twice. Completing the care clears the override.

The operational engine **does not check** the plan mode: when active, it can postpone even a Manual plant.

## Postponements and delays are not the same

- **Postponement**: an event with status `postponed` and a `postponedUntil` date. It moves only that occurrence, is not completed care and does not enter the gap calculation; when honoured and consistent it can increase the learning step.
- **Delay**: a completed watering after the due date without a recorded postponement. It is a completed care event and contributes to the observed intervals; it is not treated as a postponement.
- A postponement is considered only if it is newer than the last completed watering.
- When watering is completed with feeding due, the app can record feeding too. If it is not included, feeding is postponed to the next watering.

## Recalculation times and options

| What | When |
|---|---|
| Verdant plan | Creation/switch, “Recalculate plan”, move, daily refresh, completed watering |
| Verdant daily refresh | First cycle after local midnight; at most once per plant per day; weather enabled only |
| AI analysis | Every day after `ai_update_time` (03:00) or “Analyse now” |
| Operational engine | After a sensor poll with new readings or a manual measurement |
| Calendar and health | Computed on read; they do not rewrite the plan |

Add-on options:

| Option | Default | Effect |
|---|---|---|
| `timezone` | `Europe/Rome` | Midnight, AI time, calendar |
| `poll_interval_minutes` | 15 | Scheduler frequency: sensors, Verdant refresh, AI time check |
| `ai_update_time` | `03:00` | Earliest daily AI analysis time |
| `care_engine_mode` | `active` | Shadow or operational; single source, the web UI is read-only |
| `auto_apply_ai` | `false` | Apply AI proposals automatically |

The **default location** is not an add-on option: it is set in **Settings → Default location** and stored in the app database.

## Current limits

- Learning uses an adaptive step capped by the chosen profile; the profile does not change safety thresholds or the ±30% bound.
- The daily AI analysis receives location, postponements and delays as context, but never applies the plan automatically: proposals need approval unless `auto_apply_ai` is enabled.
- The planner uses the real position, not the Exposure field.
- Manual mode is not seasonal and does not use weather.
- The operational engine requires configured sensors and operational mode; without fresh readings it does nothing.
- There are no push notifications: AI proposals and postponements appear in the app.

## Code references

- `backend/adaptive.py`: planner, factors, learning, daily refresh.
- `backend/domain.py`: intervals, postponements, `schedule`, `learning`, `stable_water`.
- `backend/care.py`: care recording, postponements, paired feeding.
- `backend/care_operational.py`: automatic wet-soil postponement.
- `backend/care_engine.py`: sensor recommendations and factors.
- `backend/ai.py` and `backend/ai_support.py`: daily analysis, proposals and assistant.
- `backend/settings.py`: add-on options.
