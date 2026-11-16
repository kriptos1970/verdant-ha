"""Paged native iNaturalist species catalog; metadata cache stays bounded."""
import asyncio
from collections import OrderedDict
from copy import deepcopy
import json
from pathlib import Path
from time import monotonic
from urllib.parse import urlsplit
import httpx
from .knowledge import text
FOCUS=json.loads(Path(__file__).with_name('catalog_focus.json').read_text())
CACHE=OrderedDict()
PHOTO_HOSTS={'static.inaturalist.org','inaturalist-open-data.s3.amazonaws.com'}
LICENSES={'cc0','cc-by','cc-by-sa','cc-by-nc','cc-by-nd','cc-by-nc-sa','cc-by-nc-nd'}

def taxon(item):
    if not isinstance(item,dict) or type(item.get('id')) is not int or item['id']<=0 or not isinstance(item.get('name'),str):raise ValueError('Risultato catalogo non valido.')
    ancestors=item.get('ancestors') or []
    family=next((text(a.get('name')) for a in ancestors if isinstance(a,dict) and a.get('rank')=='family'),'Famiglia non disponibile')
    photo=item.get('default_photo') or {};url=photo.get('medium_url');license=text(photo.get('license_code'));attribution=text(photo.get('attribution'),2000)
    if not isinstance(url,str) or urlsplit(url).scheme!='https' or urlsplit(url).hostname not in PHOTO_HOSTS or license not in LICENSES or not attribution:url=None
    return dict(id=item['id'],scientificName=text(item['name']),commonName=text(item.get('preferred_common_name')) or text(item['name']),family=family,imageURL=url,imageLicense=license if url else None,imageAttribution=attribution if url else None,sourceURL=f"https://www.inaturalist.org/taxa/{item['id']}")

async def fetch(client,query,page,size):
    cache_key=(query.casefold(),page,size);cached=CACHE.get(cache_key)
    if cached and monotonic()-cached[0]<900:
        CACHE.move_to_end(cache_key);return deepcopy(cached[1])
    response=await client.get('https://api.inaturalist.org/v1/taxa',params={'q':query,'rank':'species','iconic_taxa':'Plantae','locale':'it','per_page':size,'page':page})
    response.raise_for_status();data=response.json()
    if not isinstance(data,dict) or not isinstance(data.get('results'),list):raise ValueError('Risposta catalogo non valida.')
    result={'results':[taxon(t) for t in data['results'][:size]],'total':data.get('total_results')}
    CACHE[cache_key]=(monotonic(),deepcopy(result));CACHE.move_to_end(cache_key)
    while len(CACHE)>128:CACHE.popitem(last=False)
    return result

def offline(name,index):
    return dict(id=f'offline-{index}',scientificName=name,commonName=name,family='Famiglia non disponibile',imageURL=None,imageLicense=None,imageAttribution=None,sourceURL=None)

async def search(query,focus,page):
    query=query.strip()
    if focus not in FOCUS:raise ValueError('Categoria del catalogo non valida.')
    warning=None
    async with httpx.AsyncClient(timeout=10,headers={'User-Agent':'PlantCareWeb/0.8.0 (botanical catalog)'}) as client:
        if query:
            try:
                data=await fetch(client,query,page,20);total=data['total'];more=(type(total) is int and page*20<total) if total is not None else len(data['results'])==20
                return dict(results=data['results'],hasNextPage=more and page<100,page=page,source='iNaturalist',warning=None)
            except (httpx.HTTPError,ValueError,TypeError,AttributeError):
                names=list(dict.fromkeys(n for values in FOCUS.values() for n in values if query.casefold() in n.casefold()))
                start=(page-1)*20
                return dict(results=[offline(n,start+i) for i,n in enumerate(names[start:start+20])],hasNextPage=start+20<len(names),page=page,source='Selezione offline',warning='Catalogo non raggiungibile. Mostro la selezione disponibile offline.')
        names=FOCUS[focus];start=(page-1)*12;selection=names[start:start+12];gate=asyncio.Semaphore(4)
        async def one(index,name):
            async with gate:
                try:
                    data=await fetch(client,name,1,5)
                    found=next((r for r in data['results'] if r['scientificName'].casefold()==name.casefold()),None)
                    if found:return found,False
                except (httpx.HTTPError,ValueError,TypeError,AttributeError):pass
                return offline(name,start+index),True
        rows=await asyncio.gather(*(one(i,n) for i,n in enumerate(selection)))
        if any(missing for _,missing in rows):warning='Alcune specie non sono disponibili online: mostro i nomi della selezione offline.'
        return dict(results=[r for r,_ in rows],hasNextPage=start+len(selection)<len(names),page=page,source='iNaturalist',warning=warning)
