from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.domain import iso, now
from plantcare_web.backend.storage import Store

HEAD={'X-PlantCare-Request':'1'}

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path/'data',tmp_path/'shared'/'photos'))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers=HEAD)

def create(client):
    last=iso(now()-timedelta(days=6))
    response=client.post('/api/plants',json=dict(name='Ficus',species='Ficus elastica',family='Moraceae',room='Salotto',wateringInterval=7,lastWatered=last,acquiredOn='2026-01-01T12:00:00Z'))
    assert response.status_code==201,response.text
    return response.json()

def measure(client,plant,value):
    return client.post(f"/api/plants/{plant['id']}/measurements",json=dict(kind='moisture',value=value,unit='%',date=iso(now())))

def test_active_engine_postpones_watering_on_wet_reliable_soil(client,monkeypatch):
    monkeypatch.setitem(main.settings.options,'care_engine_mode','active')
    plant=create(client)
    before=client.get(f"/api/plants/{plant['id']}").json()
    due=next(a for a in before['_schedule'] if a['kind']=='Annaffia')['dueDate']
    assert measure(client,plant,82).status_code==201
    saved=client.get(f"/api/plants/{plant['id']}").json()
    assert saved['nextWateringOverride']
    assert saved['nextWateringOverride']>due
    assert saved['careEngineApplied']['moisturePercent']==82
    assert saved['history'][-1]['kind']=='Aggiornamento piano'
    assert 'Motore di cura' in saved['history'][-1]['note']
    due_after=next(a for a in saved['_schedule'] if a['kind']=='Annaffia')['dueDate']
    assert due_after==saved['nextWateringOverride']
    assert measure(client,plant,80).status_code==201
    again=client.get(f"/api/plants/{plant['id']}").json()
    assert again['nextWateringOverride']==saved['nextWateringOverride']

def test_shadow_mode_keeps_the_schedule(client):
    main.settings.options['care_engine_mode']='shadow'
    plant=create(client)
    assert measure(client,plant,82).status_code==201
    saved=client.get(f"/api/plants/{plant['id']}").json()
    assert not saved.get('nextWateringOverride')
    assert not saved.get('careEngineApplied')

def test_dry_measurement_never_advances_the_due_date(client,monkeypatch):
    monkeypatch.setitem(main.settings.options,'care_engine_mode','active')
    plant=create(client)
    assert measure(client,plant,18).status_code==201
    saved=client.get(f"/api/plants/{plant['id']}").json()
    assert not saved.get('nextWateringOverride')
    assert not saved.get('careEngineApplied')
