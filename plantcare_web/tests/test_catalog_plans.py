from copy import deepcopy
from datetime import timedelta
import httpx
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main,catalog,adaptive
from plantcare_web.backend.storage import Store
from plantcare_web.backend.domain import iso,now

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path));monkeypatch.setattr(main.settings,'ingress',False);monkeypatch.setattr(main.settings,'token','');catalog.CACHE.clear()
    return TestClient(main.app,headers={'X-PlantCare-Request':'1'})

def transport(monkeypatch,handler):
    original=httpx.AsyncClient;monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))

def taxon(name='Ficus elastica',**kw):return {'id':100,'name':name,'preferred_common_name':'Ficus','ancestors':[{'rank':'family','name':'Moraceae'}],**kw}

def test_native_search_pagination_license_and_cache(client,monkeypatch):
    calls=[]
    def handler(r):
        calls.append(r);assert r.url.params['rank']=='species' and r.url.params['locale']=='it' and r.url.params['iconic_taxa']=='Plantae'
        return httpx.Response(200,json={'total_results':25,'results':[taxon(default_photo={'medium_url':'https://static.inaturalist.org/photos/12/medium.jpg','attribution':'Autore','license_code':'cc-by'})]})
    transport(monkeypatch,handler)
    data=client.get('/api/knowledge/catalog?q=Ficus').json();assert data['hasNextPage'] and data['results'][0]['family']=='Moraceae'
    assert data['results'][0]['imageAttribution']=='Autore' and data['results'][0]['imageLicense']=='cc-by'
    assert client.get('/api/knowledge/catalog?q=Ficus').json()==data and len(calls)==1
    assert not client.get('/api/knowledge/catalog?q=Ficus&page=2').json()['hasNextPage']
    assert len(calls)==2 and calls[-1].url.params['per_page']=='20'

@pytest.mark.parametrize('photo',[{'medium_url':'http://static.inaturalist.org/a.jpg','license_code':'cc-by','attribution':'A'},{'medium_url':'https://evil.example/a.jpg','license_code':'cc-by','attribution':'A'},{'medium_url':'https://static.inaturalist.org/a.jpg','license_code':None,'attribution':'A'}])
def test_unattributed_or_untrusted_photos_are_not_returned(client,monkeypatch,photo):
    transport(monkeypatch,lambda r:httpx.Response(200,json={'results':[taxon(default_photo=photo)]}))
    assert client.get('/api/knowledge/catalog?q=Ficus').json()['results'][0]['imageURL'] is None


def test_curated_categories_order_and_offline_fallback(client,monkeypatch):
    def handler(r):
        name=r.url.params['q'];return httpx.Response(200,json={'results':[taxon(name=name)]})
    transport(monkeypatch,handler)
    data=client.get('/api/knowledge/catalog?focus=Succulente').json()
    assert [r['scientificName'] for r in data['results']]==catalog.FOCUS['Succulente'][:12] and data['hasNextPage']


def test_offline_fallback(client,monkeypatch):
    transport(monkeypatch,lambda r:httpx.Response(503))
    data=client.get('/api/knowledge/catalog?q=Ficus').json()
    assert data['warning'] and data['source']=='Selezione offline' and data['results']
    assert all(r['imageURL'] is None and r['sourceURL'] is None for r in data['results'])



def request(**kw):return dict(location={'name':'Roma','latitude':42,'longitude':12.5},placement='Interno luminoso',weatherEnabled=False,climate={'averageTemperature':22,'relativeHumidity':55,'precipitationNextWeek':0},**kw)

def profile(exact=True):return dict(scientificName='Ficus elastica' if exact else 'Ficus benjamina',exactMatch=exact,wateringDays=14,wateringLabel='Minimum',source='Open Plantbook',summary='Scheda',fetchedAt=iso(now()))


def test_profile_preview_explicit_link_and_exact_apply(client,monkeypatch):
    p=client.post('/api/plants',json={'name':'Ficus','species':'Ficus elastica'}).json();path=f"/api/plants/{p['id']}"
    async def fetch(name):assert name=='Ficus elastica';return profile()
    monkeypatch.setattr(main,'fetch_botanical_profile',fetch)
    bot=client.post(path+'/botanical/preview?version=1').json()
    assert main.store.get('plants',p['id'])[1]==1 and main.store.get('plants',p['id'])[0].get('adaptivePlan') is None
    preview=client.post(path+'/adaptive/preview?version=1',json=request(botanicalPreviewID=bot['previewID'])).json()
    assert preview['plan']['botanicalWateringDays']==14 and preview['plan']['botanicalScientificName']=='Ficus elastica'
    assert not main.store.get('plants',p['id'])[0]['history']
    response=client.post(path+f"/adaptive/apply?version=1&previewID={preview['previewID']}");assert response.status_code==200,response.text
    assert response.json()['adaptivePlan']==preview['plan'] and len(response.json()['history'])==1


def test_approximate_profile_requires_confirmation_and_stale_rejected(client,monkeypatch):
    p=client.post('/api/plants',json={'name':'Ficus','species':'Ficus elastica'}).json();path=f"/api/plants/{p['id']}"
    async def fetch(name):return profile(False)
    monkeypatch.setattr(main,'fetch_botanical_profile',fetch)
    bot=client.post(path+'/botanical/preview?version=1').json()
    assert client.post(path+'/adaptive/preview?version=1',json=request(botanicalPreviewID=bot['previewID'])).status_code==422
    assert client.post(path+'/adaptive/preview?version=1',json=request(botanicalPreviewID=bot['previewID'],confirmBotanicalMatch=True)).status_code==200
    state=main.store.state('botanical-preview-'+p['id']);state['createdAt']=iso(now()-timedelta(hours=1));main.store.set_state('botanical-preview-'+p['id'],state)
    assert client.post(path+'/adaptive/preview?version=1',json=request(botanicalPreviewID=bot['previewID'],confirmBotanicalMatch=True)).status_code==409


def test_profile_request_race_and_invalid_catalog_inputs(client,monkeypatch):
    p=client.post('/api/plants',json={'name':'Ficus','species':'Ficus elastica'}).json()
    async def fetch(name):
        current,v=main.store.get('plants',p['id']);current['notes']='Modifica concorrente';main.store.put('plants',current,v);return profile()
    monkeypatch.setattr(main,'fetch_botanical_profile',fetch)
    assert client.post(f"/api/plants/{p['id']}/botanical/preview?version=1").status_code==409
    assert main.store.state('botanical-preview-'+p['id']) is None
    for suffix in ['?page=0','?page=101','?focus=invalid']:
        assert client.get('/api/knowledge/catalog'+suffix).status_code==422
