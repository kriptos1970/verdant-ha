import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main, adaptive, knowledge
from plantcare_web.backend.storage import Store

HEAD={'X-PlantCare-Request':'1'}

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

def plan_request():
    return dict(location=dict(name='Roma',latitude=42,longitude=12.5),placement='Interno luminoso',weatherEnabled=False,climate=dict(averageTemperature=22,relativeHumidity=55,precipitationNextWeek=0))

def smart_plant(client):
    p=create(client)
    preview=client.post(f"/api/plants/{p['id']}/adaptive/preview?version=1",json=plan_request())
    assert preview.status_code==200,preview.text
    data=preview.json()
    applied=client.post(f"/api/plants/{p['id']}/adaptive/apply?version=1&previewID={data['previewID']}")
    assert applied.status_code==200,applied.text
    return applied.json()

def test_move_updates_room_and_records_the_route(client):
    p=create(client)
    response=client.post(f"/api/plants/{p['id']}/move",json=dict(room='  Studio  ',placement='Pieno sole',date='2026-11-18T10:00:00Z',note='Verso la finestra',version=p['_version']))
    assert response.status_code==200,response.text
    moved=response.json()
    assert moved['room']=='Studio'
    assert moved['_version']==p['_version']+1
    event=[e for e in moved['history'] if e['kind']=='Spostamento'][-1]
    assert event['status']=='completed'
    assert event['note']=='Salotto → Studio · Verso la finestra'
    assert event['date']=='2026-11-18T10:00:00Z'

def test_move_same_room_records_the_placement_change(client):
    p=smart_plant(client)
    response=client.post(f"/api/plants/{p['id']}/move",json=dict(room='Salotto',placement='Ombra',date='2026-11-18T10:00:00Z',note='',version=p['_version']))
    assert response.status_code==200,response.text
    moved=response.json()
    assert moved['adaptivePlan']['placement']=='Ombra'
    event=[e for e in moved['history'] if e['kind']=='Spostamento'][-1]
    assert event['note']=='Interno luminoso → Ombra'

def test_smart_plan_refreshes_from_the_stored_climate_without_network(client,monkeypatch):
    p=smart_plant(client)
    old_watering=p['wateringInterval']
    async def forbidden(*args,**kwargs): raise AssertionError('A move must not fetch the weather')
    monkeypatch.setattr(adaptive,'fetch_climate',forbidden)
    response=client.post(f"/api/plants/{p['id']}/move",json=dict(room='Terrazzo',placement='Pieno sole',date='2026-07-10T10:00:00Z',note='',version=p['_version']))
    assert response.status_code==200,response.text
    moved=response.json()
    assert moved['room']=='Terrazzo'
    assert moved['carePlanMode']=='Intelligente'
    assert moved['adaptivePlan']['placement']=='Pieno sole'
    assert moved['adaptivePlan']['locationName']=='Roma'
    assert moved['adaptivePlan']['weatherEnabled'] is False
    assert moved['adaptivePlan']['wateringDays']<=old_watering

def test_move_rejects_a_stale_version_and_unknown_placement(client):
    p=create(client)
    assert client.post(f"/api/plants/{p['id']}/move",json=dict(room='Studio',placement='Pieno sole',date='2026-11-18T10:00:00Z',version=p['_version']+1)).status_code==409
    assert client.post(f"/api/plants/{p['id']}/move",json=dict(room='Studio',placement='Serra',date='2026-11-18T10:00:00Z',version=p['_version'])).status_code==422
    assert main.store.get('plants',p['id'])[0]['room']=='Salotto'

def test_move_renders_a_linked_product(client):
    product=client.post('/api/fertilizers',json=dict(name='Biogrow',category='Fertilizzante')).json()
    p=create(client,fertilizerProductID=product['id'])
    response=client.post(f"/api/plants/{p['id']}/move",json=dict(room='Studio',placement='Pieno sole',date='2026-11-18T10:00:00Z',version=p['_version']))
    assert response.status_code==200,response.text
    assert response.json()['room']=='Studio'

def test_safety_refresh_stores_the_perenual_profile(client,monkeypatch):
    p=create(client)
    monkeypatch.setitem(main.settings.options,'perenual_api_key','test-key')
    async def profile(settings,scientific):
        assert scientific=='Monstera deliciosa'
        return dict(scientificName=scientific,poisonousToHumans=True,poisonousToPets=True,source='Perenual',sourceURL='https://perenual.com/species/1',fetchedAt='2026-11-18T09:00:00Z')
    monkeypatch.setattr(knowledge,'profile',profile)
    response=client.post(f"/api/plants/{p['id']}/safety/refresh")
    assert response.status_code==200,response.text
    body=response.json()
    assert body['safetyProfile']['poisonousToPets'] is True
    assert body['safetyProfile']['sourceName']=='Perenual'
    assert body['_version']==p['_version']+1
    assert main.store.get('plants',p['id'])[0]['safetyProfile']['poisonousToHumans'] is True

def test_safety_refresh_without_data_leaves_the_plant_untouched(client,monkeypatch):
    p=create(client)
    monkeypatch.setitem(main.settings.options,'perenual_api_key','test-key')
    async def profile(settings,scientific):
        return dict(poisonousToHumans=None,poisonousToPets=None,source='Perenual',sourceURL='',fetchedAt='2026-11-18T09:00:00Z')
    monkeypatch.setattr(knowledge,'profile',profile)
    assert client.post(f"/api/plants/{p['id']}/safety/refresh").status_code==404
    assert main.store.get('plants',p['id'])[0].get('safetyProfile') is None
    assert main.store.get('plants',p['id'])[1]==p['_version']

def test_safety_refresh_requires_a_species_and_a_key(client,monkeypatch):
    p=create(client,species='')
    assert client.post(f"/api/plants/{p['id']}/safety/refresh").status_code==422
    p=create(client,name='Ficus')
    monkeypatch.delitem(main.settings.options,'perenual_api_key',raising=False)
    assert client.post(f"/api/plants/{p['id']}/safety/refresh").status_code==422
