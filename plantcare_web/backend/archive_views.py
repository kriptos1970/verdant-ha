"""Read-only projections; operational plant records remain complete."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import json
from .domain import iso


def compact(view):
    events=view.get('history') or []
    result={k:v for k,v in view.items() if k not in {'history','growthEntries','healthPhotoSessions'}}
    result.update(history=[],growthEntries=[],healthPhotoSessions=[],_summary=True,
                  _careCount=sum(not e.get('deletedAt') and e.get('status')!='postponed' for e in events))
    return result


def history_page(store,zone,page=1,limit=50,plant_id='',room='',kind='',from_day='',to_day=''):
    tz=ZoneInfo(zone)
    try:
        first=date.fromisoformat(from_day) if from_day else None
        last=date.fromisoformat(to_day) if to_day else None
    except ValueError:raise ValueError('Inserisci date valide per i filtri.')
    if first and last and first>last:raise ValueError('La data iniziale deve precedere quella finale.')
    where=["p.collection='plants'", "coalesce(json_extract(e.value,'$.deletedAt'),'')=''"]
    params=[]
    for clause,value in [("p.id=?",plant_id),("json_extract(p.payload,'$.room')=?",room),("json_extract(e.value,'$.kind')=?",kind)]:
        if value:where.append(clause);params.append(value)
    if first:
        where.append("julianday(json_extract(e.value,'$.date'))>=julianday(?)")
        params.append(iso(datetime.combine(first,time.min,tz)))
    if last and last<date.max:
        where.append("julianday(json_extract(e.value,'$.date'))<julianday(?)")
        params.append(iso(datetime.combine(last+timedelta(days=1),time.min,tz)))
    source=" FROM entities p, json_each(p.payload,'$.history') e WHERE "+' AND '.join(where)
    with store.connection() as db:
        total=db.execute('SELECT count(*)'+source,params).fetchone()[0]
        rows=db.execute("SELECT p.id, p.version, json_extract(p.payload,'$.name') name, json_extract(p.payload,'$.room') room,e.value event"+source+" ORDER BY julianday(json_extract(e.value,'$.date')) DESC,p.id,json_extract(e.value,'$.id') LIMIT ? OFFSET ?",[*params,limit,(page-1)*limit]).fetchall()
        kinds=[r[0] for r in db.execute("SELECT DISTINCT json_extract(e.value,'$.kind')"+" FROM entities p,json_each(p.payload,'$.history') e WHERE p.collection='plants' AND coalesce(json_extract(e.value,'$.deletedAt'),'')='' ORDER BY 1") if r[0]]
    return dict(items=[dict(plantID=r['id'],plantName=r['name'],room=r['room'],version=r['version'],event=json.loads(r['event'])) for r in rows],total=total,page=page,limit=limit,hasNextPage=page*limit<total,kinds=kinds)
