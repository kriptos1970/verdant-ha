import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.models import Plant
from plantcare_web.backend.storage import Store

HEAD={'X-PlantCare-Request':'1'}

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path/'data',tmp_path/'shared'/'photos'))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers=HEAD)

def create(client):
    response=client.post('/api/plants',json=dict(name='Ficus',species='Ficus elastica',room='Salotto',wateringInterval=7,lastWatered='2026-11-10T12:00:00Z',acquiredOn='2026-01-01T12:00:00Z'))
    assert response.status_code==201,response.text
    return response.json()

def test_manual_measurements_show_source_and_full_reliability(client):
    p=create(client)
    saved=client.post(f"/api/plants/{p['id']}/measurements",json=dict(kind='moisture',value=42.5,unit='%',date='2026-11-15T09:00:00Z'))
    assert saved.status_code==201,saved.text
    rows=client.get(f"/api/plants/{p['id']}/measurements").json()
    assert len(rows)==1
    assert rows[0]['source']=='manual'
    assert rows[0]['reliability']==1.0
    assert rows[0]['value']==42.5

def test_native_measurements_keep_provenance_and_reliability(client):
    p=create(client)
    main.store.set_state('native-measurements',[{
        'id':'native-1','plantID':p['id'],'kind':'substrateMoisture','value':31.5,
        'unit':'percent','source_at':'2026-11-15T09:00:00Z','source':'homeAssistant',
        'entity_id':'sensor.ficus_moisture','reliability':0.82,
    }])
    rows=client.get(f"/api/plants/{p['id']}/measurements").json()
    assert len(rows)==1
    assert rows[0]['kind']=='moisture'
    assert rows[0]['unit']=='%'
    assert rows[0]['source']=='homeAssistant'
    assert rows[0]['entity_id']=='sensor.ficus_moisture'
    assert rows[0]['reliability']==0.82

def test_native_measurements_replace_the_legacy_duplicate(client):
    p=create(client)
    client.post(f"/api/plants/{p['id']}/measurements",json=dict(kind='moisture',value=42.5,unit='%',date='2026-11-15T09:00:00Z'))
    main.store.set_state('native-measurements',[{
        'id':'native-1','plantID':p['id'],'kind':'substrateMoisture','value':42.5,
        'unit':'percent','source_at':'2026-11-15T09:00:00Z','source':'smartphoneEstimated',
        'reliability':0.55,
    }])
    rows=client.get(f"/api/plants/{p['id']}/measurements").json()
    assert len(rows)==1
    assert rows[0]['source']=='smartphoneEstimated'
    assert rows[0]['reliability']==0.55

def test_imported_sensor_rows_report_unknown_reliability(client):
    p=create(client)
    with main.store.connection() as db:
        db.execute('INSERT INTO measurements(plant_id,entity_id,kind,value,unit,measured_at,source_at) VALUES (?,?,?,?,?,?,?)',(p['id'],'sensor.ficus','temperature',21.5,'°C','2026-11-15T09:00:00Z','2026-11-15T09:00:00Z'))
    rows=client.get(f"/api/plants/{p['id']}/measurements").json()
    assert rows[0]['source']=='homeAssistant'
    assert rows[0]['reliability'] is None
