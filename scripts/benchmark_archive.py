"""Measure API reads against an isolated, synthetic archive."""
import json
import os
from datetime import date, timedelta
from math import ceil
from pathlib import Path
from statistics import median
import sys
import tempfile
from time import perf_counter
from uuid import UUID
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient


def measure(client, path, samples, params=None):
    response = client.get(path, params=params)  # Warm-up, not counted.
    response.raise_for_status()
    times = []
    for _ in range(samples):
        start = perf_counter()
        response = client.get(path, params=params)
        times.append(perf_counter() - start)
        response.raise_for_status()
    return {
        'bytes': len(response.content),
        'medianMs': round(1_000 * median(times), 1),
        'p95Ms': round(1_000 * sorted(times)[ceil(.95 * samples) - 1], 1),
    }, response


def run(plants=100, events_per_plant=500, samples=20, include_full=True):
    if min(plants, events_per_plant, samples) < 1:
        raise ValueError('Plant, event and sample counts must be positive.')
    if 'plantcare_web.backend.main' in sys.modules:
        raise RuntimeError('Run the benchmark in a fresh Python process.')
    total = plants * events_per_plant
    with tempfile.TemporaryDirectory(prefix='plantcare-benchmark-') as directory:
        # Set an isolated root before importing main, which initializes its Store.
        isolated_env = dict(PLANTCARE_DATA=directory, PLANTCARE_PHOTOS=directory+'/photos',
                            PLANTCARE_OPTIONS=directory+'/options.json', PLANTCARE_MIGRATE_DIR=directory+'/migration',
                            PLANTCARE_INGRESS='0', SUPERVISOR_TOKEN='')
        previous_env = {key: os.environ.get(key) for key in isolated_env}
        os.environ.update(isolated_env)
        try:
            from plantcare_web.backend import main
            from plantcare_web.backend.models import Plant
            if main.store.root != Path(directory) or main.store.photos != Path(directory)/'photos':
                raise RuntimeError('Refusing to seed outside the temporary archive.')
            end = date.today() - timedelta(days=1)
            start_filter = end - timedelta(days=29)
            timestamps = [(end - timedelta(days=j)).isoformat() + 'T12:00:00Z' for j in range(events_per_plant)]
            kinds = ('Annaffia', 'Concima', 'Pota')
            detail_id = str(UUID(int=1)).upper()
            seed_start = perf_counter()
            with main.store.connection() as db:
                for i in range(plants):
                    plant = Plant(id=str(UUID(int=i+1)).upper(), name=f'Pianta sintetica {i}',
                                  room=f'Stanza {i%5}', acquiredOn=timestamps[-1], lastWatered=timestamps[0]).model_dump()
                    plant['history'] = [
                        dict(id=str(UUID(int=plants + i*events_per_plant + j + 1)).upper(),
                             kind=kinds[j % len(kinds)], date=timestamp, status='completed',
                             note='Osservazione sintetica. ' * 5)
                        for j, timestamp in enumerate(timestamps)
                    ]
                    main.store.put('plants', plant, db=db)
            seed_seconds = round(perf_counter() - seed_start, 3)
            client=TestClient(main.app)
            results = {
                'plants': plants, 'events': total, 'samplesPerView': samples,
                'seedSeconds': seed_seconds, 'sqliteBytes': (Path(directory)/'plantcare.sqlite').stat().st_size,
            }
            workloads = [
                ('summary', '/api/plants', {'summary': 'true'}),
                ('historyPage', '/api/history', {'limit': 50}),
                ('historyFiltered', '/api/history', {
                    'limit': 50, 'room': 'Stanza 0', 'kind': 'Annaffia',
                    'from_day': start_filter.isoformat(), 'to_day': end.isoformat(),
                }),
                ('plantDetail', f'/api/plants/{detail_id}', {}),
                ('analytics30', '/api/analytics', {'days': 30}),
            ]
            for label, path, params in workloads:
                results[label], response = measure(client, path, samples, params)
                if label == 'historyPage':
                    history = response.json()
                    assert len(history['items']) == min(total, 50) and history['total'] == total
                if label == 'historyFiltered':
                    expected = ceil(plants / 5) * ceil(min(30, events_per_plant) / len(kinds))
                    history = response.json()
                    assert len(history['items']) == min(expected, 50) and history['total'] == expected
            if include_full:
                # Optional size reference, outside the normal UI workload.
                full, _ = measure(client, '/api/plants', 1)
                results['full'] = {'bytes': full['bytes'], 'ms': full['medianMs']}
                results['reductionPercent']=round(100*(1-results['summary']['bytes']/full['bytes']),2)
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
    parser.add_argument('--samples',type=int,default=20,help='measured requests per view, after warm-up')
    parser.add_argument('--skip-full',action='store_true',help='skip the unpaginated response when measuring UI memory')
    args=parser.parse_args()
    run(args.plants,args.events,args.samples,include_full=not args.skip_full)
