import asyncio
import httpx
import pytest
from plantcare_web.backend.plantbook import profile,aliases,watering_days
from plantcare_web.backend.settings import Settings

@pytest.mark.parametrize('name,first',[('Zamia','Zamioculcas zamiifolia'),('ZZ plant','Zamioculcas zamiifolia'),('Goeppertia makoyana','Goeppertia makoyana'),('Ficus elastica','Ficus elastica')])
def test_native_aliases(name,first):assert aliases(name)[0]==first

@pytest.mark.parametrize('words,low,high,result',[('ogni 7–10 giorni',None,None,9),('every 90 days',10,20,60),('',70,90,3),('',50,60,5),('',30,40,8),('',10,20,14),('',None,None,7)])
def test_native_intervals(words,low,high,result):assert watering_days(words,low,high)==result

def test_oauth_search_detail_and_no_credentials_in_profile(monkeypatch):
    settings=Settings();settings.options={'openplantbook_client_id':'private-id','openplantbook_secret':'private-secret'}
    def handler(r):
        if r.url.path.endswith('/token/'):
            assert b'client_secret=private-secret' in r.content;return httpx.Response(200,json={'access_token':'private-token'})
        assert r.headers['Authorization']=='Bearer private-token'
        if r.url.path.endswith('/search'):return httpx.Response(200,json={'results':[{'pid':'ficus elastica','display_pid':'Ficus elastica'}]})
        assert r.url.params['lang']=='it' and r.url.params['include']=='care'
        return httpx.Response(200,json={'pid':'ficus elastica','display_pid':'Ficus elastica','min_temp':'18','max_temp':30,'min_soil_moist':30,'max_soil_moist':50,'watering':{'description':'every 8 days'},'soil':['mix','draining']})
    original=httpx.AsyncClient;monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    result=asyncio.run(profile(settings,'Ficus elastica'));assert result['exactMatch'] and result['wateringDays']==8 and result['source']=='Open Plantbook'
    assert result['poisonousToPets'] is None and 'private' not in str(result)
