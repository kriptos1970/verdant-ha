"""Read-only collection analytics for the home and collection dashboards.

Mirrors DashboardView and CollectionAnalyticsView: completed care in the
selected period, active days, watering regularity, care mix, rooms, latest
recorded health and plants needing attention. Nothing here writes data.
"""
from collections import Counter
from datetime import timedelta
from zoneinfo import ZoneInfo
from .domain import active_history, next_water, now, parse
from .care_kinds import legacy_kind, canonical_plant
from .health import latest_health

PERIODS = {30, 90, 365}


def _local_day(value, tz):
    return value.astimezone(tz).date()


def _rounded_percentage(part, total):
    return int(part / total * 100 + .5)


def _water_dates(plant):
    return sorted(parse(e['date']) for e in active_history(plant)
                  if e['kind'] == 'water' and e.get('status') != 'postponed')


def _timeliness(plants, start, tz):
    checks = regular = 0
    for plant in plants:
        dates = _water_dates(plant)
        interval = plant.get('wateringInterval') or 0
        for previous, current in zip(dates, dates[1:]):
            if current < start:
                continue
            gap = (_local_day(current, tz) - _local_day(previous, tz)).days
            checks += 1
            if gap <= interval + 1:
                regular += 1
    return _rounded_percentage(regular, checks) if checks else None


def _attention(days_until_water, health):
    if health in {'sick', 'struggling'}:
        return {'code': 'health', 'health': health}, -100 if health == 'sick' else -50
    if days_until_water < 0:
        return {'code': 'watering', 'days': abs(days_until_water)}, 0
    return None, 0


def summary(plants, zone, days=30, at=None):
    if days not in PERIODS:
        raise ValueError('Periodo non disponibile.')
    plants = [canonical_plant(plant) for plant in plants]
    tz = ZoneInfo(zone)
    at = at or now()
    start = at - timedelta(days=days)
    today = _local_day(at, tz)

    completed = []
    daily = Counter()
    care_mix = Counter()
    health_counts = Counter()
    unrated = 0
    rooms = {}
    at_risk = []

    for plant in plants:
        room = plant.get('room') or ''
        bucket = rooms.setdefault(room, {'room': room, 'plants': 0, 'overdue': 0})
        bucket['plants'] += 1
        due = next_water(plant, tz)
        days_until = (_local_day(due, tz) - today).days
        if days_until < 0:
            bucket['overdue'] += 1

        observation = latest_health(plant)
        if observation:
            health_counts[observation] += 1
        else:
            unrated += 1

        reason, penalty = _attention(days_until, observation)
        if reason:
            at_risk.append({
                'id': plant['id'],
                'name': plant['name'],
                'room': room,
                'photoPath': plant.get('photoPath'),
                'daysUntilWatering': days_until,
                'reason': reason,
                'score': penalty + days_until,
            })

        for event in active_history(plant):
            if event.get('status') == 'postponed':
                continue
            date = parse(event['date'])
            if date < start:
                continue
            completed.append(date)
            daily[_local_day(date, tz)] += 1
            care_mix[event['kind']] += 1

    days_shown = min(days, 60)
    activity = [
        {'date': (today - timedelta(days=offset)).isoformat(),
         'count': daily[today - timedelta(days=offset)]}
        for offset in range(days_shown - 1, -1, -1)
    ]

    return {
        'days': days,
        'periodStart': start.isoformat().replace('+00:00', 'Z'),
        'generatedAt': at.isoformat().replace('+00:00', 'Z'),
        'plantCount': len(plants),
        'completedEvents': len(completed),
        'activeDays': len(daily),
        'timelinessPercent': _timeliness(plants, start, tz),
        'dailyActivity': activity,
        'careMix': [{'kind': legacy_kind(kind), 'count': count}
                    for kind, count in sorted(care_mix.items(), key=lambda item: (-item[1], item[0]))],
        'rooms': sorted(rooms.values(), key=lambda item: (-item['plants'], item['room'])),
        'health': {
            'excellent': health_counts['excellent'],
            'good': health_counts['good'],
            'struggling': health_counts['struggling'],
            'sick': health_counts['sick'],
            'unrated': unrated,
        },
        'plantsAtRisk': sorted(at_risk, key=lambda item: (item['score'], item['name']))[:8],
    }


def timeline(store, plant, limit=8):
    """Merge care events and measurements, newest first, for the plant card."""
    from .care_engine import normalized_measurements
    from .domain import iso
    with store.connection() as db:
        rows = [dict(r) for r in db.execute(
            'SELECT * FROM measurements WHERE plant_id=? ORDER BY measured_at DESC LIMIT 10000',
            (plant['id'],))]
        native = [m for m in store.state('native-measurements', [], db)
                  if m.get('plantID') == plant['id']]
    native_measurements = normalized_measurements(native)
    native_keys = {(m['kind'], m['value'], m['unit'], iso(parse(m['date'])))
                   for m in native_measurements}
    measurements = []
    for row in rows:
        normalized = normalized_measurements([row])
        if not normalized:
            continue
        item = normalized[0]
        if (item['kind'], item['value'], item['unit'], iso(parse(item['date']))) in native_keys:
            continue
        measurements.append(item)

    items = []
    for event in active_history(plant):
        items.append({
            'id': event['id'],
            'type': 'event',
            'date': event['date'],
            'kind': legacy_kind(event['kind']),
            'status': event.get('status') or 'completed',
            'note': event.get('note') or '',
            'health': event.get('health'),
            'photoPaths': event.get('photoPaths') or [],
        })
    for measurement in measurements + native_measurements:
        items.append({
            'id': measurement['id'],
            'type': 'measurement',
            'date': measurement['date'],
            'kind': measurement['kind'],
            'value': measurement['value'],
            'unit': measurement['unit'],
        })
    items.sort(key=lambda item: (parse(item['date']), str(item['id'])), reverse=True)
    return items[:limit]
