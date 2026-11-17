import base64
import json
from uuid import uuid4

import pytest

from plantcare_web.backend.care_kinds import (
    canonical_health,
    canonical_kind,
    canonical_plant,
    legacy_health,
    legacy_kind,
    legacy_view,
)
from plantcare_web.backend.models import EventRequest, Plant
from plantcare_web.backend.storage import Store
from plantcare_web.backend.archive_views import history_page


def event(kind='Annaffia', **extra):
    return {'id': str(uuid4()).upper(), 'kind': kind, 'date': '2026-11-01T12:00:00Z', **extra}


def test_kind_and_health_roundtrip():
    pairs = [
        ('Annaffia', 'water'), ('Concima', 'fertilize'), ('Ruota', 'rotate'),
        ('Rinvasa', 'repot'), ('Pota', 'prune'), ('Controlla salute', 'inspect'),
        ('Aggiorna progressi', 'progress'), ('Spostamento', 'move'),
        ('Trattamento', 'treatment'), ('Aggiornamento piano', 'planUpdate'),
    ]
    for legacy, code in pairs:
        assert canonical_kind(legacy) == code
        assert canonical_kind(code) == code
        assert legacy_kind(code) == legacy
        assert legacy_kind(legacy) == legacy
    for legacy, code in [('Malata', 'sick'), ('In difficoltà', 'struggling'), ('Buona', 'good'), ('Eccellente', 'excellent')]:
        assert canonical_health(legacy) == code
        assert canonical_health(code) == code
        assert legacy_health(code) == legacy


def test_unknown_values_are_rejected():
    with pytest.raises(ValueError):
        canonical_kind('Qualcosa')
    with pytest.raises(ValueError):
        canonical_health('Sconosciuto')


def test_models_accept_legacy_and_canonical_values():
    request = EventRequest(kind='Annaffia', health='Buona')
    assert request.kind == 'water' and request.health == 'good'
    request = EventRequest(kind='water', health='good')
    assert request.kind == 'water' and request.health == 'good'

    plant = Plant(name='Monstera', history=[event(), event('Pota', health='Eccellente')])
    assert [e['kind'] for e in plant.history] == ['water', 'prune']
    assert plant.history[1]['health'] == 'excellent'


def test_store_persists_canonical_values_and_reads_canonical(tmp_path):
    store = Store(tmp_path)
    plant = Plant(name='Monstera', growthEntries=[{'id': str(uuid4()), 'date': '2026-11-02T12:00:00Z', 'health': 'Buona'}]).model_dump()
    store.put('plants', plant)

    with store.connection() as db:
        raw = json.loads(db.execute("SELECT payload FROM entities WHERE collection='plants'").fetchone()['payload'])
    assert raw['history'] == []
    assert raw['growthEntries'][0]['health'] == 'good'

    loaded, _ = store.get('plants', plant['id'])
    assert loaded['growthEntries'][0]['health'] == 'good'


def test_legacy_view_restores_the_frontend_contract():
    view = {
        'history': [event('water', health='good')],
        'growthEntries': [{'id': str(uuid4()), 'date': '2026-11-02T12:00:00Z', 'health': 'excellent'}],
        'healthPhotoSessions': [{'id': str(uuid4()), 'date': '2026-11-02T12:00:00Z', 'health': 'struggling', 'photos': []}],
        '_schedule': [{'kind': 'water'}],
        '_actions': [{'kind': 'fertilize'}],
        '_treatments': [],
    }
    legacy = legacy_view(view)
    assert legacy['history'][0]['kind'] == 'Annaffia'
    assert legacy['history'][0]['health'] == 'Buona'
    assert legacy['growthEntries'][0]['health'] == 'Eccellente'
    assert legacy['healthPhotoSessions'][0]['health'] == 'In difficoltà'
    assert legacy['_schedule'][0]['kind'] == 'Annaffia'
    assert legacy['_actions'][0]['kind'] == 'Concima'


def test_canonical_plant_is_idempotent_and_does_not_mutate_input():
    source = {'history': [event()], 'growthEntries': []}
    first = canonical_plant(source)
    second = canonical_plant(first)
    assert first == second
    assert source['history'][0]['kind'] == 'Annaffia'


def test_history_page_reads_legacy_payloads_written_before_the_migration(tmp_path):
    store = Store(tmp_path)
    plant = {'id': str(uuid4()).upper(), 'name': 'Ficus', 'room': 'Casa', 'acquiredOn': '2026-01-01T12:00:00Z', 'history': [event('Pota')]}
    with store.connection() as db:
        db.execute("INSERT INTO entities VALUES ('plants',?,?,1)", (plant['id'], json.dumps(plant)))
    for filter_value in ('Pota', 'prune'):
        page = history_page(store, 'Europe/Rome', kind=filter_value)
        assert page['total'] == 1
        assert page['items'][0]['event']['kind'] == 'Pota'
    assert history_page(store, 'Europe/Rome')['kinds'] == ['Pota']


def test_json_export_keeps_the_legacy_italian_shape(tmp_path):
    store = Store(tmp_path)
    plant = Plant(name='Ficus', history=[event()]).model_dump()
    store.put('plants', plant)
    payload = json.loads(base64.b64decode(store.export()['payload']))
    assert payload['collections']['plants'][0]['history'][0]['kind'] == 'Annaffia'
