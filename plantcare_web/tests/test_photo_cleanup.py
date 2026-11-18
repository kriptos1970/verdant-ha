import os
import time
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.storage import Store

HEAD={'X-PlantCare-Request':'1'}
REFERENCED='a'*64+'.jpg'
ORPHAN='b'*64+'.jpg'
RECENT='c'*64+'.jpg'

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path/'data',tmp_path/'shared'/'photos'))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers=HEAD)

def photo(client,name,age=7200):
    path=main.store.photos/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b'photo')
    stamp=time.time()-age
    os.utime(path,(stamp,stamp))
    return path

def create(client):
    response=client.post('/api/plants',json=dict(name='Ficus',species='Ficus elastica',room='Salotto',wateringInterval=7,lastWatered='2026-11-10T12:00:00Z',acquiredOn='2026-01-01T12:00:00Z',photoPath=REFERENCED))
    assert response.status_code==201,response.text
    return response.json()

def test_orphans_exclude_references_and_recent_uploads(client):
    create(client)
    photo(client,REFERENCED)
    photo(client,ORPHAN)
    photo(client,RECENT,age=60)
    report=client.get('/api/photos/orphans').json()
    names={item['name'] for item in report['files']}
    assert names=={ORPHAN,RECENT}
    assert report['count']==2 and report['deletable']==1 and report['recent']==1

def test_cleanup_deletes_only_requested_old_orphans(client):
    create(client)
    photo(client,REFERENCED)
    old=photo(client,ORPHAN)
    recent=photo(client,RECENT,age=60)
    (main.store.thumbnails/ORPHAN).write_bytes(b'thumb')
    response=client.post('/api/photos/cleanup',json={'names':[ORPHAN,REFERENCED,RECENT,'bad-name']})
    assert response.status_code==200,response.text
    body=response.json()
    assert body['count']==1
    assert not old.exists()
    assert not (main.store.thumbnails/ORPHAN).exists()
    assert (main.store.photos/REFERENCED).is_file()
    assert recent.is_file()

def test_trashed_plants_keep_their_photos_until_purged(client):
    plant=create(client)
    photo(client,REFERENCED)
    assert client.delete(f"/api/plants/{plant['id']}?version={plant['_version']}").status_code==204
    report=client.get('/api/photos/orphans').json()
    assert REFERENCED not in {item['name'] for item in report['files']}
