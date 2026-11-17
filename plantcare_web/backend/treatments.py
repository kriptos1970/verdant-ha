"""Treatment cycles: native fixed start-date cadence with an authoritative ledger.

The native completedApplications value is preserved as a baseline for applications
not represented in an imported ledger. Web edits/deletions recompute counts from
active records, so a deleted application cannot leave a cycle falsely completed.
"""
from datetime import timedelta
from .domain import active_history, iso, now, parse
from .care_kinds import canonical_plant


def completed_events(plant, plan_id):
    plant = canonical_plant(plant)
    return [e for e in active_history(plant) if e.get('kind') == 'treatment'
            and e.get('treatmentPlanID') == plan_id and e.get('status') != 'postponed']


def pin_baselines(plant):
    for plan in plant.get('treatmentPlans') or []:
        if 'legacyCompletedApplications' not in plan:
            plan['legacyCompletedApplications'] = max(
                0, int(plan.get('completedApplications', 0)) - len(completed_events(plant, plan['id']))
            )


def completed_count(plant, plan):
    count = len(completed_events(plant, plan['id']))
    baseline = plan.get('legacyCompletedApplications')
    if baseline is None:
        baseline = max(0, int(plan.get('completedApplications', 0)) - count)
    return min(int(plan['totalApplications']), max(0, int(baseline)) + count)


def update_counts(plant):
    for plan in plant.get('treatmentPlans') or []:
        plan['completedApplications'] = completed_count(plant, plan)


def treatment_view(plant, plan, tz, at=None):
    plant = canonical_plant(plant)
    at = at or now()
    count = completed_count(plant, plan)
    total = int(plan['totalApplications'])
    interval = max(1, int(plan['intervalDays']))
    due = parse(plan['startDate']).astimezone(tz) + timedelta(days=count * interval)
    events = [e for e in active_history(plant) if e.get('kind') == 'treatment' and e.get('treatmentPlanID') == plan['id']]
    completions = [parse(e['date']) for e in events if e.get('status') != 'postponed']
    latest = max(completions) if completions else None
    postponed = [e for e in events if e.get('status') == 'postponed' and e.get('postponedUntil') and (latest is None or parse(e['date']) > latest)]
    if postponed:
        recent = max(postponed, key=lambda e: parse(e['date']))
        due = max(due, parse(recent['postponedUntil']))
    status = 'active'
    if plan.get('cancelledAt'):
        status = 'cancelled'
    elif count >= total:
        status = 'complete'
    elif plan.get('endDate') and due > parse(plan['endDate']):
        status = 'ended'
    final = parse(plan['startDate']).astimezone(tz) + timedelta(days=(total - 1) * interval)
    if plan.get('endDate'):
        final = min(final, parse(plan['endDate']))
    return {**plan, 'completedApplications': count, 'status': status,
            'remainingApplications': max(0, total - count), 'nextDueDate': iso(due) if status == 'active' else None,
            'calculatedEnd': iso(final)}


def treatment_actions(plant, tz, at=None, language='it'):
    at = at or now()
    result = []
    for plan in plant.get('treatmentPlans') or []:
        view = treatment_view(plant, plan, tz, at)
        if view['status'] != 'active':
            continue
        due = parse(view['nextDueDate'])
        number = view['completedApplications'] + 1
        reason = (f"{plan['productName']} · application {number} of {plan['totalApplications']}" if language=='en' else f"{plan['productName']} · intervento {number} di {plan['totalApplications']}")
        if plan.get('dose'):
            reason += ' · ' + plan['dose']
        result.append({'id': f"{plant['id']}:treatment:{plan['id']}:{number}",
                       'plantID': plant['id'], 'plantName': plant['name'], 'room': plant['room'],
                       'kind': 'treatment', 'dueDate': iso(due),
                       'daysUntil': (due.astimezone(tz).date() - at.astimezone(tz).date()).days,
                       'intervalDays': plan['intervalDays'], 'treatmentPlanID': plan['id'],
                       'productID': plan['productID'], 'applicationNumber': number, 'reason': reason})
    return result
