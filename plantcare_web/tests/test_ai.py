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

def test_advice_uses_native_instructions_and_no_unresolved_placeholders(tmp_path,monkeypatch):
    store=Store(tmp_path);p=Plant(name='Monstera',carePlanMode='AI').model_dump();store.put('plants',p)
    async def complete(settings,prompt,schema,name):
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
