"""Compare selective advice application with original Swift application methods."""
import itertools,json,os,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plantcare_web.backend.ai_support import apply_values
root=Path(__file__).resolve().parents[1];source=root.parent/'PlantCare2.0/VerdantMultiplatform/Sources/Verdant'
models=(source/'Models.swift').read_text();advice=(source/'PlantAdviceViewModel.swift').read_text()
def block(text,start):
 begin=text.index(start);opening=text.index('{',begin);depth=1;end=opening+1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[begin:end]
harness='''import Foundation
struct Plan:Equatable {var verdantFertilizingDays:Int?;var wateringDays:Int;var fertilizingDays:Int;var inspectionDays:Int;var revisionSource:CarePlanRevisionSource?;var revisedAt:Date?;var revisionProvider:String?;var revisionReason:String?;var revisionChangedIntervals:Bool?}
struct Plant:Equatable {var wateringInterval:Int;var fertilizingInterval:Int?;var inspectionInterval:Int?;var pruningInterval:Int?;var repottingInterval:Int?;var carePlanMode:CarePlanMode?;var adaptivePlan:Plan?;var fertilizerProductID:UUID?;var notes:String=""}
struct AIPlanProposalBaseline:Equatable {var plant:Plant;init(plant:Plant){self.plant=plant}}
struct PlantAdvice {var wateringDays:Int?;var fertilizingDays:Int?;var inspectionDays:Int?;var pruningDays:Int?;var repottingDays:Int?;var careNotes:String?;var summaryMarkdown:String}
struct FertilizerProduct {var id:UUID;var effectiveApplicationIntervalDays:Int}
enum CloudAIProvider {static let selected=Self.gemini;case gemini;var title:String {"Gemini"}}
enum PlantAdviceApplicationError:Error {case staleProposal}
'''
for start in ['enum CarePlanMode:','enum CarePlanRevisionSource:','enum CarePlanFertilizingPolicy {']:harness+=block(models,start)+'\n'
harness+='enum CareScheduleAlignment {\n'+block(models,'    static func fertilizingDays(')+'\n}\n'
harness+=block(advice,'struct PlantAdviceSelection {')+'\n'
harness+='struct Service {\n'+block(advice,'    func updatedPlant(')+'\n'+block(advice,'    nonisolated static func acceptedWateringDays(')+'\n'+block(advice,'    private func appendCareNotes(')+'\n}\n'
harness+=advice[advice.index('private extension Comparable {'):]
harness+='''
struct Input:Decodable {var mode:CarePlanMode;var water:Int;var feed:Int?;var baseline:Int?;var proposedWater:Int;var proposedFeed:Int;var mask:Int}
let cases=try JSONDecoder().decode([Input].self,from:FileHandle.standardInput.readDataToEndOfFile())
var output:[[String:Int]]=[]
for c in cases {
 let plan=c.baseline.map {Plan(verdantFertilizingDays:$0,wateringDays:c.water,fertilizingDays:c.feed ?? 28,inspectionDays:7)}
 let plant=Plant(wateringInterval:c.water,fertilizingInterval:c.feed,inspectionInterval:nil,pruningInterval:90,repottingInterval:365,carePlanMode:c.mode,adaptivePlan:plan,fertilizerProductID:nil)
 let proposal=PlantAdvice(wateringDays:c.proposedWater,fertilizingDays:c.proposedFeed,inspectionDays:200,pruningDays:1,repottingDays:5000,careNotes:nil,summaryMarkdown:"Consiglio")
 let selection=PlantAdviceSelection(watering:c.mask&1 != 0,fertilizing:c.mask&2 != 0,inspection:c.mask&4 != 0,pruning:c.mask&8 != 0,repotting:c.mask&16 != 0)
 let result=try Service().updatedPlant(from:proposal,selection:selection,current:plant,expectedBaseline:AIPlanProposalBaseline(plant:plant),fertilizers:[])
 output.append(["wateringInterval":result.wateringInterval,"fertilizingInterval":result.fertilizingInterval ?? -1,"inspectionInterval":result.inspectionInterval ?? -1,"pruningInterval":result.pruningInterval ?? -1,"repottingInterval":result.repottingInterval ?? -1])
}
print(String(decoding:try JSONEncoder().encode(output),as:UTF8.self))
'''
cases=[dict(mode=mode,water=water,feed=feed,baseline=baseline,proposedWater=proposed_water,proposedFeed=23,mask=mask) for mode,water,feed,baseline,proposed_water,mask in itertools.product(['Manuale','Intelligente','AI'],[7,30],[None,21],[None,56],[1,999],range(32))]
with tempfile.TemporaryDirectory(prefix='plantcare-ai-') as tmp:
 path=Path(tmp)/'oracle.swift';path.write_text(harness)
 result=subprocess.run(['swift','-module-cache-path',str(Path(tmp)/'cache'),str(path)],input=json.dumps(cases),capture_output=True,text=True,env={**os.environ,'TZ':'Europe/Rome'})
 if result.returncode:print(result.stderr);sys.exit(1)
 expected=json.loads(result.stdout)
for c,want in zip(cases,expected):
 plant=dict(wateringInterval=c['water'],fertilizingInterval=c['feed'],inspectionInterval=None,pruningInterval=90,repottingInterval=365,carePlanMode=c['mode'])
 if c['baseline'] is not None:plant['adaptivePlan']=dict(verdantFertilizingDays=c['baseline'])
 advice=dict(wateringDays=c['proposedWater'],fertilizingDays=c['proposedFeed'],inspectionDays=200,pruningDays=1,repottingDays=5000)
 selection={name:bool(c['mask']&(1<<i)) for i,name in enumerate(['watering','fertilizing','inspection','pruning','repotting'])}
 actual=apply_values(plant,advice,selection)
 assert {k:actual.get(k) if actual.get(k) is not None else -1 for k in want}==want,(c,actual,want)
print(f'Applicazione selettiva AI: {len(cases)} combinazioni equivalenti al codice Swift originale.')
