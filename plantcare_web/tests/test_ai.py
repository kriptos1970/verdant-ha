import asyncio
import pytest
from uuid import uuid4
from plantcare_web.backend import ai
from plantcare_web.backend.storage import Store
from plantcare_web.backend.storage import Conflict
from plantcare_web.backend.settings import Settings
from plantcare_web.backend.models import Plant
from plantcare_web.backend.domain import feed_days, accepted_water


@pytest.mark.parametrize('experience,low,high', [
    ('principiante', 17, 23), ('intermedio', 15, 25),
    ('esperto', 13, 27), ('professionista', 10, 30),
    ('unknown', 15, 25),
])
def test_ai_water_limits_follow_experience(experience, low, high):
    assert accepted_water(1, 20, 1, experience) == low
    assert accepted_water(999, 20, 1, experience) == high
    assert accepted_water(1, 7, 30, experience) == 30


@pytest.mark.parametrize('experience,percent,maximum', [
    ('principiante', 15, 6), ('intermedio', 25, 7),
    ('esperto', 35, 8), ('professionista', 50, 9),
])
def test_daily_prompt_and_output_share_experience_limits(tmp_path, monkeypatch, experience, percent, maximum):
    store = Store(tmp_path)
    plant = Plant(name='Pothos', carePlanMode='AI', wateringInterval=6).model_dump()
    store.put('plants', plant)
    store.set_state('preferences', {'experience': experience})

    async def complete(settings, prompt, schema, name):
        import json
        context = json.loads(prompt.split('PIANTE\n', 1)[1].split('\nData della richiesta:', 1)[0])[0]
        assert context['experienceLevel'] == experience
        assert context['wateringLimits']['maxDeviationPercent'] == percent
        assert context['wateringLimits']['maximumDays'] == maximum
        assert 'limite del 25%' not in prompt
        assert 'rinvii onorati' in prompt and 'reason' in prompt
        return {'summary': 'Revisione', 'plants': [{
            'plantID': plant['id'], 'wateringDays': 9, 'fertilizingDays': 18,
            'hasSufficientEvidence': True, 'reason': 'Due rinvii onorati indicano che gli intervalli attuali sono troppo brevi: nove giorni osservati.',
        }]}

    monkeypatch.setattr(ai, 'complete', complete)
    asyncio.run(ai.analyze(store, Settings()))
    proposal, _ = store.get('proposals', plant['id'])
    assert proposal['proposedWateringDays'] == maximum
    assert proposal['proposedFertilizingDays'] >= 2 * maximum
    if maximum != 9:
        assert '9' in proposal['reason'] and str(maximum) in proposal['reason']
        assert f'{percent}%' in proposal['reason']


def test_recent_care_and_timing_keep_postponement_evidence():
    plant = Plant(name='Pothos', wateringInterval=6).model_dump()
    plant['history'] = [
        {'kind': 'water', 'date': '2026-11-01T12:00:00Z', 'status': 'completed'},
        {'kind': 'water', 'date': '2026-11-07T12:00:00Z', 'status': 'postponed',
         'postponedUntil': '2026-11-10T12:00:00Z', 'note': 'Substrato ancora umido'},
        {'kind': 'water', 'date': '2026-11-10T12:00:00Z', 'status': 'completed'},
    ]
    context = ai.daily_context(plant, [])
    postponed = next(e for e in context['recentCare'] if e['status'] == 'postponed')
    assert postponed['postponedUntil'] == '2026-11-10T12:00:00Z'
    assert postponed['note'] == 'Substrato ancora umido'
    timing = context['careTiming']['water']
    assert timing['recentCompletedGapsDays'] == [9]
    assert timing['honoredPostponements'] == 1
    assert timing['postponements'][0]['completedOn'] == '2026-11-10'
    assert timing['postponements'][0]['completedGapDays'] == 9
    text = ai.care_timing_text(plant)
    assert 'Substrato ancora umido' in text
    assert 'completata: 2026-11-10, intervallo: 9 giorni' in text


def test_changed_profile_rejects_out_of_bounds_pending_proposal(tmp_path):
    store = Store(tmp_path)
    plant = Plant(name='Pothos', carePlanMode='AI', wateringInterval=6).model_dump()
    store.put('plants', plant)
    store.put('proposals', {
        'id': plant['id'], 'expectedVersion': 1, 'proposedWateringDays': 9,
        'proposedFertilizingDays': 18, 'reason': 'Rinvii onorati', 'provider': 'test',
    })
    store.set_state('preferences', {'experience': 'intermedio'})
    with pytest.raises(Conflict, match='profilo attuale'):
        ai.apply(store, plant['id'])
    assert store.get('plants', plant['id'])[0]['wateringInterval'] == 6
    store.set_state('preferences', {'experience': 'professionista'})
    saved, _ = ai.apply(store, plant['id'])
    assert saved['wateringInterval'] == 9
    assert saved['fertilizingInterval'] == 18


def test_profile_change_during_analysis_preserves_existing_proposal(tmp_path, monkeypatch):
    store = Store(tmp_path)
    plant = Plant(name='Pothos', carePlanMode='AI', wateringInterval=6).model_dump()
    store.put('plants', plant)
    store.set_state('preferences', {'experience': 'professionista'})
    old = {'id': plant['id'], 'marker': 'previous proposal'}
    store.put('proposals', old)

    async def complete(*args):
        store.set_state('preferences', {'experience': 'principiante'})
        return {'summary': 'Revisione', 'plants': [{
            'plantID': plant['id'], 'wateringDays': 9, 'fertilizingDays': 18,
            'hasSufficientEvidence': True, 'reason': 'Rinvii onorati',
        }]}

    monkeypatch.setattr(ai, 'complete', complete)
    with pytest.raises(Conflict, match='esperienza è cambiato'):
        asyncio.run(ai.analyze(store, Settings()))
    assert store.get('proposals', plant['id'])[0] == old


def test_ai_gets_early_watering_events_with_recorded_and_inferred_sources():
    plant = Plant(name='Pothos', wateringInterval=10).model_dump()
    plant['history'] = [
        {'kind': 'water', 'date': '2026-11-01T12:00:00Z', 'status': 'completed'},
        {'kind': 'water', 'date': '2026-11-08T12:00:00Z', 'status': 'completed'},
        {'kind': 'water', 'date': '2026-11-15T12:00:00Z', 'status': 'completed',
         'wateringDueDate': '2026-11-18T12:00:00Z', 'note': 'Substrato asciutto'},
    ]
    context = ai.daily_context(plant, [])
    timing = context['careTiming']['water']
    assert timing['earlyWaterings'] == 1
    assert timing['inferredEarlyWaterings'] == 1
    early = timing['earlyWateringEvents'][-1]
    assert early['daysEarly'] == 3
    assert early['note'] == 'Substrato asciutto'
    assert early['source'] == 'recordedSchedule'
    assert context['recentCare'][0]['wateringDueDate'] == '2026-11-18T12:00:00Z'
    assert 'Annaffiature anticipate: 1 registrate, 1 stimate' in ai.care_timing_text(plant)


@pytest.mark.parametrize('water', [1, 3, 7, 30, 120])
@pytest.mark.parametrize('desired', [-1, 1, 7, 23, 120, 365])
def test_fertilizing_requires_at_least_two_watering_cycles(water, desired):
    assert 2 * water <= feed_days(desired, water) <= 365


def test_advice_corrects_overfrequent_feeding_and_constrains_schema(tmp_path, monkeypatch):
    store = Store(tmp_path)
    plant = Plant(name='Monstera', carePlanMode='AI', wateringInterval=7).model_dump()
    store.put('plants', plant)

    async def complete(settings, prompt, schema, name):
        assert 'fertilizingDays >= 2 * wateringDays' in prompt
        allowed = schema['properties']['fertilizingDays']['enum']
        assert min(allowed) == 14
        assert all(days % 7 == 0 for days in allowed)
        return dict(wateringDays=7, fertilizingDays=1, inspectionDays=7,
                    pruningDays=90, repottingDays=365, careNotes='', summaryMarkdown='')

    monkeypatch.setattr(ai, 'complete', complete)
    result = asyncio.run(ai.advice(store, Settings(), plant['id'], 'Come concimare?'))
    assert result['fertilizingDays'] == 14

def test_daily_preserves_native_prompt_and_clamps_results(tmp_path,monkeypatch):
    store=Store(tmp_path)
    p=Plant(name='Sansevieria',species='Dracaena trifasciata',light='Luce bassa',carePlanMode='AI',wateringInterval=30,fertilizingInterval=90).model_dump()
    store.put('plants',p)
    captured=[]
    async def complete(settings,prompt,schema,name):
        captured.append(prompt)
        return {'summary':'Valutazione','plants':[{'plantID':p['id'],'wateringDays':1,'fertilizingDays':1,'hasSufficientEvidence':True,'reason':'Luce bassa e riserva idrica.'}]}
    monkeypatch.setattr(ai,'complete',complete)
    result=asyncio.run(ai.analyze(store,Settings()))
    assert result['proposals']==1
    proposal,_=store.get('proposals',p['id'])
    assert proposal['proposedWateringDays']==30
    assert proposal['proposedFertilizingDays']==60
    assert 'fertilizingDays >= 2 * wateringDays' in captured[0]
    assert 'Non usare il valore AI del giorno precedente' in captured[0]
    assert 'Non applicare nuovamente la percentuale del ritmo' in captured[0]
    assert 'RINVII E RITARDI' in captured[0]
    assert 'locationName' in captured[0]
    assert 'careTiming' in captured[0]
    assert 'experienceLevel' in captured[0]
    applied,_=ai.apply(store,p['id'])
    assert applied['wateringInterval']==30
    assert applied['history'][-1]['kind']=='planUpdate'
    assert store.list('proposals')==[]

def test_insufficient_evidence_never_proposes_change(tmp_path,monkeypatch):
    store=Store(tmp_path)
    p=Plant(name='Pothos',carePlanMode='AI',wateringInterval=7).model_dump();store.put('plants',p)
    async def complete(*args):
        return {'summary':'Nessuna modifica','plants':[{'plantID':p['id'],'wateringDays':20,'fertilizingDays':40,'hasSufficientEvidence':True,'reason':'Dati insufficienti per una revisione.'}]}
    monkeypatch.setattr(ai,'complete',complete)
    assert asyncio.run(ai.analyze(store,Settings()))['proposals']==0
    assert store.get('plants',p['id'])[0]['wateringInterval']==7

def test_care_timing_distinguishes_postponements_and_delays():
    plant={'id':'P1','name':'Test','species':'Monstera','category':'Tropicale','room':'Salotto','light':'Luce indiretta','wateringInterval':7,'fertilizingInterval':21,'lastWatered':'2026-11-01T12:00:00Z','history':[
        {'kind':'water','date':'2026-11-01T12:00:00Z','status':'completed'},
        {'kind':'water','date':'2026-11-05T12:00:00Z','status':'completed'},
        {'kind':'water','date':'2026-11-10T12:00:00Z','status':'postponed','postponedUntil':'2026-11-13T12:00:00Z','note':'Terreno ancora umido'},
        {'kind':'water','date':'2026-11-18T12:00:00Z','status':'completed'},
        {'kind':'water','date':'2026-11-18T12:00:00Z','status':'postponed','postponedUntil':'2026-11-21T12:00:00Z'},
        {'kind':'fertilize','date':'2026-11-02T12:00:00Z','status':'completed'},
        {'kind':'fertilize','date':'2026-11-03T12:00:00Z','status':'postponed','postponedUntil':'2026-11-06T12:00:00Z'},
        {'kind':'fertilize','date':'2026-11-07T12:00:00Z','status':'completed'},
    ]}
    timing=ai.care_timing(plant,'Europe/Rome')
    assert timing['water']['honoredPostponements']==1
    assert timing['water']['honoredCycles']==1
    assert timing['water']['pendingPostponements']==1
    assert timing['water']['earlyPostponements']==0
    assert timing['water']['recentCompletedGapsDays']==[4,13]
    assert timing['water']['postponements'][0]['outcome']=='pending'
    assert timing['water']['postponements'][1]['note']=='Terreno ancora umido'
    assert timing['fertilize']['honoredPostponements']==1
    assert timing['fertilize']['recentCompletedGapsDays']==[5]


def test_daily_context_includes_location_and_timing():
    plant={'id':'P2','name':'Test','species':'Monstera','category':'Tropicale','room':'Salotto','light':'Luce indiretta','wateringInterval':7,'fertilizingInterval':21,'lastWatered':'2026-11-01T12:00:00Z','history':[],'adaptivePlan':{'locationName':'Roma'}}
    item=ai.daily_context(plant,[],{'name':'Italia'},'Europe/Rome','esperto')
    assert item['locationName']=='Roma'
    assert item['experienceLevel']=='esperto'
    assert item['careTiming']['water']['postponements']==[]
    assert 'recentCompletedGapsDays' in item['careTiming']['water']


def test_advice_uses_native_instructions_and_no_unresolved_placeholders(tmp_path,monkeypatch):
    store=Store(tmp_path);p=Plant(name='Monstera',carePlanMode='AI').model_dump();store.put('plants',p)
    captured_advice=[]
    async def complete(settings,prompt,schema,name):
        captured_advice.append(prompt)
        assert 'Sei l\'assistente botanico di Verdant.' in prompt
        assert '{v' not in prompt
        assert 'CONTESTO STAGIONALE' not in prompt
        assert 'Non ricevi e non analizzi fotografie' in prompt
        assert 'Non derivare nuovi intervalli dal valore AI applicato in precedenza.' in prompt
        return {'wateringDays':999,'fertilizingDays':23,'inspectionDays':7,'pruningDays':90,'repottingDays':365,'careNotes':'Controlla il terreno','summaryMarkdown':'Irrigazione'}
    monkeypatch.setattr(ai,'complete',complete)
    result=asyncio.run(ai.advice(store,Settings(),p['id'],'Come sta?'))
    assert result['wateringDays']==7
    assert result['fertilizingDays']==21
    assert 'RINVII RECENTI' in captured_advice[0]
    assert 'LOCALITÀ' in captured_advice[0]
    assert 'ESPERIENZA DEL COLTATORE' in captured_advice[0]
