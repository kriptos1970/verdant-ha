from datetime import datetime, timezone
import pytest
from plantcare_web.backend.health import assess, latest_observation
from plantcare_web.backend.care_kinds import legacy_plant

AT = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)


def plant(**values):
    result = dict(
        id='11111111-1111-4111-8111-111111111111', name='Test', species='Test species',
        room='Studio', category='Tropicale', light='Luce indiretta',
        wateringInterval=7, lastWatered='2026-11-17T12:00:00Z',
        acquiredOn='2026-11-17T12:00:00Z', history=[],
    )
    result.update(values)
    return result


def health(**values):
    return assess(plant(**values), 'Europe/Rome', at=AT)


def test_untouched_plant_matches_native_baseline():
    result = health()
    assert result['score'] == 92
    assert result['labelCode'] == 'health.label.good'
    assert result['tipCode'] == 'health.tip.allGood'
    assert result['tipParams'] == {}


def test_bright_indirect_readings_do_not_lower_the_score():
    baseline = health()
    measured = health(lightMeasurements=[
        {'date': f'2026-11-{day}T13:00:00Z', 'estimatedLux': 24000}
        for day in (16, 15, 14)
    ])
    assert measured['score'] == baseline['score']
    assert measured['tipCode'] == 'health.tip.allGood'


def test_very_low_light_penalty_requires_three_readings():
    two = health(lightMeasurements=[
        {'date': '2026-11-16T13:00:00Z', 'estimatedLux': 200},
        {'date': '2026-11-15T13:00:00Z', 'estimatedLux': 200},
    ])
    three = health(lightMeasurements=[
        {'date': f'2026-11-{day}T13:00:00Z', 'estimatedLux': 200}
        for day in (16, 15, 14)
    ])
    assert two['score'] == 92
    assert three['score'] == 88
    assert three['tipCode'] == 'health.tip.light'


def test_recent_observation_changes_score_and_label():
    excellent = health(growthEntries=[{'date': '2026-11-17T10:00:00Z', 'health': 'excellent'}])
    struggling = health(growthEntries=[{'date': '2026-11-17T10:00:00Z', 'health': 'struggling'}])
    assert excellent['score'] == 98 and excellent['labelCode'] == 'health.label.good'
    assert struggling['score'] == 72 and struggling['labelCode'] == 'health.label.watch'
    assert struggling['tipCode'] == 'health.tip.observation'
    assert struggling['tipParams'] == {'health': 'struggling'}


def test_observation_weight_fades_with_age():
    fresh = health(growthEntries=[{'date': '2026-11-17T10:00:00Z', 'health': 'struggling'}])
    old = health(growthEntries=[{'date': '2026-09-01T10:00:00Z', 'health': 'struggling'}])
    expired = health(growthEntries=[{'date': '2026-05-01T10:00:00Z', 'health': 'struggling'}])
    assert fresh['score'] == 72
    assert old['score'] == 82
    assert expired['score'] == 92


def test_overdue_watering_lowers_the_score_materially():
    overdue = health(lastWatered='2026-11-07T12:00:00Z')
    assert overdue['score'] == 68
    assert overdue['labelCode'] == 'health.label.attention'
    assert overdue['tipCode'] == 'health.tip.wateringLate.other'
    assert overdue['tipParams'] == {'count': 3}


def test_watering_penalty_is_capped():
    very_late = health(lastWatered='2026-09-01T12:00:00Z')
    assert very_late['score'] == 62


def test_missing_routine_checks_reduce_the_score():
    unchecked = health(acquiredOn='2026-10-18T12:00:00Z', inspectionInterval=7, progressInterval=14)
    assert unchecked['score'] == 74
    assert unchecked['labelCode'] == 'health.label.watch'
    assert unchecked['tipCode'] == 'health.tip.inspectionLate.other'
    assert unchecked['tipParams'] == {'count': 23}


def test_postponed_routine_does_not_remain_in_the_overview():
    postponed = health(
        acquiredOn='2026-10-18T12:00:00Z', inspectionInterval=7,
        history=[{'id': 'P', 'kind': 'inspect', 'date': '2026-11-17T09:00:00Z',
                  'status': 'postponed', 'postponedUntil': '2026-11-20T12:00:00Z'}],
    )
    assert postponed['score'] == 92
    assert postponed['labelCode'] == 'health.label.good'
    assert 'in ritardo' not in postponed['tipFallback']


def test_disabled_interval_is_not_restored_by_the_adaptive_plan():
    disabled = health(acquiredOn='2026-10-18T12:00:00Z', inspectionInterval=None,
                      adaptivePlan={'inspectionDays': 7})
    assert disabled['score'] == 92


def test_photo_sessions_count_as_the_latest_observation():
    result = health(healthPhotoSessions=[
        {'id': 'S', 'date': '2026-11-17T09:00:00Z', 'health': 'sick'},
    ])
    assert result['score'] == 57
    assert result['labelCode'] == 'health.label.attention'


def test_latest_observation_includes_photos_and_events():
    p = plant(
        growthEntries=[{'id': 'G', 'date': '2026-11-10T10:00:00Z', 'health': 'good'}],
        healthPhotoSessions=[{'id': 'S', 'date': '2026-11-15T10:00:00Z', 'health': 'excellent'}],
        history=[{'id': 'E', 'kind': 'inspect', 'date': '2026-11-12T10:00:00Z',
                  'status': 'completed', 'health': 'struggling'}],
    )
    assert latest_observation(p) == (datetime(2026, 11, 15, 10, tzinfo=timezone.utc), 'excellent')


def test_health_codes_survive_legacy_projection():
    p = plant(history=[{'id': 'E', 'kind': 'inspect', 'date': '2026-11-17T10:00:00Z',
                        'status': 'completed', 'health': 'In difficoltà'}])
    result = assess(legacy_plant(p), 'Europe/Rome', at=AT)
    assert result['score'] == 72
    assert result['labelCode'] == 'health.label.watch'


def test_english_fallback_is_available_for_non_ui_clients():
    result = assess(plant(lastWatered='2026-11-07T12:00:00Z'), 'Europe/Rome', at=AT, language='en')
    assert result['labelFallback'] == 'Needs attention'
    assert result['tipFallback'] == 'Watering 3 days late.'


def test_invalid_timezone_is_rejected():
    with pytest.raises(Exception):
        assess(plant(), 'Not/AZone', at=AT)
