import base64
import hashlib
import io
import json
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from PIL import Image
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

def native_envelope(plants,photos=None):
    payload=json.dumps({'plants':plants,'fertilizers':[],'photos':photos or {}},ensure_ascii=False).encode()
    return {'version':3,'checksum':hashlib.sha256(payload).hexdigest(),'payload':base64.b64encode(payload).decode()}

def test_edit_concurrency_and_persistence(client):
    p=create(client)
    p['name']='Monstera grande'
    assert client.put(f"/api/plants/{p['id']}?version=1",json=p).status_code==200
    assert client.put(f"/api/plants/{p['id']}?version=1",json=p).status_code==409
    reopened=Store(main.store.root,main.store.photos)
    assert reopened.get('plants',p['id'])[0]['name']=='Monstera grande'

def test_mutations_require_same_origin_custom_header(client):
    other=TestClient(main.app)
    assert other.post('/api/plants',json={'name':'X'}).status_code==403

def test_duplicate_event_and_delete_recalculate(client):
    p=create(client)
    event={'id':str(uuid4()).upper(),'kind':'Annaffia','date':'2026-11-09T12:00:00Z'}
    path=f"/api/plants/{p['id']}/events"
    a=client.post(path,json=event);assert a.status_code==200,a.text
    assert client.post(path,json=event).json()['_version']==a.json()['_version']
    assert len(client.get('/api/plants').json()[0]['history'])==1
    deleted=client.delete(path+'/'+event['id']+'?version=2');assert deleted.status_code==200,deleted.text
    assert deleted.json()['_schedule'][0]['dueDate']=='2026-01-08T12:00:00Z'

def test_postponement_and_invalid_kind(client):
    p=create(client)
    path=f"/api/plants/{p['id']}/events"
    assert client.post(path,json={'kind':'Qualcosa'}).status_code==422
    assert client.post(path,json={'kind':'Annaffia','status':'postponed'}).status_code==422
    event={'kind':'Annaffia','status':'postponed','date':'2026-11-01T12:00:00Z','postponedUntil':'2026-12-01T12:00:00Z'}
    assert client.post(path,json=event).json()['_schedule'][0]['dueDate']=='2026-12-01T12:00:00Z'

def test_water_and_fertilizer_are_atomic(client):
    p=create(client,fertilizingInterval=7,lastFertilized='2026-11-01T12:00:00Z')
    event={'kind':'Annaffia','date':'2026-11-08T12:00:00Z','includingFertilizing':True}
    result=client.post(f"/api/plants/{p['id']}/events",json=event)
    assert result.status_code==200,result.text
    assert {e['kind'] for e in result.json()['history']}=={'Annaffia','Concima'}

def test_native_import_epoch_checksum_and_idempotence(client):
    p={'id':str(uuid4()).upper(),'name':'Pothos','species':'Epipremnum aureum','room':'Studio','lastWatered':0,'acquiredOn':0}
    envelope=native_envelope([p])
    data=json.dumps(envelope).encode()
    preview=client.post('/api/import/preview',files={'file':('backup.json',data,'application/json')})
    assert preview.status_code==200,preview.text
    assert preview.json()['counts']['plants']==1
    first=client.post('/api/import',files={'file':('backup.json',data)});assert first.status_code==200,first.text
    assert client.get('/api/plants').json()[0]['acquiredOn']=='2001-01-01T00:00:00Z'
    assert client.post('/api/import',files={'file':('backup.json',data)}).json()['alreadyImported'] is True
    envelope['checksum']='bad'
    assert client.post('/api/import',files={'file':('backup.json',json.dumps(envelope).encode())}).status_code==422
    assert len(client.get('/api/plants').json())==1

def test_import_on_nonempty_archive_fails_atomically(client):
    create(client)
    p={'id':str(uuid4()),'name':'X'}
    raw=json.dumps(native_envelope([p])).encode()
    assert client.post('/api/import',files={'file':('x.json',raw)}).status_code==409
    assert len(client.get('/api/plants').json())==1

def test_photo_storage_thumbnails_and_backup_roundtrip(client,tmp_path):
    image=Image.new('RGB',(1000,800),'green');buffer=io.BytesIO();image.save(buffer,format='PNG')
    uploaded=client.post('/api/photos',files={'file':('x.png',buffer.getvalue(),'image/png')})
    assert uploaded.status_code==201,uploaded.text
    path=uploaded.json()['path']
    assert (main.store.photos/path).exists()
    assert client.get('/api/photos/'+path+'?thumb=true').status_code==200
    assert (main.store.thumbnails/path).exists()
    create(client,photoPath=path)
    exported=client.get('/api/backup?format=json');assert exported.status_code==200,exported.text
    original=main.store
    main.store=Store(tmp_path/'restore')
    try:
        response=client.post('/api/import',files={'file':('web.json',exported.content)})
        assert response.status_code==200,response.text
        assert len(main.store.list('plants'))==1
        assert (main.store.photos/path).exists()
    finally: main.store=original

def test_external_photo_names_not_served(client):
    assert client.get('/api/photos/not-a-photo.jpg').status_code==404
    assert client.post('/api/photos',files={'file':('x.txt',b'not image')}).status_code==422

def test_secrets_never_exposed(client,monkeypatch):
    monkeypatch.setattr(main.settings,'options',{'ai_provider':'openai','openai_api_key':'very-secret','exposed_entities':[]})
    response=client.get('/api/settings')
    assert 'very-secret' not in response.text
    assert response.json()['aiConfigured'] is True

def test_stale_ai_proposal_rejected(client):
    p=create(client,carePlanMode='AI')
    main.store.put('proposals',{'id':p['id'],'plantID':p['id'],'expectedVersion':1,'proposedWateringDays':8,'proposedFertilizingDays':24,'reason':'Clima caldo','provider':'test'})
    p['notes']='Modificata dopo la proposta'
    client.put(f"/api/plants/{p['id']}?version=1",json=p)
    assert client.get('/api/proposals').json()[0]['stale'] is True
    assert client.post(f"/api/proposals/{p['id']}/apply").status_code==409
    assert client.get('/api/plants').json()[0]['wateringInterval']==7

def test_ingress_rejects_spoofed_headers(client,monkeypatch):
    monkeypatch.setattr(main.settings,'ingress',True)
    assert client.get('/health',headers={'X-Forwarded-For':'172.30.32.2'}).status_code==403

def test_measurements_and_unconfigured_ai(client):
    p=create(client)
    assert client.post(f"/api/plants/{p['id']}/measurements",json={'kind':'illuminance','value':1200,'unit':'lx'}).status_code==201
    assert len(client.get(f"/api/plants/{p['id']}/measurements").json())==1
    assert client.post(f"/api/plants/{p['id']}/advice",json={'question':'Come sta?'}).status_code==422

def test_zip_backup_streams_and_restores_photos(client,tmp_path):
    image=Image.new('RGB',(100,80),'green');data=io.BytesIO();image.save(data,format='PNG')
    path=client.post('/api/photos',files={'file':('x.png',data.getvalue())}).json()['path']
    original_plant=create(client,photoPath=path)
    backup=client.get('/api/backup')
    assert backup.status_code==200,backup.text
    assert backup.content[:2]==b'PK'
    import zipfile
    with zipfile.ZipFile(io.BytesIO(backup.content)) as z:
        assert 'photos/'+path in z.namelist()
        assert 'manifest.json' in z.namelist()
    original=main.store
    main.store=Store(tmp_path/'zip-restore')
    try:
        preview=client.post('/api/import/preview',files={'file':('web.zip',backup.content)})
        assert preview.status_code==200,preview.text
        assert preview.json()['missingPhotos']==[]
        restored=client.post('/api/import',files={'file':('web.zip',backup.content)})
        assert restored.status_code==200,restored.text
        assert main.store.get('plants',original_plant['id'])[0]['photoPath']==path
        assert (main.store.photos/path).exists()
    finally: main.store=original

def test_zip_rejects_path_traversal_without_mutating(client):
    import zipfile
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,'w') as z:
        z.writestr('data.json','{}')
        z.writestr('../evil','bad')
        z.writestr('manifest.json',json.dumps({'format':'plantcare-web-zip','version':1,'files':{'data.json':hashlib.sha256(b'{}').hexdigest(),'../evil':hashlib.sha256(b'bad').hexdigest()}}))
    response=client.post('/api/import',files={'file':('web.zip',raw.getvalue())})
    assert response.status_code==422,response.text
    assert main.store.list('plants')==[]
