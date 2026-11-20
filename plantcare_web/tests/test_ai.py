import asyncio
from uuid import uuid4
from plantcare_web.backend import ai
from plantcare_web.backend.storage import Store
from plantcare_web.backend.settings import Settings
from plantcare_web.backend.models import Plant

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
    assert proposal['proposedFertilizingDays']==30
    assert 'Non usare il valore AI del giorno precedente' in captured[0]
    assert 'Non applicare nuovamente la percentuale del ritmo' in captured[0]
    assert 'RINVII E RITARDI' in captured[0]
    assert 'locationName' in captured[0]
    assert 'careTiming' in captured[0]
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
    assert timing['water']['pendingPostponements']==1
    assert timing['water']['earlyPostponements']==0
    assert timing['water']['recentCompletedGapsDays']==[4,13]
    assert timing['water']['postponements'][0]['outcome']=='pending'
    assert timing['water']['postponements'][1]['note']=='Terreno ancora umido'
    assert timing['fertilize']['honoredPostponements']==1
    assert timing['fertilize']['recentCompletedGapsDays']==[5]


def test_daily_context_includes_location_and_timing():
    plant={'id':'P2','name':'Test','species':'Monstera','category':'Tropicale','room':'Salotto','light':'Luce indiretta','wateringInterval':7,'fertilizingInterval':21,'lastWatered':'2026-11-01T12:00:00Z','history':[],'adaptivePlan':{'locationName':'Roma'}}
    item=ai.daily_context(plant,[],{'name':'Italia'},'Europe/Rome')
    assert item['locationName']=='Roma'
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
