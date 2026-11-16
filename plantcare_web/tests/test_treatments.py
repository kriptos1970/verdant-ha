from datetime import datetime, timezone
from uuid import uuid4
import json
import pytest
from plantcare_web.tests.test_api import client,create,native_envelope
from plantcare_web.backend import main,domain,care,treatments

@pytest.fixture(autouse=True)
def clock(monkeypatch):
    fixed=lambda:datetime(2026,11,15,12,tzinfo=timezone.utc)
    for module in [main,domain,care,treatments]: monkeypatch.setattr(module,'now',fixed)


def product(client,**extra):
    r=client.post('/api/fertilizers',json={'name':'Prodotto di prova','dosage':'Dose da etichetta','applicationMethod':'Applicazione fogliare',**extra})
    assert r.status_code==201,r.text
    return r.json()


def cycle(client,p,f,**extra):
    r=client.post(f"/api/plants/{p['id']}/treatments?version={p['_version']}",json={'productID':f['id'],'startDate':'2026-11-15T12:00:00Z','intervalDays':7,'totalApplications':3,'dose':'Dose da etichetta','notes':'Note del ciclo',**extra})
    assert r.status_code==201,r.text
    return r.json()


def apply(client,p,action,**extra):
    data={'plantID':p['id'],'eventID':str(uuid4()).upper(),'expectedActionID':action['id'],'operation':'complete',**extra}
    return client.post('/api/care-round/actions',json=data),data


def test_cycle_complete_retry_and_delete_recompute(client):
    p=create(client);f=product(client);p=cycle(client,p,f)
    a=next(a for a in p['_actions'] if a['kind']=='Trattamento')
    done,data=apply(client,p,a)
    assert done.status_code==200,done.text
    saved=done.json()['plant'];plan=saved['_treatments'][0]
    assert plan['completedApplications']==1
    assert plan['nextDueDate']=='2026-11-22T12:00:00Z'
    retry=client.post('/api/care-round/actions',json=data)
    assert retry.status_code==200 and retry.json()['replayed'] is True
    assert retry.json()['plant']['_version']==saved['_version']
    assert len(retry.json()['plant']['history'])==1
    duplicate,_=apply(client,p,a)
    assert duplicate.status_code==409
    event=saved['history'][0]
    deleted=client.delete(f"/api/plants/{p['id']}/events/{event['id']}?version={saved['_version']}")
    assert deleted.status_code==200,deleted.text
    assert deleted.json()['_treatments'][0]['completedApplications']==0
    assert deleted.json()['_treatments'][0]['nextDueDate']=='2026-11-15T12:00:00Z'


def test_two_cycles_postponement_is_scoped(client):
    p=create(client);f=product(client);p=cycle(client,p,f);p=cycle(client,p,f)
    actions=[a for a in p['_actions'] if a['kind']=='Trattamento']
    result,_=apply(client,p,actions[0],operation='postpone')
    assert result.status_code==200,result.text
    plans=result.json()['plant']['_treatments']
    affected=next(x for x in plans if x['id']==actions[0]['treatmentPlanID'])
    other=next(x for x in plans if x['id']!=actions[0]['treatmentPlanID'])
    assert affected['nextDueDate']=='2026-11-16T12:00:00Z'
    assert other['nextDueDate']=='2026-11-15T12:00:00Z'
    assert affected['completedApplications']==0
    assert result.json()['completedEvents']==0


def test_end_date_and_cancel_resume(client):
    p=create(client);f=product(client);p=cycle(client,p,f,endDate='2026-11-16T23:59:59Z')
    plan=p['_treatments'][0]
    blocked=client.delete(f"/api/fertilizers/{f['id']}?version={f['_version']}")
    assert blocked.status_code==409
    cancel=client.delete(f"/api/plants/{p['id']}/treatments/{plan['id']}?version={p['_version']}")
    assert cancel.status_code==200
    p=cancel.json();assert p['_treatments'][0]['status']=='cancelled'
    assert not any(a['kind']=='Trattamento' for a in p['_actions'])
    resume=client.post(f"/api/plants/{p['id']}/treatments/{plan['id']}/resume?version={p['_version']}")
    assert resume.status_code==200
    p=resume.json();a=next(a for a in p['_actions'] if a['kind']=='Trattamento')
    done,_=apply(client,p,a);assert done.status_code==200
    p=done.json()['plant'];assert p['_treatments'][0]['status']=='ended'
    assert not any(a['kind']=='Trattamento' for a in p['_actions'])


def test_postpone_beyond_end_rejected_atomically(client):
    p=create(client);f=product(client);p=cycle(client,p,f,endDate='2026-11-15T23:59:59Z')
    a=next(a for a in p['_actions'] if a['kind']=='Trattamento')
    result,_=apply(client,p,a,operation='postpone')
    assert result.status_code==422
    p=client.get('/api/plants').json()[0]
    assert p['history']==[] and p['_treatments'][0]['completedApplications']==0


def test_cycle_validation_and_stale_edit(client):
    p=create(client);f=product(client);p=cycle(client,p,f)
    plan=p['_treatments'][0]
    fields={k:plan[k] for k in ['id','productID','startDate','intervalDays','totalApplications','endDate','dose','notes'] if k in plan}
    fields['intervalDays']=0
    url=f"/api/plants/{p['id']}/treatments/{plan['id']}?version={p['_version']}"
    assert client.put(url,json=fields).status_code==422
    fields['intervalDays']=14
    result=client.put(url,json=fields);assert result.status_code==200,result.text
    assert client.put(url,json=fields).status_code==409
    fresh=result.json();fresh['treatmentPlans'][0]['completedApplications']=3
    assert client.put(f"/api/plants/{p['id']}?version={fresh['_version']}",json=fresh).status_code==422


def test_native_cycle_epoch_and_missing_ledger_baseline_preserved(client):
    pid=str(uuid4()).upper();fid=str(uuid4()).upper();tid=str(uuid4()).upper()
    plant={'id':pid,'name':'Pianta importata','lastWatered':0,'acquiredOn':0,'treatmentPlans':[{'id':tid,'productID':fid,'productName':'Prodotto importato','startDate':0,'intervalDays':7,'totalApplications':4,'completedApplications':2,'dose':'Dose importata','notes':''}]}
    raw=json.dumps(native_envelope([plant])).encode()
    result=client.post('/api/import',files={'file':('native.json',raw)})
    assert result.status_code==200,result.text
    p=client.get('/api/plants').json()[0]
    assert p['_treatments'][0]['startDate']=='2001-01-01T00:00:00Z'
    a=next(a for a in p['_actions'] if a.get('treatmentPlanID')==tid)
    assert a['applicationNumber']==3
    done,_=apply(client,p,a);assert done.status_code==200,done.text
    p=done.json()['plant'];assert p['_treatments'][0]['completedApplications']==3
    e=p['history'][0]
    r=client.delete(f"/api/plants/{pid}/events/{e['id']}?version={p['_version']}")
    assert r.json()['_treatments'][0]['completedApplications']==2


def test_round_water_feed_grouping_and_replay_count(client):
    p=create(client,lastWatered='2026-11-08T12:00:00Z',fertilizingInterval=7,lastFertilized='2026-11-08T12:00:00Z')
    assert len(p['_actions'])==1
    a=p['_actions'][0];assert a['includesFertilizing'] is True
    done,data=apply(client,p,a,includingFertilizing=True)
    assert done.status_code==200,done.text
    assert done.json()['completedEvents']==2
    assert {e['kind'] for e in done.json()['plant']['history']}=={'Annaffia','Concima'}
    retry=client.post('/api/care-round/actions',json=data)
    assert retry.json()['completedEvents']==2
    assert len(retry.json()['plant']['history'])==2


def test_foliar_product_is_not_combined_with_watering(client):
    f=product(client)
    p=create(client,lastWatered='2026-11-08T12:00:00Z',fertilizingInterval=7,lastFertilized='2026-11-08T12:00:00Z',fertilizerProductID=f['id'])
    assert len(p['_actions'])==2
    water=next(a for a in p['_actions'] if a['kind']=='Annaffia')
    assert water['includesFertilizing'] is False
    done,_=apply(client,p,water,includingFertilizing=True)
    assert done.status_code==200
    assert [e['kind'] for e in done.json()['plant']['history']]==['Annaffia']


def test_editing_application_status_recalculates_cycle(client):
    p=create(client);f=product(client);p=cycle(client,p,f)
    a=next(a for a in p['_actions'] if a['kind']=='Trattamento')
    done,_=apply(client,p,a);p=done.json()['plant'];e=p['history'][0]
    change={**e,'status':'postponed','postponedUntil':'2026-11-17T12:00:00Z'}
    response=client.put(f"/api/plants/{p['id']}/events/{e['id']}?version={p['_version']}",json=change)
    assert response.status_code==200,response.text
    plan=response.json()['_treatments'][0]
    assert plan['completedApplications']==0 and plan['nextDueDate']=='2026-11-17T12:00:00Z'
