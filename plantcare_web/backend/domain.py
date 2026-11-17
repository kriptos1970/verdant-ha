"""Ports of Models.swift scheduling and CarePlanLearner.swift.

Dates are ISO UTC on the wire, calendar arithmetic uses the configured timezone.
Native import alone accepts Swift's seconds since 2001-01-01.
"""
import math
import unicodedata
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .care_kinds import canonical_kind, canonical_plant

UTC = timezone.utc
KINDS = {"water": "wateringInterval", "fertilize": "fertilizingInterval", "rotate": "rotationInterval", "repot": "repottingInterval", "prune": "pruningInterval", "inspect": "inspectionInterval", "progress": "progressInterval"}
EXTRA_KINDS = {"move", "treatment", "planUpdate"}

def now():
    return datetime.now(UTC)

def iso(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')

def parse(value):
    if not isinstance(value, str):
        raise ValueError('Data ISO non valida')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result

def swift_round(value):
    return math.floor(value + .5) if value >= 0 else math.ceil(value - .5)

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(c))

def active_history(plant):
    return [e for e in plant.get('history', []) if not e.get('deletedAt')]

def care_state(plant, kind):
    kind = canonical_kind(kind)
    records = [e for e in plant.get('history', []) if e['kind'] == kind]
    active = [e for e in records if not e.get('deletedAt')]
    completed = [parse(e['date']) for e in active if e.get('status') != 'postponed']
    completion = max(completed) if completed else None
    acquired = parse(plant['acquiredOn'])
    legacy_key = {'water': 'lastWatered', 'fertilize': 'lastFertilized'}.get(kind)
    anchor = completion or (acquired if records else parse(plant.get(legacy_key) or plant['acquiredOn']))
    postponed = [e for e in active if e.get('status') == 'postponed']
    latest = max(postponed, key=lambda e: parse(e['date'])) if postponed else None
    defer = parse(latest['postponedUntil']) if latest and latest.get('postponedUntil') and (completion is None or parse(latest['date']) > completion) else None
    return anchor, defer

def next_water(plant, tz):
    anchor, deferred = care_state(plant, 'water')
    calculated = anchor.astimezone(tz) + timedelta(days=plant['wateringInterval'])
    return max([calculated] + ([parse(plant['nextWateringOverride'])] if plant.get('nextWateringOverride') else []) + ([deferred] if deferred else []))

def aligned_date(requested, water, interval, tz):
    requested_day = requested.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    first = water.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    steps = max(0, math.ceil((requested_day.date() - first.date()).days / max(1, interval)))
    return first + timedelta(days=steps * max(1, interval))

def schedule(plant, zone='Europe/Rome', at=None, language='it'):
    plant = canonical_plant(plant)
    tz = ZoneInfo(zone)
    today = (at or now()).astimezone(tz).date()
    water = next_water(plant, tz)
    result = []
    for kind, key in KINDS.items():
        interval = plant.get(key)
        if not interval or interval <= 0:
            continue
        anchor, deferred = care_state(plant, kind)
        if kind == 'water':
            due = water
        elif kind == 'fertilize':
            if plant.get('nextFertilizingOverride'):
                due = parse(plant['nextFertilizingOverride'])
            else:
                due = aligned_date(anchor.astimezone(tz) + timedelta(days=interval), water, plant['wateringInterval'], tz)
        else:
            due = anchor.astimezone(tz) + timedelta(days=interval)
        if deferred:
            due = max(due, deferred)
        result.append({'id': plant['id'] + ':' + kind, 'plantID': plant['id'], 'plantName': plant['name'], 'room': plant['room'], 'kind': kind, 'dueDate': iso(due), 'daysUntil': (due.astimezone(tz).date() - today).days, 'intervalDays': interval})
    from .treatments import treatment_actions
    result.extend(treatment_actions(plant,tz,at,language))
    return sorted(result, key=lambda a: (a['dueDate'], a['kind']))

def high_reserve(plant):
    species = normalize(plant.get('name', '') + ' ' + plant.get('species', ''))
    return plant.get('category') == 'Succulenta' or any(t in species for t in ['zamioculcas', 'zz plant', 'sansevieria', 'dracaena trifasciata', 'dracaena angolensis', 'dracaena masoniana', 'dracaena cylindrica'])

def minimum_water(plant):
    if not high_reserve(plant):
        return 1
    placement = (plant.get('adaptivePlan') or {}).get('placement')
    return {'Pieno sole': 12, 'Balcone riparato': 14, 'Interno luminoso': 18, 'Mezza ombra · balcone': 24, 'Patio': 24, 'Ombra': 30, 'Pianerottolo': 30, 'Interno poco luminoso': 30}.get(placement, {'Sole diretto': 12, 'Luce intensa': 14, 'Luce indiretta': 24, 'Luce bassa': 30}.get(plant.get('light'), 30))

def feed_days(desired, water):
    water = max(1, water)
    return min(365, max(1, swift_round(max(water, desired) / water)) * water)

def stable_water(plant):
    plan = plant.get('adaptivePlan') or {}
    baseline = plan.get('verdantWateringDays') or plan.get('botanicalWateringDays')
    minimum = minimum_water(plant)
    if baseline is not None:
        multiplier = {'Molto frequente': .7, 'Frequente': .85, 'Normale': 1, 'Diradata': 1.15, 'Molto diradata': 1.3}.get(plant.get('careFrequencyPreference'), 1)
        return min(120, max(minimum, swift_round(max(minimum, baseline) * multiplier)))
    return min(120, max(minimum, plant['wateringInterval']))

def learning(plant, baseline, zone, language='it'):
    plant = canonical_plant(plant)
    dates = sorted(parse(e['date']).astimezone(ZoneInfo(zone)).date() for e in active_history(plant) if e['kind'] == 'water' and e.get('status') != 'postponed')
    if len(dates) < 3:
        return None
    recent = dates[-7:]
    gaps = sorted((b-a).days for a,b in zip(recent, recent[1:]) if (b-a).days > 0)
    if len(gaps) < 2:
        return None
    n = len(gaps)
    median = gaps[n//2] if n % 2 else swift_round((gaps[n//2-1] + gaps[n//2])/2)
    baseline = max(2, baseline)
    distance = max(1, swift_round(baseline * .3))
    target = min(min(35, baseline + distance), max(max(2, baseline-distance), median))
    current = min(35, max(2, plant['wateringInterval']))
    learned = current + (1 if target > current else -1 if target < current else 0)
    explanation=(f'The latest care suggests about {median} days between waterings. Prudent change: {learned-current:+d} day.' if language=='en' else f'Le ultime cure indicano circa {median} giorni tra le annaffiature. Variazione prudente: {learned-current:+d} giorno.')
    return {'completedWaterings': len(recent), 'observedIntervalDays': median, 'baselineIntervalDays': baseline, 'learnedIntervalDays': learned, 'confidence': min(1, n/6), 'explanation': explanation, 'updatedAt': iso(now())}

def evidence(declared, reason):
    signals = ['dati insufficienti', 'non ci sono dati sufficienti', 'non abbiamo dati sufficienti', 'mancano dati', 'mancano informazioni', 'mantengo gli intervalli', 'manteniamo gli intervalli', 'mantenere gli intervalli', 'intervalli attuali', 'continuiamo con gli intervalli']
    return declared is True and not any(s in normalize(reason) for s in signals)

def accepted_water(proposed, baseline, minimum):
    lower = max(minimum, math.ceil(max(1, baseline)*.75))
    upper = max(lower, min(120, math.floor(max(1, baseline)*1.25)))
    return min(upper, max(lower, proposed))

def plant_view(plant, zone, version, product=None, language='it'):
    from .treatments import treatment_view
    return {**plant, '_version': version, '_schedule': schedule(plant, zone, language=language), '_actions': pending_actions(plant,zone,product=product,language=language), '_treatments': [treatment_view(plant,p,ZoneInfo(zone)) for p in plant.get('treatmentPlans') or []], '_learning': learning(plant, stable_water(plant), zone, language)}


def uses_watering(product):
    if not product:
        return True
    method = normalize(product.get('applicationMethod') or '')
    if any(term in method for term in ['foglia', 'foliar', 'spruzz', 'nebulizz']):
        return False
    if any(term in method for term in ['annaff', 'irrig', 'dilui', 'sciogl', 'disciol']):
        return True
    return (product.get('form') or 'Liquido') in {'Liquido', 'Polvere'}


def most_recent_occurrence(first, interval, tz, at):
    """PlantStore.swift CareScheduleProjection.mostRecentOccurrence, calendar days."""
    interval = max(1, interval)
    if first >= at:
        return first
    local = first.astimezone(tz)
    elapsed = (at.astimezone(tz).date() - local.date()).days
    result = local + timedelta(days=max(0, elapsed // interval) * interval)
    while result + timedelta(days=interval) <= at:
        result += timedelta(days=interval)
    return result


def pending_actions(plant, zone='Europe/Rome', at=None, product=None, language='it'):
    tz = ZoneInfo(zone)
    at = at or now()
    result = []
    for action in schedule(plant, zone, at, language):
        if not action.get('treatmentPlanID'):
            due = most_recent_occurrence(parse(action['dueDate']), action['intervalDays'], tz, at)
            action = {**action, 'dueDate': iso(due), 'daysUntil': (due.astimezone(tz).date() - at.astimezone(tz).date()).days}
        action = {**action, 'id': action['id'] + ':' + action['dueDate'], 'includesFertilizing': False}
        result.append(action)
    if uses_watering(product):
        raw_feed=next((a for a in schedule(plant,zone,at,language) if a['kind']=='fertilize'),None)
        for a in result:
            if a['kind']=='water':
                a['canIncludeFertilizing']=bool(raw_feed and (parse(raw_feed['dueDate']).astimezone(tz).date()<=at.astimezone(tz).date() or parse(raw_feed['dueDate']).astimezone(tz).date()==parse(a['dueDate']).astimezone(tz).date()))
        water = next((a for a in result if a['kind'] == 'water'), None)
        feed = next((a for a in result if a['kind'] == 'fertilize'), None)
        if water and feed and parse(water['dueDate']).astimezone(tz).date() == parse(feed['dueDate']).astimezone(tz).date():
            water['includesFertilizing'] = True
            result.remove(feed)
    return sorted(result, key=lambda a: (a['dueDate'], a['kind'], a['id']))
