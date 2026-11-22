"""Read-only projections; operational plant records remain complete."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import json
from .domain import iso
from .care_kinds import canonical_kind, legacy_event, legacy_kind


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
    if kind:
        try: kind=canonical_kind(kind)
        except ValueError: raise ValueError('Tipo di cura non valido.') from None
    where=[]
    params=[]
    for clause,value in [('plant_id=?',plant_id),('room=?',room)]:
        if value:where.append(clause);params.append(value)
    if kind:
        # Old payloads keep the Italian value until rewritten; match both.
        where.append('kind IN (?,?)')
        params.extend([kind, legacy_kind(kind)])
    if first:
        where.append('event_date>=julianday(?)')
        params.append(iso(datetime.combine(first,time.min,tz)))
    if last and last<date.max:
        where.append('event_date<julianday(?)')
        params.append(iso(datetime.combine(last+timedelta(days=1),time.min,tz)))
    source=' FROM care_history_index'+(' WHERE '+' AND '.join(where) if where else '')
    order='event_date DESC, plant_id, event_id, position'
    with store.connection() as db:
        db.execute('BEGIN')
        total=db.execute('SELECT count(*)'+source,params).fetchone()[0]
        rows=db.execute(f"""
            WITH selected AS (
                SELECT plant_id, position, event_date, event_id, room
                {source} ORDER BY {order} LIMIT ? OFFSET ?
            )
            SELECT p.id, p.version, json_extract(p.payload,'$.name') name, selected.room,
                   json_extract(p.payload,'$.history[' || selected.position || ']') event
            FROM selected JOIN entities p ON p.collection='plants' AND p.id=selected.plant_id
            ORDER BY {order}
        """,[*params,limit,(page-1)*limit]).fetchall()
        kinds=sorted({legacy_kind(r[0]) for r in db.execute('SELECT DISTINCT kind FROM care_history_index WHERE kind IS NOT NULL') if r[0]})
    return dict(items=[dict(plantID=r['id'],plantName=r['name'],room=r['room'],version=r['version'],event=legacy_event(json.loads(r['event']))) for r in rows],total=total,page=page,limit=limit,hasNextPage=page*limit<total,kinds=kinds)
