"""Open Plantbook provider using Verdant's aliases and interval rules."""
import math
import re
import unicodedata
from urllib.parse import quote
import httpx
from .domain import iso, now, swift_round
from .knowledge import text
BASE='https://open.plantbook.io/api/v1'

def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD',value.casefold().strip()) if not unicodedata.combining(c))

def aliases(name):
    value=normalized(name)
    if value in {'zamia','gemma di zanzibar','zanzibar gem','zz plant'} or 'zamioculcas' in value:return ['Zamioculcas zamiifolia','Zamioculcas','Zanzibar gem']
    if value.startswith('goeppertia '):return [name,'Calathea '+name.split(' ',1)[1]]
    return list(dict.fromkeys([name,name.split(' ')[0]]))

def care_text(value):
    if isinstance(value,str):return value[:10000]
    if isinstance(value,list):return ', '.join(v for v in value if isinstance(v,str))[:10000]
    if isinstance(value,dict):return next((text(value[k],10000) for k in ['description','summary','value','frequency'] if isinstance(value.get(k),str)), '')
    return ''

def number(value):
    if isinstance(value,bool):return None
    try: result=float(value)
    except (TypeError,ValueError):return None
    return result if math.isfinite(result) else None

def watering_days(watering,minimum,maximum):
    lower=watering.lower()
    if 'day' in lower or 'giorn' in lower:
        match=re.search(r'(\d+)\s*(?:-|–|—|to|a)\s*(\d+)\s*(?:days?|giorni?)',lower)
        if match:return max(1,min(60,swift_round((int(match[1])+int(match[2]))/2)))
        match=re.search(r'(\d+)\s*(?:days?|giorni?)',lower)
        if match:return max(1,min(60,int(match[1])))
    values=[v for v in [minimum,maximum] if v is not None];midpoint=sum(values)/max(1,len(values))
    return 3 if midpoint>=70 else 5 if midpoint>=50 else 8 if midpoint>=30 else 14 if midpoint>=1 else 7

async def profile(settings,name):
    client_id=settings.options.get('openplantbook_client_id','').strip();secret=settings.options.get('openplantbook_secret','').strip()
    if not client_id or not secret:raise ValueError('Configura Client ID e Secret di Open Plantbook nelle opzioni dell’add-on.')
    async with httpx.AsyncClient(timeout=30) as client:
        r=await client.post(BASE+'/token/',data={'grant_type':'client_credentials','client_id':client_id,'client_secret':secret});r.raise_for_status()
        try:token=r.json()['access_token']
        except (KeyError,ValueError,TypeError):raise ValueError('Open Plantbook non ha restituito un token utilizzabile.') from None
        if not isinstance(token,str) or not token:raise ValueError('Open Plantbook non ha restituito un token utilizzabile.')
        headers={'Authorization':'Bearer '+token,'Accept':'application/json'}
        match=None
        for alias in aliases(name):
            r=await client.get(BASE+'/plant/search',params={'alias':alias},headers=headers);r.raise_for_status()
            data=r.json();items=data if isinstance(data,list) else next((data[k] for k in ['results','data','plants'] if isinstance(data.get(k),list)),[]) if isinstance(data,dict) else []
            items=[i for i in items if isinstance(i,dict) and isinstance(i.get('pid'),str) and i['pid']]
            if items:
                match=next((i for i in items if normalized(str(i.get('display_pid','')))==normalized(alias) or normalized(i['pid'])==normalized(alias)),items[0]);break
        if not match:return None
        pid=match['pid']
        if len(pid)>300:raise ValueError('Identificativo Open Plantbook non valido.')
        r=await client.get(BASE+'/plant/detail/'+quote(pid,safe='')+'/',params={'lang':'it','include':'care'},headers=headers);r.raise_for_status()
        data=r.json()
        if not isinstance(data,dict):raise ValueError('Scheda Open Plantbook non utilizzabile.')
        scientific=text(data.get('display_pid')) or text(data.get('pid')) or name
        minimum=number(data.get('min_soil_moist'));maximum=number(data.get('max_soil_moist'))
        watering=care_text(data.get('watering'));sun=care_text(data.get('sunlight'));soil=care_text(data.get('soil'))
        summary=' · '.join(label+': '+care_text(data.get(k)) for label,k in [('Concimazione','fertilization'),('Potatura','pruning')] if care_text(data.get(k)))
        ranges=[{'title':label,'minimum':number(data.get('min_'+key)),'maximum':number(data.get('max_'+key)),'unit':unit} for label,key,unit in [('Temperatura','temp','°C'),('Umidità aria','env_humid','%'),('Umidità terreno','soil_moist','%'),('Luce','light_lux','lux'),('Conducibilità terreno','soil_ec','µS/cm')]]
        return dict(speciesID=0,scientificName=scientific,exactMatch=normalized(scientific)==normalized(name),wateringDays=watering_days(watering,minimum,maximum),wateringLabel=f'umidità del terreno {int(minimum)}–{int(maximum)}%' if minimum is not None and maximum is not None else watering or 'soglia della scheda botanica',sunlight=[sun] if sun else [],soil=[soil] if soil else [],careLevel='',summary=summary,source='Open Plantbook',sourceURL='https://open.plantbook.io/',fetchedAt=iso(now()),poisonousToHumans=None,poisonousToPets=None,ranges=ranges)
