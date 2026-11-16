"""Execute the original Swift learner/alignment methods and compare their Python ports.

Run from repository root. Requires the sibling PlantCare2.0 sources and Swift.
No original source is modified; the harness is created in the system temp directory.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plantcare_web.backend.domain import learning, feed_days, aligned_date, parse, iso, most_recent_occurrence
from zoneinfo import ZoneInfo
root=Path(__file__).resolve().parents[1]
source=root.parent/'PlantCare2.0/VerdantMultiplatform/Sources/Verdant'
models=(source/'Models.swift').read_text()
learner=(source/'CarePlanLearner.swift').read_text()

def method(name,text=models,prefix="    static func "):
    start=text.index(prefix+name)
    opening=text.index('{',start)
    depth=1;end=opening+1
    while depth:
        if text[end]=='{': depth+=1
        elif text[end]=='}': depth-=1
        end+=1
    return text[start:end]

harness='''import Foundation
struct CareEvent { enum Kind { case water, fertilize }; enum Status { case completed, postponed }; var kind:Kind;var status:Status?;var date:Date }
struct CareLearningSummary {var completedWaterings:Int;var observedIntervalDays:Int;var baselineIntervalDays:Int;var learnedIntervalDays:Int;var confidence:Double;var explanation:String;var updatedAt:Date}
'''+learner+'\nenum CareScheduleAlignment {\n'+method('fertilizingDays(')+'\n'+method('nextWateringDate(')+'\n}\n'+'''
let formatter=ISO8601DateFormatter()
var rows:[[String:Any]]=[]
for baseline in [2,7,14,30] {
 for current in [2,7,15,30] {
  for gap in [1,5,9,20] {
   let dates=(0..<4).map { Date(timeIntervalSince1970:1735732800+Double($0*gap*86400)) }
   let events=dates.map { CareEvent(kind:.water,status:.completed,date:$0) }
   let summary=CarePlanLearner.wateringSummary(history:events,baselineDays:baseline,currentDays:current)!
   rows.append(["type":"learning","baseline":baseline,"current":current,"gap":gap,"learned":summary.learnedIntervalDays,"median":summary.observedIntervalDays])
  }
 }
}
for water in [1,7,12,30,60] {
 for desired in [7,21,28,42,84,365] {
  rows.append(["type":"feed","water":water,"desired":desired,"result":CareScheduleAlignment.fertilizingDays(desired,wateringDays:water)])
 }
}
for requested in ["2026-10-24T12:00:00Z","2026-10-25T12:00:00Z","2026-10-31T12:00:00Z","2026-11-10T12:00:00Z"] {
 let water=formatter.date(from:"2026-10-24T12:00:00Z")!
 let result=CareScheduleAlignment.nextWateringDate(onOrAfter:formatter.date(from:requested)!,nextWatering:water,wateringDays:7)
 rows.append(["type":"alignment","requested":requested,"water":"2026-10-24T12:00:00Z","result":formatter.string(from:result)])
}
let data=try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys])
print(String(decoding:data,as:UTF8.self))
'''
store_source=(source/'PlantStore.swift').read_text()
extra_types="""
struct Plant { var id=UUID(); var name="Pianta" }
struct ScheduledCareAction { enum Kind {case treatment}; var plantID:UUID; var plantName:String; var kind:Kind; var dueDate:Date;var reason:String;var treatmentPlanID:UUID?;var productID:UUID?;var applicationNumber:Int? }
"""+models[models.index('struct TreatmentPlan:'):models.index('enum CarePlanMode:')]+"\nenum ProjectionOracle {\n"+method('mostRecentOccurrence(',store_source)+"\n}\n"+"enum TreatmentOracle {\n"+method('nextTreatmentAction(',store_source,'    private func ').replace('private func','static func',1)+"\n}\n"
harness=harness.replace('let formatter=ISO8601DateFormatter()',extra_types+'\nlet formatter=ISO8601DateFormatter()')
extra_cases="""
for interval in [1,7,14,30] {
 for date in ["2026-10-24T12:00:00Z","2026-10-25T08:00:00Z","2026-11-15T12:00:00Z","2026-12-01T12:00:00Z"] {
  let first=formatter.date(from:"2026-10-24T12:00:00Z")!
  let at=formatter.date(from:date)!
  let result=ProjectionOracle.mostRecentOccurrence(startingAt:first,intervalDays:interval,now:at)
  rows.append(["type":"projection","interval":interval,"at":date,"result":formatter.string(from:result)])
 }
}
for interval in [1,7,14,30] {
 for completed in [0,1,2,3] {
  for end in ["","2026-10-25T23:59:59Z","2026-12-31T23:59:59Z"] {
   let plan=TreatmentPlan(productID:UUID(),productName:"Prodotto",startDate:formatter.date(from:"2026-10-24T12:00:00Z")!,intervalDays:interval,totalApplications:3,completedApplications:completed,endDate:end.isEmpty ? nil : formatter.date(from:end),dose:"Dose",notes:"")
   let action=TreatmentOracle.nextTreatmentAction(for:plan,plant:Plant())
   rows.append(["type":"treatment","interval":interval,"completed":completed,"end":end,"result":action.map {formatter.string(from:$0.dueDate)} ?? "none"])
  }
 }
}
"""
harness=harness.replace('let data=try JSONSerialization.data',extra_cases+'\nlet data=try JSONSerialization.data')
with tempfile.TemporaryDirectory(prefix='plantcare-swift-') as temporary:
    path=Path(temporary)/'oracle.swift';path.write_text(harness)
    result=subprocess.run(['swift','-module-cache-path',str(Path(temporary)/'cache'),str(path)],capture_output=True,text=True,env={**os.environ,'TZ':'Europe/Rome'},check=True)
rows=json.loads(result.stdout)
from datetime import datetime,timedelta,timezone
for row in rows:
    if row['type']=='learning':
        origin=datetime.fromtimestamp(1735732800,timezone.utc)
        plant={'wateringInterval':row['current'],'history':[{'kind':'Annaffia','status':'completed','date':iso(origin+timedelta(days=i*row['gap']))} for i in range(4)]}
        actual=learning(plant,row['baseline'],'Europe/Rome')
        assert actual['learnedIntervalDays']==row['learned'],row
        assert actual['observedIntervalDays']==row['median'],row
    elif row['type']=='feed': assert feed_days(row['desired'],row['water'])==row['result'],row
    elif row['type']=='projection':
        assert iso(most_recent_occurrence(parse('2026-10-24T12:00:00Z'),row['interval'],ZoneInfo('Europe/Rome'),parse(row['at'])))==row['result'],row
    elif row['type']=='treatment':
        from plantcare_web.backend.treatments import treatment_view
        plan={'id':'cycle','productID':'product','productName':'Prodotto','startDate':'2026-10-24T12:00:00Z','intervalDays':row['interval'],'totalApplications':3,'completedApplications':row['completed'],'endDate':row['end'] or None,'dose':'Dose','notes':''}
        value=treatment_view({'history':[]},plan,ZoneInfo('Europe/Rome'))
        assert (value['nextDueDate'] or 'none')==row['result'],row
    else: assert iso(aligned_date(parse(row['requested']),parse(row['water']),7,ZoneInfo('Europe/Rome')))==row['result'],row
print(f"Equivalenza verificata: {len(rows)} casi eseguiti con il codice Swift originale.")
