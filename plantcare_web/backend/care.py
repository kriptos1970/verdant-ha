"""Atomic care commands shared by the calendar, plant detail and guided round."""
from uuid import uuid4
from zoneinfo import ZoneInfo
from .domain import active_history, care_state, iso, now, parse, pending_actions, schedule, uses_watering
from .storage import Conflict
from .treatments import pin_baselines, treatment_view, update_counts


def event_payload(body):
    return {k: v for k, v in body.model_dump().items()
            if k not in {'includingFertilizing', 'expectedApplicationNumber', 'scheduledDueDate'}}


def validate_postponement(body):
    if body.status == 'postponed' and (not body.postponedUntil or parse(body.postponedUntil) <= parse(body.date)):
        raise ValueError('Il rinvio deve essere successivo alla data della cura.')


def record(plant, body, zone, product=None):
    validate_postponement(body)
    if any(e['id'] == body.id for e in plant['history']):
        return False
    tz = ZoneInfo(zone)
    day = lambda value: parse(value).astimezone(tz).date()
    if body.kind == 'Annaffia' and body.status == 'completed' and any(
        e['kind'] == 'Annaffia' and e.get('status') == 'completed' and parse(e['date']) == parse(body.date)
        for e in active_history(plant)
    ):
        return False
    if body.kind == 'Concima' and body.status == 'completed':
        fed = any(e['kind'] == 'Concima' and e.get('status') != 'postponed' and day(e['date']) == day(body.date)
                  for e in active_history(plant))
        if not any(e['kind'] == 'Concima' for e in plant['history']) and plant.get('lastFertilized'):
            fed = fed or day(plant['lastFertilized']) == day(body.date)
        if fed:
            return False
    if body.scheduledDueDate:
        current = next((a for a in pending_actions(plant, zone, product=product)
                        if a['kind'] == body.kind and a.get('treatmentPlanID') == body.treatmentPlanID), None)
        if current is None or parse(current['dueDate']) != parse(body.scheduledDueDate):
            raise Conflict('Questa attività è cambiata. Ricarica il calendario prima di registrarla.')
    pin_baselines(plant)
    plan = None
    if body.treatmentPlanID:
        if body.kind != 'Trattamento':
            raise ValueError('Un ciclo può essere associato solo a un trattamento.')
        plan = next((p for p in plant.get('treatmentPlans') or [] if p['id'] == body.treatmentPlanID), None)
        if plan is None:
            raise ValueError('Ciclo di trattamento non trovato.')
        state = treatment_view(plant, plan, tz)
        if state['status'] != 'active':
            raise Conflict('Il ciclo non è più attivo.')
        if body.expectedApplicationNumber != state['completedApplications'] + 1:
            raise Conflict('Questa applicazione è già stata registrata o il ciclo è cambiato. Ricarica la scheda.')
        if body.status == 'postponed' and plan.get('endDate') and parse(body.postponedUntil) > parse(plan['endDate']):
            raise ValueError('Il rinvio supera la data finale del ciclo. Modifica prima la durata del ciclo.')
    before = schedule(plant, zone, parse(body.date))
    event = event_payload(body)
    event.update(schemaVersion=2, createdAt=iso(now()), updatedAt=iso(now()), revision=1, origin='user')
    if plan:
        event['productID'] = plan['productID']
        event['applicationNumber'] = body.expectedApplicationNumber
        description = f"{plan['productName']} · intervento {body.expectedApplicationNumber} di {plan['totalApplications']}"
        if plan.get('dose'):
            description += ' · ' + plan['dose']
        event['note'] = ' · '.join(p for p in [description, body.note] if p)
    plant['history'].append(event)
    if body.status == 'completed' and body.kind == 'Annaffia':
        plant['lastWatered'] = body.date
        plant['nextWateringOverride'] = None
        from .adaptive import learn_after_watering
        learn_after_watering(plant,zone,parse(body.date))
        feed = next((a for a in before if a['kind'] == 'Concima'), None)
        water = next((a for a in before if a['kind'] == 'Annaffia'), None)
        due = uses_watering(product) and feed and (
            day(feed['dueDate']) <= day(body.date) or
            day(feed['dueDate']) == day(body.scheduledDueDate or water['dueDate'])
        )
        fed = any(e['kind'] == 'Concima' and e.get('status') != 'postponed' and day(e['date']) == day(body.date)
                  for e in active_history(plant))
        if not any(e['kind'] == 'Concima' for e in plant['history']) and plant.get('lastFertilized'):
            fed = fed or day(plant['lastFertilized']) == day(body.date)
        if due and not fed:
            feed_event = {**event, 'id': str(uuid4()).upper(), 'kind': 'Concima', 'productID': plant.get('fertilizerProductID')}
            plant['nextFertilizingOverride'] = None
            if body.includingFertilizing:
                plant['lastFertilized'] = body.date
            else:
                if not any(e['kind'] == 'Concima' for e in plant['history']) and plant.get('lastFertilized'):
                    plant['history'].append({**event, 'id': str(uuid4()).upper(), 'kind': 'Concima', 'date': plant['lastFertilized']})
                feed_event.update(status='postponed', postponedUntil=next(a['dueDate'] for a in schedule(plant, zone) if a['kind'] == 'Annaffia'))
            plant['history'].append(feed_event)
            if body.includingFertilizing:
                event['pairedFertilizingEventID']=feed_event['id']
    elif body.status == 'completed' and body.kind == 'Concima':
        plant['lastFertilized'] = body.date
        plant['nextFertilizingOverride'] = None
    update_counts(plant)
    return True


def recalculate(plant):
    """Ledger facts remain authoritative after edits and tombstones."""
    for kind, last_key, override_key in [
        ('Annaffia', 'lastWatered', 'nextWateringOverride'),
        ('Concima', 'lastFertilized', 'nextFertilizingOverride'),
    ]:
        if not any(e['kind'] == kind for e in plant['history']):
            continue
        completions = [parse(e['date']) for e in active_history(plant) if e['kind'] == kind and e.get('status') != 'postponed']
        plant[last_key] = iso(max(completions)) if completions else (plant['acquiredOn'] if kind == 'Annaffia' else None)
        _, deferred = care_state(plant, kind)
        plant[override_key] = iso(deferred) if deferred else None
    update_counts(plant)
