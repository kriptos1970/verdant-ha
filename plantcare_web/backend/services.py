"""HA sensor polling; observations remain observations, never inferred diagnoses."""
import asyncio
import math
import logging
from datetime import timedelta
import httpx
from .domain import now, iso, parse

SUPPORTED={'temperature','humidity','illuminance','moisture','conductivity'}
log=logging.getLogger('plantcare')

async def sensors(settings):
    if not settings.token:
        return []
    async with httpx.AsyncClient(timeout=15) as client:
        response=await client.get(settings.ha_url+'/states',headers={'Authorization':'Bearer '+settings.token})
        response.raise_for_status()
    exposed=set(settings.options.get('exposed_entities',[]))
    result=[]
    for state in response.json():
        attrs=state.get('attributes',{})
        entity=state.get('entity_id')
        kind=attrs.get('device_class')
        if entity not in exposed or kind not in SUPPORTED:
            continue
        try:
            value=float(state['state'])
            if not math.isfinite(value): continue
        except (ValueError,TypeError):
            continue
        unit=attrs.get('unit_of_measurement','')
        if kind=='temperature' and unit=='°F': value=(value-32)*5/9; unit='°C'
        if kind=='conductivity' and unit=='mS/cm': value*=1000; unit='µS/cm'
        result.append({'entityID':entity,'name':attrs.get('friendly_name',entity),'kind':kind,'value':value,'unit':unit,'updatedAt':state.get('last_updated')})
    return sorted(result,key=lambda x:x['name'])

async def poll(store,settings):
    readings=await sensors(settings)
    with store.connection() as db:
        mappings=store.state('sensor-mappings',[],db)
        plants=[p for p,_ in store.list('plants',db)]
        for reading in readings:
            matching=[m for m in mappings if m['entityID']==reading['entityID']]
            explicit={m.get('plantID') for m in matching if m.get('plantID')}
            ids=set(explicit)
            for m in matching:
                if m.get('room'):
                    ids.update(p['id'] for p in plants if p['room']==m['room'])
            for pid in ids:
                if not any(p['id']==pid for p in plants): continue
                # Store an observation once; repeated polls must not inflate confidence.
                if db.execute('SELECT 1 FROM measurements WHERE plant_id=? AND entity_id=? AND source_at=? AND kind=? AND value=? AND unit=? LIMIT 1',(pid,reading['entityID'],reading['updatedAt'],reading['kind'],reading['value'],reading['unit'])).fetchone(): continue
                db.execute('INSERT INTO measurements(plant_id,entity_id,kind,value,unit,measured_at,source_at) VALUES (?,?,?,?,?,?,?)',(pid,reading['entityID'],reading['kind'],reading['value'],reading['unit'],iso(now()),reading['updatedAt']))
        cutoff=iso(now()-timedelta(days=int(settings.options.get('measurement_retention_days',365))))
        db.execute('DELETE FROM measurements WHERE measured_at < ?', (cutoff,))
        store.set_state('sensor-status',{'lastRun':iso(now()),'readings':len(readings),'error':None},db)
    return readings

async def notify(settings,message):
    if not settings.token: return
    async with httpx.AsyncClient(timeout=15) as client:
        result=await client.post(settings.ha_url+'/services/persistent_notification/create',headers={'Authorization':'Bearer '+settings.token},json={'title':'PlantCare','message':message,'notification_id':'plantcare-ai'})
        result.raise_for_status()

async def scheduler(store,settings):
    from .ai import analyze
    minutes=max(1,int(settings.options.get('poll_interval_minutes',15)))
    while True:
        try:
            await poll(store,settings)
        except Exception:
            log.exception('Campionamento sensori non riuscito')
            store.set_state('sensor-status',{'lastRun':iso(now()),'error':'Home Assistant non raggiungibile. Riproverò al prossimo ciclo.'})
        try:
            from .adaptive import refresh_all
            await refresh_all(store,settings)
        except Exception:
            log.exception('Ricalcolo adattivo non riuscito')
        try:
            from zoneinfo import ZoneInfo
            local=now().astimezone(ZoneInfo(settings.zone))
            day=local.date().isoformat()
            if local.strftime('%H:%M')>=settings.options.get('ai_update_time','03:00') and store.state('last-ai-day')!=day and settings.public()['aiConfigured']:
                result=await analyze(store,settings)
                if not result.get('skipped'):store.set_state('last-ai-day',day)
        except Exception:
            log.exception('Analisi AI periodica non riuscita')
        await asyncio.sleep(minutes*60)
