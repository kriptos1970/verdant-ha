"""Read-only Care Engine shadow-v1. Ports native decision gates, never writes schedules."""
import hashlib
import json
import math
from statistics import median
from datetime import timedelta
from zoneinfo import ZoneInfo
from .domain import now, parse, iso, active_history, schedule, care_state

THRESHOLDS = {'slight':45.,'moderate':35.,'deep':25.,'complete':15.}
WEIGHTS = dict(profileQuality=.25,measurementCoverage=.30,freshnessReliability=.20,setupCompleteness=.10,historyMaturity=.15)

def clamp(value): return min(1,max(0,value))

def confidence(components, penalties=(), ceiling=None):
    applicable = [(clamp(v),WEIGHTS[k]) for k,v in components.items() if v is not None]
    weight = sum(w for _,w in applicable)
    value = clamp((sum(v*w for v,w in applicable)/weight if weight else 0)-sum(max(0,p['value']) for p in penalties))
    if ceiling is not None: value = min(value,clamp(ceiling))
    return dict(value=value,band='veryLow' if value<.40 else 'moderate' if value<.70 else 'good' if value<.85 else 'high',components=components,penalties=list(penalties))


def dry_down(measurements, events, setup, at, target=None):
    water = sorted(parse(e['date']) for e in events if e['kind']=='Annaffia' and e.get('status')=='completed' and parse(e['date'])<=at)
    empty = dict(currentTrend=None,baseline=None,estimatedHoursToTarget=None,uncertaintyHours=None,completedCycleCount=0,excludedCycleCount=0)
    if not water: return empty
    recorded = parse(setup['recordedAt']) if setup.get('recordedAt') else None
    invalidations = [parse(e['date']) for e in events if e['kind'] in ['Rinvasa','Spostamento'] and e.get('status')=='completed']+([recorded] if recorded else [])
    points = sorted([m for m in measurements if m['kind']=='moisture' and m['unit']=='%' and 0<=m['value']<=100 and parse(m['date'])<=at],key=lambda m:(parse(m['date']),str(m['id'])))
    def trend(points,start):
        if len(points)<3 or (parse(points[-1]['date'])-parse(points[0]['date'])).total_seconds()<43200: return None
        slopes = [(b['value']-a['value'])/((parse(b['date'])-parse(a['date'])).total_seconds()/3600) for i,a in enumerate(points) for b in points[i+1:] if parse(b['date'])>parse(a['date'])]
        if not slopes or median(slopes)>=0 or sum(b['value']<=a['value'] for a,b in zip(points,points[1:]))/(len(points)-1)<.6: return None
        signatures = {m['sourceIdentifier'] for m in points}
        if len(signatures)!=1: return None
        return dict(startedAt=iso(start),lastMeasuredAt=points[-1]['date'],pointCount=len(points),dryingRatePercentPerHour=-median(slopes),latestMoisturePercent=points[-1]['value'],reliability=clamp(sum(m['reliability'] for m in points)/len(points)),sourceSignature=next(iter(signatures)))
    completed,excluded = [],0
    for start,end in zip(water,water[1:]):
        current = None if any(start<d<end for d in invalidations) or (recorded and start<recorded) else trend([m for m in points if start<=parse(m['date'])<end],start)
        if current: completed.append(current)
        else: excluded+=1
    current = None if recorded and recorded>water[-1] else trend([m for m in points if parse(m['date'])>=water[-1]],water[-1])
    signature = current['sourceSignature'] if current else completed[-1]['sourceSignature'] if completed else None
    comparable = [c for c in completed if c['sourceSignature']==signature]
    baseline = None
    if len(comparable)>=3:
        rate = median(c['dryingRatePercentPerHour'] for c in comparable)
        mad = median(abs(c['dryingRatePercentPerHour']-rate) for c in comparable)
        reliability = sum(c['reliability'] for c in comparable)/len(comparable)
        baseline = dict(comparableCycleCount=len(comparable),medianDryingRatePercentPerHour=rate,medianAbsoluteDeviation=mad,confidence=clamp(reliability*(.45+.55*min(1,(len(comparable)-2)/5))))
    eta,uncertainty = None,None
    if current and target is not None and current['latestMoisturePercent']>target:
        rate = baseline['medianDryingRatePercentPerHour'] if baseline else current['dryingRatePercentPerHour']
        eta = (current['latestMoisturePercent']-target)/rate
        relative = max(.15,min(1,baseline['medianAbsoluteDeviation']/max(rate,.001))) if baseline else .75
        uncertainty = max(1,eta*relative)
    return dict(currentTrend=current,baseline=baseline,estimatedHoursToTarget=eta,uncertaintyHours=uncertainty,completedCycleCount=len(completed),excludedCycleCount=excluded+len(completed)-len(comparable))


def normalized_measurements(rows):
    result = []
    kinds = {'substrateMoisture':'moisture','substrateEC':'conductivity','illuminance':'illuminance','temperature':'temperature','humidity':'humidity'}
    units = {'percent':'%','celsius':'°C','microsiemensPerCentimeter':'µS/cm','lx':'lux','μS/cm':'µS/cm','uS/cm':'µS/cm'}
    for row in rows:
        try:
            value = float(row['value'])
            if not math.isfinite(value): continue
            kind = kinds.get(row['kind'],row['kind'])
            unit = units.get(row['unit'],row['unit'])
            # HA source_at is the observation time, NOT our polling time.
            date = row.get('source_at') or row.get('measuredAt') or row.get('measured_at') or row.get('date')
            parse(date)
            source = row.get('source') or ('manual' if row.get('entity_id')=='manual' else 'homeAssistant')
            if source=='homeAssistant' and not row.get('source_at'): continue
            result.append(dict(id=str(row['id']),kind=kind,value=value,unit=unit,date=date,reliability=clamp(float(row.get('reliability',.55 if source=='smartphoneEstimated' else 1))),sourceIdentifier=row.get('sourceIdentifier') or row.get('entity_id') or source))
        except (ValueError,TypeError,KeyError): continue
    return result


def profiles(biology):
    result = dict(biology.get('careProfiles') or {})
    classification=biology.get('lightClassification') or {}
    if classification.get('profileID') and (result.get('light') or {}).get('source')!='manualOverride':
        result['light']=dict(profile=dict(operationalProfileID=classification['profileID']),confidence=classification.get('confidence',0))
    water = result.get('water') or {}
    if water.get('source')!='manualOverride':
        adaptation = (biology.get('ecology') or {}).get('droughtAdaptation')
        dry = {'none':'slight','moderate':'moderate','xerophytic':'deep','succulent':'complete'}.get(adaptation,'unknown')
        result['water'] = dict(profile=dict(preferredDryDown=dry),confidence=(.72 if (biology.get('ecology') or {}).get('evidence') else .55) if dry!='unknown' else .25)
    return result


def plant_state(plant,at):
    events = [e for e in active_history(plant) if parse(e['date'])<=at]
    repots = [e for e in events if e['kind']=='Rinvasa' and e.get('status')=='completed']
    if repots:
        last=max(repots,key=lambda e:parse(e['date']))
        if (at-parse(last['date'])).total_seconds()<=30*86400: return 'recentlyRepotted',1,[last['id']]
    health=sorted([e for e in events if e.get('health')],key=lambda e:parse(e['date']),reverse=True)
    if health and health[0]['health'] in ['Malata','In difficoltà']: return 'stressed',.9,[health[0]['id']]
    if len(health)>1 and health[1]['health'] in ['Malata','In difficoltà'] and health[0]['health'] in ['Buona','Eccellente']: return 'recovering',.75,[e['id'] for e in health[:2]]
    growth=sorted([e for e in plant.get('growthEntries') or [] if parse(e['date'])<=at],key=lambda e:parse(e['date']),reverse=True)
    if growth and (at-parse(growth[0]['date'])).total_seconds()<=60*86400: return ('activeGrowth' if growth[0]['health'] in ['Buona','Eccellente'] else 'slowGrowth'),.7,[growth[0]['id']]
    return 'unknown',0,[]


def evaluate(plant,rows=(),biology=None,zone='Europe/Rome',at=None):
    at=at or now(); biology=biology or {}; setup=plant.get('setup') or {}; resolved=profiles(biology) if biology else {}
    measures=normalized_measurements(rows)
    if not measures:
        measures=normalized_measurements([dict(id=m['id'],kind='illuminance',value=m['estimatedLux'],unit='lux',date=m['date'],source='smartphoneEstimated') for m in plant.get('lightMeasurements') or []])
    fingerprint=hashlib.sha256(json.dumps(dict(plant=plant,measurements=measures,biology=biology,at=iso(at)),sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    recommendations=[]
    def add(domain,action,urgency,components,gate=None,missing=(),factors=(),signals=(),ceiling=None,penalties=(),validity=43200):
        denominator=sum(w*clamp(c) for _,w,c in signals)
        support=sum(max(-1,min(1,s))*clamp(w)*clamp(c) for s,w,c in signals)/denominator if denominator else 0
        seed='|'.join([plant['id'],domain,'care-engine-v1','care-policy-shadow-v1',fingerprint])
        recommendations.append(dict(id=hashlib.sha256(seed.encode()).hexdigest(),plantID=plant['id'],domain=domain,action=action,urgency=urgency,decisionStrength=clamp(abs(support)),confidence=confidence(components,penalties,ceiling),factors=sorted(factors,key=lambda f:(not f['id'].startswith('gate.'),-f['impact'],f['id'])),missingInputs=sorted(missing),validFrom=iso(at),validUntil=iso(at+timedelta(seconds=validity)),engineVersion='care-engine-v1',policyVersion='care-policy-shadow-v1',inputFingerprint=fingerprint,safetyGate=gate))
    def gate(code,outcome='restricted',ids=()): return dict(code=code,outcome=outcome,evidenceIDs=list(ids))
    def factor(id,direction='neutral',impact=2,reliability=1,ids=(),**params): return dict(id=id,direction=direction,impact=impact,confidence=clamp(reliability),evidenceIDs=sorted(ids),parameters={k:f'{v:.3f}' if isinstance(v,float) else str(v) for k,v in params.items()})
    def fresh(kind,unit,seconds): return sorted([m for m in measures if m['kind']==kind and m['unit']==unit and 0<=(at-parse(m['date'])).total_seconds()<=seconds and (kind not in ['moisture','humidity'] or 0<=m['value']<=100)],key=lambda m:(parse(m['date']),m['id']),reverse=True)
    water=resolved.get('water') or {}; water_profile=water.get('profile') or {}; water_quality=water.get('confidence',0)
    threshold=THRESHOLDS.get(water_profile.get('preferredDryDown'))
    drying=dry_down(measures,active_history(plant),setup,at,threshold)
    cycles=drying['completedCycleCount']; maturity=0 if cycles==0 else .35 if cycles<=2 else .60 if cycles<=4 else .80 if cycles<=7 else 1
    setup_score=sum(bool(setup.get(k)) for k in ['container','substrate'])/2
    missing=[name for key,name in [('container','containerSetup'),('substrate','substrateProperties')] if not setup.get(key)]
    due=next(a for a in schedule(plant,zone,at) if a['kind']=='Annaffia')
    days=due['daysUntil']; schedule_id='legacy-schedule-'+plant['id']
    moisture=fresh('moisture','%',43200)
    if moisture:
        m=moisture[0]; reliable=m['reliability']>=.65; v=m['value']; container=setup.get('container') or {}
        drainage=container.get('drainageHoles') is False or container.get('drainageQuality')=='poor'
        if v>=70: action,urgency,code,outcome='waitToWater',0,'water.moisture_high','blocked'
        elif not reliable: action,urgency,code,outcome='checkSubstrate',1,'water.measurement_unreliable','restricted'
        elif threshold is None or water_quality<.55: action,urgency,code,outcome='checkSubstrate',1,'water.profile_insufficient','restricted'
        elif drainage: action,urgency,code,outcome='checkSubstrate',2,'water.drainage_risk','restricted'
        elif v<=threshold: action,urgency,code,outcome='waterNow',3 if v<=max(5,threshold-8) else 2,'water.measured_dry','passed'
        elif v<=threshold+10: action,urgency,code,outcome='checkSubstrate',1,'water.approaching_dry_down','passed'
        else: action,urgency,code,outcome='waitToWater',0,'water.above_dry_down','passed'
        factors=[factor('water.moisture.current','supports' if action=='waterNow' else 'opposes',3,m['reliability'],[m['id']],percent=float(v),ageSeconds=(at-parse(m['date'])).total_seconds())]
        if water_profile: factors.append(factor('water.profile.dry_down.'+water_profile.get('preferredDryDown','unknown'),reliability=water_quality,**({'thresholdPercent':float(threshold)} if threshold else {})))
        if drainage: factors.append(factor('water.setup.drainage_risk','opposes',3))
        if drying['currentTrend']:
            t=drying['currentTrend']; factors.append(factor('water.dry_down.current_rate',reliability=t['reliability'],percentPerHour=t['dryingRatePercentPerHour'],points=t['pointCount']))
        if drying['baseline']:
            b=drying['baseline']; factors.append(factor('water.dry_down.baseline',reliability=b['confidence'],percentPerHour=b['medianDryingRatePercentPerHour'],cycles=b['comparableCycleCount']))
        if drying['estimatedHoursToTarget'] is not None:
            eta=drying['estimatedHoursToTarget']; factors.append(factor('water.dry_down.eta','supports' if eta<=24 else 'neutral',reliability=(drying['baseline'] or {}).get('confidence',m['reliability']*.5),ids=[m['id']],hours=eta,uncertaintyHours=drying['uncertaintyHours']))
        factors.append(factor('water.schedule.due_secondary' if days<=0 else 'water.schedule.future_secondary','supports' if days<=0 else 'neutral',1,.35,[schedule_id]))
        if threshold is None or water_quality<.55: missing.append('reliableSpeciesProfile')
        add('water',action,urgency,dict(profileQuality=water_quality,measurementCoverage=min(1,len(moisture)/2),freshnessReliability=m['reliability'],setupCompleteness=setup_score,historyMaturity=maturity),gate(code,outcome,[m['id']]),missing,factors,[(1 if action=='waterNow' else -1,.8,m['reliability']),(1 if days<=0 else 0,.15,.35)],None if reliable and threshold is not None else .39,[] if reliable else [dict(code='water.unreliable_measurement',value=.20)])
    else:
        factors=[factor('water.schedule.due' if days<=0 else 'water.schedule.future','supports' if days<=0 else 'neutral',2 if days<=0 else 1,.35,[schedule_id],**({'daysOverdue':max(0,-days)} if days<=0 else {'daysUntilDue':days}))]
        if water_profile: factors.append(factor('water.profile.dry_down.'+water_profile.get('preferredDryDown','unknown'),impact=1,reliability=water_quality,preferredDryDown=water_profile.get('preferredDryDown','unknown')))
        add('water','checkSubstrate' if days<=0 else 'observe',2 if days<=-3 else 1 if days<=0 else 0,dict(profileQuality=water_quality,measurementCoverage=0,freshnessReliability=.35,setupCompleteness=setup_score,historyMaturity=maturity),gate('water.no_reliable_moisture',ids=[schedule_id]),missing+['substrateMoisture'],factors,[(1 if days<=0 else 0,.35,.35)],.39)
    state,state_confidence,state_ids=plant_state(plant,at)
    ec=fresh('conductivity','µS/cm',43200); ec=ec[0] if ec else None
    nutrition=resolved.get('nutrition') or {}; quality=nutrition.get('confidence',0); profile=nutrition.get('profile')
    high_ec=bool(ec and ec['value']>=(1200 if (profile or {}).get('saltSensitivity') in ['high','veryHigh'] else 2000))
    anchor,_=care_state(plant,'Concima'); last_feed=(at-anchor).total_seconds()/86400 if plant.get('lastFertilized') or any(e['kind']=='Concima' for e in plant['history']) else None
    if state=='recentlyRepotted': action,code,outcome='waitToFertilize','nutrition.recently_repotted','blocked'
    elif state in ['stressed','recovering']: action,code,outcome='waitToFertilize','nutrition.plant_stressed','blocked'
    elif high_ec: action,code,outcome='waitToFertilize','nutrition.high_ec','blocked'
    elif profile is None or quality<.55: action,code,outcome='insufficientData','nutrition.profile_insufficient','restricted'
    elif state!='activeGrowth': action,code,outcome='observe','nutrition.active_growth_unconfirmed','restricted'
    elif last_feed is not None and last_feed<21: action,code,outcome='waitToFertilize','nutrition.recent_application','passed'
    else: action,code,outcome='fertilize','nutrition.conditions_support_feeding','passed'
    factors=[factor('nutrition.state.'+state,'supports' if action=='fertilize' else 'opposes',3,state_confidence,state_ids)]
    if ec: factors.append(factor('nutrition.substrate_ec','opposes' if high_ec else 'neutral',3 if high_ec else 2,ec['reliability'],[ec['id']],microsiemensPerCM=float(ec['value'])))
    if last_feed is not None: factors.append(factor('nutrition.last_application','opposes' if last_feed<21 else 'neutral',reliability=.35,ids=[schedule_id],days=last_feed))
    gate_ids=[ec['id']] if code=='nutrition.high_ec' else [schedule_id] if code=='nutrition.recent_application' else [] if code=='nutrition.profile_insufficient' else state_ids
    add('nutrition',action,1 if action=='fertilize' else 0,dict(profileQuality=quality,measurementCoverage=1 if ec else 0,freshnessReliability=ec['reliability'] if ec else None,setupCompleteness=1 if setup.get('substrate') else 0,historyMaturity=state_confidence),gate(code,outcome,gate_ids),['reliableSpeciesProfile'] if quality<.55 else [],factors,[(1 if action=='fertilize' else -1,1,max(state_confidence,ec['reliability'] if ec else 0))],.39 if action=='insufficientData' else None,validity=86400)
    provider=plant.get('openPlantbookProfile') or {}
    for domain,unit,min_key,max_key,provider_min,provider_max,climate_key,missing_name in [('temperature','°C','preferredMinimumCelsius','preferredMaximumCelsius','minimumTemperature','maximumTemperature','averageTemperature','currentTemperature'),('humidity','%','preferredMinimumPercent','preferredMaximumPercent','minimumAirHumidity','maximumAirHumidity','relativeHumidity','currentHumidity')]:
        candidates=sorted([m for m in measures if m['kind']==domain and m['unit']==unit and (domain!='humidity' or 0<=m['value']<=100)],key=lambda m:parse(m['date']),reverse=True)
        observed=candidates[0] if candidates else None
        plan=plant.get('adaptivePlan') or {}
        if observed is None and plan.get('generatedAt'): observed=dict(value=plan[climate_key],date=plan['generatedAt'],reliability=.45)
        assignment=resolved.get(domain) or {}; profile=assignment.get('profile') or {min_key:provider.get(provider_min),max_key:provider.get(provider_max)}
        quality=assignment.get('confidence',.65 if provider.get(provider_min) is not None or provider.get(provider_max) is not None else 0)
        low,high=profile.get(min_key),profile.get(max_key)
        code='climate.measurement_missing' if observed is None else 'climate.measurement_stale' if not 0<=(at-parse(observed['date'])).total_seconds()<=21600 else 'climate.profile_insufficient' if (low is None and high is None) or quality<.55 else None
        if code:
            add(domain,'insufficientData',0,dict(profileQuality=0,measurementCoverage=0,freshnessReliability=0,setupCompleteness=None,historyMaturity=None),gate(code),[missing_name],ceiling=.39,validity=21600)
        else:
            below,above=low is not None and observed['value']<low,high is not None and observed['value']>high
            action=('warmEnvironment' if below else 'coolEnvironment' if above else 'maintainClimate') if domain=='temperature' else ('increaseHumidity' if below else 'reduceHumidity' if above else 'maintainClimate')
            add(domain,action,2 if below or above else 0,dict(profileQuality=quality,measurementCoverage=1,freshnessReliability=observed['reliability'],setupCompleteness=None,historyMaturity=None),gate('climate.fresh_profiled_observation','passed'),factors=[factor(domain+'.current_value','supports' if below or above else 'neutral',3 if below or above else 2,observed['reliability'],value=float(observed['value']))],signals=[(1 if below or above else 0,1,observed['reliability'])],validity=21600)
    light_recommendation(plant,measures,biology,resolved,zone,at,add,gate,factor)
    return dict(mode='shadow',engineVersion='care-engine-v1',policyVersion='care-policy-shadow-v1',evaluatedAt=iso(at),inputFingerprint=fingerprint,recommendations=sorted(recommendations,key=lambda r:r['domain']),dryDown=drying)


def light_recommendation(plant,measures,biology,resolved,zone,at,add,gate,factor):
    from pathlib import Path
    catalog=json.loads(Path(__file__).with_name('light_profiles.json').read_text())
    classification=biology.get('lightClassification') or {}
    assignment=resolved.get('light') or {}
    profile_id=(assignment.get('profile') or {}).get('operationalProfileID') or classification.get('profileID')
    quality=min(classification.get('confidence',0),{'manualOverride':1,'curatedSpecies':1,'artificialIntelligence':.65,'ecologyRules':.70,'genusPrior':.55,'familyPrior':.40,'genericFallback':.25}.get(classification.get('source'),0))
    provider=plant.get('openPlantbookProfile') or {}
    if profile_id:
        bounds=catalog.get(profile_id,catalog['GENERIC'])
    else:
        low,high=provider.get('minimumLightLux'),provider.get('maximumLightLux')
        if low is None or high is None or low>=high: low,high={'Luce bassa':(250,1000),'Luce indiretta':(1000,5000),'Luce intensa':(5000,20000),'Sole diretto':(20000,100000)}[plant['light']]
        bounds=[max(50,low*.35),low,low,high,high*1.5,max(60000,high*2),max(100000,high*3)]
    inputs=[m for m in measures if m['kind']=='illuminance' and m['unit']=='lux']
    normalized=[]
    for m in inputs:
        local=parse(m['date']).astimezone(ZoneInfo(zone)); current=at.astimezone(ZoneInfo(zone))
        # Calendar dateComponents(.day) counts full local-day increments, including DST.
        age=(current.replace(tzinfo=None)-local.replace(tzinfo=None)).total_seconds()/86400
        if not -1<age<31: continue
        hour=local.hour
        band=.35 if 6<=hour<9 else .75 if 9<=hour<12 else 1 if 12<=hour<16 else .65 if 16<=hour<19 else .3 if 19<=hour<21 else None
        if band is not None: normalized.append((m['value']/band,m['value']>=50000))
    average=sum(v for v,_ in normalized)/len(normalized) if normalized else None
    direct=sum(d for _,d in normalized)
    if average is None: status='insufficientData'
    elif average<bounds[0]: status='veryLow'
    elif average<bounds[1]: status='belowTarget'
    elif average<bounds[2]: status='adequate'
    elif average<=bounds[3]: status='ideal'
    elif direct<3 or average<=bounds[4]: status='brightIndirect'
    elif average>=bounds[5]: status='monitorDirectSun'
    else: status='brightIndirect'
    action={'veryLow':'improveLight','belowTarget':'improveLight','adequate':'maintainLight','ideal':'maintainLight','brightIndirect':'maintainLight','monitorDirectSun':'monitorDirectSun','insufficientData':'insufficientData'}[status]
    supports=status in ['veryLow','belowTarget','monitorDirectSun']
    reliability=sum(m['reliability'] for m in inputs)/len(inputs) if inputs else 0
    fresh_inputs=[m for m in inputs if 0<=(at-parse(m['date'])).total_seconds()<=30*86400]
    freshness=sum(m['reliability'] for m in fresh_inputs)/len(fresh_inputs) if fresh_inputs else 0
    ids=[m['id'] for m in inputs]
    f=factor('light.status.'+status,'supports' if supports else 'neutral',3 if status=='veryLow' else 2,reliability,ids,consideredMeasurements=len(normalized),excludedMeasurements=len(inputs)-len(normalized),possibleDirectSunReadings=direct)
    safety=gate('light.insufficient_daytime_readings','blocked',ids) if not normalized else gate('light.direct_sun_not_repeated','restricted',ids) if status=='brightIndirect' and direct>0 else None
    missing=(['sufficientLightCoverage'] if not normalized else [])+(['reliableSpeciesProfile'] if quality<.65 else [])
    add('light',action,2 if status=='veryLow' else 1 if status in ['belowTarget','monitorDirectSun'] else 0,dict(profileQuality=quality,measurementCoverage=min(1,len(normalized)/3),freshnessReliability=freshness,setupCompleteness=None,historyMaturity=None),safety,missing,[f],[] if not normalized else [(1 if supports else .5,1,reliability)],0 if not normalized else .59 if profile_id in [None,'GENERIC'] else None,validity=86400)
