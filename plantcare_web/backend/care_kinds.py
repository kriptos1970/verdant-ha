"""Canonical care values and conversion from the legacy Italian archive values.

Storage and the engine use stable English codes. The API and backups keep the
native Italian values so the current frontend and older releases remain
compatible; imported archives and pre-migration payloads are normalized on read.
"""
KIND_TO_CODE = {
    'Annaffia': 'water',
    'Concima': 'fertilize',
    'Ruota': 'rotate',
    'Rinvasa': 'repot',
    'Pota': 'prune',
    'Controlla salute': 'inspect',
    'Aggiorna progressi': 'progress',
    'Spostamento': 'move',
    'Trattamento': 'treatment',
    'Aggiornamento piano': 'planUpdate',
}
CODE_TO_KIND = {code: kind for kind, code in KIND_TO_CODE.items()}
KIND_CODES = frozenset(CODE_TO_KIND)
LEGACY_KINDS = frozenset(KIND_TO_CODE)

HEALTH_TO_CODE = {
    'Malata': 'sick',
    'In difficoltà': 'struggling',
    'Buona': 'good',
    'Eccellente': 'excellent',
}
CODE_TO_HEALTH = {code: health for health, code in HEALTH_TO_CODE.items()}
HEALTH_CODES = frozenset(CODE_TO_HEALTH)
LEGACY_HEALTH = frozenset(HEALTH_TO_CODE)


def canonical_kind(value):
    if value in KIND_TO_CODE:
        return KIND_TO_CODE[value]
    if value in CODE_TO_KIND:
        return value
    raise ValueError('Tipo di cura non valido')


def legacy_kind(value):
    if value in CODE_TO_KIND:
        return CODE_TO_KIND[value]
    if value in KIND_TO_CODE:
        return value
    raise ValueError('Tipo di cura non valido')


def canonical_health(value):
    if value in HEALTH_TO_CODE:
        return HEALTH_TO_CODE[value]
    if value in CODE_TO_HEALTH:
        return value
    raise ValueError('Stato di salute non valido')


def legacy_health(value):
    if value in CODE_TO_HEALTH:
        return CODE_TO_HEALTH[value]
    if value in HEALTH_TO_CODE:
        return value
    raise ValueError('Stato di salute non valido')


def canonical_event(event):
    result = dict(event)
    if 'kind' in result:
        result['kind'] = canonical_kind(result['kind'])
    if result.get('health'):
        result['health'] = canonical_health(result['health'])
    return result


def legacy_event(event):
    result = dict(event)
    if 'kind' in result:
        result['kind'] = legacy_kind(result['kind'])
    if result.get('health'):
        result['health'] = legacy_health(result['health'])
    return result


def _convert_plant(plant, event_converter):
    result = dict(plant)
    for key in ('history', 'growthEntries', 'healthPhotoSessions'):
        value = result.get(key)
        if isinstance(value, list):
            result[key] = [event_converter(item) if isinstance(item, dict) else item for item in value]
    return result


def canonical_plant(plant):
    return _convert_plant(plant, canonical_event)


def legacy_plant(plant):
    return _convert_plant(plant, legacy_event)


def canonical_action(action):
    result = dict(action)
    if 'kind' in result:
        result['kind'] = canonical_kind(result['kind'])
    return result


def legacy_action(action):
    result = dict(action)
    if 'kind' in result:
        result['kind'] = legacy_kind(result['kind'])
    return result


def legacy_view(view):
    """Convert an internal plant view to the legacy Italian API contract."""
    result = _convert_plant(view, legacy_event)
    for key in ('_schedule', '_actions'):
        value = result.get(key)
        if isinstance(value, list):
            result[key] = [legacy_action(item) if isinstance(item, dict) else item for item in value]
    return result
