"""Provider model discovery and native advice application rules."""
import copy
import re
import httpx
from .domain import now, iso, parse, feed_days
from .storage import Conflict


ADVICE_CONTEXT_VERSION = 5


def advice_context_current(advice):
    return advice.get('contextVersion') == ADVICE_CONTEXT_VERSION


def climate_context(plan):
    """Saved plans are snapshots, never evidence of current weather."""
    try:
        stamp = iso(parse(plan.get('generatedAt')))
    except (ValueError, TypeError, OverflowError):
        stamp = None
    return {'source': 'saved-plan', 'generatedAt': stamp, 'currentWeather': False}


def text_model(model):
    return model.startswith(('gpt-','o1','o3','o4','chatgpt-')) and not any(s in model.lower() for s in ['audio','realtime','transcribe','tts','image','embedding','instruct'])


def effective_settings(store,settings):
    result=copy.copy(settings);result.options=dict(settings.options)
    selected=store.state('ai-model-selection') or {}
    if selected.get('model') and selected.get('provider')==settings.options.get('ai_provider') and selected.get('configuredModel','')==(settings.options.get('ai_model') or ''):
        result.options['ai_model']=selected['model']
    return result


async def models(settings):
    info=settings.public()
    if not info['aiConfigured']: raise ValueError('Configura provider e chiave nelle opzioni dell’add-on.')
    provider=info['aiProvider'];items=[];token=None
    async with httpx.AsyncClient(timeout=20) as client:
        for _ in range(20):
            if provider=='openai':
                response=await client.get('https://api.openai.com/v1/models',headers={'Authorization':'Bearer '+settings.options['openai_api_key']})
            else:
                response=await client.get('https://generativelanguage.googleapis.com/v1beta/models',headers={'x-goog-api-key':settings.options['gemini_api_key']},params={'pageSize':1000,**({'pageToken':token} if token else {})})
            response.raise_for_status();data=response.json()
            if provider=='openai':
                items += [m['id'] for m in data.get('data',[]) if isinstance(m.get('id'),str) and text_model(m['id'])]
                break
            items += [m['name'].removeprefix('models/') for m in data.get('models',[]) if 'generateContent' in m.get('supportedGenerationMethods',[]) and isinstance(m.get('name'),str) and 'gemini' in m['name'].lower()]
            next_token=data.get('nextPageToken')
            if not next_token:break
            if next_token==token:raise ValueError('Il provider ha restituito un catalogo incompleto. Riprova.')
            token=next_token
        else:raise ValueError('Il catalogo supera il limite di pagine. Riprova con un altro provider.')
    natural=lambda value:[(1,int(s)) if s.isdigit() else (0,s.lower()) for s in re.split(r'(\d+)',value)]
    return dict(provider=provider,models=sorted(set(items),key=natural),selectedModel=info['aiModel'])


def advice_values(result,plant,water):
    """PlantAdviceViewModel normalizes model output to stable native baselines."""
    result=copy.deepcopy(result)
    result['wateringDays']=water
    result['fertilizingDays']=feed_days(min(365,max(7,result['fertilizingDays'])),water)
    result['inspectionDays']=(plant.get('adaptivePlan') or {}).get('inspectionDays') or plant.get('inspectionInterval') or 7
    result['pruningDays']=plant.get('pruningInterval') or 90
    result['repottingDays']=plant.get('repottingInterval') or (730 if plant.get('category')=='Succulenta' else 365)
    return result


def apply_values(plant,advice,selection,product_days=None):
    """PlantAdviceApplicationService.updatedPlant; all values are server-owned."""
    plant=copy.deepcopy(plant)
    selected=lambda key:bool(selection.get(key,False))
    if selected('watering'):plant['wateringInterval']=min(120,max(1,advice['wateringDays']))
    if selected('fertilizing'):
        mode=plant.get('carePlanMode') or 'AI';plan=plant.get('adaptivePlan') or {}
        if mode=='Manuale':
            value=plant.get('fertilizingInterval')
            plant['fertilizingInterval']=min(365,max(7,value)) if value is not None else None
        else:
            value=(plan.get('verdantFertilizingDays') or product_days or plant.get('fertilizingInterval')) if mode=='Intelligente' else advice['fertilizingDays']
            plant['fertilizingInterval']=feed_days(value,plant['wateringInterval']) if value is not None else None
    if plant.get('fertilizingInterval') is not None and (selected('watering') or selected('fertilizing')):
        plant['fertilizingInterval']=feed_days(plant['fertilizingInterval'],plant['wateringInterval'])
    for key,field,low,high in [('inspection','inspectionInterval',1,90),('pruning','pruningInterval',14,730),('repotting','repottingInterval',30,1095)]:
        if selected(key):plant[field]=min(high,max(low,advice[field.replace('Interval','Days')]))
    return plant


def preview_advice(store,plant_id,request):
    with store.connection() as db:
        saved=store.state('ai-advice-'+plant_id,None,db)
        plant,version=store.get('plants',plant_id,db)
        if not saved or saved['id']!=request.adviceID or saved.get('applied') or not advice_context_current(saved) or version!=saved['expectedVersion']:
            raise Conflict('Il consiglio o la pianta sono cambiati. Richiedi una nuova analisi.')
        product_days=None
        if plant.get('fertilizerProductID'):
            try:product,_=store.get('fertilizers',plant['fertilizerProductID'],db);product_days=product.get('applicationIntervalDays')
            except KeyError:pass
        result=apply_values(plant,saved,request.model_dump(exclude={'adviceID'}),product_days)
        return {k:result.get(k) for k in ['wateringInterval','fertilizingInterval','inspectionInterval','pruningInterval','repottingInterval']}


def apply_advice(store,plant_id,request):
    from uuid import uuid4
    with store.connection() as db:
        saved=store.state('ai-advice-'+plant_id,None,db)
        if not saved or saved['id']!=request.adviceID:raise Conflict('Il consiglio è cambiato. Richiedi una nuova analisi.')
        plant,version=store.get('plants',plant_id,db)
        if saved.get('applied'):return plant,version
        if not advice_context_current(saved):raise Conflict('Il contesto del consiglio è cambiato. Richiedi una nuova analisi.')
        if version!=saved['expectedVersion']:raise Conflict('Piano o cronologia cambiati dopo l’analisi. Richiedi un nuovo consiglio.')
        product_days=None
        if plant.get('fertilizerProductID'):
            try:product,_=store.get('fertilizers',plant['fertilizerProductID'],db);product_days=product.get('applicationIntervalDays')
            except KeyError:pass
        selection=request.model_dump(exclude={'adviceID'})
        result=apply_values(plant,saved,selection,product_days)
        if result.get('adaptivePlan'):
            plan=result['adaptivePlan'];plan['wateringDays']=result['wateringInterval']
            if result.get('fertilizingInterval') is not None:plan['fertilizingDays']=result['fertilizingInterval']
            if result.get('inspectionInterval') is not None:plan['inspectionDays']=result['inspectionInterval']
            if any(selection.values()):plan.update(revisionSource='AI',revisedAt=iso(now()),revisionProvider=saved['provider'],revisionReason=saved['summaryMarkdown'],revisionChangedIntervals=True)
        note=saved['careNotes'].strip()
        if note:
            from zoneinfo import ZoneInfo
            stamp=now().astimezone(ZoneInfo(saved.get('timezone','Europe/Rome'))).date().isoformat()
            entry=f'Indicazioni AI ({stamp}): {note}'
            if entry not in result.get('notes',''):
                combined='\n\n'.join(s for s in [result.get('notes',''),entry] if s)
                if len(combined)>20000:raise ValueError('Le note supererebbero il limite di 20.000 caratteri. Riduci le note della scheda prima di applicare il consiglio.')
                result['notes']=combined
        result['history'].append(dict(id=str(uuid4()).upper(),kind='planUpdate',date=iso(now()),status='completed',origin='user',note=f"Consigli AI applicati ({saved['provider']}). Campi: {', '.join(k for k,v in selection.items() if v) or 'solo note'}.",schemaVersion=2))
        p,v=store.put('plants',result,version,db)
        saved.update(applied=True,appliedAt=iso(now()));store.set_state('ai-advice-'+plant_id,saved,db)
        return p,v
