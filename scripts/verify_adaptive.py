"""Compare Python adaptive planner with unmodified Swift source over a branch matrix."""
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plantcare_web.backend.adaptive import make_plan, PLACEMENTS
from plantcare_web.backend.domain import parse
root=Path(__file__).resolve().parents[1]
source=root.parent/'PlantCare2.0/VerdantMultiplatform/Sources/Verdant'
models=(source/'Models.swift').read_text()
adaptive=(source/'AdaptiveCarePlanner.swift').read_text()
def block(text,start):
    begin=text.index(start);opening=text.index('{',begin);depth=1;end=opening+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[begin:end]
harness='import Foundation\n'
harness+=block(adaptive,'struct LocationMatch:')+'\n'+block(adaptive,'struct ClimateSnapshot:')+'\n'
harness+='enum CareLocationPreferences { static var location:LocationMatch? { nil } }\n'
harness+='enum CareDomain:String,Codable,Hashable {case water,nutrition}\n'
harness+=models[models.index('enum PlantPlacement:'):models.index('enum CarePlanRevisionSource:')]
harness+=block(models,'enum CarePlanRevisionSource:')+'\n'
harness+='struct BotanicalCareProfile { var wateringDays:Int;var wateringLabel:String;var sunlight:[String];var soil:[String];var source:String;var summary:String? }\n'
harness+='enum CareScheduleAlignment {\n'+block(models,'    static func fertilizingDays(')+'\n}\n'
harness+=block(adaptive,'enum AdaptiveCarePlanner {')+'\n'
harness+='''
struct Input:Decodable {var species:String;var family:String;var placement:PlantPlacement;var location:LocationMatch;var climate:ClimateSnapshot;var date:String;var botanical:Int?}
let data=FileHandle.standardInput.readDataToEndOfFile()
let cases=try JSONDecoder().decode([Input].self,from:data)
let formatter=ISO8601DateFormatter()
let plans=cases.map { c in
 AdaptiveCarePlanner.makePlan(species:c.species,family:c.family,placement:c.placement,location:c.location,climate:c.climate,date:formatter.date(from:c.date)!,botanicalProfile:c.botanical.map { BotanicalCareProfile(wateringDays:$0,wateringLabel:"dalla scheda salvata",sunlight:[],soil:[],source:"Perenual",summary:nil) })
}
let encoder=JSONEncoder();encoder.dateEncodingStrategy = .iso8601
print(String(decoding:try encoder.encode(plans),as:UTF8.self))
'''
cases=[]
for (species,family),placement,month,latitude,(temp,humidity,rain),botanical in itertools.product(
 [('Monstera deliciosa','Araceae'),('Aloe vera','Asphodelaceae'),('Zamioculcas zamiifolia','Araceae'),('Dracaena trifasciata',''),('Fern','Pteridaceae'),('Phalaenopsis','Orchidaceae'),('Unknown',''),('Unknown','Cactaceae')],
 PLACEMENTS,[1,4,7,10],[42,-33],[(10,80,20),(22,55,0),(25,39,16),(30,75,15)], [None,4]):
    cases.append(dict(species=species,family=family,placement=placement,location=dict(name='Roma',detail='Lazio, Italia',latitude=latitude,longitude=12.5),climate=dict(averageTemperature=temp,relativeHumidity=humidity,precipitationNextWeek=rain),date=f'2026-{month:02}-15T12:00:00Z',botanical=botanical))
with tempfile.TemporaryDirectory(prefix='plantcare-adaptive-') as tmp:
    path=Path(tmp)/'oracle.swift';path.write_text(harness)
    result=subprocess.run(['swift','-module-cache-path',str(Path(tmp)/'cache'),str(path)],input=json.dumps(cases),capture_output=True,text=True,env={**os.environ,'TZ':'Europe/Rome'})
    if result.returncode: print(result.stderr);sys.exit(1)
    expected=json.loads(result.stdout)
for c,want in zip(cases,expected):
    botanical=dict(wateringDays=c['botanical'],source='Perenual',wateringLabel='dalla scheda salvata') if c['botanical'] else None
    got=make_plan(c['species'],c['family'],c['placement'],c['location'],c['climate'],parse(c['date']),botanical=botanical)
    got={k:v for k,v in got.items() if v is not None}
    assert got==want, (c,[(k,got.get(k),want.get(k)) for k in got.keys()|want.keys() if got.get(k)!=want.get(k)])
print(f'Pianificatore adattivo: {len(cases)} piani identici al codice Swift originale (intervalli, motivazioni, aggiustamenti e metadati).')
