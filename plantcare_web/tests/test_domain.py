"""Behavior fixtures derived from Models.swift/CarePlanLearner.swift, not UI internals."""
from datetime import datetime, timezone
from uuid import uuid4
from plantcare_web.backend.domain import schedule, learning, accepted_water, minimum_water, stable_water
from plantcare_web.backend.care_kinds import canonical_kind

def plant(**values):
    return dict(id=str(uuid4()).upper(),name='Monstera',species='Monstera deliciosa',room='Salotto',category='Tropicale',light='Luce indiretta',wateringInterval=7,fertilizingInterval=21,acquiredOn='2026-01-01T12:00:00Z',lastWatered='2026-11-01T12:00:00Z',history=[],**values)

def action(p,kind): return next(x for x in schedule(p,'Europe/Rome',datetime(2026,11,8,tzinfo=timezone.utc)) if x['kind']==canonical_kind(kind))

def test_fertilizer_aligns_with_first_water_on_or_after_requested():
    p=plant();p['lastFertilized']='2026-10-20T12:00:00Z'
    assert action(p,'Concima')['dueDate']=='2026-11-14T23:00:00Z'

def test_deleted_water_is_authoritative_does_not_resurrect_legacy_date():
    p=plant();p['history']=[{'id':'e','kind':'Annaffia','date':'2026-11-05T12:00:00Z','deletedAt':'2026-11-06T12:00:00Z','status':'completed'}]
    assert action(p,'Annaffia')['dueDate']=='2026-01-08T12:00:00Z'

def test_latest_completed_and_postponements_reduce_in_date_order():
    p=plant();p['history']=[{'kind':'Annaffia','date':'2026-11-02T12:00:00Z','status':'completed'},{'kind':'Annaffia','date':'2026-11-04T12:00:00Z','status':'postponed','postponedUntil':'2026-11-20T12:00:00Z'}]
    assert action(p,'Annaffia')['dueDate']=='2026-11-20T12:00:00Z'
    p['history'].append({'kind':'Annaffia','date':'2026-11-05T12:00:00Z','status':'completed'})
    assert action(p,'Annaffia')['dueDate']=='2026-11-12T12:00:00Z'

def test_calendar_arithmetic_crosses_dst_without_shifting_local_hour():
    p=plant();p['lastWatered']='2026-10-24T10:00:00Z';p['wateringInterval']=2
    assert action(p,'Annaffia')['dueDate']=='2026-10-26T11:00:00Z'

def test_water_override_only_postpones():
    p=plant();p['nextWateringOverride']='2026-11-02T00:00:00Z'
    assert action(p,'Annaffia')['dueDate']=='2026-11-08T12:00:00Z'

def test_learning_requires_three_dates_and_moves_only_one_day():
    p=plant()
    p['history']=[{'kind':'Annaffia','date':f'2026-11-{d:02}T12:00:00Z','status':'completed'} for d in [1,10]]
    assert learning(p,7,'Europe/Rome') is None
    p['history'].append({'kind':'Annaffia','date':'2026-11-19T12:00:00Z','status':'completed'})
    result=learning(p,7,'Europe/Rome')
    assert result['learnedIntervalDays']==8
    assert result['observedIntervalDays']==9
    assert result['confidence']==2/6

def test_learning_uses_honoured_postponements_for_a_two_day_step():
    p=plant();p['wateringInterval']=7
    p['history']=[
        {'kind':'Annaffia','date':'2026-11-01T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-10T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-20T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-03T12:00:00Z','status':'postponed','postponedUntil':'2026-11-06T12:00:00Z'},
        {'kind':'Annaffia','date':'2026-11-12T12:00:00Z','status':'postponed','postponedUntil':'2026-11-15T12:00:00Z'},
    ]
    result=learning(p,7,'Europe/Rome')
    assert result['observedIntervalDays']==10
    assert result['honoredPostponements']==2
    assert result['adaptiveStepDays']==2
    assert result['learnedIntervalDays']==9


def test_learning_uses_early_postponements_for_a_two_day_step():
    p=plant();p['wateringInterval']=7
    p['history']=[
        {'kind':'Annaffia','date':'2026-11-01T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-05T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-09T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-02T12:00:00Z','status':'postponed','postponedUntil':'2026-11-10T12:00:00Z'},
        {'kind':'Annaffia','date':'2026-11-06T12:00:00Z','status':'postponed','postponedUntil':'2026-11-12T12:00:00Z'},
    ]
    result=learning(p,7,'Europe/Rome')
    assert result['earlyPostponements']==2
    assert result['adaptiveStepDays']==2
    assert result['learnedIntervalDays']==5


def test_learning_does_not_accelerate_for_late_gaps_without_postponement():
    p=plant();p['wateringInterval']=7
    p['history']=[
        {'kind':'Annaffia','date':'2026-11-01T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-11T12:00:00Z','status':'completed'},
        {'kind':'Annaffia','date':'2026-11-21T12:00:00Z','status':'completed'},
    ]
    result=learning(p,7,'Europe/Rome')
    assert result['lateGapsWithoutPostponement']==2
    assert result['adaptiveStepDays']==1
    assert result['learnedIntervalDays']==8


def test_succulent_safety_has_priority_over_ai_25_percent():
    p=plant();p['category']='Succulenta';p['light']='Luce bassa'
    assert minimum_water(p)==30
    assert accepted_water(1,7,30)==30

def test_stable_baseline_does_not_compound_yesterdays_ai():
    p=plant();p['adaptivePlan']={'verdantWateringDays':12};p['wateringInterval']=15;p['careFrequencyPreference']='Frequente'
    assert stable_water(p)==10
    assert accepted_water(100,stable_water(p),1)==12
