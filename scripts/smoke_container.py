"""In-container smoke test without publishing ports or contacting external services."""
import asyncio
import httpx
from datetime import datetime,timezone
from uuid import uuid4
from backend.main import app, store
from backend.ai_support import ADVICE_CONTEXT_VERSION

async def smoke():
    trusted=httpx.ASGITransport(app=app,client=('172.30.32.2',12345))
    async with httpx.AsyncClient(transport=trusted,base_url='http://plantcare') as client:
        assert (await client.get('/health')).status_code==200
        home=await client.get('/')
        assert home.status_code==200 and 'PlantCare' in home.text
        created=await client.post('/api/plants',headers={'X-PlantCare-Request':'1'},json={'name':'Test container','room':'Test'})
        assert created.status_code==201,created.text
        assert len((await client.get('/api/plants')).json())==1
        plant=created.json()
        product=await client.post('/api/fertilizers',headers={'X-PlantCare-Request':'1'},json={'name':'Prodotto smoke','category':'Altro trattamento'})
        assert product.status_code==201,product.text
        cycle=await client.post(f"/api/plants/{plant['id']}/treatments?version={plant['_version']}",headers={'X-PlantCare-Request':'1'},json={'productID':product.json()['id'],'startDate':datetime.now(timezone.utc).isoformat(),'intervalDays':7,'totalApplications':3,'dose':'Da etichetta'})
        assert cycle.status_code==201,cycle.text
        action=next(a for a in cycle.json()['_actions'] if a['kind']=='Trattamento')
        command={'plantID':plant['id'],'eventID':str(uuid4()).upper(),'expectedActionID':action['id'],'operation':'complete'}
        done=await client.post('/api/care-round/actions',headers={'X-PlantCare-Request':'1'},json=command)
        assert done.status_code==200,done.text
        assert done.json()['plant']['_treatments'][0]['completedApplications']==1
        replay=await client.post('/api/care-round/actions',headers={'X-PlantCare-Request':'1'},json=command)
        assert replay.status_code==200 and replay.json()['replayed'] is True
        assert replay.json()['plant']['_version']==done.json()['plant']['_version']
        insights=await client.get(f"/api/plants/{plant['id']}/care-engine")
        assert insights.status_code==200 and len(insights.json()['recommendations'])==5,insights.text
        current=(await client.get('/api/plants')).json()[0]
        data={'location':{'name':'Test','latitude':42,'longitude':12.5},'placement':'Interno luminoso','weatherEnabled':False,'climate':{'averageTemperature':22,'relativeHumidity':55,'precipitationNextWeek':0}}
        path=f"/api/plants/{plant['id']}/adaptive"
        preview=await client.post(path+f"/preview?version={current['_version']}",headers={'X-PlantCare-Request':'1'},json=data)
        assert preview.status_code==200,preview.text
        saved=await client.post(path+f"/apply?version={current['_version']}&previewID={preview.json()['previewID']}",headers={'X-PlantCare-Request':'1'})
        assert saved.status_code==200,saved.text
        assert saved.json()['adaptivePlan']==preview.json()['plan']
        current=saved.json()
        summary=(await client.get('/api/plants?summary=true')).json()[0]
        assert summary['_summary'] and summary['history']==[] and summary['_careCount']>=1
        detail=(await client.get(f"/api/plants/{plant['id']}")).json()
        assert detail['history']==current['history']
        history=(await client.get('/api/history?limit=1')).json()
        assert len(history['items'])==1 and history['total']>=1

        store.set_state('ai-advice-'+plant['id'],{'contextVersion':ADVICE_CONTEXT_VERSION,'id':'smoke-advice','expectedVersion':current['_version'],'provider':'simulato','model':'nessuno','createdAt':datetime.now(timezone.utc).isoformat(),'wateringDays':7,'fertilizingDays':28,'inspectionDays':7,'pruningDays':90,'repottingDays':365,'careNotes':'Solo collaudo isolato','summaryMarkdown':'Risposta simulata','applied':False})
        advice_path=f"/api/plants/{plant['id']}/advice"
        selection={'adviceID':'smoke-advice','inspection':True}
        headers={'X-PlantCare-Request':'1'}
        preview=await client.post(advice_path+'/preview',headers=headers,json=selection)
        assert preview.status_code==200,preview.text
        applied=await client.post(advice_path+'/apply',headers=headers,json=selection)
        assert applied.status_code==200 and applied.json()['inspectionInterval']==7,applied.text
        assert applied.json()['wateringInterval']==current['wateringInterval']
        assert (await client.get(advice_path)).json()['applied'] is True
        assert (await client.post('/api/ai/models',headers=headers)).status_code==422
        backup=await client.get('/api/backup')
        assert backup.status_code==200 and backup.content.startswith(b'PK')
    untrusted=httpx.ASGITransport(app=app,client=('127.0.0.1',12345))
    async with httpx.AsyncClient(transport=untrusted,base_url='http://plantcare') as client:
        assert (await client.get('/health')).status_code==403
    print('Smoke container OK: UI, API, SQLite, trattamento, replay, piano intelligente, shadow engine, consiglio AI selettivo, backup ZIP e confine Ingress.')
asyncio.run(smoke())
