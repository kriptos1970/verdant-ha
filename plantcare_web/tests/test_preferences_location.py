import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.storage import Store

HEAD={'X-PlantCare-Request':'1'}
LOCATION=dict(name='Roma',detail='Lazio, Italia',latitude=41.8933,longitude=12.4829)

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path/'data',tmp_path/'shared'/'photos'))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers=HEAD)

def test_default_location_can_be_saved_read_and_cleared(client):
    assert client.get('/api/preferences/location').json() is None
    saved=client.put('/api/preferences/location',json=LOCATION)
    assert saved.status_code==200,saved.text
    assert saved.json()==LOCATION
    assert client.get('/api/preferences/location').json()==LOCATION
    assert client.get('/api/settings').json()['location']==LOCATION
    assert client.delete('/api/preferences/location').status_code==204
    assert client.get('/api/preferences/location').json() is None
    assert client.get('/api/settings').json()['location'] is None

def test_default_location_validates_coordinates_and_name(client):
    assert client.put('/api/preferences/location',json={**LOCATION,'latitude':91}).status_code==422
    assert client.put('/api/preferences/location',json={**LOCATION,'longitude':-181}).status_code==422
    assert client.put('/api/preferences/location',json={**LOCATION,'name':''}).status_code==422
    assert client.get('/api/preferences/location').json() is None

def test_location_search_returns_open_meteo_matches(client,monkeypatch):
    calls=[]
    async def geocode(query,language):
        calls.append((query,language))
        return [dict(name='Roma',detail='Lazio, Italia',latitude=41.8933,longitude=12.4829)]
    monkeypatch.setattr(main,'geocode_locations',geocode)
    response=client.get('/api/weather/locations?q=Roma')
    assert response.status_code==200,response.text
    assert response.json()[0]['name']=='Roma'
    assert calls==[('Roma','it')]

def test_location_search_reports_remote_errors(client,monkeypatch):
    async def geocode(query,language):
        raise ValueError('offline')
    monkeypatch.setattr(main,'geocode_locations',geocode)
    assert client.get('/api/weather/locations?q=Roma').status_code==502
    assert client.get('/api/weather/locations?q=R').status_code==422
