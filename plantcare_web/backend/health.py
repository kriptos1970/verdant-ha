"""Plant health index, a faithful port of Plant.healthAssessment in Models.swift.

The score is intentionally identical to the native app: watering and feeding
delays, the latest recorded observation, overdue routine checks and repeated
light readings. The API exposes stable codes so the interface can translate
labels and tips without duplicating the calculation.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo
from .domain import active_history, aligned_date, care_state, next_water, now, parse
from .care_kinds import canonical_plant

# Same thresholds as PlantDetailView/CollectionAnalytics.
LABELS = ((85, 'good'), (70, 'watch'), (0, 'attention'))
ROUTINES = (
    ('inspect', 'inspectionInterval', 10, 'health.tip.inspectionLate'),
    ('progress', 'progressInterval', 8, 'health.tip.progressLate'),
)
TIMED_TIPS = {'health.tip.wateringLate', 'health.tip.fertilizingLate',
              'health.tip.inspectionLate', 'health.tip.progressLate'}


def _rounded(value):
    """Swift's FloatingPoint.rounded(): half away from zero, not banker's."""
    return int(value + .5) if value >= 0 else int(value - .5)


def _local_day(value, tz):
    return value.astimezone(tz).date()


def _day_gap(start, end, tz):
    return (_local_day(end, tz) - _local_day(start, tz)).days


def latest_observation(plant, include_photos=True):
    """Latest health observation across growth, health photos and care events."""
    candidates = []
    for entry in plant.get('growthEntries') or []:
        if entry.get('health') and entry.get('date'):
            candidates.append((parse(entry['date']), entry['health']))
    if include_photos:
        for session in plant.get('healthPhotoSessions') or []:
            if session.get('health') and session.get('date'):
                candidates.append((parse(session['date']), session['health']))
    for event in active_history(plant):
        if event.get('health') and event.get('date'):
            candidates.append((parse(event['date']), event['health']))
    if not candidates:
        return None
    # Swift max(by:) keeps the first element on equal dates: growth, photos, events.
    best = candidates[0]
    for candidate in candidates[1:]:
        if candidate[0] > best[0]:
            best = candidate
    return best


def latest_health(plant):
    """Analytics projection: growth entries and care events, as in CollectionAnalyticsView."""
    observation = latest_observation(plant, include_photos=False)
    return observation[1] if observation else None


def _next_fertilizing(plant, tz):
    interval = plant.get('fertilizingInterval')
    if not interval:
        return None
    anchor, deferred = care_state(plant, 'fertilize')
    if plant.get('nextFertilizingOverride'):
        due = parse(plant['nextFertilizingOverride'])
    else:
        due = aligned_date(
            anchor.astimezone(tz) + timedelta(days=interval),
            next_water(plant, tz),
            plant['wateringInterval'],
            tz,
        )
    if deferred:
        due = max(due, deferred)
    return due


def _overdue_routine(plant, kind, interval, maximum, today, tz):
    if not interval or interval <= 0:
        return None
    events = active_history(plant)
    completed = [parse(e['date']) for e in events if e['kind'] == kind and e.get('status') != 'postponed']
    last = max(completed) if completed else parse(plant['acquiredOn'])
    calculated = last.astimezone(tz) + timedelta(days=interval)
    postponed = [e for e in events
                 if e['kind'] == kind and e.get('status') == 'postponed'
                 and e.get('postponedUntil') and parse(e['date']) > last]
    if postponed:
        latest = max(postponed, key=lambda e: parse(e['date']))
        calculated = max(calculated, parse(latest['postponedUntil']))
    delay = max(0, _day_gap(calculated, today, tz))
    if delay <= 0:
        return None
    return min(maximum, 2 + delay), delay


def _light_target(plant):
    profile = plant.get('openPlantbookProfile') or {}
    low, high = profile.get('minimumLightLux'), profile.get('maximumLightLux')
    if low is not None and high is not None and low < high:
        return max(50, low * .35), low, low, high, high * 1.5, max(60000, high * 2)
    low, high = {
        'Luce bassa': (250, 1000),
        'Luce indiretta': (1000, 5000),
        'Luce intensa': (5000, 20000),
        'Sole diretto': (20000, 100000),
    }.get(plant.get('light'), (1000, 5000))
    return max(50, low * .35), low, low, high, high * 1.5, max(60000, high * 2)


def light_status(plant, at, tz):
    """Port of LightEvaluationEngine.evaluate with profileID nil (health usage)."""
    measurements = plant.get('lightMeasurements') or []
    normalized = []
    for measurement in measurements:
        try:
            date = parse(measurement['date'])
            age = _day_gap(date, at, tz)
            if not 0 <= age <= 30:
                continue
            hour = date.astimezone(tz).hour
            factor = (.35 if 6 <= hour < 9 else .75 if 9 <= hour < 12 else
                      1 if 12 <= hour < 16 else .65 if 16 <= hour < 19 else
                      .3 if 19 <= hour < 21 else None)
            if factor is None:
                continue
            lux = float(measurement['estimatedLux'])
            normalized.append((lux / factor, lux >= 50000))
        except (KeyError, TypeError, ValueError):
            continue
    if not normalized:
        return 'insufficientData'
    floor, adequate, ideal_min, ideal_max, tolerable, stress = _light_target(plant)
    average = sum(value for value, _ in normalized) / len(normalized)
    direct = sum(1 for _, is_direct in normalized if is_direct)
    if average < floor:
        return 'veryLow'
    if average < adequate:
        return 'belowTarget'
    if average < ideal_min:
        return 'adequate'
    if average <= ideal_max:
        return 'ideal'
    if direct < 3 or average <= tolerable:
        return 'brightIndirect'
    if average >= stress:
        return 'monitorDirectSun'
    return 'brightIndirect'


def _fallback(key, count, language='it'):
    # Backend fallback copy for non-UI clients; the interface uses the codes.
    if language == 'en':
        return {
            'health.tip.wateringLate.one': f'Watering {count} day late.',
            'health.tip.wateringLate.other': f'Watering {count} days late.',
            'health.tip.fertilizingLate.one': f'Feeding {count} day late.',
            'health.tip.fertilizingLate.other': f'Feeding {count} days late.',
            'health.tip.inspectionLate.one': f'Health check {count} day late.',
            'health.tip.inspectionLate.other': f'Health check {count} days late.',
            'health.tip.progressLate.one': f'Progress update {count} day late.',
            'health.tip.progressLate.other': f'Progress update {count} days late.',
        }[key]
    return {
        'health.tip.wateringLate.one': f'Annaffiatura in ritardo di {count} giorno.',
        'health.tip.wateringLate.other': f'Annaffiatura in ritardo di {count} giorni.',
        'health.tip.fertilizingLate.one': f'Concimazione in ritardo di {count} giorno.',
        'health.tip.fertilizingLate.other': f'Concimazione in ritardo di {count} giorni.',
        'health.tip.inspectionLate.one': f'Controllo salute in ritardo di {count} giorno.',
        'health.tip.inspectionLate.other': f'Controllo salute in ritardo di {count} giorni.',
        'health.tip.progressLate.one': f'Aggiornamento progressi in ritardo di {count} giorno.',
        'health.tip.progressLate.other': f'Aggiornamento progressi in ritardo di {count} giorni.',
    }[key]


def assess(plant, zone, at=None, language='it'):
    """Return the native health score, label code and the most urgent tip."""
    plant = canonical_plant(plant)
    tz = ZoneInfo(zone)
    at = at or now()
    today = at.astimezone(tz)
    score = 92
    concerns = []

    if plant.get('wateringInterval'):
        delay = max(0, _day_gap(next_water(plant, tz), today, tz))
        if delay > 0:
            penalty = min(30, delay * 8)
            score -= penalty
            concerns.append((penalty, 'health.tip.wateringLate', {'count': delay}))
    fertilizing = _next_fertilizing(plant, tz)
    if fertilizing is not None:
        delay = max(0, _day_gap(fertilizing, today, tz))
        if delay > 0:
            penalty = min(12, delay * 2)
            score -= penalty
            concerns.append((penalty, 'health.tip.fertilizingLate', {'count': delay}))

    observation = latest_observation(plant)
    if observation:
        date, health = observation
        age = max(0, _day_gap(date, today, tz))
        weight = 1. if age <= 45 else .5 if age <= 120 else 0.
        adjustment = {'excellent': 6, 'good': 0, 'struggling': -20, 'sick': -35}.get(health, 0)
        weighted = _rounded(adjustment * weight)
        score += weighted
        if weighted < 0:
            concerns.append((-weighted, 'health.tip.observation', {'health': health}))

    for kind, field, maximum, key in ROUTINES:
        overdue = _overdue_routine(plant, kind, plant.get(field), maximum, today, tz)
        if overdue:
            penalty, delay = overdue
            score -= penalty
            concerns.append((penalty, key, {'count': delay}))

    if len(plant.get('lightMeasurements') or []) >= 3:
        status = light_status(plant, at, tz)
        if status in {'veryLow', 'monitorDirectSun'}:
            score -= 4
            concerns.append((4, 'health.tip.light', {}))

    score = max(20, min(100, score))
    label = next(code for threshold, code in LABELS if score >= threshold)
    urgent = None
    for candidate in concerns:
        if urgent is None or candidate[0] > urgent[0]:
            urgent = candidate
    if urgent:
        _, code, params = urgent
        if code in TIMED_TIPS:
            tip_code = f"{code}.{'one' if params['count'] == 1 else 'other'}"
            fallback = _fallback(tip_code, params['count'], language)
        else:
            tip_code = code
            fallback = _MESSAGES[language][code]
    else:
        tip_code = 'health.tip.lastObservation' if observation else 'health.tip.allGood'
        params = {'health': observation[1]} if observation else {}
        fallback = _MESSAGES[language][tip_code]
    return {
        'score': score,
        'labelCode': f'health.label.{label}',
        'labelFallback': _LABELS[language][label],
        'tipCode': tip_code,
        'tipParams': params,
        'tipFallback': fallback,
    }


_LABELS = {
    'it': {'good': 'Sta bene', 'watch': 'Da osservare', 'attention': 'Serve attenzione'},
    'en': {'good': 'Looking good', 'watch': 'Worth watching', 'attention': 'Needs attention'},
}

_MESSAGES = {
    'it': {
        'health.tip.allGood': 'Cure principali in regola. Registra un controllo per rendere l’indice più preciso.',
        'health.tip.lastObservation': 'Ultimo controllo registrato. Cure principali in regola.',
        'health.tip.observation': 'Ultimo controllo con segnali da osservare.',
        'health.tip.light': 'Le misure luce suggeriscono di verificare la posizione con altre letture.',
    },
    'en': {
        'health.tip.allGood': 'Main care is on track. Record a check to make the index more precise.',
        'health.tip.lastObservation': 'Latest check recorded. Main care is on track.',
        'health.tip.observation': 'The latest check shows something worth watching.',
        'health.tip.light': 'Light readings suggest checking the position with more measurements.',
    },
}
