"""Execute original Swift shadow evaluators against the web port (no original files changed)."""
import itertools,json,os,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plantcare_web.backend.care_engine import evaluate
from plantcare_web.backend.domain import parse
root=Path(__file__).resolve().parents[1];source=root.parent/'PlantCare2.0/VerdantMultiplatform/Sources/Verdant'
models=(source/'Models.swift').read_text();species=(source/'SpeciesBiology.swift').read_text();profiles=(source/'CareProfiles.swift').read_text()
stubs='''
struct PlantSetup:Hashable,Sendable {var container:Container?;var substrate:Substrate?;var recordedAt:Date?}
struct Container:Hashable,Sendable {var drainageHoles:Bool?;var drainageQuality:Drainage}
enum Drainage:String,Sendable {case poor,good}
struct Substrate:Hashable,Sendable {}
struct CareEvent:Sendable {enum Kind {case water,repot,move};enum Status {case completed,postponed};enum Health {case sick,struggling,good,excellent};var id:UUID;var kind:Kind;var status:Status?;var date:Date;var health:Health?}
struct GrowthEntry:Sendable {var id:UUID;var date:Date;var health:CareEvent.Health}
struct Plant:Sendable {var activeHistory:[CareEvent];var growthEntries:[GrowthEntry]?}
struct CareMeasurement:Sendable {var id:UUID;var kind:MeasurementKind;var value:Double;var unit:MeasurementUnit;var measuredAt:Date;var source:MeasurementSource;var reliability:Double;var sourceIdentifier:String?}
enum LightLevel:String,Sendable {case low,indirect,bright,direct}
struct LightMeasurement {var id:UUID;var date:Date;var estimatedLux:Double;var note:String?;var isPossibleDirectSun:Bool {estimatedLux>=50000}}
'''
harness='import Foundation\n'+species[:species.index('enum SpeciesClimate:')]+profiles[:profiles.index('struct CareProfileResolver:')]+stubs
for name in ['CareEngineModels.swift','CareEngine.swift','DryDownAnalyzer.swift','LegacyDomainEvaluators.swift','AdvancedDomainEvaluators.swift']:
    harness+='\n'+(source/'CareEngine'/name).read_text()
harness+='\n'+(source/'LightEvaluationEngine.swift').read_text()
harness+='''
struct Input:Decodable {var moisture:Double?;var reliability:Double;var dry:String;var quality:Double;var drainage:Bool;var ec:Double?;var state:String;var light:Double?;var temp:Double?;var humidity:Double?;var age:Double;var lightCount:Int?;var lightProfile:String?}
let cases=try JSONDecoder().decode([Input].self,from:FileHandle.standardInput.readDataToEndOfFile())
let formatter=ISO8601DateFormatter();let at=formatter.date(from:"2026-11-15T12:00:00Z")!;let pid=UUID(uuidString:"11111111-1111-1111-1111-111111111111")!
let engine=CareEngine(evaluators:[LegacyWaterDomainEvaluator(),LegacyLightDomainEvaluator(),NutritionDomainEvaluator(),ClimateDomainEvaluator(domain:.temperature),ClimateDomainEvaluator(domain:.humidity)])
var outputs:[[CareRecommendation]]=[]
for c in cases {
 var measurements:[CareMeasurementInput]=[]
 func append(_ value:Double?,_ kind:MeasurementKind,_ unit:MeasurementUnit,_ index:Int) {
  if let value { measurements.append(.init(id:UUID(uuidString:String(format:"00000000-0000-0000-0000-%012d",index))!,kind:kind,value:value,unit:unit,measuredAt:at.addingTimeInterval(-c.age),source:.sensor,reliability:c.reliability)) }
 }
 append(c.moisture,.substrateMoisture,.percent,1);append(c.ec,.substrateEC,.microsiemensPerCentimeter,2);append(c.light,.illuminance,.lux,3);if (c.lightCount ?? 1)>1 {for index in 6..<(5+c.lightCount!) {append(c.light,.illuminance,.lux,index)}};append(c.temp,.temperature,.celsius,4);append(c.humidity,.humidity,.percent,5)
 let species=SpeciesContext(biologyID:nil,scientificName:nil,genus:nil,family:nil,profileQuality:0,lightProfileID:c.lightProfile.flatMap {LightProfileID(rawValue:$0)},waterProfile:c.dry=="nil" ? nil : WaterCareProfile(droughtTolerance:.unknown,preferredDryDown:PreferredDryDown(rawValue:c.dry)!,rootWaterloggingSensitivity:.unknown,waterRetentionPreference:.unknown,rootAerationRequirement:.unknown),waterProfileQuality:c.lightProfile != nil && c.dry=="nil" ? 0.25 : c.quality,temperatureProfile:.init(preferredMinimumCelsius:18,preferredMaximumCelsius:28),temperatureProfileQuality:0.65,humidityProfile:.init(preferredMinimumPercent:40,preferredMaximumPercent:70),humidityProfileQuality:0.65,nutritionProfile:c.quality==0 ? nil : .init(nutrientDemand:.moderate,saltSensitivity:.high),nutritionProfileQuality:c.quality,evidence:[])
 let evidence=EvidenceReference(id:"legacy-schedule-"+pid.uuidString,source:.legacySchedule,reliability:0.35)
 let legacy=LegacyScheduleContext(lastWateredAt:formatter.date(from:"2026-11-01T12:00:00Z"),wateringIntervalDays:7,legacyNextWateringAt:formatter.date(from:"2026-11-08T12:00:00Z"),lastFertilizedAt:nil,fertilizingIntervalDays:nil,source:evidence)
 let temp=c.temp.map {ObservedValue(value:$0,observedAt:at.addingTimeInterval(-c.age),source:.sensor,reliability:c.reliability)}
 let humidity=c.humidity.map {ObservedValue(value:$0,observedAt:at.addingTimeInterval(-c.age),source:.sensor,reliability:c.reliability)}
 let state=PlantStateSnapshot(state:PlantOperationalState(rawValue:c.state)!,confidence:c.state=="unknown" ? 0 : c.state=="recentlyRepotted" ? 1 : c.state=="stressed" ? 0.9 : 0.7,observedAt:nil,evidenceIDs:[])
 let setup=c.drainage ? PlantSetup(container:Container(drainageHoles:false,drainageQuality:.poor),substrate:nil,recordedAt:nil) : nil
 let context=CareContext(plantID:pid,evaluationDate:at,species:species,legacySchedule:legacy,environment:.init(temperatureCelsius:temp,relativeHumidityPercent:humidity,placement:nil,seasonLabel:nil),measurements:measurements,history:.init(completedWateringDates:[],comparableWateringCycles:0,dryDown:.empty),light:.init(fallbackLight:.indirect,providerMinimumLux:nil,providerMaximumLux:nil),setup:setup,plantState:state,missingInputs:[],inputFingerprint:"oracle")
 outputs.append(engine.evaluate(context))
}
let encoder=JSONEncoder();encoder.dateEncodingStrategy = .iso8601
var dryRows:[[String:Any]]=[]
for cycles in [0,1,2,3,4] {
 for mixed in [false,true] {
  for changedSetup in [false,true] {
   var events:[CareEvent]=[];var measures:[CareMeasurement]=[]
   let origin=at.addingTimeInterval(-Double(cycles*4+1)*86400)
   for cycle in 0...cycles {
    let start=origin.addingTimeInterval(Double(cycle*4)*86400)
    events.append(.init(id:UUID(),kind:.water,status:.completed,date:start,health:nil))
    for hour in [0,12,24] {
     measures.append(.init(id:UUID(),kind:.substrateMoisture,value:70-Double(hour),unit:.percent,measuredAt:start.addingTimeInterval(Double(hour)*3600),source:.sensor,reliability:1,sourceIdentifier:mixed && cycle==cycles && hour==24 ? "replacement" : "soil"))
    }
   }
   let setup=changedSetup ? PlantSetup(container:nil,substrate:nil,recordedAt:at.addingTimeInterval(-3600)) : nil
   let d=DryDownAnalyzer().analyze(measurements:measures,events:events,setup:setup,evaluationDate:at,targetMoisturePercent:35)
   dryRows.append(["cycles":cycles,"mixed":mixed,"changedSetup":changedSetup,"completed":d.completedCycleCount,"excluded":d.excludedCycleCount,"rate":d.currentTrend?.dryingRatePercentPerHour as Any? ?? NSNull(),"baselineCount":d.baseline?.comparableCycleCount as Any? ?? NSNull(),"confidence":d.baseline?.confidence as Any? ?? NSNull(),"eta":d.estimatedHoursToTarget as Any? ?? NSNull(),"uncertainty":d.uncertaintyHours as Any? ?? NSNull()])
  }
 }
}
let recommendations=try JSONSerialization.jsonObject(with:encoder.encode(outputs))
print(String(decoding:try JSONSerialization.data(withJSONObject:["recommendations":recommendations,"dryDown":dryRows]),as:UTF8.self))
'''
cases=[]
for moisture,reliability,(dry,quality),drainage,age in itertools.product([None,5,15,25,35,45,55,70,100],[.55,1],[('nil',0),('unknown',.25),('complete',.8),('moderate',.8)],[False,True],[0,43200,43201,-1]):
    cases.append(dict(moisture=moisture,reliability=reliability,dry=dry,quality=quality,drainage=drainage,ec=None,state='unknown',light=None,temp=None,humidity=None,age=age))
for ec,state,quality,temp,humidity,age in itertools.product([None,1199,1200,2000],['unknown','recentlyRepotted','stressed','activeGrowth'],[0,.8],[10,22,35],[20,55,85],[0,21601]):
    cases.append(dict(moisture=None,reliability=1,dry='nil' if not quality else 'complete',quality=quality,drainage=False,ec=ec,state=state,light=1000,temp=temp,humidity=humidity,age=age))
for profile in [None,'GENERIC','TROPICAL_UNDERSTORY','SUCCULENT_BRIGHT_LIGHT']:
    for light,age,count in itertools.product([100,350,1000,5000,20000,50000,100000],[0,12*3600,30*86400,31*86400,-1],[1,3]):
        cases.append(dict(moisture=None,reliability=1,dry='nil',quality=0,drainage=False,ec=None,state='unknown',light=light,temp=None,humidity=None,age=age,lightCount=count,lightProfile=profile))
with tempfile.TemporaryDirectory(prefix='plantcare-engine-') as tmp:
    path=Path(tmp)/'oracle.swift';path.write_text(harness)
    result=subprocess.run(['swift','-module-cache-path',str(Path(tmp)/'cache'),str(path)],input=json.dumps(cases),capture_output=True,text=True,env={**os.environ,'TZ':'Europe/Rome'})
    if result.returncode:print(result.stderr);sys.exit(1)
    output=json.loads(result.stdout);expected=output['recommendations']
for c,want in zip(cases,expected):
    p=dict(id='11111111-1111-1111-1111-111111111111',name='Test',room='Casa',species='',light='Luce indiretta',wateringInterval=7,acquiredOn='2026-11-01T12:00:00Z',lastWatered='2026-11-01T12:00:00Z',history=[],openPlantbookProfile=dict(minimumTemperature=18,maximumTemperature=28,minimumAirHumidity=40,maximumAirHumidity=70))
    if c['drainage']:p['setup']=dict(container=dict(drainageHoles=False,drainageQuality='poor'))
    if c['state'] in ['recentlyRepotted','stressed']:p['history']=[dict(id='state',kind='Rinvasa' if c['state']=='recentlyRepotted' else 'Controlla salute',status='completed',health='Malata' if c['state']=='stressed' else None,date='2026-11-15T12:00:00Z')]
    elif c['state']=='activeGrowth':p['growthEntries']=[dict(id='state',health='Buona',date='2026-11-15T12:00:00Z')]
    bio={} if c['dry']=='nil' else dict(careProfiles=dict(water=dict(source='manualOverride',confidence=c['quality'],profile=dict(preferredDryDown=c['dry']))))
    if c['quality']:bio.setdefault('careProfiles',{})['nutrition']=dict(confidence=c['quality'],profile=dict(nutrientDemand='moderate',saltSensitivity='high'))
    if c.get('lightProfile'):bio.setdefault('careProfiles',{})['light']=dict(profile=dict(operationalProfileID=c['lightProfile']))
    from datetime import timedelta
    at=parse('2026-11-15T12:00:00Z');rows=[]
    for index,(key,unit) in enumerate([('moisture','%'),('ec','µS/cm'),('light','lux'),('temp','°C'),('humidity','%')],1):
        if c[key] is not None:rows.append(dict(id=f'00000000-0000-0000-0000-{index:012}',kind={'ec':'conductivity','light':'illuminance','temp':'temperature'}.get(key,key),value=c[key],unit=unit,date=(at-timedelta(seconds=c['age'])).isoformat(),source='sensor',reliability=c['reliability']))
    if c.get('lightCount',1)>1:
        light_row=next(r for r in rows if r['kind']=='illuminance')
        rows.extend([{**light_row,'id':f'00000000-0000-0000-0000-{i:012}'} for i in range(6,5+c['lightCount'])])
    got=evaluate(p,rows,bio,at=at)['recommendations']
    for a,b in zip(got,want):
        for key in ['domain','action','urgency','missingInputs']:
            assert a[key]==b[key],(c,key,a[key],b[key])
        assert abs(a['confidence']['value']-b['confidence']['value'])<1e-10,(c,a['domain'],a['confidence'],b['confidence'])
        assert abs(a['decisionStrength']-b['decisionStrength'])<1e-10,(c,a['domain'],'strength',a,b)
        assert (a.get('safetyGate') or {}).get('code')==(b.get('safetyGate') or {}).get('code'),(c,a,b)
print(f'Care Engine shadow: {len(cases)} contesti / {len(cases)*5} raccomandazioni equivalenti a Swift per decisioni, priorità, confidenza, dati mancanti e gate.')

from plantcare_web.backend.care_engine import dry_down,normalized_measurements
from plantcare_web.backend.domain import iso
for case in output['dryDown']:
    at=parse('2026-11-15T12:00:00Z');origin=at-timedelta(days=case['cycles']*4+1);events=[];rows=[]
    for cycle in range(case['cycles']+1):
        start=origin+timedelta(days=cycle*4)
        events.append(dict(id=str(cycle),kind='Annaffia',status='completed',date=iso(start)))
        for hour in [0,12,24]:
            rows.append(dict(id=str(cycle*3+hour),kind='moisture',value=70-hour,unit='%',date=iso(start+timedelta(hours=hour)),source='sensor',reliability=1,sourceIdentifier='replacement' if case['mixed'] and cycle==case['cycles'] and hour==24 else 'soil'))
    setup=dict(recordedAt=iso(at-timedelta(hours=1))) if case['changedSetup'] else {}
    got=dry_down(normalized_measurements(rows),events,setup,at,35)
    actual=dict(completed=got['completedCycleCount'],excluded=got['excludedCycleCount'],rate=(got['currentTrend'] or {}).get('dryingRatePercentPerHour'),baselineCount=(got['baseline'] or {}).get('comparableCycleCount'),confidence=(got['baseline'] or {}).get('confidence'),eta=got['estimatedHoursToTarget'],uncertainty=got['uncertaintyHours'])
    for k,v in actual.items():assert v==case[k] or (v is not None and case[k] is not None and abs(v-case[k])<1e-10),(case,k,v)
print(f"Asciugatura: {len(output['dryDown'])} serie equivalenti a Swift per cicli, sorgenti, cambio setup, tendenza, baseline, ETA e incertezza.")
