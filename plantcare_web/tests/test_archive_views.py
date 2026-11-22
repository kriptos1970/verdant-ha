from copy import deepcopy
import json
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.models import Plant
from plantcare_web.backend.storage import Store

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    monkeypatch.setattr(main.settings,'zone','Europe/Rome')
    return TestClient(main.app,headers={'X-PlantCare-Request':'1'})

def seed(name='Ficus',room='Casa',events=None):
    p=Plant(name=name,room=room,acquiredOn='2025-01-01T12:00:00Z',lastWatered='2025-01-01T12:00:00Z').model_dump()
    p['history']=events or []
    main.store.put('plants',p)
    return p

def event(day='2026-11-16T10:00:00Z',**extra):
    return dict(id=str(uuid4()).upper(),kind='Annaffia',date=day,status='completed',**extra)

def test_summary_retains_schedule_counts_and_full_record(client):
    events=[event(),event(deletedAt='2026-11-16T11:00:00Z')]
    postponed=event();postponed.update(status='postponed',postponedUntil='2026-11-20T12:00:00Z');events.append(postponed)
    p=seed(events=events)
    p['growthEntries']=[{'id':'growth','note':'Non perdere','photoPaths':['a.jpg']}]
    p['healthPhotoSessions']=[{'id':'health','photos':[{'path':'b.jpg'}]}]
    main.store.put('plants',p,1)
    before=deepcopy(main.store.get('plants',p['id']))
    full=client.get('/api/plants').json()[0]
    summary=client.get('/api/plants?summary=true').json()[0]
    assert summary['_summary'] and summary['_careCount']==1
    assert summary['history']==summary['growthEntries']==summary['healthPhotoSessions']==[]
    for field in ['_schedule','_actions','_treatments','_learning','_version']:
        assert summary[field]==full[field]
    assert client.get('/api/plants/'+p['id']).json()==full
    assert client.put('/api/plants/'+p['id']+'?version=2',json=summary).status_code==422
    assert main.store.get('plants',p['id'])==before
    assert client.get('/api/plants/absent').status_code==404

def test_history_stable_paging_ties_and_filters(client):
    a=seed(events=[event(note='a',deletedAt='') for _ in range(63)])
    b=seed('Menta','Balcone')
    b['history']=[{**event(), 'kind':'Pota'} for _ in range(45)]+[event(deletedAt='2026-11-17T10:00:00Z')]
    main.store.put('plants',b,1)
    before=main.store.list('plants')
    pages=[client.get('/api/history',params={'page':n}).json() for n in [1,2,3]]
    assert [len(p['items']) for p in pages]==[50,50,8]
    assert pages[0]['total']==108 and pages[0]['hasNextPage'] and not pages[2]['hasNextPage']
    ids=[r['event']['id'] for p in pages for r in p['items']]
    assert len(set(ids))==108
    assert client.get('/api/history?room=Balcone&kind=Pota').json()['total']==45
    assert client.get('/api/history',params={'plant_id':a['id']}).json()['total']==63
    assert client.get('/api/history?room=Assente').json()['items']==[]
    assert pages[0]['kinds']==['Annaffia','Pota']
    assert main.store.list('plants')==before

def test_dates_use_local_calendar_across_dst(client):
    # Rome's 25 October 2026 is a 25-hour local day.
    seed(events=[event(day=t) for t in ['2026-10-24T21:59:59Z','2026-10-24T22:00:00Z','2026-10-25T22:59:59Z','2026-10-25T23:00:00Z']])
    rows=client.get('/api/history?from_day=2026-10-25&to_day=2026-10-25').json()
    assert rows['total']==2
    assert {r['event']['date'] for r in rows['items']}=={'2026-10-24T22:00:00Z','2026-10-25T22:59:59Z'}


def test_existing_database_backfills_history_without_rewriting_payload(client, tmp_path, monkeypatch):
    path = tmp_path / 'legacy'
    path.mkdir()
    plant = Plant(name='Legacy', room='Studio').model_dump()
    entry = event(day='2026-10-25T00:00:00+02:00', note='Legacy text')
    plant['history'] = [entry, event(deletedAt='2026-11-18T12:00:00Z')]
    payload = json.dumps(plant)
    with sqlite3.connect(path / 'plantcare.sqlite') as db:
        db.execute('CREATE TABLE entities(collection TEXT, id TEXT, payload TEXT, version INTEGER, PRIMARY KEY(collection,id))')
        db.execute('INSERT INTO entities VALUES (?,?,?,?)', ('plants', plant['id'], payload, 7))
    for _ in range(2):
        store = Store(path)
        monkeypatch.setattr(main, 'store', store)
        history = client.get('/api/history', params={'kind': 'water', 'room': 'Studio', 'from_day': '2026-10-25'}).json()
        assert history['total'] == 1
        assert history['items'][0]['event'] == entry
        assert history['items'][0]['version'] == 7
        with store.connection() as db:
            assert db.execute('SELECT payload FROM entities').fetchone()[0] == payload


def test_history_index_tracks_edits_and_rollbacks(client):
    original = event(note='Before')
    plant = seed(events=[original])
    plant['name'] = 'Renamed'
    main.store.put('plants', plant, 1)
    first = client.get('/api/history').json()['items'][0]
    assert (first['plantName'], first['version']) == ('Renamed', 2)
    plant['room'] = 'Studio'
    main.store.put('plants', plant, 2)
    assert client.get('/api/history', params={'room': 'Casa'}).json()['total'] == 0
    assert client.get('/api/history', params={'room': 'Studio'}).json()['total'] == 1

    edited = {**original, 'kind': 'Pota', 'date': '2026-12-01T12:00:00Z'}
    plant['history'] = [edited]
    with pytest.raises(RuntimeError):
        with main.store.connection() as db:
            main.store.put('plants', plant, 3, db)
            raise RuntimeError('Abort the transaction')
    assert client.get('/api/history', params={'kind': 'Pota'}).json()['total'] == 0
    assert client.get('/api/history', params={'kind': 'Annaffia'}).json()['total'] == 1
    main.store.put('plants', plant, 3)
    assert client.get('/api/history').json()['items'][0]['event'] == edited
    plant['history'][0]['deletedAt'] = '2026-12-02T12:00:00Z'
    main.store.put('plants', plant, 4)
    assert client.get('/api/history').json()['total'] == 0


def test_history_index_replaces_events_on_backup_restore(client):
    saved = event(note='Saved')
    plant = seed(events=[saved])
    backup = client.get('/api/backup').content
    current = {**event(note='Current'), 'kind': 'Pota'}
    plant['history'] = [current]
    main.store.put('plants', plant, 1)
    seed(name='Other', events=[event()])
    assert client.get('/api/history').json()['total'] == 2
    response = client.post('/api/import?replace=true', files={'file': ('archive.zip', backup)})
    assert response.status_code == 200, response.text
    history = client.get('/api/history').json()
    assert history['total'] == 1
    assert history['kinds'] == ['Annaffia']
    assert history['items'][0]['event']['id'] == saved['id']


def test_hard_delete_removes_index_rows(client):
    plant = seed(events=[event()])
    main.store.delete('plants', plant['id'], 1)
    assert client.get('/api/history').json()['total'] == 0

@pytest.mark.parametrize('params',[{'page':0},{'limit':101},{'limit':0},{'from_day':'bad'},{'from_day':'2026-11-20','to_day':'2026-11-01'}])
def test_invalid_history_pagination_and_dates(client,params):
    assert client.get('/api/history',params=params).status_code==422
