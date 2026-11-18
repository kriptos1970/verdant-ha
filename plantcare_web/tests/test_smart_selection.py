import httpx
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main, adaptive
from plantcare_web.backend.storage import Store

HEAD={'X-PlantCare-Request':'1'}
CLIMATE=dict(averageTemperature=22,relativeHumidity=55,precipitationNextWeek=0)
LOCATION=dict(name='Roma',detail='Lazio, Italia',latitude=41.89,longitude=12.5)

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path/'data',tmp_path/'shared'/'photos'))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers=HEAD)

def create(client,**extra):
    data={'name':'Monstera','species':'Monstera deliciosa','family':'Araceae','room':'Salotto','wateringInterval':7,'lastWatered':'2026-11-01T12:00:00Z','acquiredOn':'2026-01-01T12:00:00Z',**extra}
    response=client.post('/api/plants',json=data)
    assert response.status_code==201,response.text
    return response.json()

def weather(monkeypatch):
    calls=[]
    async def climate(location):
        calls.append(location)
        return dict(CLIMATE)
    monkeypatch.setattr(adaptive,'fetch_climate',climate)
    return calls

def test_manual_plant_can_switch_to_verdant_from_the_editor(client,monkeypatch):
    main.store.set_state('location',LOCATION)
    calls=weather(monkeypatch)
    p=create(client)
    response=client.put(f"/api/plants/{p['id']}?version={p['_version']}",json={**p,'carePlanMode':'Intelligente','adaptivePlan':{'placement':'Pieno sole'}})
    assert response.status_code==200,response.text
    saved=response.json()
    assert saved['carePlanMode']=='Intelligente'
    assert saved['adaptivePlan']['placement']=='Pieno sole'
    assert saved['adaptivePlan']['weatherEnabled'] is True
    assert saved['adaptivePlan']['locationName'].startswith('Roma')
    assert saved['wateringInterval']==saved['adaptivePlan']['wateringDays']
    assert calls and calls[0]['name']=='Roma'

def test_verdant_switch_requires_the_default_location(client):
    p=create(client)
    response=client.put(f"/api/plants/{p['id']}?version={p['_version']}",json={**p,'carePlanMode':'Intelligente'})
    assert response.status_code==422
    assert 'località predefinita' in response.text
    assert main.store.get('plants',p['id'])[0]['carePlanMode']=='Manuale'

def test_verdant_weather_failure_leaves_the_plant_manual(client,monkeypatch):
    main.store.set_state('location',LOCATION)
    async def fail(location):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr(adaptive,'fetch_climate',fail)
    p=create(client)
    response=client.put(f"/api/plants/{p['id']}?version={p['_version']}",json={**p,'carePlanMode':'Intelligente'})
    assert response.status_code==502
    assert main.store.get('plants',p['id'])[0]['carePlanMode']=='Manuale'
    assert main.store.get('plants',p['id'])[1]==p['_version']

def test_new_plant_can_start_in_verdant(client,monkeypatch):
    main.store.set_state('location',LOCATION)
    weather(monkeypatch)
    p=create(client,carePlanMode='Intelligente')
    assert p['carePlanMode']=='Intelligente'
    assert p['adaptivePlan']['weatherEnabled'] is True
    assert p['history']==[]
    assert p['wateringInterval']==p['adaptivePlan']['wateringDays']
