"""Compare diagnosis combinations and seasonal values with native Swift execution."""
from pathlib import Path
import json,re,subprocess,tempfile,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plantcare_web.backend.health_guides import diagnosis, practical_guide, SYMPTOMS
from plantcare_web.backend.models import Plant
root=Path(__file__).resolve().parents[1]
native=root.parent/'PlantCare2.0/VerdantMultiplatform/Sources/Verdant'
source=(native/'ToolViews.swift').read_text()
body=source.split('    private var advice: String {',1)[1].split('\n    }\n}',1)[0]
values=(native/'GrowthAndKnowledgeViews.swift').read_text().split('    private var values: [Point] {',1)[1].split('\n    }',1)[0]
values=values.replace('plant.category == .succulent','succulent').replace('plant.adaptivePlan?.placement.isOutdoor == true','outdoor').replace('plant.wateringInterval','interval')
code='''import Foundation
enum Symptom: Int, CaseIterable { case yellow, dry, drooping, spots, pests, slow }
func advice(_ selectedSymptoms:Set<Symptom>) -> String {'''+body+'''}
var answers:[String]=[]
for mask in 1..<64 { answers.append(advice(Set(Symptom.allCases.filter{mask & (1 << $0.rawValue) != 0}))) }
struct Point:Codable {let month:Int; let days:Int}
func seasonal(_ succulent:Bool,_ outdoor:Bool,_ interval:Int) -> [Point] { return '''+values+'''}
var rhythms:[[Point]]=[]
for succulent in [false,true] { for outdoor in [false,true] { for interval in [1,7,9,10,30,120] { rhythms.append(seasonal(succulent,outdoor,interval)) } } }
struct Results:Codable {let answers:[String];let rhythms:[[Point]]}
print(String(data:try JSONEncoder().encode(Results(answers:answers,rhythms:rhythms)),encoding:.utf8)!)
'''
with tempfile.TemporaryDirectory(prefix='plantcare-health-') as folder:
    path=Path(folder)/'verify.swift';path.write_text(code)
    data=json.loads(subprocess.check_output(['swift','-module-cache-path',folder+'/cache',str(path)],text=True))
for mask,answer in enumerate(data['answers'],1):
    assert diagnosis([s for i,s in enumerate(SYMPTOMS) if mask & (1<<i)])==answer
index=0
for succulent in [False,True]:
    for outdoor in [False,True]:
        for interval in [1,7,9,10,30,120]:
            p=Plant(name='Test',category='Succulenta' if succulent else 'Tropicale',wateringInterval=interval).model_dump()
            p['adaptivePlan']={'placement':'Pieno sole' if outdoor else 'Pianerottolo'}
            assert practical_guide(p)['seasonal']==data['rhythms'][index];index+=1
# Text guide payload must stay faithful to the original action steps and tips.
text=(native/'CareEventViews.swift').read_text()
section=text.split('    private var guide: CareActionGuideContent',1)[1].split('    private func guide(',1)[0]
guides=json.loads((root/'plantcare_web/frontend/src/data/care-guides.json').read_text())
assert len(guides)==9
for guide in guides:
    assert len(guide['steps'])==3
    for step in guide['steps']:assert f'"{step["title"]}", "{step["detail"]}"' in section
    assert guide['tip'] in section
print('OK: 63 combinazioni diagnosi, 288 valori stagionali e 9 guide native.')
