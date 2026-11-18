import asyncio
import base64
import binascii
import io
import json
import math
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo
import httpx
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Query, Body, Form
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError
from .settings import Settings
from . import __version__
from .storage import Store, Conflict
from .models import Plant, Product, EventRequest, Question, Mapping, Measurement, TreatmentInput, RoundCommand, AdaptiveRequest, MoveRequest, CareLocation, AIModelSelection, AdviceSelection, HealthPhotoSession, LanguagePreference
from .domain import iso, now, parse, plant_view, schedule, active_history, pending_actions
from .care_kinds import legacy_view, legacy_action, canonical_health
from .backup import decode_archive, decode_zip, export_zip, import_archive, summary, MAX_ARCHIVE, resolve_existing_photos
from . import services, ai, care, adaptive
from .treatments import pin_baselines, update_counts, treatment_view

settings=Settings()
store=Store(settings.directory,settings.photo_directory)

@asynccontextmanager
async def lifespan(app):
    store.purge_expired()
    task=asyncio.create_task(services.scheduler(store,settings))
    try: yield
    finally:
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)

app=FastAPI(title='PlantCare Web',version=__version__,lifespan=lifespan,docs_url='/api/docs',openapi_url='/api/openapi.json')

@app.middleware('http')
async def boundary(request,call_next):
    if settings.ingress and (not request.client or request.client.host!='172.30.32.2'):
        return JSONResponse({'detail':'Accesso consentito solo tramite Home Assistant Ingress.','code':'forbidden'},status_code=403)
    if request.method in {'POST','PUT','PATCH','DELETE'} and request.headers.get('x-plantcare-request')!='1':
        return JSONResponse({'detail':'Richiesta non valida.','code':'forbidden'},status_code=403)
    length=request.headers.get('content-length')
    limit=2*1024**3 if request.url.path in {'/api/import','/api/import/preview'} else MAX_ARCHIVE+1024*1024
    if length and (not length.isdigit() or int(length)>limit):
        return JSONResponse({'detail':'Richiesta troppo grande.','code':'too_large'},status_code=413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path.startswith('/api') and not request.url.path.startswith('/api/photos/'):
        response.headers['Cache-Control']='no-store'
    return response

ERROR_CODES={400:'bad_request',401:'unauthorized',403:'forbidden',404:'not_found',409:'conflict',413:'too_large',422:'validation',424:'remote',502:'remote'}
@app.exception_handler(StarletteHTTPException)
async def http_error(request,error):
    return JSONResponse({'detail':error.detail,'code':ERROR_CODES.get(error.status_code,'error')},status_code=error.status_code,headers=getattr(error,'headers',None))
@app.exception_handler(RequestValidationError)
async def request_validation(request,error):
    return JSONResponse({'detail':'Controlla i dati inseriti.','code':'validation'},status_code=422)
@app.exception_handler(Conflict)
async def conflict(request,error): return JSONResponse({'detail':str(error),'code':'conflict'},status_code=409)
@app.exception_handler(KeyError)
async def missing(request,error): return JSONResponse({'detail':'Elemento non trovato.','code':'not_found'},status_code=404)
@app.exception_handler(ValueError)
async def invalid(request,error): return JSONResponse({'detail':str(error),'code':'validation'},status_code=422)
@app.exception_handler(httpx.HTTPError)
async def remote_error(request,error):
    from .remote_errors import describe
    status,detail=describe(error)
    return JSONResponse({'detail':detail,'code':'remote'},status_code=status)

@app.get('/health')
def health(): return {'status':'ok','version':__version__}
@app.get('/api/settings')
def public_settings(): return {**ai.effective_settings(store,settings).public(),'sensorStatus':store.state('sensor-status'),'aiStatus':store.state('ai-status'),'location':store.state('location'),'adaptiveStatus':store.state('adaptive-status')}

def linked_product(plant, db=None):
    if not plant.get('fertilizerProductID'):
        return None
    try:
        return store.get('fertilizers',plant['fertilizerProductID'],db)[0]
    except KeyError:
        return None


def render_plant(plant, version, db=None):
    from .services import message_language
    return legacy_view(plant_view(plant,settings.zone,version,product=linked_product(plant,db),language=message_language(store,settings)))

@app.get('/api/plants')
def list_plants(summary:bool=False):
    from .archive_views import compact
    return [compact(render_plant(p,v)) if summary else render_plant(p,v) for p,v in store.list('plants')]

@app.get('/api/analytics')
def analytics(days:int=Query(default=30)):
    from .analytics import PERIODS, summary
    if days not in PERIODS:
        raise HTTPException(422,'Scegli un periodo di 30, 90 o 365 giorni.')
    return summary([p for p,_ in store.list('plants')],settings.zone,days)

@app.get('/api/plants/{plant_id}/timeline')
def plant_timeline(plant_id:str,limit:int=Query(default=8,ge=1,le=50)):
    plant,_=store.get('plants',plant_id)
    from .analytics import timeline
    return {'items':timeline(store,plant,limit)}


@app.get('/api/plants/{plant_id}')
def get_plant(plant_id:str):
    p,v=store.get('plants',plant_id)
    return render_plant(p,v)

@app.get('/api/history')
def list_history(page:int=Query(default=1,ge=1,le=1000000),limit:int=Query(default=50,ge=1,le=100),plant_id:str='',room:str='',kind:str='',from_day:str='',to_day:str=''):
    from .archive_views import history_page
    return history_page(store,settings.zone,page,limit,plant_id,room,kind,from_day,to_day)
@app.post('/api/plants',status_code=201)
def create_plant(body:Plant):
    value=body.model_dump()
    if value.get('carePlanMode')=='Intelligente':
        raise HTTPException(422,'Salva la pianta in Manuale, poi usa Configura piano intelligente dalla sua scheda.')
    if value['history'] or value.get('treatmentPlans'): raise HTTPException(422,'Usa il flusso di importazione per le cronologie esistenti.')
    p,v=store.put('plants',value)
    return render_plant(p,v)
@app.put('/api/plants/{plant_id}')
def update_plant(plant_id:str,body:Plant,version:int=Query(ge=1)):
    if body.model_extra and body.model_extra.get('_summary'):raise HTTPException(422,'Apri la scheda completa prima di modificarla.')
    if body.id!=plant_id: raise HTTPException(422,'Identificativo non corrispondente.')
    with store.connection() as db:
        old,_=store.get('plants',plant_id,db)
        value=body.model_dump()
        if value['history']!=old['history']: raise HTTPException(422,'Modifica le cure dal diario.')
        if value.get('treatmentPlans')!=old.get('treatmentPlans'): raise HTTPException(422,'Modifica i cicli dalla sezione Trattamenti.')
        if value.get('carePlanMode')=='Intelligente' and old.get('carePlanMode')!='Intelligente': raise HTTPException(422,'Usa Configura piano intelligente dalla scheda della pianta.')
        if old.get('carePlanMode')=='Intelligente' and value.get('adaptivePlan'):
            if any(value.get(k)!=old.get(k) for k in ['wateringInterval','fertilizingInterval','inspectionInterval']):
                value['adaptivePlan']={**value['adaptivePlan'],'revisionSource':'Modifica manuale','revisedAt':iso(now())}
        p,v=store.put('plants',value,version,db)
    return render_plant(p,v)
@app.delete('/api/plants/{plant_id}',status_code=204)
def delete_plant(plant_id:str,version:int=Query(ge=1)): store.trash(plant_id,version)

@app.post('/api/plants/{plant_id}/move')
def move_plant(plant_id:str,body:MoveRequest):
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        if current!=body.version: raise Conflict('La scheda è cambiata. Ricarica prima di spostare la pianta.')
        previous_room=plant.get('room','')
        plan=plant.get('adaptivePlan')
        previous_placement=(plan or {}).get('placement')
        plant['room']=body.room
        if plan:
            plan['placement']=body.placement
            if plant.get('carePlanMode')=='Intelligente' and all(plan.get(k) is not None for k in ['locationName','latitude','longitude','averageTemperature','relativeHumidity','precipitationNextWeek']):
                location=dict(name=plan['locationName'],detail='',latitude=plan['latitude'],longitude=plan['longitude'])
                climate={k:plan[k] for k in ['averageTemperature','relativeHumidity','precipitationNextWeek']}
                refreshed=adaptive.make_plan(plant['species'],plant.get('family') or '',body.placement,location,climate,parse(body.date),settings.zone,adaptive.saved_botanical(plan))
                refreshed['weatherEnabled']=plan.get('weatherEnabled',False)
                adaptive.apply_plan(plant,refreshed,settings.zone,plan,parse(body.date))
        route=f"{previous_room} → {plant['room']}" if previous_room!=plant['room'] else f"{previous_placement or previous_room} → {body.placement}"
        note=' · '.join(value for value in [route,body.note.strip()] if value)
        plant.setdefault('history',[]).append({'id':str(uuid4()).upper(),'kind':'move','date':iso(parse(body.date)),'status':'completed','note':note,'origin':'user','schemaVersion':2})
        p,v=store.put('plants',plant,current,db)
    return render_plant(p,v)

@app.post('/api/plants/{plant_id}/safety/refresh')
async def refresh_safety(plant_id:str):
    plant,version=store.get('plants',plant_id)
    species=plant.get('species','').strip()
    if not species: raise HTTPException(422,'Indica la specie prima di cercare i dati di sicurezza.')
    from .knowledge import profile as perenual_profile
    if not settings.options.get('perenual_api_key','').strip():
        raise HTTPException(422,'Aggiungi la chiave Perenual nelle opzioni dell’add-on per scaricare i dati di sicurezza.')
    try:
        botanical=await perenual_profile(settings,species)
    except (ValueError,httpx.HTTPError) as error:
        raise HTTPException(502,'Perenual non ha risposto. Riprova più tardi.') from error
    if not botanical or (botanical.get('poisonousToHumans') is None and botanical.get('poisonousToPets') is None):
        raise HTTPException(404,'Perenual non riporta dati di sicurezza per questa specie.')
    safety=dict(poisonousToHumans=botanical.get('poisonousToHumans'),poisonousToPets=botanical.get('poisonousToPets'),sourceName=botanical.get('source') or 'Perenual',sourceURL=botanical.get('sourceURL') or 'https://perenual.com',fetchedAt=botanical.get('fetchedAt') or iso(now()))
    with store.connection() as db:
        current,latest=store.get('plants',plant_id,db)
        if latest!=version or current.get('species','').strip()!=species: raise Conflict('La pianta è cambiata durante la ricerca. Riprova.')
        current['safetyProfile']=safety
        p,v=store.put('plants',current,latest,db)
    return {'safetyProfile':safety,'_version':v}

def trash_item(plant,version,deleted):
    from datetime import timedelta
    removed=parse(deleted)
    expires=removed+timedelta(days=store.TRASH_DAYS)
    return {'id':plant['id'],'name':plant.get('name',''),'species':plant.get('species',''),'room':plant.get('room',''),'photoPath':plant.get('photoPath'),'deletedAt':deleted,'expiresAt':iso(expires),'daysLeft':max(0,math.ceil((expires-now()).total_seconds()/86400)),'_version':version}

@app.get('/api/trash')
def trash(): 
    store.purge_expired()
    return {'retentionDays':store.TRASH_DAYS,'items':[trash_item(p,v,d) for p,v,d in store.trash_list()]}

@app.post('/api/trash/{plant_id}/restore')
def restore_plant(plant_id:str,version:int=Query(ge=1)):
    v=store.restore(plant_id,version)
    p,_=store.get('plants',plant_id)
    return render_plant(p,v)

@app.delete('/api/trash/{plant_id}',status_code=204)
def purge_plant(plant_id:str,version:int=Query(ge=1)): store.purge(plant_id,version)

@app.delete('/api/trash',status_code=204)
def empty_trash(): store.purge_all()

async def proposed_plan(plant, body, version=None):
    location = body.location.model_dump()
    climate = await adaptive.fetch_climate(location) if body.weatherEnabled else body.climate.model_dump()
    previous = plant.get('adaptivePlan') or {}
    botanical=adaptive.saved_botanical(previous)
    if body.botanicalPreviewID:
        saved=store.state('botanical-preview-'+plant['id'])
        if not saved or saved['id']!=body.botanicalPreviewID or saved['version']!=version or (now()-parse(saved['createdAt'])).total_seconds()>1800:raise Conflict('Profilo botanico scaduto o cambiato. Consulta nuovamente la specie.')
        botanical=saved['profile']
        if not botanical.get('exactMatch') and not body.confirmBotanicalMatch:raise HTTPException(422,'Conferma la corrispondenza botanica prima di usare una specie approssimativa.')
        if type(botanical.get('wateringDays')) is not int or not 1<=botanical['wateringDays']<=60:raise HTTPException(422,'Profilo botanico non utilizzabile per il piano.')
    from .services import message_language
    plan = adaptive.make_plan(plant['species'],plant.get('family') or '',body.placement,location,climate,zone=settings.zone,botanical=botanical,language=message_language(store,settings))
    if body.botanicalPreviewID:
        plan.update(botanicalScientificName=botanical['scientificName'],botanicalFetchedAt=botanical['fetchedAt'],botanicalExactMatch=botanical['exactMatch'])
    plan['weatherEnabled'] = body.weatherEnabled
    candidate = {**plant,'carePlanMode':'Intelligente'}
    adaptive.apply_plan(candidate,plan,settings.zone,previous or None)
    return candidate

@app.post('/api/plants/{plant_id}/adaptive/preview')
async def preview_adaptive(plant_id:str,body:AdaptiveRequest,version:int=Query(ge=1)):
    plant,current=store.get('plants',plant_id)
    if version!=current: raise Conflict('La scheda è cambiata. Ricarica prima di calcolare il piano.')
    candidate=await proposed_plan(plant,body,current)
    _,latest=store.get('plants',plant_id)
    if latest!=current:raise Conflict('La pianta è cambiata durante il calcolo. Ricalcola il piano.')
    previewID=str(uuid4())
    store.set_state('adaptive-preview-'+plant_id,{'id':previewID,'version':version,'plan':candidate['adaptivePlan'],'createdAt':iso(now())})
    return {'plan':candidate['adaptivePlan'],'expectedVersion':version,'previewID':previewID}

@app.post('/api/plants/{plant_id}/adaptive/apply')
def apply_adaptive(plant_id:str,previewID:str=Query(min_length=1,max_length=100),version:int=Query(ge=1)):
    plant,current=store.get('plants',plant_id)
    if version!=current: raise Conflict('La scheda è cambiata. Ricarica prima di applicare il piano.')
    preview=store.state('adaptive-preview-'+plant_id)
    if not preview or preview['id']!=previewID or preview['version']!=version or (now()-parse(preview['createdAt'])).total_seconds()>1800:
        raise Conflict('Anteprima scaduta o cambiata. Ricalcola il piano prima di applicarlo.')
    plan=preview['plan']
    candidate={**plant,'carePlanMode':'Intelligente','adaptivePlan':plan,'wateringInterval':plan['wateringDays'],'fertilizingInterval':plan['fertilizingDays']}
    if plant.get('inspectionInterval') is not None: candidate['inspectionInterval']=plan['inspectionDays']
    candidate['history']=plant['history']+[{'id':str(uuid4()).upper(),'kind':'planUpdate','date':iso(now()),'status':'completed','note':'Piano intelligente ricalcolato con il pianificatore nativo.','origin':'user','schemaVersion':2}]
    with store.connection() as db:
        p,v=store.put('plants',candidate,version,db)
    return render_plant(p,v)

@app.get('/api/preferences')
def preferences(): return store.state('preferences',{'language':settings.options.get('language','auto')})
@app.put('/api/preferences')
def save_preferences(body:LanguagePreference):
    store.set_state('preferences',body.model_dump())
    return body
@app.get('/api/preferences/location')
def default_location(): return store.state('location')
@app.put('/api/preferences/location')
def save_default_location(body:CareLocation):
    location=body.model_dump()
    store.set_state('location',location)
    return location
@app.delete('/api/preferences/location',status_code=204)
def clear_default_location(): store.set_state('location',None)

async def geocode_locations(query,language):
    async with httpx.AsyncClient(timeout=20) as client:
        response=await client.get('https://geocoding-api.open-meteo.com/v1/search',params={'name':query,'count':8,'language':language,'format':'json'})
        response.raise_for_status()
    results=response.json().get('results') or []
    return [{'name':item.get('name') or '','detail':', '.join(value for value in [item.get('admin1'),item.get('country')] if value),'latitude':item['latitude'],'longitude':item['longitude']} for item in results if item.get('name') and item.get('latitude') is not None and item.get('longitude') is not None]

@app.get('/api/weather/locations')
async def location_search(q:str=Query(min_length=2,max_length=100)):
    from .services import message_language
    try:
        return await geocode_locations(q.strip(),'en' if message_language(store,settings)=='en' else 'it')
    except (httpx.HTTPError,ValueError,KeyError,TypeError) as error:
        raise HTTPException(502,'Open-Meteo non ha risposto. Riprova più tardi.') from error

@app.get('/api/fertilizers')
def products(): return [{**p,'_version':v} for p,v in store.list('fertilizers')]
@app.post('/api/fertilizers',status_code=201)
def create_product(body:Product):
    p,v=store.put('fertilizers',body.model_dump())
    return {**p,'_version':v}
@app.put('/api/fertilizers/{identifier}')
def update_product(identifier:str,body:Product,version:int=Query(ge=1)):
    if body.id!=identifier: raise HTTPException(422,'Identificativo non corrispondente.')
    p,v=store.put('fertilizers',body.model_dump(),version)
    return {**p,'_version':v}
@app.delete('/api/fertilizers/{identifier}',status_code=204)
def delete_product(identifier:str,version:int=Query(ge=1)):
    for p,_ in store.list('plants'):
        if p.get('fertilizerProductID')==identifier or any(t['productID']==identifier and treatment_view(p,t,ZoneInfo(settings.zone))['status']=='active' for t in p.get('treatmentPlans') or []):
            raise Conflict('Il prodotto è associato a una pianta o a un ciclo attivo. Rimuovi prima l’associazione o interrompi il ciclo.')
    store.delete('fertilizers',identifier,version)

@app.get('/api/schedule')
def calendar():
    from .services import message_language
    language=message_language(store,settings)
    return sorted([legacy_action(a) for p,_ in store.list('plants') for a in pending_actions(p,settings.zone,product=linked_product(p),language=language)],key=lambda a:(a['dueDate'],a['plantName']))

@app.post('/api/plants/{plant_id}/events')
def add_event(plant_id:str,body:EventRequest):
    with store.connection() as db:
        plant,version=store.get('plants',plant_id,db)
        changed=care.record(plant,body,settings.zone,linked_product(plant,db))
        p,v=store.put('plants',plant,version,db) if changed else (plant,version)
        return render_plant(p,v,db)

@app.put('/api/plants/{plant_id}/events/{event_id}')
def edit_event(plant_id:str,event_id:str,body:EventRequest,version:int=Query(ge=1)):
    if body.id!=event_id: raise HTTPException(422,'Identificativo non corrispondente.')
    if body.status=='postponed' and (not body.postponedUntil or parse(body.postponedUntil)<=parse(body.date)): raise HTTPException(422,'Data di rinvio non valida.')
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        event=next((e for e in plant['history'] if e['id']==event_id and not e.get('deletedAt')),None)
        if event is None: raise KeyError(event_id)
        pin_baselines(plant)
        if 'treatmentPlanID' in body.model_fields_set and body.treatmentPlanID!=event.get('treatmentPlanID'):
            raise HTTPException(422,'Il ciclo di una registrazione esistente non può essere cambiato.')
        if event.get('treatmentPlanID') and body.kind!='treatment':
            raise HTTPException(422,'Una registrazione del ciclo deve restare un trattamento.')
        fields=care.event_payload(body)
        for key in ['treatmentPlanID','productID']:
            if key not in body.model_fields_set: fields.pop(key,None)
        event.update(fields)
        event.update(updatedAt=iso(now()),revision=event.get('revision',1)+1)
        care.recalculate(plant)
        p,v=store.put('plants',plant,version,db)
    return render_plant(p,v)

@app.delete('/api/plants/{plant_id}/events/{event_id}')
def delete_event(plant_id:str,event_id:str,version:int=Query(ge=1)):
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        event=next((e for e in plant['history'] if e['id']==event_id),None)
        if event is None: raise KeyError(event_id)
        pin_baselines(plant)
        event.update(deletedAt=iso(now()),updatedAt=iso(now()),revision=event.get('revision',1)+1)
        care.recalculate(plant)
        p,v=store.put('plants',plant,version,db)
    return render_plant(p,v)

@app.post('/api/care-round/actions')
def round_action(body:RoundCommand):
    from datetime import timedelta
    with store.connection() as db:
        plant,version=store.get('plants',body.plantID,db)
        existing=next((e for e in plant['history'] if e['id']==body.eventID),None)
        if existing:
            if existing.get('sourceActionID')!=body.expectedActionID:
                raise Conflict('Identificativo della registrazione già utilizzato.')
            completed=0 if existing.get('deletedAt') or existing.get('status')=='postponed' else 1
            if completed and any(e['id']==existing.get('pairedFertilizingEventID') for e in active_history(plant)):
                completed+=1
            return {'plant':render_plant(plant,version,db),'completedEvents':completed,'replayed':True}
        product=linked_product(plant,db)
        action=next((a for a in pending_actions(plant,settings.zone,product=product) if a['id']==body.expectedActionID),None)
        if action is None:
            raise Conflict('L’attività è cambiata durante il giro. Aggiorna le attività prima di continuare.')
        date=now()
        postponed=body.operation=='postpone'
        event=EventRequest(id=body.eventID,kind=action['kind'],date=iso(date),
            status='postponed' if postponed else 'completed',
            postponedUntil=iso(date.astimezone(ZoneInfo(settings.zone))+timedelta(days=1)) if postponed else None,
            note=body.note,includingFertilizing=body.includingFertilizing,
            treatmentPlanID=action.get('treatmentPlanID'),productID=action.get('productID'),
            expectedApplicationNumber=action.get('applicationNumber'),scheduledDueDate=action['dueDate'])
        care.record(plant,event,settings.zone,product)
        record=next(e for e in plant['history'] if e['id']==body.eventID)
        record['sourceActionID']=body.expectedActionID
        completed=0 if postponed else 1+int(bool(record.get('pairedFertilizingEventID')))
        p,v=store.put('plants',plant,version,db)
        return {'plant':render_plant(p,v,db),'completedEvents':completed,'replayed':False}

@app.post('/api/plants/{plant_id}/treatments',status_code=201)
def create_treatment(plant_id:str,body:TreatmentInput,version:int=Query(ge=1)):
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        product,_=store.get('fertilizers',body.productID,db)
        plans=plant.get('treatmentPlans') or []
        if any(p['id']==body.id for p in plans):
            raise Conflict('Questo ciclo è già presente. Ricarica la scheda.')
        plan={**body.model_dump(),'productName':product['name'],'completedApplications':0,'legacyCompletedApplications':0}
        plant['treatmentPlans']=plans+[plan]
        p,v=store.put('plants',plant,version,db)
        return render_plant(p,v,db)

@app.put('/api/plants/{plant_id}/treatments/{plan_id}')
def edit_treatment(plant_id:str,plan_id:str,body:TreatmentInput,version:int=Query(ge=1)):
    if body.id!=plan_id: raise HTTPException(422,'Identificativo non corrispondente.')
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        plan=next((p for p in plant.get('treatmentPlans') or [] if p['id']==plan_id),None)
        if plan is None: raise KeyError(plan_id)
        pin_baselines(plant)
        count=treatment_view(plant,plan,ZoneInfo(settings.zone))['completedApplications']
        if body.totalApplications<count: raise HTTPException(422,'Il totale non può essere inferiore alle applicazioni già registrate.')
        product,_=store.get('fertilizers',body.productID,db)
        plan.update(body.model_dump())
        plan['productName']=product['name']
        update_counts(plant)
        p,v=store.put('plants',plant,version,db)
        return render_plant(p,v,db)

@app.delete('/api/plants/{plant_id}/treatments/{plan_id}')
def cancel_treatment(plant_id:str,plan_id:str,version:int=Query(ge=1)):
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        plan=next((p for p in plant.get('treatmentPlans') or [] if p['id']==plan_id),None)
        if plan is None: raise KeyError(plan_id)
        plan['cancelledAt']=iso(now())
        p,v=store.put('plants',plant,version,db)
        return render_plant(p,v,db)

@app.post('/api/plants/{plant_id}/treatments/{plan_id}/resume')
def resume_treatment(plant_id:str,plan_id:str,version:int=Query(ge=1)):
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        plan=next((p for p in plant.get('treatmentPlans') or [] if p['id']==plan_id),None)
        if plan is None: raise KeyError(plan_id)
        store.get('fertilizers',plan['productID'],db)
        plan['cancelledAt']=None
        p,v=store.put('plants',plant,version,db)
        return render_plant(p,v,db)

@app.post('/api/photos',status_code=201)
async def upload_photo(file:UploadFile=File()):
    max_bytes=int(settings.options.get('max_photo_mb',20))*1024*1024
    content=await file.read(max_bytes+1)
    if len(content)>max_bytes: raise HTTPException(413,'Fotografia oltre il limite configurato.')
    try:
        with Image.open(io.BytesIO(content)) as image:
            image=ImageOps.exif_transpose(image)
            image.thumbnail((2400,2400))
            output=io.BytesIO()
            image.convert('RGB').save(output,format='JPEG',quality=88)
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError): raise HTTPException(422,'Immagine non supportata. Usa JPEG, PNG o WebP.')
    import shutil
    if shutil.disk_usage(store.photos).free < len(output.getvalue())+50*1024*1024:
        raise HTTPException(507,'Spazio insufficiente nella cartella delle foto.')
    path=store.write_photo(output.getvalue())
    return {'path':path}
@app.post('/api/identify')
async def identify_plant(file:UploadFile=File(), organ:str=Form('leaf'), consent:bool=Form(False)):
    from .knowledge import identify
    if not consent: raise HTTPException(422,'Conferma l’invio della fotografia a Pl@ntNet.')
    max_bytes=int(settings.options.get('max_photo_mb',20))*1024*1024
    content=await file.read(max_bytes+1)
    if len(content)>max_bytes: raise HTTPException(413,'Fotografia oltre il limite configurato.')
    return await identify(settings,content,organ)

@app.get('/api/knowledge/plants/{plant_id}/guide')
def plant_guide(plant_id:str,language:str='it'):
    from .health_guides import practical_guide
    plant,_=store.get('plants',plant_id)
    from .services import message_language
    language=language if language in {'it','en'} else message_language(store,settings)
    return practical_guide(plant,language)

@app.post('/api/knowledge/diagnosis')
def guided_diagnosis(body:dict=Body(...)):
    from .health_guides import diagnosis
    plant_id=body.get('plantID');symptoms=body.get('symptoms')
    if not isinstance(plant_id,str) or not isinstance(symptoms,list) or len(symptoms)>6 or any(not isinstance(s,str) for s in symptoms):
        raise HTTPException(422,'Scegli una pianta e i sintomi osservati.')
    store.get('plants',plant_id)
    from .services import message_language
    language=body.get('language')
    language=language if language in {'it','en'} else message_language(store,settings)
    return {'plantID':plant_id,'advice':diagnosis(symptoms,language)}

@app.get('/api/knowledge/species')
def species_library():
    return [dict(id=p['id'],scientificName=p.get('canonicalScientificName',''),family=p.get('family',''),genus=p.get('genus',''),synonyms=p.get('synonyms',[]),updatedAt=p.get('updatedAt')) for p,_ in store.list('speciesBiologies')]

async def fetch_botanical_profile(name):
    if settings.options.get('openplantbook_client_id') and settings.options.get('openplantbook_secret'):
        from .plantbook import profile as plantbook_profile
        try:
            result=await plantbook_profile(settings,name.strip())
            if result:return result
        except (ValueError,httpx.HTTPError):
            if not settings.options.get('perenual_api_key'):raise
        if not settings.options.get('perenual_api_key'):return None
    from .knowledge import profile
    return await profile(settings,name)

@app.get('/api/knowledge/catalog')
async def online_catalog(q:str=Query(default='',max_length=200),focus:str='Da interno',page:int=Query(default=1,ge=1,le=100)):
    from .catalog import search
    return await search(q,focus,page)

@app.post('/api/knowledge/profile')
async def botanical_profile(body:dict=Body(...)):
    name=body.get('scientificName')
    if not isinstance(name,str) or not name.strip() or len(name)>300:raise HTTPException(422,'Inserisci il nome scientifico della specie.')
    return await fetch_botanical_profile(name.strip())

@app.post('/api/plants/{plant_id}/botanical/preview')
async def preview_botanical_profile(plant_id:str,version:int=Query(ge=1)):
    plant,current=store.get('plants',plant_id)
    if version!=current:raise Conflict('La pianta è cambiata. Riapri la scheda.')
    if not plant['species'].strip():raise HTTPException(422,'Indica la specie prima di consultare il profilo botanico.')
    profile=await fetch_botanical_profile(plant['species'])
    if not profile:return {'profile':None,'previewID':None}
    _,actual=store.get('plants',plant_id)
    if actual!=current:raise Conflict('La pianta è cambiata durante la ricerca. Riapri la scheda.')
    identifier=str(uuid4())
    store.set_state('botanical-preview-'+plant_id,{'id':identifier,'version':current,'profile':profile,'createdAt':iso(now())})
    return {'profile':profile,'previewID':identifier}

@app.get('/api/photos/{filename}')
def photo(filename:str, thumb:bool=False):
    if len(filename)!=68 or not filename.endswith('.jpg') or any(c not in '0123456789abcdef' for c in filename[:-4]): raise KeyError(filename)
    path=store.photos/filename
    if not path.is_file(): raise KeyError(filename)
    if thumb:
        cached=store.thumbnails/filename
        if not cached.exists():
            with store.thumbnails_lock:
                if not cached.exists():
                    try:
                        temporary=cached.with_suffix('.tmp')
                        with Image.open(path) as image:
                            image.draft('RGB',(480,480))
                            image=ImageOps.exif_transpose(image)
                            image.thumbnail((480,480))
                            image.convert('RGB').save(temporary,format='JPEG',quality=76,progressive=True)
                        temporary.replace(cached)
                    except (OSError,UnidentifiedImageError):
                        try: temporary.unlink()
                        except OSError: pass
                        raise HTTPException(422,'Miniatura non disponibile.')
        path=cached
    etag=f'"{filename}-thumb"' if thumb else f'"{filename}"'
    return FileResponse(path,headers={'Cache-Control':'private, max-age=31536000, immutable','ETag':etag})

async def handle_import(file,commit=False):
    import tempfile
    import zipfile
    with tempfile.TemporaryDirectory(prefix='import-',dir=store.root) as temporary:
        path=Path(temporary)/'upload'
        size=0
        with path.open('wb') as target:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>2*1024**3: raise HTTPException(413,'Backup oltre il limite di 2 GB.')
                target.write(chunk)
        try:
            is_zip=zipfile.is_zipfile(path)
            if not is_zip and size>MAX_ARCHIVE: raise ValueError('Backup JSON oltre il limite di 150 MB.')
            archive=decode_zip(path,temporary) if is_zip else decode_archive(path.read_bytes())
            resolve_existing_photos(archive,store.photos)
            return import_archive(store,archive) if commit else summary(archive)
        except (KeyError,TypeError,ValueError,ValidationError,binascii.Error,zipfile.BadZipFile) as e:
            raise HTTPException(422,'Backup non valido: '+str(e)[:250])

@app.post('/api/import/preview')
async def preview_import(file:UploadFile=File()): return await handle_import(file)
@app.post('/api/import')
async def commit_import(file:UploadFile=File()): return await handle_import(file,True)
@app.get('/api/storage')
def storage_status():
    import shutil
    usage=shutil.disk_usage(store.photos)
    files=list(store.photos.glob('*.jpg'))
    return {'photoDirectory':str(store.photos),'photos':len(files),'photoBytes':sum(p.stat().st_size for p in files),'databaseBytes':sum(p.stat().st_size for p in store.root.glob('plantcare.sqlite*')),'freeBytes':usage.free,'shared':str(store.photos).startswith('/share/')}

@app.get('/api/backup')
def backup(format:str='zip'):
    if format=='json':
        return JSONResponse(store.export(),headers={'Content-Disposition':'attachment; filename="plantcare-backup.json"'})
    from starlette.background import BackgroundTask
    import shutil
    path=export_zip(store)
    return FileResponse(path,filename='plantcare-backup.zip',media_type='application/zip',background=BackgroundTask(shutil.rmtree,path.parent))

@app.get('/api/sensors')
async def get_sensors(): return await services.sensors(settings)
@app.get('/api/sensor-mappings')
def mappings(): return store.state('sensor-mappings',[])
@app.put('/api/sensor-mappings')
def save_mappings(body:list[Mapping]):
    exposed=set(settings.options.get('exposed_entities',[]))
    plants=[p for p,_ in store.list('plants')]
    for mapping in body:
        if mapping.entityID not in exposed: raise HTTPException(422,'Sensore non autorizzato nelle opzioni dell’add-on.')
        if bool(mapping.plantID)==bool(mapping.room): raise HTTPException(422,'Scegli una pianta oppure una stanza.')
        if mapping.plantID and not any(p['id']==mapping.plantID for p in plants): raise HTTPException(422,'Pianta non trovata.')
    store.set_state('sensor-mappings',[m.model_dump() for m in body])
    return body
@app.post('/api/sensors/poll')
async def sample(): return await services.poll(store,settings)
@app.get('/api/plants/{plant_id}/care-engine')
def shadow_engine(plant_id:str):
    from .care_engine import evaluate
    with store.connection() as db:
        plant,_=store.get('plants',plant_id,db)
        biology=None
        if plant.get('speciesBiologyID'):
            try: biology,_=store.get('speciesBiologies',plant['speciesBiologyID'],db)
            except KeyError: pass
        rows=[dict(r) for r in db.execute('SELECT * FROM measurements WHERE plant_id=? ORDER BY measured_at DESC LIMIT 10000',(plant_id,))]
        native=[m for m in store.state('native-measurements',[],db) if m.get('plantID')==plant_id]
    # Native originals retain provenance/reliability that the legacy SQL projection lacks.
    from .care_engine import normalized_measurements
    native_keys={(m['kind'],m['value'],m['unit'],iso(parse(m['date']))) for m in normalized_measurements(native)}
    rows=[r for r in rows if not any((m['kind'],m['value'],m['unit'],iso(parse(m['date']))) in native_keys for m in normalized_measurements([r]))]
    return evaluate(plant,rows+native,biology,settings.zone)

@app.get('/api/plants/{plant_id}/measurements')
def measurements(plant_id:str):
    store.get('plants',plant_id)
    with store.connection() as db:
        rows=[dict(r) for r in db.execute('SELECT * FROM measurements WHERE plant_id=? ORDER BY measured_at DESC LIMIT 10000',(plant_id,))]
        native=[m for m in store.state('native-measurements',[],db) if m.get('plantID')==plant_id]
    from .care_engine import normalized_measurements
    normalized=normalized_measurements(native)
    native_keys={(m['kind'],m['value'],m['unit'],iso(parse(m['date']))) for m in normalized}
    result=[]
    for m in normalized:
        source='manual' if m['sourceIdentifier']=='manual' else 'smartphoneEstimated' if m['sourceIdentifier']=='smartphoneEstimated' else 'homeAssistant'
        result.append({'id':m['id'],'kind':m['kind'],'value':m['value'],'unit':m['unit'],'measured_at':m['date'],'source_at':m['date'],'entity_id':m['sourceIdentifier'],'source':source,'reliability':round(m['reliability'],2)})
    for row in rows:
        item=normalized_measurements([row])
        if item and (item[0]['kind'],item[0]['value'],item[0]['unit'],iso(parse(item[0]['date']))) in native_keys: continue
        source='manual' if row.get('entity_id')=='manual' else 'homeAssistant'
        result.append({**row,'source':source,'reliability':1.0 if source=='manual' else None})
    result.sort(key=lambda m: m.get('measured_at') or '',reverse=True)
    return result[:500]
@app.post('/api/plants/{plant_id}/measurements',status_code=201)
def add_measurement(plant_id:str,body:Measurement):
    store.get('plants',plant_id)
    with store.connection() as db:
        db.execute('INSERT INTO measurements(plant_id,entity_id,kind,value,unit,measured_at,source_at) VALUES (?,?,?,?,?,?,?)',(plant_id,'manual',body.kind,body.value,body.unit,body.date,body.date))
    return body

@app.get('/api/proposals')
def proposals():
    result=[]
    for p,_ in store.list('proposals'):
        try: plant,version=store.get('plants',p['plantID'])
        except KeyError: continue
        result.append({**p,'stale':version!=p['expectedVersion'] or plant.get('carePlanMode')!='AI'})
    return result
@app.post('/api/ai/models')
async def ai_models():
    from .ai_support import models,effective_settings
    return await models(effective_settings(store,settings))

@app.put('/api/ai/model')
async def select_ai_model(body:AIModelSelection):
    from .ai_support import models
    catalog=await models(settings)
    if body.model not in catalog['models']:raise HTTPException(422,'Modello non presente nel catalogo di questo provider.')
    store.set_state('ai-model-selection',{'provider':catalog['provider'],'model':body.model,'configuredModel':settings.options.get('ai_model') or ''})
    return public_settings()

@app.get('/api/plants/{plant_id}/advice')
def last_advice(plant_id:str):
    _,version=store.get('plants',plant_id)
    result=store.state('ai-advice-'+plant_id)
    from .ai_support import advice_context_current
    return {**result,'stale':(version!=result['expectedVersion'] or not advice_context_current(result)) and not result.get('applied')} if result else None

@app.post('/api/plants/{plant_id}/advice/preview')
def preview_advice(plant_id:str,body:AdviceSelection):
    from .ai_support import preview_advice
    return preview_advice(store,plant_id,body)

@app.post('/api/plants/{plant_id}/advice/apply')
def apply_advice(plant_id:str,body:AdviceSelection):
    from .ai_support import apply_advice
    p,v=apply_advice(store,plant_id,body)
    return render_plant(p,v)

@app.post('/api/ai/analyze')
async def analyze(): return await ai.analyze(store,settings)
@app.post('/api/proposals/{plant_id}/apply')
def apply_proposal(plant_id:str):
    p,v=ai.apply(store,plant_id)
    return render_plant(p,v)
@app.delete('/api/proposals/{plant_id}',status_code=204)
def reject_proposal(plant_id:str):
    with store.connection() as db: db.execute('DELETE FROM entities WHERE collection=? AND id=?',('proposals',plant_id))
@app.post('/api/plants/{plant_id}/advice')
async def advice(plant_id:str,body:Question): return await ai.advice(store,settings,plant_id,body.question)

@app.post('/api/plants/{plant_id}/health-photos',status_code=201)
def add_health_photos(plant_id:str,body:HealthPhotoSession,version:int=Query(ge=1)):
    payload=body.model_dump()
    with store.connection() as db:
        plant,current=store.get('plants',plant_id,db)
        sessions=plant.get('healthPhotoSessions') or []
        previous=next((s for s in sessions if s['id']==body.id),None)
        if previous:
            if previous!=payload:raise Conflict('Identificativo del controllo già utilizzato con dati diversi.')
            return render_plant(plant,current,db)
        if current!=version:raise Conflict('La pianta è cambiata. Riapri il controllo prima di salvare.')
        if any(e.get('id')==body.id for e in plant['history']):raise Conflict('Identificativo del controllo già presente nella cronologia.')
        if any(not (store.photos/photo.path).is_file() for photo in body.photos):raise HTTPException(422,'Una fotografia non è disponibile. Riprova il caricamento.')
        plant['healthPhotoSessions']=sorted(sessions+[payload],key=lambda s:s['date'],reverse=True)
        plant['history'].append({'id':body.id,'kind':'inspect','date':body.date,'note':body.note.strip(),'health':body.health,'status':'completed','origin':'user','schemaVersion':2})
        p,v=store.put('plants',plant,current,db)
        return render_plant(p,v,db)

@app.post('/api/plants/{plant_id}/growth',status_code=201)
def growth(plant_id:str,body:dict=Body()):
    try:
        health=canonical_health(body.get('health'))
    except ValueError:
        raise HTTPException(422,'Stato di salute non valido.') from None
    date=iso(parse(body.get('date') or iso(now())))
    paths=body.get('photoPaths',[])
    if not isinstance(paths,list) or any(not isinstance(p,str) or '/' in p or not (store.photos/p).is_file() for p in paths): raise HTTPException(422,'Fotografia non disponibile.')
    with store.connection() as db:
        plant,version=store.get('plants',plant_id,db)
        entry={'id':str(uuid4()).upper(),'date':date,'health':health,'heightCM':body.get('heightCM'),'note':str(body.get('note',''))[:20000],'photoPaths':paths}
        plant['growthEntries']=(plant.get('growthEntries') or [])+[entry]
        plant['history'].append({'id':str(uuid4()).upper(),'kind':'progress','date':date,'status':'completed','note':entry['note'],'origin':'user','schemaVersion':2})
        p,v=store.put('plants',plant,version,db)
    return render_plant(p,v)

frontend=Path(__file__).resolve().parents[1]/'frontend'/'dist'
if frontend.exists():
    app.mount('/assets',StaticFiles(directory=frontend/'assets'),name='assets')
    @app.get('/')
    def index(): return FileResponse(frontend/'index.html',headers={'Cache-Control':'no-cache'})
