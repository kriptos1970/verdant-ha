import httpx
import pytest
from plantcare_web.backend.remote_errors import describe

@pytest.mark.parametrize('code,reason,message,expected',[
 (400,'API_KEY_INVALID','api key includes SECRET','non è valida'),
 (403,'API_KEY_HTTP_REFERRER_BLOCKED','SECRET','restrizioni'),
 (403,'','SECRET','non autorizza'),
 (400,'','User location is not supported','località'),
 (404,'','SECRET','non è disponibile'),
 (429,'','SECRET','credito'),
 (503,'','SECRET','HTTP 503'),
])
def test_provider_errors_are_actionable_and_do_not_echo_secrets(code,reason,message,expected):
 request=httpx.Request('GET','https://generativelanguage.googleapis.com/v1beta/models')
 response=httpx.Response(code,json={'error':{'message':message,'details':[{'reason':reason}]}},request=request)
 error=httpx.HTTPStatusError('SECRET',request=request,response=response)
 status,detail=describe(error)
 assert status in (422,424) and expected in detail
 assert 'SECRET' not in detail

@pytest.mark.parametrize('kind',[httpx.ConnectError,httpx.ReadTimeout])
def test_network_failures_survive_ingress_and_hide_raw_errors(kind):
 status,detail=describe(kind('SECRET',request=httpx.Request('GET','https://api.openai.com/v1/models')))
 assert status==424 and 'SECRET' not in detail and 'OpenAI' in detail
