"""Operational Care Engine: conservative, measurement-driven schedule adjustment.

Only postpones watering when a fresh, reliable moisture reading says the
substrate is still wet. It never marks care as completed and never advances a
due date.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo
from uuid import uuid4
from .domain import iso, now, parse, schedule
from .storage import Conflict


def evaluate_plant(store, settings, plant_id):
    from .care_engine import evaluate, normalized_measurements
    with store.connection() as db:
        plant, _ = store.get('plants', plant_id, db)
        biology = None
        if plant.get('speciesBiologyID'):
            try:
                biology, _ = store.get('speciesBiologies', plant['speciesBiologyID'], db)
            except KeyError:
                pass
        rows = [dict(r) for r in db.execute('SELECT * FROM measurements WHERE plant_id=? ORDER BY measured_at DESC LIMIT 10000', (plant_id,))]
        native = [m for m in store.state('native-measurements', [], db) if m.get('plantID') == plant_id]
    native_keys = {(m['kind'], m['value'], m['unit'], iso(parse(m['date']))) for m in normalized_measurements(native)}
    rows = [r for r in rows if not any((m['kind'], m['value'], m['unit'], iso(parse(m['date']))) in native_keys for m in normalized_measurements([r]))]
    return evaluate(plant, rows + native, biology, settings.zone)


def apply_safe_adjustment(store, settings, plant_id, at=None):
    if settings.options.get('care_engine_mode', 'shadow') != 'active':
        return None
    at = at or now()
    try:
        result = evaluate_plant(store, settings, plant_id)
    except (KeyError, ValueError):
        return None
    water = next((r for r in result.get('recommendations', []) if r.get('domain') == 'water'), None)
    if not water or water.get('action') != 'waitToWater':
        return None
    gate = water.get('safetyGate') or {}
    if gate.get('outcome') not in {'passed', 'blocked'}:
        return None
    confidence = float((water.get('confidence') or {}).get('value', 0))
    threshold = 0.35 if gate.get('code') == 'water.moisture_high' else 0.55
    if confidence < threshold:
        return None
    moisture = next((f for f in water.get('factors', []) if f.get('id') == 'water.moisture.current'), None)
    if not moisture:
        return None
    try:
        percent = float((moisture.get('parameters') or {}).get('percent'))
        reliability = float(moisture.get('reliability', moisture.get('confidence', 0)))
    except (TypeError, ValueError):
        return None
    if reliability < 0.65:
        return None
    if gate.get('code') not in {'water.moisture_high', 'water.above_dry_down'}:
        return None
    try:
        plant, version = store.get('plants', plant_id)
        due = next(a for a in schedule(plant, settings.zone, at) if a['kind'] == 'water')
    except (KeyError, StopIteration):
        return None
    current_due = parse(due['dueDate'])
    # One automatic postponement per watering cycle: wait for care or a manual reset.
    if plant.get('careEngineApplied') and plant.get('nextWateringOverride'):
        try:
            if parse(plant['nextWateringOverride']) > at:
                return None
        except (TypeError, ValueError):
            pass
    eta = (result.get('dryDown') or {}).get('estimatedHoursToTarget')
    if eta is not None and eta > 0:
        target = at + timedelta(hours=min(float(eta) + 6, 14 * 24))
    else:
        target = max(current_due, at + timedelta(days=2))
    target = min(target, at + timedelta(days=14))
    if target <= current_due + timedelta(hours=12):
        return None
    fingerprint = result.get('inputFingerprint')
    if plant.get('careEngineApplied', {}).get('fingerprint') == fingerprint:
        return None
    from .services import message_language
    english = message_language(store, settings) == 'en'
    reason = (
        f"Care engine: watering postponed to {target.astimezone(ZoneInfo(settings.zone)).strftime('%d/%m/%Y')}. "
        f"Substrate at {percent:.0f}% (reliability {round(reliability * 100)}%)."
        if english
        else f"Motore di cura: annaffiatura rinviata al {target.astimezone(ZoneInfo(settings.zone)).strftime('%d/%m/%Y')}. "
        f"Terreno al {percent:.0f}% (affidabilità {round(reliability * 100)}%)."
    )
    plant['nextWateringOverride'] = iso(target)
    plant['careEngineApplied'] = {
        'fingerprint': fingerprint,
        'appliedAt': iso(at),
        'previousDue': iso(current_due),
        'newDue': iso(target),
        'reason': reason,
        'measurementID': (moisture.get('evidenceIDs') or [None])[0],
        'moisturePercent': percent,
        'confidence': round(float((water.get('confidence') or {}).get('value', 0)), 3),
    }
    plant.setdefault('history', []).append({
        'id': str(uuid4()).upper(),
        'kind': 'planUpdate',
        'date': iso(at),
        'status': 'completed',
        'note': reason,
        'origin': 'system',
        'schemaVersion': 2,
    })
    try:
        with store.connection() as db:
            store.put('plants', plant, version, db)
    except Conflict:
        return None
    return plant['careEngineApplied']
