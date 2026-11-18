import json
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.storage import Store

HEAD={'X-PlantCare-Request':'1'}

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path/'data',tmp_path/'shared'/'photos'))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers=HEAD)

def create(client,**extra):
    data={'name':'Monstera','species':'Monstera deliciosa','room':'Salotto','wateringInterval':7,'lastWatered':'2026-11-01T12:00:00Z','acquiredOn':'2026-01-01T12:00:00Z',**extra}
    response=client.post('/api/plants',json=data)
    assert response.status_code==201,response.text
    return response.json()

def test_deleted_plant_leaves_the_archive_but_stays_in_the_trash(client):
    p=create(client)
    assert client.get('/api/plants').json()
    deleted=client.delete(f"/api/plants/{p['id']}?version={p['_version']}")
    assert deleted.status_code==204,deleted.text
    assert client.get('/api/plants').json()==[]
    assert client.get(f"/api/plants/{p['id']}").status_code==404
    assert client.get('/api/schedule').json()==[]
    assert client.get('/api/analytics').json()['plantCount']==0
    trash=client.get('/api/trash').json()
    assert trash['retentionDays']==30
    assert [(i['name'],i['daysLeft']) for i in trash['items']]==[('Monstera',30)]
    assert trash['items'][0]['_version']==p['_version']+1

def test_restore_returns_the_plant_with_a_new_version(client):
    p=create(client)
    assert client.delete(f"/api/plants/{p['id']}?version={p['_version']}").status_code==204
    item=client.get('/api/trash').json()['items'][0]
    stale=client.post(f"/api/trash/{p['id']}/restore?version={p['_version']}")
    assert stale.status_code==409
    restored=client.post(f"/api/trash/{p['id']}/restore?version={item['_version']}")
    assert restored.status_code==200,restored.text
    body=restored.json()
    assert body['name']=='Monstera'
    assert body['_version']==item['_version']+1
    assert client.get('/api/trash').json()['items']==[]
    assert client.get(f"/api/plants/{p['id']}").status_code==200
    assert client.get('/api/schedule').json()

def test_permanent_delete_removes_the_plant(client):
    p=create(client)
    client.delete(f"/api/plants/{p['id']}?version={p['_version']}")
    item=client.get('/api/trash').json()['items'][0]
    assert client.delete(f"/api/trash/{p['id']}?version={p['_version']}").status_code==409
    assert client.delete(f"/api/trash/{p['id']}?version={item['_version']}").status_code==204
    assert client.get('/api/trash').json()['items']==[]
    assert client.post(f"/api/trash/{p['id']}/restore?version={item['_version']+1}").status_code==404

def test_empty_trash_and_expired_plants_are_purged(client):
    first=create(client,name='Ficus')
    second=create(client,name='Pothos')
    for plant in (first,second):
        assert client.delete(f"/api/plants/{plant['id']}?version={plant['_version']}").status_code==204
    with main.store.connection() as db:
        db.execute("UPDATE entities SET deleted_at='2026-01-01T00:00:00Z' WHERE id=?",(first['id'],))
    items=client.get('/api/trash').json()['items']
    assert [i['name'] for i in items]==['Pothos']
    assert client.delete('/api/trash').status_code==204
    assert client.get('/api/trash').json()['items']==[]

def test_export_does_not_include_trashed_plants(client):
    keep=create(client,name='Ficus')
    gone=create(client,name='Pothos')
    client.delete(f"/api/plants/{gone['id']}?version={gone['_version']}")
    exported=main.store.export()
    import base64
    payload=json.loads(base64.b64decode(exported['payload']))
    assert [p['name'] for p in payload['collections']['plants']]==['Ficus']
    assert keep['name'] in [p['name'] for p in payload['collections']['plants']]
