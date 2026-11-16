import io
import json
import asyncio
import httpx
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from plantcare_web.backend import knowledge, main
from plantcare_web.backend.settings import Settings
from plantcare_web.backend.storage import Store


def image_bytes():
    output=io.BytesIO();exif=Image.Exif();exif[270]='private metadata'
    Image.new('RGB',(3000,1500),'green').save(output,'JPEG',exif=exif)
    return output.getvalue()


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'store',Store(tmp_path))
    monkeypatch.setattr(main.settings,'ingress',False)
    monkeypatch.setattr(main.settings,'token','')
    monkeypatch.setattr(main.settings,'options',{'plantnet_api_key':'plantnet-secret','perenual_api_key':'perenual-secret'})
    return TestClient(main.app,headers={'X-PlantCare-Request':'1'})


def transport(monkeypatch,handler):
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))


def candidate(name='Aloe vera',score=.87):
    return {'score':score,'species':{'scientificNameWithoutAuthor':name,'commonNames':['Aloe'],'family':{'scientificNameWithoutAuthor':'Asphodelaceae'}}}


def test_recognition_native_request_normalization_and_no_archive_writes(client,monkeypatch):
    def handler(request):
        assert request.url.host=='my-api.plantnet.org'
        assert request.url.params['lang']=='it' and request.url.params['api-key']=='plantnet-secret'
        body=request.content
        assert b'name="organs"' in body and b'flower' in body
        raw=body[body.index(b'\xff\xd8'):];raw=raw[:raw.index(b'\xff\xd9')+2]
        with Image.open(io.BytesIO(raw)) as photo:
            assert photo.size==(2000,1000) and len(photo.getexif())==0
        return httpx.Response(200,json={'results':[candidate() for _ in range(8)]})
    transport(monkeypatch,handler)
    before=main.store.list('plants')
    result=client.post('/api/identify',data={'organ':'flower','consent':'true'},files={'file':('my-garden.jpg',image_bytes(),'image/jpeg')})
    assert result.status_code==200,result.text
    assert len(result.json()['candidates'])==5
    assert result.json()['candidates'][0]['category']=='Succulenta'
    assert 'secret' not in result.text and not list(main.store.photos.iterdir())
    assert main.store.list('plants')==before


def test_recognition_requires_consent_key_valid_organ_and_image(client,monkeypatch):
    def no_network(*args):pytest.fail('Must not send a request')
    transport(monkeypatch,no_network)
    path='/api/identify'
    assert client.post(path,files={'file':('a.jpg',b'bad')}).status_code==422
    for organ,content in [('invalid',image_bytes()),('leaf',b'invalid image')]:
        assert client.post(path,data={'consent':'true','organ':organ},files={'file':('a.jpg',content)}).status_code==422
    main.settings.options['plantnet_api_key']=''
    assert 'Configura' in client.post(path,data={'consent':'true'},files={'file':('a.jpg',image_bytes())}).json()['detail']
    main.settings.options['max_photo_mb']=1
    assert client.post(path,data={'consent':'true'},files={'file':('a.jpg',b'x'*(1024*1024+1))}).status_code==413


@pytest.mark.parametrize('status',[401,403,429,500])
def test_recognition_errors_do_not_echo_key(client,monkeypatch,status):
    transport(monkeypatch,lambda r:httpx.Response(status,json={'message':'plantnet-secret '+str(r.url)}))
    response=client.post('/api/identify',data={'consent':'true'},files={'file':('a.jpg',image_bytes())})
    assert response.status_code in (422,424) and 'secret' not in response.text
    assert 'Pl@ntNet' in response.text


@pytest.mark.parametrize('payload,code',[({'results':[]},200),({'results':[candidate(score=2)]},422),({'not-results':[]},422)])
def test_recognition_empty_and_malformed_results(client,monkeypatch,payload,code):
    transport(monkeypatch,lambda r:httpx.Response(200,json=payload))
    response=client.post('/api/identify',data={'consent':'true'},files={'file':('a.jpg',image_bytes())})
    assert response.status_code==code


@pytest.mark.parametrize('label,value,unit,expected',[('minimum','2-4','days',14),('average','10-11','days',11),('none','1','days',30),('frequent','2','weeks',3),('frequent','100','days',60)])
def test_perenual_native_watering_rules(label,value,unit,expected):
    assert knowledge.watering_days({'value':value,'unit':unit},label)==expected


def test_perenual_exact_match_and_unknown_safety(client,monkeypatch):
    def handler(r):
        assert r.url.params['key']=='perenual-secret'
        if r.url.path.endswith('species-list'):
            return httpx.Response(200,json={'data':[{'id':1,'scientific_name':['Wrong plant']},{'id':2,'scientific_name':['Ficus elastica']}]})
        assert r.url.path.endswith('/2')
        return httpx.Response(200,json={'scientific_name':['Ficus elastica'],'watering':'Minimum','watering_general_benchmark':{'value':'3-5','unit':'days'},'sunlight':['part shade'],'poisonous_to_pets':True})
    transport(monkeypatch,handler)
    response=client.post('/api/knowledge/profile',json={'scientificName':'Ficus elastica'})
    assert response.status_code==200,response.text
    p=response.json();assert p['exactMatch'] and p['wateringDays']==14
    assert p['poisonousToPets'] is True and p['poisonousToHumans'] is None
    assert not main.store.list('plants') and not main.store.list('speciesBiologies')


@pytest.mark.parametrize('status',[403,429])
def test_perenual_synonym_brief_fallback_and_approximate_match(client,monkeypatch,status):
    queries=[]
    def handler(r):
        if r.url.path.endswith('species-list'):
            queries.append(r.url.params['q'])
            return httpx.Response(200,json={'data':[] if len(queries)==1 else [{'id':3,'scientific_name':['Calathea orbifolia'],'watering':'Average','sunlight':['part shade']}]})
        return httpx.Response(status)
    transport(monkeypatch,handler)
    response=client.post('/api/knowledge/profile',json={'scientificName':'Goeppertia orbifolia'})
    assert queries==['Goeppertia orbifolia','Calathea orbifolia']
    p=response.json();assert p['source']=='Perenual · scheda sintetica' and not p['exactMatch']
    assert p['poisonousToPets'] is None and p['soil']==[]


def test_local_library_and_public_settings_hide_secrets(client):
    main.store.put('speciesBiologies',{'id':'species-1','canonicalScientificName':'Ficus elastica','family':'Moraceae','genus':'Ficus','synonyms':[],'providerIdentifiers':{'private':'do-not-return'}})
    result=client.get('/api/knowledge/species').json()
    assert result[0]['scientificName']=='Ficus elastica' and 'providerIdentifiers' not in result[0]
    settings=client.get('/api/settings').json()
    assert settings['services']=={'plantnet':True,'perenual':True,'openplantbook':False}
    assert 'secret' not in json.dumps(settings)
