import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import main
from plantcare_web.backend.storage import Store
from plantcare_web.backend.health_guides import diagnosis, practical_guide
from plantcare_web.backend.models import Plant

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    return TestClient(main.app,headers={'X-PlantCare-Request':'1'})


def test_guides_and_diagnosis_leave_plant_archive_unchanged(client):
    p=client.post('/api/plants',json={'name':'Ficus','wateringInterval':9}).json()
    before=client.get('/api/plants').json()
    response=client.post('/api/knowledge/diagnosis',json={'plantID':p['id'],'symptoms':['Macchie','Foglie gialle']})
    assert response.status_code==200 and 'foglie gialle' in response.json()['advice']
    guide=client.get(f"/api/knowledge/plants/{p['id']}/guide").json()
    assert len(guide['ranges'])==3 and len(guide['tiles'])==6 and len(guide['seasonal'])==12
    assert client.get('/api/plants').json()==before
    assert not main.store.list('recommendations') and not main.store.list('proposals')


@pytest.mark.parametrize('symptoms',[[],['other'],[None],['Foglie gialle']*7,'Foglie gialle'])
def test_invalid_symptoms_are_rejected(client,symptoms):
    p=client.post('/api/plants',json={'name':'Test'}).json()
    assert client.post('/api/knowledge/diagnosis',json={'plantID':p['id'],'symptoms':symptoms}).status_code==422


def test_unknown_plant_is_rejected(client):
    assert client.post('/api/knowledge/diagnosis',json={'plantID':'missing','symptoms':['Insetti']}).status_code==404
    assert client.get('/api/knowledge/plants/missing/guide').status_code==404


def test_native_drainage_family_and_outdoor_rules():
    p=Plant(name='Monstera',family='Araceae',wateringInterval=10).model_dump()
    guide=practical_guide(p)
    assert guide['tiles'][0]['value']=='Mix arioso per aroidi'
    assert guide['seasonal'][5]['days']==8
    p.update(potHasDrainage=False,adaptivePlan={'placement':'Pieno sole'})
    guide=practical_guide(p)
    assert guide['tiles'][0]['tip']=='Attenzione: il vaso non ha drenaggio.'
    assert guide['seasonal'][5]['days']==7
    assert 'asciutto' in diagnosis(['Punte secche','Insetti'])
