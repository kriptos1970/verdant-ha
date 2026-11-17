"""Synthetic read-only API workload. Never opens an operational archive."""
import json
import os
from pathlib import Path
import sys
import tempfile
from time import perf_counter
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient


def run(plants=100, events_per_plant=500):
    total=plants*events_per_plant
    with tempfile.TemporaryDirectory(prefix='plantcare-benchmark-') as directory:
        # Set an isolated root before importing main, which initializes its Store.
        previous_env={key:os.environ.get(key) for key in ['PLANTCARE_DATA','PLANTCARE_PHOTOS','PLANTCARE_OPTIONS','PLANTCARE_INGRESS','SUPERVISOR_TOKEN']}
        os.environ.update(PLANTCARE_DATA=directory,PLANTCARE_PHOTOS=directory+'/photos',PLANTCARE_OPTIONS=directory+'/options.json',PLANTCARE_INGRESS='0',SUPERVISOR_TOKEN='')
        try:
            from plantcare_web.backend import main
            from plantcare_web.backend.models import Plant
            for i in range(plants):
                plant=Plant(name=f'Pianta sintetica {i}',room=f'Stanza {i%5}',acquiredOn='2025-01-01T12:00:00Z',lastWatered='2026-11-01T12:00:00Z').model_dump()
                plant['history']=[dict(id=str(uuid4()).upper(),kind='Annaffia',date=f'2026-10-{j%28+1:02}T12:00:00Z',status='completed',note='Osservazione sintetica. '*5) for j in range(events_per_plant)]
                main.store.put('plants',plant)
            client=TestClient(main.app)
            results={}
            for label,path in [('full','/api/plants'),('summary','/api/plants?summary=true'),('historyPage','/api/history?limit=50')]:
                start=perf_counter();response=client.get(path);response.raise_for_status()
                results[label]={'bytes':len(response.content),'seconds':round(perf_counter()-start,3)}
                if label=='historyPage':assert len(response.json()['items'])==50 and response.json()['total']==total
            results['plants']=plants;results['events']=total
            results['reductionPercent']=round(100*(1-results['summary']['bytes']/results['full']['bytes']),2)
            assert results['reductionPercent']>90
            print(json.dumps(results,indent=2))
            return results
        finally:
            for key,value in previous_env.items():
                if value is None:os.environ.pop(key,None)
                else:os.environ[key]=value

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Synthetic read-only API workload.')
    parser.add_argument('--plants',type=int,default=100)
    parser.add_argument('--events',type=int,default=500,help='events per plant')
    args=parser.parse_args()
    run(args.plants,args.events)
