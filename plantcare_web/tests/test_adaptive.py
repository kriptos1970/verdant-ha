from copy import deepcopy
from datetime import timedelta
from uuid import uuid4
import asyncio
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main, adaptive, services
from plantcare_web.backend.care_engine import evaluate, dry_down, normalized_measurements
from plantcare_web.backend.storage import Store
from plantcare_web.backend.domain import parse, iso

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path))
    monkeypatch.setattr(main.settings,'ingress',False)
    return TestClient(main.app,headers={'X-PlantCare-Request':'1'})

def plant(client,**kw):
    r=client.post('/api/plants',json=dict(name='Monstera',species='Monstera deliciosa',family='Araceae',**kw))
    assert r.status_code==201,r.text
    return r.json()

def request(**kw):
    return dict(location=dict(name='Roma',latitude=42,longitude=12.5),placement='Interno luminoso',weatherEnabled=False,climate=dict(averageTemperature=22,relativeHumidity=55,precipitationNextWeek=0),**kw)

def test_preview_exact_apply_and_version_guard(client,monkeypatch):
    p=plant(client);path=f"/api/plants/{p['id']}/adaptive"
    async def forbidden(*a): raise AssertionError('Weather must be opt-in')
    monkeypatch.setattr(adaptive,'fetch_climate',forbidden)
    r=client.post(path+'/preview?version=1',json=request());assert r.status_code==200,r.text
    preview=r.json();assert main.store.get('plants',p['id'])[1]==1
    assert main.store.get('plants',p['id'])[0].get('adaptivePlan') is None
    r=client.post(path+f"/apply?version=1&previewID={preview['previewID']}");assert r.status_code==200,r.text
    result=r.json();assert result['adaptivePlan']==preview['plan']
    assert result['wateringInterval']==preview['plan']['wateringDays']
    assert result['carePlanMode']=='Intelligente'
    assert result['history'][-1]['kind']=='Aggiornamento piano'
    assert client.post(path+f"/apply?version=1&previewID={preview['previewID']}").status_code==409
    assert client.post(path+'/apply?version=2&previewID=wrong').status_code==409


def test_obsolete_preview_cannot_overwrite_user_edit(client):
    p=plant(client);path=f"/api/plants/{p['id']}"
    preview=client.post(path+'/adaptive/preview?version=1',json=request()).json()
    p['name']='Nome cambiato';assert client.put(path+'?version=1',json=p).status_code==200
    assert client.post(path+f"/adaptive/apply?version=1&previewID={preview['previewID']}").status_code==409
    assert main.store.get('plants',p['id'])[0]['name']=='Nome cambiato'


def test_expired_preview_and_validation(client,monkeypatch):
    p=plant(client);path=f"/api/plants/{p['id']}/adaptive"
    r=client.post(path+'/preview?version=1',json=request());preview=r.json()
    state=main.store.state('adaptive-preview-'+p['id']);state['createdAt']='2000-01-01T00:00:00Z';main.store.set_state('adaptive-preview-'+p['id'],state)
    assert client.post(path+f"/apply?version=1&previewID={preview['previewID']}").status_code==409
    data=request();data['location']['latitude']=91
    assert client.post(path+'/preview?version=1',json=data).status_code==422
    data=request();data['climate']=None
    assert client.post(path+'/preview?version=1',json=data).status_code==422
    for payload in [dict(kind='moisture',value=101,unit='%'),dict(kind='temperature',value=20,unit='%')]:
        assert client.post(f"/api/plants/{p['id']}/measurements",json=payload).status_code==422


def test_daily_refresh_opt_in_once_and_preserve_manual(client,monkeypatch):
    p=plant(client);base=main.store.get('plants',p['id'])[0]
    plan=adaptive.make_plan(base['species'],base['family'],'Interno luminoso',request()['location'],request()['climate'],parse('2025-07-01T12:00:00Z'))
    plan.update(weatherEnabled=False,revisionSource='Modifica manuale')
    base.update(carePlanMode='Intelligente',adaptivePlan=plan,wateringInterval=13,fertilizingInterval=52)
    main.store.put('plants',base,1)
    calls=[]
    async def climate(location):calls.append(location);return dict(averageTemperature=10,relativeHumidity=80,precipitationNextWeek=20)
    monkeypatch.setattr(adaptive,'fetch_climate',climate)
    asyncio.run(adaptive.refresh_all(main.store,main.settings));assert not calls
    base,version=main.store.get('plants',p['id']);base['adaptivePlan']['weatherEnabled']=True;main.store.put('plants',base,version)
    assert asyncio.run(adaptive.refresh_all(main.store,main.settings))['updated']==1
    actual,version=main.store.get('plants',p['id']);assert actual['wateringInterval']==13 and actual['fertilizingInterval']==52
    assert actual['adaptivePlan']['revisionSource']=='Modifica manuale'
    assert asyncio.run(adaptive.refresh_all(main.store,main.settings))['updated']==0
    assert len(calls)==1


def test_daily_refresh_failure_and_race_preserve_archive(client,monkeypatch):
    p=plant(client);base,version=main.store.get('plants',p['id']);plan=adaptive.make_plan('Monstera','Araceae','Interno luminoso',request()['location'],request()['climate'],parse('2025-07-01T12:00:00Z'));plan['weatherEnabled']=True
    base.update(carePlanMode='Intelligente',adaptivePlan=plan);main.store.put('plants',base,version)
    async def fail(location):raise RuntimeError('offline')
    monkeypatch.setattr(adaptive,'fetch_climate',fail)
    assert asyncio.run(adaptive.refresh_all(main.store,main.settings))['errors']==1
    assert main.store.get('plants',p['id'])[0]['adaptivePlan']==plan
    async def race(location):
        item,v=main.store.get('plants',p['id']);item['name']='Modifica concorrente';main.store.put('plants',item,v)
        return request()['climate']
    monkeypatch.setattr(adaptive,'fetch_climate',race)
    assert asyncio.run(adaptive.refresh_all(main.store,main.settings))['errors']==1
    assert main.store.get('plants',p['id'])[0]['name']=='Modifica concorrente'


def test_shadow_is_read_only_stale_moisture_and_fresh_high_moisture(client):
    p=plant(client);path=f"/api/plants/{p['id']}"
    before=main.store.get('plants',p['id'])
    r=client.get(path+'/care-engine');assert r.status_code==200,r.text
    assert len(r.json()['recommendations'])==5
    assert main.store.get('plants',p['id'])==before
    at=main.now()
    stale=dict(id=1,entity_id='sensor.old',kind='moisture',unit='%',value=90,measured_at=iso(at),source_at=iso(at-timedelta(days=2)))
    def water(rows):return next(r for r in evaluate(before[0],rows,at=at)['recommendations'] if r['domain']=='water')
    assert water([stale])['safetyGate']['code']=='water.no_reliable_moisture'
    stale['source_at']=iso(at)
    assert water([stale])['safetyGate']['code']=='water.moisture_high'
    assert water([stale])['action']=='waitToWater'


def test_poll_deduplicates_unchanged_observation(client,monkeypatch):
    p=plant(client)
    main.store.set_state('sensor-mappings',[dict(entityID='sensor.soil',plantID=p['id'])])
    async def readings(settings):return [dict(entityID='sensor.soil',kind='moisture',value=40,unit='%',updatedAt='2026-11-15T12:00:00Z')]
    monkeypatch.setattr(services,'sensors',readings)
    asyncio.run(services.poll(main.store,main.settings));asyncio.run(services.poll(main.store,main.settings))
    with main.store.connection() as db:assert db.execute('SELECT COUNT(*) FROM measurements').fetchone()[0]==1


def test_drydown_source_change_and_setup_invalidate_history():
    at=parse('2026-11-15T12:00:00Z');events=[];rows=[]
    for cycle in range(5):
        start=at-timedelta(days=16-cycle*4)
        events.append(dict(id=str(uuid4()),kind='Annaffia',status='completed',date=iso(start)))
        for hour,value in [(0,70),(12,58),(24,46)]:
            if start+timedelta(hours=hour)<=at+timedelta(days=1): rows.append(dict(id=str(uuid4()),kind='moisture',value=value,unit='%',date=iso(start+timedelta(hours=hour)),source='sensor',sourceIdentifier='soil',reliability=1))
    at+=timedelta(days=1)
    result=dry_down(normalized_measurements(rows),events,{},at,35)
    assert result['baseline']['comparableCycleCount']==4
    assert result['estimatedHoursToTarget']==11
    assert result['uncertaintyHours']==pytest.approx(1.65)
    changed=dry_down(normalized_measurements(rows),events,dict(recordedAt=iso(at-timedelta(hours=1))),at,35)
    assert changed['currentTrend'] is None and changed['baseline'] is None
    rows[-1]['sourceIdentifier']='replacement'
    assert dry_down(normalized_measurements(rows),events,{},at,35)['currentTrend'] is None


def test_smart_learning_after_water_is_prudent_and_idempotent(client):
    p=plant(client);item,v=main.store.get('plants',p['id'])
    item.update(carePlanMode='Intelligente',wateringInterval=7,adaptivePlan=dict(wateringDays=7,verdantWateringDays=7,revisionSource='Verdant'))
    item['history']=[dict(id=str(uuid4()),kind='Annaffia',status='completed',date=f'2026-11-{day:02}T12:00:00Z') for day in [1,6]]
    main.store.put('plants',item,v)
    event=dict(id=str(uuid4()),kind='Annaffia',date='2026-11-11T12:00:00Z')
    result=client.post(f"/api/plants/{p['id']}/events",json=event)
    assert result.status_code==200,result.text
    assert result.json()['wateringInterval']==6
    assert result.json()['adaptivePlan']['careLearning']['observedIntervalDays']==5
    replay=client.post(f"/api/plants/{p['id']}/events",json=event)
    assert replay.json()['_version']==result.json()['_version']
    assert replay.json()['wateringInterval']==6


def test_learning_updates_deferred_fertilizer_to_new_water_date(client):
    product=client.post('/api/fertilizers',json=dict(name='Concime liquido',form='Liquido')).json()
    p=plant(client,fertilizingInterval=7,lastFertilized='2026-11-01T12:00:00Z',fertilizerProductID=product['id'])
    item,v=main.store.get('plants',p['id'])
    item.update(carePlanMode='Intelligente',wateringInterval=7,adaptivePlan=dict(wateringDays=7,verdantWateringDays=7,revisionSource='Verdant'))
    item['history']=[dict(id=str(uuid4()),kind='Annaffia',status='completed',date=f'2026-11-{day:02}T12:00:00Z') for day in [1,6]]
    main.store.put('plants',item,v)
    r=client.post(f"/api/plants/{p['id']}/events",json=dict(kind='Annaffia',date='2026-11-11T12:00:00Z'))
    assert r.status_code==200,r.text
    assert r.json()['wateringInterval']==6
    deferred=next(e for e in r.json()['history'] if e['kind']=='Concima' and e['status']=='postponed')
    assert deferred['postponedUntil']=='2026-11-17T12:00:00Z'
