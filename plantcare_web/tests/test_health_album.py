import io
from copy import deepcopy
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.storage import Store
from uuid import uuid4

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path));monkeypatch.setattr(main.settings,'ingress',False);monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers={'X-PlantCare-Request':'1'})

def setup(client):
    plant=client.post('/api/plants',json={'name':'Monstera'}).json()
    image=io.BytesIO();Image.new('RGB',(50,30),'green').save(image,'JPEG')
    path=client.post('/api/photos',files={'file':('test.jpg',image.getvalue(),'image/jpeg')}).json()['path']
    body={'id':str(uuid4()).upper(),'date':'2026-11-15T12:00:00Z','health':'Buona','note':'Osservazione','photos':[{'id':str(uuid4()).upper(),'angle':a,'path':path,'annotations':[{'id':str(uuid4()),'x':.2,'y':.8,'note':'Zona da controllare'}]} for a in ['Foglia · sopra','Foglia · sotto','Fusto','Terreno']]}
    return plant,body

def test_atomic_native_health_event_and_retry(client):
    p,body=setup(client);url=f"/api/plants/{p['id']}/health-photos?version={p['_version']}"
    response=client.post(url,json=body);assert response.status_code==201,response.text
    result=response.json();assert len(result['healthPhotoSessions'])==1 and len(result['history'])==1
    assert result['history'][0]['kind']=='Controlla salute' and result['history'][0]['health']=='Buona'
    assert result['wateringInterval']==p['wateringInterval']
    assert client.post(url,json=body).json()['_version']==result['_version']
    changed=deepcopy(body);changed['note']='Dati diversi'
    assert client.post(url,json=changed).status_code==409
    assert len(main.store.get('plants',p['id'])[0]['history'])==1

@pytest.mark.parametrize('kind',['missing-angle','duplicate-angle','missing-file','traversal','bad-marker','duplicate-marker'])
def test_invalid_session_never_creates_partial_history(client,kind):
    p,body=setup(client)
    if kind=='missing-angle':body['photos'].pop()
    if kind=='duplicate-angle':body['photos'][0]['angle']='Terreno'
    if kind=='missing-file':body['photos'][0]['path']='a'*64+'.jpg'
    if kind=='traversal':body['photos'][0]['path']='../options.json'
    if kind=='bad-marker':body['photos'][0]['annotations'][0]['x']=1.01
    if kind=='duplicate-marker':body['photos'][0]['annotations']*=2
    assert client.post(f"/api/plants/{p['id']}/health-photos?version={p['_version']}",json=body).status_code==422
    saved,_=main.store.get('plants',p['id']);assert not saved.get('healthPhotoSessions') and saved['history']==[]

def test_stale_plant_never_overwrites_history(client):
    p,body=setup(client);current,v=main.store.get('plants',p['id']);current['notes']='Modifica concorrente';main.store.put('plants',current,v)
    assert client.post(f"/api/plants/{p['id']}/health-photos?version={p['_version']}",json=body).status_code==409
    assert main.store.get('plants',p['id'])[0]['notes']=='Modifica concorrente'
