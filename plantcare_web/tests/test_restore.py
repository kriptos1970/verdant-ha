import io
import json
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from plantcare_web.backend import main
from plantcare_web.backend.storage import Conflict, Store

HEAD={'X-PlantCare-Request':'1'}

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path/'data',tmp_path/'shared'/'photos'))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers=HEAD)

def create(client,name='Monstera',**extra):
    data={'name':name,'species':'Monstera deliciosa','room':'Salotto','wateringInterval':7,'lastWatered':'2026-11-01T12:00:00Z','acquiredOn':'2026-01-01T12:00:00Z',**extra}
    response=client.post('/api/plants',json=data)
    assert response.status_code==201,response.text
    return response.json()

def photo(client):
    image=Image.new('RGB',(40,30),'green');data=io.BytesIO();image.save(data,format='PNG')
    response=client.post('/api/photos',files={'file':('x.png',data.getvalue())})
    assert response.status_code==201,response.text
    return response.json()['path']

def snapshot_plants(store):
    path=store.root/'restore-snapshot.sqlite'
    assert path.is_file()
    with sqlite3.connect(path) as db:
        return {row[0] for row in db.execute("SELECT id FROM entities WHERE collection='plants'")}

def test_preview_reports_the_archive_that_would_be_replaced(client):
    create(client,'Ficus')
    exported=client.get('/api/backup')
    response=client.post('/api/import/preview',files={'file':('web.zip',exported.content)})
    assert response.status_code==200,response.text
    body=response.json()
    assert body['web'] is True
    assert body['current']=={'plants':1,'trashed':0,'entities':1,'measurements':0}
    assert client.get('/api/plants').json()[0]['name']=='Ficus'

def test_zip_restore_replaces_the_archive_only_with_the_replace_flag(client):
    path=photo(client)
    original=create(client,'Ficus',photoPath=path)
    client.post(f"/api/plants/{original['id']}/measurements",json={'kind':'illuminance','value':1200,'unit':'lx'})
    backup=client.get('/api/backup').content
    later=create(client,'Pothos')

    refused=client.post('/api/import',files={'file':('web.zip',backup)})
    assert refused.status_code==409,refused.text
    assert {p['name'] for p in client.get('/api/plants').json()}=={'Ficus','Pothos'}
    assert not (main.store.root/'restore-snapshot.sqlite').exists()

    restored=client.post('/api/import?replace=true',files={'file':('web.zip',backup)})
    assert restored.status_code==200,restored.text
    assert restored.json()['replaced'] is True
    plants=client.get('/api/plants').json()
    assert [p['id'] for p in plants]==[original['id']]
    assert later['id'] not in {p['id'] for p in plants}
    assert client.get(f"/api/plants/{original['id']}/measurements").json()[0]['value']==1200
    # Photos are content-addressed and never deleted by a restore.
    assert (main.store.photos/path).exists()
    assert snapshot_plants(main.store)=={original['id'],later['id']}

def test_restoring_the_same_zip_again_is_allowed(client):
    create(client,'Ficus')
    backup=client.get('/api/backup').content
    first=client.post('/api/import?replace=true',files={'file':('web.zip',backup)})
    assert first.status_code==200,first.text
    second=client.post('/api/import?replace=true',files={'file':('web.zip',backup)})
    assert second.status_code==200,second.text
    assert second.json()['replaced'] is True
    assert len(client.get('/api/plants').json())==1

def test_native_backups_still_require_an_empty_archive(client):
    import base64,hashlib
    create(client,'Ficus')
    payload=json.dumps({'plants':[{'id':str(uuid4()),'name':'Pothos'}],'fertilizers':[],'photos':{}}).encode()
    envelope={'version':3,'checksum':hashlib.sha256(payload).hexdigest(),'payload':base64.b64encode(payload).decode()}
    response=client.post('/api/import?replace=true',files={'file':('native.json',json.dumps(envelope).encode())})
    assert response.status_code==409,response.text
    assert [p['name'] for p in client.get('/api/plants').json()]==['Ficus']

def test_failed_restore_keeps_the_previous_archive(client,monkeypatch):
    create(client,'Ficus')
    create(client,'Aloe')
    backup=client.get('/api/backup').content
    later=create(client,'Pothos')
    store=main.store
    original_put=Store.put
    calls={'n':0}
    def flaky(self,collection,payload,expected=None,db=None):
        calls['n']+=1
        if calls['n']>1: raise Conflict('Errore simulato')
        return original_put(self,collection,payload,expected,db)
    monkeypatch.setattr(store,'put',flaky.__get__(store,Store))
    failing=TestClient(main.app,headers=HEAD,raise_server_exceptions=False)
    response=failing.post('/api/import?replace=true',files={'file':('web.zip',backup)})
    assert response.status_code==409,response.text
    names={p['name'] for p in client.get('/api/plants').json()}
    assert names=={'Ficus','Aloe','Pothos'}
    assert later['id'] in {p['id'] for p in client.get('/api/plants').json()}
    assert len(snapshot_plants(store))==3
