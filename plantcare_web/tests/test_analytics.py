from datetime import datetime, timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import analytics, main
from plantcare_web.backend.models import Plant
from plantcare_web.backend.storage import Store

AT = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)


def plant(**values):
    result = dict(
        id=str(uuid4()).upper(), name='Ficus', species='Ficus elastica', room='Casa',
        category='Tropicale', light='Luce indiretta', wateringInterval=7,
        lastWatered='2026-11-17T12:00:00Z', acquiredOn='2026-01-01T12:00:00Z', history=[],
    )
    result.update(values)
    return result


def event(kind='water', date='2026-11-16T12:00:00Z', status='completed', **values):
    return {'id': str(uuid4()).upper(), 'kind': kind, 'date': date, 'status': status, **values}


def test_empty_collection_has_zero_filled_activity():
    result = analytics.summary([], 'Europe/Rome', 30, AT)
    assert result['completedEvents'] == 0
    assert result['activeDays'] == 0
    assert result['timelinessPercent'] is None
    assert len(result['dailyActivity']) == 30
    assert result['dailyActivity'][-1] == {'date': '2026-11-17', 'count': 0}
    assert result['plantsAtRisk'] == []
    assert result['health'] == {'excellent': 0, 'good': 0, 'struggling': 0, 'sick': 0, 'unrated': 0}


def test_period_excludes_deleted_postponed_and_old_events():
    events = [
        event(date='2026-11-17T10:00:00Z'),
        event(date='2026-11-16T10:00:00Z', deletedAt='2026-11-16T11:00:00Z'),
        event(date='2026-11-15T10:00:00Z', status='postponed', postponedUntil='2026-11-20T10:00:00Z'),
        event(date='2026-10-01T10:00:00Z'),
        event(kind='fertilize', date='2026-11-14T10:00:00Z'),
    ]
    result = analytics.summary([plant(history=events)], 'Europe/Rome', 30, AT)
    assert result['completedEvents'] == 2
    assert result['activeDays'] == 2
    assert result['dailyActivity'][-1]['count'] == 1
    assert {item['kind']: item['count'] for item in result['careMix']} == {'Annaffia': 1, 'Concima': 1}


def test_period_selector_changes_the_window_and_chart_length():
    events = [event(date='2026-09-01T10:00:00Z')]
    month = analytics.summary([plant(history=events)], 'Europe/Rome', 30, AT)
    quarter = analytics.summary([plant(history=events)], 'Europe/Rome', 90, AT)
    year = analytics.summary([plant(history=events)], 'Europe/Rome', 365, AT)
    assert (month['completedEvents'], quarter['completedEvents'], year['completedEvents']) == (0, 1, 1)
    assert len(month['dailyActivity']) == 30
    assert len(quarter['dailyActivity']) == 90
    assert len(year['dailyActivity']) == 365


def test_timeliness_compares_gaps_with_the_watering_interval():
    p = plant(wateringInterval=7, history=[
        event(date='2026-11-16T12:00:00Z'),
        event(date='2026-11-10T12:00:00Z'),  # 6 days: regular
        event(date='2026-11-03T12:00:00Z'),  # 7 days: regular
    ])
    regular = analytics.summary([p], 'Europe/Rome', 30, AT)
    assert regular['timelinessPercent'] == 100

    late = plant(wateringInterval=7, history=[
        event(date='2026-11-16T12:00:00Z'),
        event(date='2026-11-04T12:00:00Z'),  # 12 days: late
        event(date='2026-11-03T12:00:00Z'),  # 1 day: regular
    ])
    assert analytics.summary([late], 'Europe/Rome', 30, AT)['timelinessPercent'] == 50


def test_rooms_and_overdue_plants():
    overdue = plant(name='Ficus', room='Casa', lastWatered='2026-11-01T12:00:00Z')
    ok = plant(name='Menta', room='Balcone', lastWatered='2026-11-17T12:00:00Z')
    result = analytics.summary([overdue, ok], 'Europe/Rome', 30, AT)
    assert result['rooms'] == [
        {'room': 'Balcone', 'plants': 1, 'overdue': 0},
        {'room': 'Casa', 'plants': 1, 'overdue': 1},
    ]
    assert result['plantsAtRisk'][0]['name'] == 'Ficus'
    assert result['plantsAtRisk'][0]['reason'] == {'code': 'watering', 'days': 9}


def test_latest_health_counts_and_risk_order():
    sick = plant(name='Sick', room='Casa', lastWatered='2026-11-17T12:00:00Z',
                 history=[event(kind='inspect', health='Malata', date='2026-11-16T10:00:00Z')])
    struggling = plant(name='Struggling', room='Casa', lastWatered='2026-11-17T12:00:00Z',
                       growthEntries=[{'id': 'G', 'date': '2026-11-15T10:00:00Z', 'health': 'struggling'}])
    excellent = plant(name='Excellent', room='Casa', lastWatered='2026-11-17T12:00:00Z',
                      growthEntries=[{'id': 'G', 'date': '2026-11-15T10:00:00Z', 'health': 'excellent'}])
    unrated = plant(name='Unrated', room='Casa', lastWatered='2026-11-17T12:00:00Z')
    result = analytics.summary([unrated, excellent, struggling, sick], 'Europe/Rome', 30, AT)
    assert result['health'] == {'excellent': 1, 'good': 0, 'struggling': 1, 'sick': 1, 'unrated': 1}
    assert [item['name'] for item in result['plantsAtRisk']] == ['Sick', 'Struggling']
    assert result['plantsAtRisk'][0]['reason'] == {'code': 'health', 'health': 'sick'}


def test_plants_at_risk_is_limited_to_eight():
    plants = [plant(name=f'P{index}', lastWatered='2026-10-01T12:00:00Z') for index in range(12)]
    assert len(analytics.summary(plants, 'Europe/Rome', 30, AT)['plantsAtRisk']) == 8


def test_health_counts_ignore_photos_like_the_native_analytics():
    p = plant(healthPhotoSessions=[{'id': 'S', 'date': '2026-11-15T10:00:00Z', 'health': 'sick'}])
    assert analytics.summary([p], 'Europe/Rome', 30, AT)['health'] == {
        'excellent': 0, 'good': 0, 'struggling': 0, 'sick': 0, 'unrated': 1,
    }


def test_unknown_period_is_rejected():
    with pytest.raises(ValueError):
        analytics.summary([], 'Europe/Rome', 10, AT)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'store', Store(tmp_path))
    monkeypatch.setattr(main.settings, 'ingress', False)
    monkeypatch.setattr(main.settings, 'token', '')
    monkeypatch.setattr(main.settings, 'zone', 'Europe/Rome')
    return TestClient(main.app, headers={'X-PlantCare-Request': '1'})


def test_analytics_endpoint_contract(client):
    p = Plant(name='Ficus', room='Casa', acquiredOn='2026-01-01T12:00:00Z',
              lastWatered='2026-11-01T12:00:00Z').model_dump()
    main.store.put('plants', p)
    response = client.get('/api/analytics?days=90')
    assert response.status_code == 200
    data = response.json()
    assert data['days'] == 90 and data['plantCount'] == 1
    assert 'history' not in data
    assert data['plantsAtRisk'][0]['id'] == p['id']
    assert client.get('/api/analytics?days=10').status_code == 422


def test_plant_view_exposes_health_without_removing_history(client, monkeypatch):
    from plantcare_web.backend import health
    monkeypatch.setattr(health, 'now', lambda: AT)
    p = Plant(name='Ficus', room='Casa', acquiredOn='2026-01-01T12:00:00Z',
              lastWatered='2026-11-17T12:00:00Z').model_dump()
    p['history'] = [event(date='2026-11-16T12:00:00Z')]
    main.store.put('plants', p)
    view = client.get('/api/plants/' + p['id']).json()
    assert view['_health']['score'] == 92
    assert view['_health']['labelCode'] == 'health.label.good'
    summary = client.get('/api/plants?summary=true').json()[0]
    assert summary['_health'] == view['_health']
    assert summary['history'] == []


def test_timeline_merges_events_and_measurements_newest_first(client):
    p = Plant(name='Ficus', room='Casa', acquiredOn='2026-01-01T12:00:00Z',
              lastWatered='2026-11-01T12:00:00Z').model_dump()
    p['history'] = [
        event(date='2026-11-16T10:00:00Z', note='Annaffiata'),
        event(kind='prune', date='2026-11-12T10:00:00Z'),
        event(kind='fertilize', date='2026-11-10T10:00:00Z', deletedAt='2026-11-10T11:00:00Z'),
    ]
    main.store.put('plants', p)
    assert client.post(f"/api/plants/{p['id']}/measurements", json={
        'kind': 'moisture', 'value': 42.5, 'unit': '%', 'date': '2026-11-15T09:00:00Z',
    }).status_code == 201
    items = client.get(f"/api/plants/{p['id']}/timeline?limit=8").json()['items']
    assert [item['type'] for item in items] == ['event', 'measurement', 'event']
    assert items[0]['kind'] == 'Annaffia' and items[0]['note'] == 'Annaffiata'
    assert items[1]['kind'] == 'moisture' and items[1]['value'] == 42.5
    assert items[2]['kind'] == 'Pota'
    assert len(client.get(f"/api/plants/{p['id']}/timeline?limit=1").json()['items']) == 1
    assert client.get(f"/api/plants/{p['id']}/timeline?limit=0").status_code == 422


def test_timeline_removes_native_measurement_duplicates(client):
    p = Plant(name='Ficus', room='Casa', acquiredOn='2026-01-01T12:00:00Z').model_dump()
    main.store.put('plants', p)
    client.post(f"/api/plants/{p['id']}/measurements", json={
        'kind': 'moisture', 'value': 42.5, 'unit': '%', 'date': '2026-11-15T09:00:00Z',
    })
    main.store.set_state('native-measurements', [{
        'id': 'native-1', 'plantID': p['id'], 'kind': 'moisture', 'value': 42.5,
        'unit': '%', 'date': '2026-11-15T09:00:00Z', 'source': 'smartphoneEstimated',
    }])
    items = client.get(f"/api/plants/{p['id']}/timeline").json()['items']
    assert len([item for item in items if item['type'] == 'measurement']) == 1
