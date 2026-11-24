import asyncio
import copy
import hashlib
import json
import re
from pathlib import Path
from uuid import uuid4
import httpx
from zoneinfo import ZoneInfo
from .care_kinds import canonical_kind, legacy_kind
from .domain import active_history, parse, stable_water, minimum_water, accepted_water, ai_watering_limits, early_watering_evidence, feed_days, evidence, iso, now, normalize_experience
from .storage import Conflict
from .ai_support import effective_settings, advice_values, climate_context, ADVICE_CONTEXT_VERSION

lock=asyncio.Lock()
advice_lock=asyncio.Lock()
DAILY_SCHEMA={'type':'object','additionalProperties':False,'properties':{'plants':{'type':'array','items':{'type':'object','additionalProperties':False,'properties':{'plantID':{'type':'string'},'wateringDays':{'type':'integer'},'fertilizingDays':{'type':'integer'},'reason':{'type':'string'},'hasSufficientEvidence':{'type':'boolean'}},'required':['plantID','wateringDays','fertilizingDays','reason','hasSufficientEvidence']}},'summary':{'type':'string'}},'required':['plants','summary']}
ADVICE_SCHEMA={'type':'object','additionalProperties':False,'properties':{**{k:{'type':'integer'} for k in ['wateringDays','fertilizingDays','inspectionDays','pruningDays','repottingDays']},'careNotes':{'type':'string'},'summaryMarkdown':{'type':'string'}},'required':['wateringDays','fertilizingDays','inspectionDays','pruningDays','repottingDays','careNotes','summaryMarkdown']}

async def complete(settings,prompt,schema,name):
    info=settings.public()
    if not info['aiConfigured']:
        raise ValueError('Configura provider e chiave AI nelle opzioni dell’add-on.')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}',info['aiModel']):raise ValueError('Nome del modello non valido. Verifica le opzioni AI.')
    async with httpx.AsyncClient(timeout=120) as client:
        if info['aiProvider']=='openai':
            response=await client.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':'Bearer '+settings.options['openai_api_key']},json={'max_completion_tokens':4000,'model':info['aiModel'],'messages':[{'role':'user','content':prompt}],'response_format':{'type':'json_schema','json_schema':{'name':name,'strict':True,'schema':schema}}})
            response.raise_for_status()
            choices=response.json().get('choices') or []
            if not choices or choices[0].get('finish_reason')!='stop' or choices[0].get('message',{}).get('refusal'):
                raise ValueError('Il provider non ha completato una risposta utilizzabile. Riprova.')
            text=choices[0]['message'].get('content')
        else:
            response=await client.post('https://generativelanguage.googleapis.com/v1beta/models/'+info['aiModel']+':generateContent',headers={'x-goog-api-key':settings.options['gemini_api_key']},json={'contents':[{'role':'user','parts':[{'text':prompt}]}],'generationConfig':{'temperature':0,'maxOutputTokens':4000,'responseMimeType':'application/json','responseJsonSchema':schema}})
            response.raise_for_status()
            candidates=response.json().get('candidates') or []
            if not candidates or candidates[0].get('finishReason')!='STOP':
                raise ValueError('Il provider non ha completato una risposta utilizzabile. Riprova.')
            text=''.join(p.get('text','') for p in candidates[0].get('content',{}).get('parts',[]) if not p.get('thought'))
    if not isinstance(text,str) or len(text)>1_000_000: raise ValueError('Risposta AI vuota o troppo grande.')
    try: result=json.loads(text)
    except (ValueError,TypeError): raise ValueError('Il provider ha restituito una risposta non strutturata. Riprova.') from None
    if not isinstance(result,dict): raise ValueError('Risposta AI non strutturata')
    return result

def stable_feed(plant,water):
    plan=plant.get('adaptivePlan') or {}
    baseline=plan.get('verdantFertilizingDays')
    preference_applies=baseline is not None or bool(plan) or plant.get('fertilizingInterval') is None
    if baseline is None: baseline=plan.get('fertilizingDays') if plan else plant.get('fertilizingInterval')
    if baseline is None: baseline=28 if minimum_water(plant)>1 else 21
    if minimum_water(plant)>1:
        season=plan.get('seasonName','').lower()
        baseline=max(baseline,84 if 'riposo' in season else 42 if 'transizione' in season else 28)
    if preference_applies:
        from .domain import swift_round
        baseline=swift_round(baseline*{'Molto frequente':.7,'Frequente':.85,'Normale':1,'Diradata':1.15,'Molto diradata':1.3}.get(plant.get('careFrequencyPreference'),1))
    return feed_days(baseline,water)

def care_timing(plant,zone='Europe/Rome'):
    """Structured care timing for the AI: postponements are intentional, not delays."""
    tz=ZoneInfo(zone)
    def day(value):
        return parse(value).astimezone(tz).date()
    def kind_events(kind):
        result=[]
        for event in active_history(plant):
            try: event_kind=canonical_kind(event.get('kind',''))
            except ValueError: continue
            if event_kind==kind: result.append(event)
        return result
    def kind_timing(kind,interval):
        events=kind_events(kind)
        completed=sorted({day(e['date']) for e in events if e.get('status')!='postponed'})
        gaps=[(b-a).days for a,b in zip(completed,completed[1:]) if (b-a).days>0][-8:]
        raw=[e for e in events if e.get('status')=='postponed' and e.get('postponedUntil')]
        raw.sort(key=lambda e:e.get('date',''),reverse=True)
        postponements=[]
        for e in raw[:6]:
            start=day(e['date']); due=day(e['postponedUntil'])
            after=[d for d in completed if d>start]
            if not after: outcome='pending'
            elif min(after)>=due: outcome='honored'
            else: outcome='early'
            postponements.append({'date':iso(parse(e['date'])),'postponedUntil':iso(parse(e['postponedUntil'])),'deferredDays':max(0,(due-start).days),'note':str(e.get('note') or '')[:300],'outcome':outcome})
            previous=[d for d in completed if d<=start]
            postponements[-1].update(completedOn=min(after).isoformat() if after else None,
                                    completedGapDays=(min(after)-max(previous)).days if after and previous else None)
        starts={day(e['date']) for e in raw}
        late=0
        for a,b in zip(completed,completed[1:]):
            gap=(b-a).days
            if interval and gap>interval+2 and not any(a<start<=b for start in starts): late+=1
        return {'recentCompletedGapsDays':gaps,'postponements':postponements,'honoredPostponements':sum(1 for p in postponements if p['outcome']=='honored'),'pendingPostponements':sum(1 for p in postponements if p['outcome']=='pending'),'earlyPostponements':sum(1 for p in postponements if p['outcome']=='early'),'lateGapsWithoutPostponement':late,
                'honoredCycles':len({p['completedOn'] for p in postponements if p['outcome']=='honored'}),
                'earlyCycles':len({p['completedOn'] for p in postponements if p['outcome']=='early'})}
    return {'water':{**kind_timing('water',plant.get('wateringInterval') or 0),**early_watering_evidence(plant,zone)},
            'fertilize':kind_timing('fertilize',plant.get('fertilizingInterval') or 0)}

def care_timing_text(plant,zone='Europe/Rome',language='it'):
    timing=care_timing(plant,zone)
    def line(kind,label):
        data=timing[kind]
        items=[]
        for item in data['postponements']:
            note=f" · nota: {item['note']}" if item['note'] else ''
            completed=''
            if item['completedOn']:
                completed=(f" · completed: {item['completedOn']}"
                           if language=='en' else f" · completata: {item['completedOn']}")
                if item['completedGapDays'] is not None:
                    completed+=(f", gap: {item['completedGapDays']} days"
                                if language=='en' else f", intervallo: {item['completedGapDays']} giorni")
            items.append(f"{item['date'][:10]} → {item['postponedUntil'][:10]} ({item['deferredDays']} g, {item['outcome']}{note}{completed})")
        detail='; '.join(items) if items else ('nessuno' if language!='en' else 'none')
        if language=='en':
            text=f"{label}: honored {data['honoredPostponements']}, pending {data['pendingPostponements']}, early {data['earlyPostponements']}, late gaps without postponement {data['lateGapsWithoutPostponement']}; recent gaps {data['recentCompletedGapsDays']} days; {detail}."
        else:
            text=f"{label}: onorati {data['honoredPostponements']}, in attesa {data['pendingPostponements']}, anticipati {data['earlyPostponements']}, ritardi senza rinvio {data['lateGapsWithoutPostponement']}; intervalli recenti {data['recentCompletedGapsDays']} giorni; {detail}."
        if kind=='water':
            text+=(f" Honoured postponement cycles: {data['honoredCycles']}. Early waterings: {data['earlyWaterings']} recorded, {data['inferredEarlyWaterings']} inferred; "
                   if language=='en' else f" Cicli con rinvii onorati: {data['honoredCycles']}. Annaffiature anticipate: {data['earlyWaterings']} registrate, {data['inferredEarlyWaterings']} stimate; ")
            text+=json.dumps(data['earlyWateringEvents'],ensure_ascii=False)
        return text
    return line('water','Annaffiatura' if language!='en' else 'Watering')+' '+line('fertilize','Concimazione' if language!='en' else 'Feeding')

def daily_context(plant,products,location=None,zone='Europe/Rome',experience='intermedio'):
    water=stable_water(plant)
    item={'plantID':plant['id'],'name':plant['name'],'species':plant['species'],'category':plant['category'],'wateringProfile':'Succulenta' if plant['category']=='Succulenta' else 'Alta riserva idrica' if minimum_water(plant)>1 else 'Standard','room':plant['room'],'light':plant['light'],'wateringDaysCurrent':plant['wateringInterval'],'wateringDaysVerdantBaseline':water,'careFrequencyPreference':plant.get('careFrequencyPreference') or 'Normale','fertilizingDaysVerdantBaseline':stable_feed(plant,water),'fertilizingDaysCurrent':plant.get('fertilizingInterval'),'fertilizerProductLinked':bool(plant.get('fertilizerProductID')),'lastWatered':plant['lastWatered'],'potDiameterCM':plant.get('potDiameterCM'),'potMaterial':plant.get('potMaterial') or 'non indicato','drainage':plant.get('potHasDrainage')}
    product=next((p for p in products if p['id']==plant.get('fertilizerProductID')),None)
    if product:
        item.update(fertilizerProduct=product['name'],fertilizerManufacturerDays=product.get('applicationIntervalDays'))
    plan=plant.get('adaptivePlan') or {}
    item['locationName']=plan.get('locationName') or (location or {}).get('name') or 'Località non indicata'
    item['experienceLevel']=normalize_experience(experience)
    item['wateringLimits']=ai_watering_limits(water,minimum_water(plant),experience)
    item['recentCare']=[
        {'kind':legacy_kind(e['kind']),'date':e['date'],'status':e.get('status') or 'completed',
         **({'wateringDueDate':e['wateringDueDate']} if e.get('wateringDueDate') else {}),
         **({'postponedUntil':e.get('postponedUntil'),'note':str(e.get('note') or '')[:300]} if e.get('status')=='postponed' else {})}
        for e in sorted(active_history(plant),key=lambda e:e['date'],reverse=True)[:6]
    ]
    item['careTiming']=care_timing(plant,zone)
    for dest,source in [('season','seasonName'),('temperatureC','averageTemperature'),('humidityPercent','relativeHumidity'),('rainNext7DaysMM','precipitationNextWeek'),('placement','placement')]:
        if source in plan: item[dest]=plan[source]
    if plan: item['climateContext']=climate_context(plan)
    return item

async def analyze(store,settings):
    settings=effective_settings(store,settings)
    if lock.locked(): raise Conflict('Analisi già in corso.')
    async with lock:
        from .services import message_language
        language=message_language(store,settings)
        plants=[(p,v) for p,v in store.list('plants') if p.get('carePlanMode')=='AI']
        if not plants: return {'summary':'No plants with an AI plan.' if language=='en' else 'Nessuna pianta con piano AI.','proposals':0,'skipped':True}
        products=[p for p,_ in store.list('fertilizers')]
        experience=normalize_experience((store.state('preferences') or {}).get('experience'))
        context=[daily_context(p,products,store.state('location') or {},settings.zone,experience) for p,_ in plants]
        prompt=Path(__file__).with_name('daily_prompt.txt').read_text().replace('{plants}',json.dumps(context,ensure_ascii=False))
        prompt+='\nData della richiesta: '+iso(now())+'\nI dati climatici sono istantanee del piano salvato: cita climateContext.generatedAt, oppure specifica data sconosciuta. Non presentarli come meteo attuale, stagione attuale o previsioni attuali; non giustificare modifiche con quei dati storici.'
        if language=='en': prompt+='\nWrite summary and every explanatory text in English.'
        result=await complete(settings,prompt,DAILY_SCHEMA,'verdant_daily_plans')
        if not isinstance(result.get('summary'),str):raise ValueError('Sintesi AI non valida.')
        suggestions=result.get('plants')
        if not isinstance(suggestions,list) or any(not isinstance(p,dict) or not isinstance(p.get('plantID'),str) for p in suggestions) or {p.get('plantID') for p in suggestions} != {p['id'] for p,_ in plants} or len(suggestions)!=len(plants):
            raise ValueError('La risposta AI non corrisponde alle piante inviate.')
        proposals=[]
        for plant,version in plants:
            suggestion=next(s for s in suggestions if s['plantID']==plant['id'])
            reason=suggestion.get('reason')
            if not isinstance(reason,str) or len(reason)>20000 or type(suggestion.get('hasSufficientEvidence')) is not bool or any(type(suggestion.get(k)) is not int or abs(suggestion[k])>10**12 for k in ['wateringDays','fertilizingDays']):
                raise ValueError('Valori AI non validi')
            if not evidence(suggestion.get('hasSufficientEvidence'),reason): continue
            limits=ai_watering_limits(stable_water(plant),minimum_water(plant),experience)
            water=accepted_water(suggestion['wateringDays'],stable_water(plant),minimum_water(plant),experience)
            if water!=suggestion['wateringDays']:
                reason+=(
                    f" Safety adjustment: AI requested {suggestion['wateringDays']} days; accepted {water} days "
                    f"(profile {experience}, ±{limits['maxDeviationPercent']}%, permitted {limits['minimumDays']}–{limits['maximumDays']} days)."
                    if language=='en' else
                    f" Correzione di sicurezza: AI {suggestion['wateringDays']} giorni, accettati {water} giorni "
                    f"(profilo {experience}, ±{limits['maxDeviationPercent']}%, intervallo ammesso {limits['minimumDays']}–{limits['maximumDays']} giorni)."
                )
            feed=feed_days(suggestion['fertilizingDays'],water)
            if water==plant['wateringInterval'] and feed==plant.get('fertilizingInterval'): continue
            proposals.append({'id':plant['id'],'plantID':plant['id'],'plantName':plant['name'],'expectedVersion':version,'currentWateringDays':plant['wateringInterval'],'currentFertilizingDays':plant.get('fertilizingInterval'),'proposedWateringDays':water,'proposedFertilizingDays':feed,'reason':reason,'provider':settings.public()['aiProvider'],'model':settings.public()['aiModel'],'createdAt':iso(now())})
        with store.connection() as db:
            if normalize_experience((store.state('preferences',None,db) or {}).get('experience'))!=experience:
                raise Conflict('Il profilo di esperienza è cambiato durante l’analisi. Genera una nuova proposta.')
            for original,expected in plants:
                current,actual=store.get('plants',original['id'],db)
                if actual!=expected or current.get('carePlanMode')!='AI':raise Conflict('Una pianta è cambiata durante l’analisi. Ripeti prima di applicare le proposte.')
            for plant,_ in plants:
                db.execute('DELETE FROM entities WHERE collection=? AND id=?',('proposals',plant['id']))
            for proposal in proposals: store.put('proposals',proposal,db=db)
            status={'summary':str(result.get('summary',''))[:1000],'proposals':len(proposals),'lastRun':iso(now())}
            store.set_state('ai-status',status,db)
        applied=0
        if settings.options.get('auto_apply_ai',False):
            for proposal in proposals:
                try:apply(store,proposal['plantID']);applied+=1
                except (Conflict,KeyError):pass
        status['applied']=applied
        if proposals:
            from .services import notify
            try:
                message=(f"{len(proposals)} plan changes proposed. {applied} applied automatically. Open Verdant → More → AI plan to review them." if language=='en' else f"{len(proposals)} modifiche proposte per i piani AI. {applied} applicate automaticamente. Apri Verdant → Altro → Piano AI per esaminarle.")
                await notify(settings,message)
                status['notificationError']=None
            except httpx.HTTPError:status['notificationError']='Notifica non inviata. Le proposte restano disponibili in Verdant.'
        store.set_state('ai-status',status)
        from zoneinfo import ZoneInfo
        store.set_state('last-ai-day',now().astimezone(ZoneInfo(settings.zone)).date().isoformat())
        return status

def apply(store,plant_id):
    with store.connection() as db:
        proposal,_=store.get('proposals',plant_id,db)
        plant,version=store.get('plants',plant_id,db)
        if version!=proposal['expectedVersion'] or plant.get('carePlanMode')!='AI':
            raise Conflict('La pianta è cambiata dopo l’analisi. Genera una nuova proposta.')
        experience=normalize_experience((store.state('preferences',None,db) or {}).get('experience'))
        if accepted_water(proposal['proposedWateringDays'],stable_water(plant),minimum_water(plant),experience)!=proposal['proposedWateringDays']:
            raise Conflict('La proposta supera i limiti del profilo attuale. Genera una nuova proposta.')
        proposal['proposedFertilizingDays']=feed_days(proposal['proposedFertilizingDays'],proposal['proposedWateringDays'])
        plant.update(wateringInterval=proposal['proposedWateringDays'],fertilizingInterval=proposal['proposedFertilizingDays'])
        if plant.get('adaptivePlan'):
            plant['adaptivePlan'].update(wateringDays=proposal['proposedWateringDays'],fertilizingDays=proposal['proposedFertilizingDays'],revisionSource='AI',revisedAt=iso(now()),revisionReason=proposal['reason'],revisionProvider=proposal['provider'],revisionChangedIntervals=True)
        plant['history'].append({'id':str(uuid4()).upper(),'kind':'planUpdate','date':iso(now()),'status':'completed','origin':'system','note':f"Piano AI applicato ({proposal['provider']}). {proposal['reason']}", 'schemaVersion':2})
        saved=store.put('plants',plant,version,db)
        db.execute('DELETE FROM entities WHERE collection=? AND id=?',('proposals',plant_id))
        return saved

async def advice(store,settings,plant_id,question):
    if advice_lock.locked():raise Conflict('Una richiesta all’assistente è già in corso. Attendi il risultato.')
    async with advice_lock:return await _advice(store,settings,plant_id,question)

async def _advice(store,settings,plant_id,question):
    settings=effective_settings(store,settings)
    plant,version=store.get('plants',plant_id)
    water=stable_water(plant)
    plan=plant.get('adaptivePlan') or {}
    profile='Succulenta' if plant.get('category')=='Succulenta' else 'Alta riserva idrica' if minimum_water(plant)>1 else 'Standard'
    values=[plant['name'],plant['species'],plant.get('family') or 'non indicata',plant['category'],profile,plant['room'],plant['light'],plant.get('lastFertilized') or 'non indicata',plant.get('fertilizerType') or 'non indicato',str(plant['fertilizingInterval'])+' giorni' if plant.get('fertilizingInterval') else 'non impostato',plant.get('notes') or 'nessuna',plan.get('seasonName','non indicata'),plan.get('placement','non indicato'),plan.get('locationName','non indicata'),str(plan.get('averageTemperature','non indicata')),str(plan.get('relativeHumidity','non indicata')),str(plan.get('precipitationNextWeek','non indicata')),plan.get('verdantWateringDays',plan.get('wateringDays','non indicato')),plant['wateringInterval'],question,water,stable_feed(plant,water),plan.get('inspectionDays') or plant.get('inspectionInterval') or 7,plant.get('pruningInterval') or 90,plant.get('repottingInterval') or (730 if plant['category']=='Succulenta' else 365)]
    blocks=json.loads(Path(__file__).with_name('advice_prompt.json').read_text())
    if not plan: blocks.pop(1)
    prompt='\n\n'.join(blocks)
    for index,value in enumerate(values): prompt=prompt.replace('{v'+str(index)+'}',str(value))
    climate=climate_context(plan) if plan else None
    from .services import message_language
    language=message_language(store,settings)
    location_name=plan.get('locationName') or (store.state('location') or {}).get('name') or ('non indicata' if language!='en' else 'not specified')
    prompt+='\n\nLOCALITÀ: '+str(location_name)
    experience=normalize_experience((store.state('preferences') or {}).get('experience'))
    prompt+='\nESPERIENZA DEL COLTATORE: '+experience
    prompt+=('\nPer un principiante spiega e resta conservativo; per un professionista puoi dare più peso a rinvii ripetuti e coerenti, senza superare mai le soglie di sicurezza.' if language!='en' else '\nFor a beginner, explain and stay conservative; for a professional, you may give more weight to repeated, consistent postponements without ever exceeding safety thresholds.')
    prompt+='\nRINVII RECENTI (scelte intenzionali del coltivatore, non ritardi; non sono cure completate): '+care_timing_text(plant,settings.zone,language)
    prompt+='\n\nDATA DELLA RICHIESTA: '+iso(now())[:10]
    if climate:
        prompt+='\nData del contesto stagionale e climatico salvato: '+(climate['generatedAt'] or 'sconosciuta')+'\nQuesti dati provengono dal piano salvato, non da una lettura meteo attuale. Cita esplicitamente la data (oppure data sconosciuta) se li menzioni. Non presentarli come stagione, temperatura, umidità o pioggia attuali e non usarli per giustificare cambiamenti delle frequenze attuali. La pioggia era prevista nei sette giorni successivi alla data del piano, non alla richiesta.'
    if language=='en': prompt+='\nAnswer in English: summaryMarkdown and careNotes must be written in English.'
    info=settings.public()
    signature=hashlib.sha256((info['aiProvider']+'\n'+info['aiModel']+'\n'+prompt).encode()).hexdigest()
    cached=store.state('ai-advice-'+plant_id)
    if cached and cached.get('contextVersion')==ADVICE_CONTEXT_VERSION and cached.get('requestSignature')==signature and cached['expectedVersion']==version and not cached.get('applied'):
        return cached
    schema=copy.deepcopy(ADVICE_SCHEMA)
    for key,value in [('wateringDays',water),('inspectionDays',values[22]),('pruningDays',values[23]),('repottingDays',values[24])]:schema['properties'][key]['enum']=[value]
    schema['properties']['fertilizingDays']['enum']=[days for days in range(2*water,366,water) if days>=7]
    result=await complete(settings,prompt,schema,'verdant_care')
    if any(type(result.get(k)) is not int or abs(result[k])>10**12 for k in ['wateringDays','fertilizingDays','inspectionDays','pruningDays','repottingDays']) or not isinstance(result.get('summaryMarkdown'),str):
        raise ValueError('Risposta AI non valida')
    if not isinstance(result.get('careNotes'),str): raise ValueError('Indicazioni AI non valide.')
    result=advice_values(result,plant,water)
    info=settings.public()
    result.update(contextVersion=ADVICE_CONTEXT_VERSION,climateContext=climate,id=str(uuid4()),expectedVersion=version,provider=info['aiProvider'],model=info['aiModel'],createdAt=iso(now()),timezone=settings.zone,applied=False,requestSignature=signature)
    with store.connection() as db:
        _,current=store.get('plants',plant_id,db)
        if current!=version:raise Conflict('La scheda è cambiata durante l’analisi. Richiedi un nuovo consiglio.')
        store.set_state('ai-advice-'+plant_id,result,db)
    return result
