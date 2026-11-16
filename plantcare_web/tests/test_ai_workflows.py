import asyncio
import json
from copy import deepcopy
import httpx
import pytest
from fastapi.testclient import TestClient
from plantcare_web.backend import ai, main, services
from plantcare_web.backend.ai_support import models,effective_settings
from plantcare_web.backend.models import Plant,AdviceSelection
from plantcare_web.backend.settings import Settings
from plantcare_web.backend.storage import Store,Conflict

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    monkeypatch.setattr(main.settings,'options',dict(ai_provider='openai',openai_api_key='test-secret',ai_model='gpt-5-nano'))
    return TestClient(main.app,headers={'X-PlantCare-Request':'1'})

def plant(client,**kw):return client.post('/api/plants',json=dict(name='Monstera',carePlanMode='AI',**kw)).json()

def advice_result():return dict(wateringDays=999,fertilizingDays=23,inspectionDays=999,pruningDays=1,repottingDays=1,careNotes='Controlla il terriccio.',summaryMarkdown='Osserva la pianta.')


def test_selective_advice_apply_notes_idempotence_and_stale(client,monkeypatch):
    async def complete(*a):return advice_result()
    monkeypatch.setattr(ai,'complete',complete)
    p=plant(client,wateringInterval=7,inspectionInterval=12,pruningInterval=100)
    path=f"/api/plants/{p['id']}/advice"
    r=client.post(path,json={'question':'Come sta?'});assert r.status_code==200,r.text
    proposal=r.json();assert proposal['inspectionDays']==12 and proposal['pruningDays']==100 and proposal['repottingDays']==365
    assert client.get(path).json()['id']==proposal['id']
    apply=dict(adviceID=proposal['id'],fertilizing=True)
    r=client.post(path+'/apply',json=apply);assert r.status_code==200,r.text
    current=r.json();assert current['fertilizingInterval']==21 and current['wateringInterval']==7
    assert current['pruningInterval']==100 and current.get('repottingInterval') is None
    assert 'Controlla il terriccio.' in current['notes']
    assert client.post(path+'/apply',json=apply).json()['_version']==current['_version']
    proposal=client.post(path,json={'question':'Ancora?'}).json()
    current['name']='Nome nuovo';assert client.put(f"/api/plants/{p['id']}?version={current['_version']}",json=current).status_code==200
    assert client.get(path).json()['stale']
    assert client.post(path+'/apply',json={'adviceID':proposal['id'],'watering':True}).status_code==409


def test_advice_race_preserves_previous_result(client,monkeypatch):
    p=plant(client);path=f"/api/plants/{p['id']}/advice"
    async def complete(*a):return advice_result()
    monkeypatch.setattr(ai,'complete',complete)
    previous=client.post(path,json={'question':'Prima'}).json()
    async def race(*a):
        value,v=main.store.get('plants',p['id']);value['notes']='Cambiata durante la richiesta';main.store.put('plants',value,v)
        return advice_result()
    monkeypatch.setattr(ai,'complete',race)
    assert client.post(path,json={'question':'Seconda'}).status_code==409
    assert main.store.state('ai-advice-'+p['id'])['id']==previous['id']


def transport(monkeypatch,handler):
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))

@pytest.mark.parametrize('provider',['openai','gemini'])
def test_provider_requests_and_structured_response(provider,monkeypatch):
    settings=Settings();settings.options=dict(ai_provider=provider,openai_api_key='openai-secret',gemini_api_key='gemini-secret')
    def handle(request):
        payload=json.loads(request.content)
        assert 'secret' not in str(request.url)
        if provider=='openai':
            assert request.headers['Authorization']=='Bearer openai-secret'
            assert payload['response_format']['json_schema']['strict'] is True
            return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(advice_result())}}]})
        assert request.headers['x-goog-api-key']=='gemini-secret'
        assert payload['generationConfig']['responseMimeType']=='application/json'
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'private thought','thought':True},{'text':json.dumps(advice_result())}]}}]})
    transport(monkeypatch,handle)
    assert asyncio.run(ai.complete(settings,'prompt',ai.ADVICE_SCHEMA,'advice'))==advice_result()

@pytest.mark.parametrize('response',[
 {'choices':[{'finish_reason':'length','message':{'content':'{}'}}]},
 {'choices':[{'finish_reason':'stop','message':{'refusal':'No','content':'{}'}}]},
 {'choices':[{'finish_reason':'stop','message':{'content':'invalid'}}]},
 {'choices':[]},
])
def test_incomplete_refused_invalid_responses(response,monkeypatch):
    settings=Settings();settings.options=dict(ai_provider='openai',openai_api_key='secret')
    transport(monkeypatch,lambda request:httpx.Response(200,json=response))
    with pytest.raises(ValueError):asyncio.run(ai.complete(settings,'prompt',ai.ADVICE_SCHEMA,'advice'))


def test_catalog_pagination_filter_and_selected_model(client,monkeypatch):
    requests=[]
    def handle(request):
        requests.append(request)
        return httpx.Response(200,json=dict(data=[{'id':s} for s in ['gpt-5-nano','gpt-5-audio','text-embedding-3-small','o3','gpt-5-mini']]))
    transport(monkeypatch,handle)
    r=client.post('/api/ai/models');assert r.status_code==200,r.text
    assert r.json()['models']==['gpt-5-mini','gpt-5-nano','o3']
    assert 'test-secret' not in r.text
    assert client.put('/api/ai/model',json={'model':'missing'}).status_code==422
    r=client.put('/api/ai/model',json={'model':'gpt-5-mini'});assert r.status_code==200,r.text
    assert r.json()['aiModel']=='gpt-5-mini'
    main.settings.options['ai_model']='gpt-5-nano-updated'
    assert client.get('/api/settings').json()['aiModel']=='gpt-5-nano-updated'


def test_gemini_catalog_pages(monkeypatch):
    settings=Settings();settings.options=dict(ai_provider='gemini',gemini_api_key='secret')
    def handle(request):
        assert request.headers['x-goog-api-key']=='secret'
        if request.url.params.get('pageToken')=='second':return httpx.Response(200,json=dict(models=[dict(name='models/gemini-3',supportedGenerationMethods=['generateContent'])]))
        return httpx.Response(200,json=dict(nextPageToken='second',models=[dict(name='models/gemini-2',supportedGenerationMethods=['generateContent']),dict(name='models/embed',supportedGenerationMethods=['embedContent'])]))
    transport(monkeypatch,handle)
    assert asyncio.run(models(settings))['models']==['gemini-2','gemini-3']


def test_daily_notification_failure_does_not_lose_proposals(client,monkeypatch):
    p=plant(client)
    async def complete(*a):return dict(summary='Revisione',plants=[dict(plantID=p['id'],wateringDays=9,fertilizingDays=28,hasSufficientEvidence=True,reason='Consumo osservato.')])
    async def fail(*a):raise httpx.ConnectError('Offline')
    monkeypatch.setattr(ai,'complete',complete);monkeypatch.setattr(services,'notify',fail)
    r=client.post('/api/ai/analyze');assert r.status_code==200,r.text
    assert r.json()['notificationError'] and len(main.store.list('proposals'))==1
    assert main.store.state('last-ai-day')


def test_daily_race_leaves_previous_proposals(client,monkeypatch):
    p=plant(client)
    main.store.put('proposals',dict(id=p['id'],sentinel=True))
    async def race(*a):
        value,v=main.store.get('plants',p['id']);value['notes']='New';main.store.put('plants',value,v)
        return dict(summary='Revisione',plants=[dict(plantID=p['id'],wateringDays=9,fertilizingDays=28,hasSufficientEvidence=True,reason='Consumo osservato.')])
    monkeypatch.setattr(ai,'complete',race)
    assert client.post('/api/ai/analyze').status_code==409
    assert main.store.get('proposals',p['id'])[0]['sentinel']


def test_auto_application_marks_native_revision_source(client,monkeypatch):
    p=plant(client)
    value,v=main.store.get('plants',p['id']);value['adaptivePlan']=dict(verdantWateringDays=7,wateringDays=7,inspectionDays=7);main.store.put('plants',value,v)
    main.settings.options['auto_apply_ai']=True
    async def complete(*a):return dict(summary='Revisione',plants=[dict(plantID=p['id'],wateringDays=9,fertilizingDays=28,hasSufficientEvidence=True,reason='Consumo osservato.')])
    async def notify(*a):pass
    monkeypatch.setattr(ai,'complete',complete);monkeypatch.setattr(services,'notify',notify)
    r=client.post('/api/ai/analyze');assert r.status_code==200,r.text
    assert r.json()['applied']==1
    assert main.store.get('plants',p['id'])[0]['adaptivePlan']['revisionSource']=='AI'


def test_selection_preview_matches_actual_in_manual_mode(client,monkeypatch):
    async def complete(*a):return advice_result()
    monkeypatch.setattr(ai,'complete',complete)
    p=plant(client)
    current,v=main.store.get('plants',p['id']);current.update(carePlanMode='Manuale',wateringInterval=7,fertilizingInterval=None);main.store.put('plants',current,v)
    path=f"/api/plants/{p['id']}/advice"
    advice=client.post(path,json={'question':'Consiglio'}).json()
    selection={'adviceID':advice['id'],'fertilizing':True,'inspection':True}
    preview=client.post(path+'/preview',json=selection);assert preview.status_code==200,preview.text
    assert preview.json()['fertilizingInterval'] is None
    assert main.store.get('plants',p['id'])[1]==v+1
    actual=client.post(path+'/apply',json=selection).json()
    assert all(actual.get(k)==value for k,value in preview.json().items())


def test_provider_http_error_never_exposes_api_key(client,monkeypatch):
    p=plant(client)
    transport(monkeypatch,lambda request:httpx.Response(401,json={'error':{'message':'test-secret'}}))
    r=client.post(f"/api/plants/{p['id']}/advice",json={'question':'Come sta?'})
    assert r.status_code==422 and 'test-secret' not in r.text
    assert main.store.state('ai-advice-'+p['id']) is None


def test_repeated_advice_uses_cache_and_dynamic_native_schema(client,monkeypatch):
    calls=[]
    async def complete(settings,prompt,schema,name):
        calls.append(name)
        assert schema['properties']['wateringDays']['enum']==[7]
        assert schema['properties']['inspectionDays']['enum']==[7]
        assert schema['properties']['pruningDays']['enum']==[90]
        assert schema['properties']['repottingDays']['enum']==[365]
        return advice_result()
    monkeypatch.setattr(ai,'complete',complete)
    p=plant(client);path=f"/api/plants/{p['id']}/advice"
    first=client.post(path,json={'question':'Come sta?'}).json()
    second=client.post(path,json={'question':'Come sta?'}).json()
    assert first['id']==second['id'] and len(calls)==1
    assert client.post(path,json={'question':'Altra domanda'}).json()['id']!=first['id']
    assert len(calls)==2

@pytest.mark.parametrize('stamp,expected', [('2026-09-20T10:00:00Z','2026-09-20T10:00:00Z'),(None,None),('invalid',None)])
def test_saved_climate_is_dated_and_legacy_advice_is_blocked(client,monkeypatch,stamp,expected):
    p=plant(client)
    value,version=main.store.get('plants',p['id'])
    value['adaptivePlan']={'generatedAt':stamp,'seasonName':'Crescita attiva','averageTemperature':22.65}
    main.store.put('plants',value,version)
    captured=[]
    async def complete(settings,prompt,*args):
        captured.append(prompt)
        return advice_result()
    monkeypatch.setattr(ai,'complete',complete)
    path=f"/api/plants/{p['id']}/advice"
    proposal=client.post(path,json={'question':'Come sta?'}).json()
    assert proposal['climateContext']=={'source':'saved-plan','generatedAt':expected,'currentWeather':False}
    assert (expected or 'sconosciuta') in captured[0]
    assert 'non da una lettura meteo attuale' in captured[0]
    assert 'non usarli per giustificare cambiamenti' in captured[0]
    assert client.post(path+'/preview',json={'adviceID':proposal['id'],'watering':True}).status_code==200
    legacy=dict(proposal);legacy.pop('contextVersion');main.store.set_state('ai-advice-'+p['id'],legacy)
    assert client.get(path).json()['stale']
    for action in ['preview','apply']:
        assert client.post(path+'/'+action,json={'adviceID':proposal['id'],'watering':True}).status_code==409
    regenerated=client.post(path,json={'question':'Come sta?'}).json()
    assert regenerated['id']!=proposal['id']
