import { useState, useEffect } from "react";
import { Sprout, LoaderCircle } from "lucide-react";
import { api } from "./api";
import { Modal } from "./ui";
import type { Plant } from "./types";
import { useI18n, type MessageKey } from "./i18n";
import { useDomainLabels } from "./domain-labels";

export type AdaptivePlan = {
  placement: string; locationName: string; latitude: number; longitude: number;
  wateringDays: number; fertilizingDays: number; inspectionDays: number;
  averageTemperature: number; relativeHumidity: number; precipitationNextWeek: number;
  seasonName: string; generatedAt: string; weatherEnabled?: boolean;
  botanicalScientificName?:string;botanicalFetchedAt?:string;botanicalSource?:string;botanicalWateringDays?:number;
  rationale: string[]; revisionReason?: string;
  adjustments?: {id:string; domain:string; factor:string; baselineDays:number; resultingDays:number; explanation:string}[];
  climateRevisionHistory?: {id:string; date:string; previousWateringDays:number; newWateringDays:number; previousFertilizingDays:number; newFertilizingDays:number}[];
};
export const placements = ["Balcone riparato","Pieno sole","Ombra","Mezza ombra · balcone","Patio","Pianerottolo","Interno luminoso","Interno poco luminoso"];
export function AdaptiveEditor({plant,onClose,onApplied,defaultLocation}:{plant:Plant;onClose:()=>void;onApplied:()=>Promise<void>;defaultLocation?:{name:string;latitude:number;longitude:number}|null}) {
  const {t,formatDate}=useI18n();
  const {placementLabel}=useDomainLabels();
  const old=plant.adaptivePlan;
  const [placement,setPlacement]=useState(old?.placement || "Interno luminoso");
  const [name,setName]=useState(old?.locationName || defaultLocation?.name || "");
  const [latitude,setLatitude]=useState(old?.latitude?.toString() ?? defaultLocation?.latitude?.toString() ?? "");
  const [longitude,setLongitude]=useState(old?.longitude?.toString() ?? defaultLocation?.longitude?.toString() ?? "");
  const [weather,setWeather]=useState(old?.weatherEnabled || false);
  const [temperature,setTemperature]=useState(old?.averageTemperature ?? 22);
  const [humidity,setHumidity]=useState(old?.relativeHumidity ?? 55);
  const [rain,setRain]=useState(old?.precipitationNextWeek ?? 0);
  const [preview,setPreview]=useState<{plan:AdaptivePlan;previewID:string;expectedVersion:number}>();
  const [busy,setBusy]=useState(false),[error,setError]=useState("");
  const [applied,setApplied]=useState(false);
  const [botanical,setBotanical]=useState<{previewID:string;profile:{scientificName:string;exactMatch:boolean;source:string;wateringDays:number;wateringLabel:string;fetchedAt:string}}>();
  const [useBotanical,setUseBotanical]=useState(false),[confirmMatch,setConfirmMatch]=useState(false),[botanicalBusy,setBotanicalBusy]=useState(false),[botanicalMessage,setBotanicalMessage]=useState('');
  return <Modal title={t("adaptive.title")} onClose={onClose}>
    <form className="editor" onChange={()=>setPreview(undefined)} onSubmit={async e=>{
      e.preventDefault();if(botanicalBusy)return;setBusy(true);setError("");
      try { setPreview(await api(`plants/${plant.id}/adaptive/preview?version=${plant._version}`,{method:"POST",body:JSON.stringify({placement,location:{name,latitude:Number(latitude),longitude:Number(longitude)},weatherEnabled:weather,...(useBotanical&&botanical?{botanicalPreviewID:botanical.previewID,confirmBotanicalMatch:confirmMatch}:{}),climate:{averageTemperature:temperature,relativeHumidity:humidity,precipitationNextWeek:rain}})})); }
      catch(e){setError((e as Error).message)} finally{setBusy(false)}
    }}>
      <fieldset disabled={busy || applied} className="adaptive-fields"><p className="muted">{t("adaptive.intro")}</p>
      <div className="form-grid">
        <label>{t("adaptive.placement")}<select value={placement} onChange={e=>setPlacement(e.target.value)}>{placements.map(p=><option key={p} value={p}>{placementLabel(p)}</option>)}</select></label>
        <label>{t("adaptive.location")}<input required value={name} maxLength={200} onChange={e=>setName(e.target.value)} placeholder={t("adaptive.locationPlaceholder")}/></label>
        <label>{t("adaptive.latitude")}<input required type="number" step="any" min={-90} max={90} value={latitude} onChange={e=>setLatitude(e.target.value)}/></label>
        <label>{t("adaptive.longitude")}<input required type="number" step="any" min={-180} max={180} value={longitude} onChange={e=>setLongitude(e.target.value)}/></label>
      </div>
      <label className="check-label"><input type="checkbox" checked={weather} onChange={e=>setWeather(e.target.checked)}/> {t("adaptive.weather")}</label>
      <p className="muted small-text">{weather ? t("adaptive.weatherHint") : t("adaptive.manualHint")}</p>
      {!weather && <div className="form-grid">
        <label>{t("adaptive.temperature")}<input required type="number" step="0.1" min={-90} max={65} value={temperature} onChange={e=>setTemperature(Number(e.target.value))}/></label>
        <label>{t("adaptive.humidity")}<input required type="number" min={0} max={100} value={humidity} onChange={e=>setHumidity(Number(e.target.value))}/></label>
        <label>{t("adaptive.rain")}<input required type="number" step="0.1" min={0} max={5000} value={rain} onChange={e=>setRain(Number(e.target.value))}/></label>
      </div>}
      <section className="botanical-plan-choice"><h3>{t("adaptive.botanicalTitle")}</h3><p className="muted small-text">{t("adaptive.botanicalText")}</p><button type="button" className="button secondary" disabled={botanicalBusy||!plant.species} onClick={async()=>{setBotanicalBusy(true);setBotanicalMessage('');setBotanical(undefined);setUseBotanical(false);setConfirmMatch(false);setPreview(undefined);try{const data=await api<{previewID:string;profile:NonNullable<typeof botanical>['profile']|null}>(`plants/${plant.id}/botanical/preview?version=${plant._version}`,{method:'POST'});if(data.profile)setBotanical({previewID:data.previewID,profile:data.profile});else setBotanicalMessage(t('adaptive.noProfile'))}catch(e){setBotanicalMessage((e as Error).message)}finally{setBotanicalBusy(false)}}}>{botanicalBusy?t('adaptive.consulting'):t('adaptive.consult')}</button>{botanicalMessage&&<p role="status">{botanicalMessage}</p>}{botanical&&<div className="guide-tip"><strong>{botanical.profile.scientificName}</strong><p className="small-text">{botanical.profile.source} · {formatDate(botanical.profile.fetchedAt)} · {t('adaptive.baseWater',{days:botanical.profile.wateringDays})}</p><p className="small-text">{botanical.profile.wateringLabel}</p>{!botanical.profile.exactMatch&&<label className="check-label"><input type="checkbox" checked={confirmMatch} onChange={e=>{setConfirmMatch(e.target.checked);if(!e.target.checked)setUseBotanical(false);setPreview(undefined)}}/>{t("adaptive.approximate")}</label>}<label className="check-label"><input type="checkbox" checked={useBotanical} disabled={!botanical.profile.exactMatch&&!confirmMatch} onChange={e=>{setUseBotanical(e.target.checked);setPreview(undefined)}}/>{t('adaptive.useProfile')}</label></div>}</section>
      {error && <p className="error" role="alert">{error}</p>}
      {preview && <div className="plan-preview" aria-live="polite">
        <h3>{preview.plan.seasonName}</h3>
        <div className="plan-intervals"><span>{t("adaptive.previewWater")}<strong>{t("adaptive.previewIntervals",{from:plant.wateringInterval,to:preview.plan.wateringDays})}</strong></span><span>{t("adaptive.previewFeed")}<strong>{t("adaptive.previewIntervals",{from:plant.fertilizingInterval ?? "—",to:preview.plan.fertilizingDays})}</strong></span></div>
        {preview.plan.botanicalScientificName && <p className="small-text">{t("adaptive.linkedProfile",{name:preview.plan.botanicalScientificName,source:preview.plan.botanicalSource ?? ""})}</p>}
        {preview.plan.rationale.map((r,i)=><p className="small-text" key={i}>{r}</p>)}
        <p className="muted small-text">{t("adaptive.recalcNote")}</p>
      </div>}
      <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>{t("adaptive.cancel")}</button><button className="button secondary" disabled={busy || botanicalBusy || applied}>{busy && <LoaderCircle size={16} className="spin"/>}{t("adaptive.calculate")}</button>
      {preview && <button type="button" className="button primary" disabled={busy || botanicalBusy || applied} onClick={async()=>{
        setBusy(true);setError("");try{await api(`plants/${plant.id}/adaptive/apply?version=${preview.expectedVersion}&previewID=${encodeURIComponent(preview.previewID)}`,{method:"POST"});setApplied(true);await onApplied();onClose()}catch(e){setError((e as Error).message)}finally{setBusy(false)}
      }}><Sprout size={16}/>{t("adaptive.apply")}</button>}</div>
    </fieldset></form>
  </Modal>
}

type Recommendation={domain:string;action:string;confidence:{value:number};components?:Record<string,number|null>;safetyGate?:{code:string};missingInputs:string[];factors:{id:string;parameters:Record<string,string>}[]};
const domainKeys:Record<string,MessageKey>={water:'insights.domain.water',nutrition:'insights.domain.nutrition',light:'insights.domain.light',temperature:'insights.domain.temperature',humidity:'insights.domain.humidity'};
const actionKeys:Record<string,MessageKey>={waterNow:'insights.action.waterNow',checkSubstrate:'insights.action.checkSubstrate',waitToWater:'insights.action.waitToWater',improveLight:'insights.action.improveLight',maintainLight:'insights.action.maintainLight',monitorDirectSun:'insights.action.monitorDirectSun',observe:'insights.action.observe',insufficientData:'insights.action.insufficientData',fertilize:'insights.action.fertilize',waitToFertilize:'insights.action.waitToFertilize',warmEnvironment:'insights.action.warmEnvironment',coolEnvironment:'insights.action.coolEnvironment',increaseHumidity:'insights.action.increaseHumidity',reduceHumidity:'insights.action.reduceHumidity',maintainClimate:'insights.action.maintainClimate'};
const reasonKeys:Record<string,MessageKey>={'water.moisture_high':'insights.reason.water_high','water.measurement_unreliable':'insights.reason.water_unreliable','water.profile_insufficient':'insights.reason.water_profile','water.drainage_risk':'insights.reason.water_drainage','water.measured_dry':'insights.reason.water_dry','water.approaching_dry_down':'insights.reason.water_approaching','water.above_dry_down':'insights.reason.water_above','water.no_reliable_moisture':'insights.reason.water_no_moisture','nutrition.recently_repotted':'insights.reason.nutrition_repotted','nutrition.plant_stressed':'insights.reason.nutrition_stressed','nutrition.high_ec':'insights.reason.nutrition_high_ec','nutrition.profile_insufficient':'insights.reason.nutrition_profile','nutrition.active_growth_unconfirmed':'insights.reason.nutrition_growth','nutrition.recent_application':'insights.reason.nutrition_recent','nutrition.conditions_support_feeding':'insights.reason.nutrition_conditions','climate.measurement_missing':'insights.reason.climate_missing','climate.measurement_stale':'insights.reason.climate_stale','climate.profile_insufficient':'insights.reason.climate_profile','climate.fresh_profiled_observation':'insights.reason.climate_fresh','light.insufficient_daytime_readings':'insights.reason.light_readings','light.direct_sun_not_repeated':'insights.reason.light_direct'};
const missingKeys:Record<string,MessageKey>={substrateMoisture:'insights.missing.substrateMoisture',containerSetup:'insights.missing.containerSetup',substrateProperties:'insights.missing.substrateProperties',reliableSpeciesProfile:'insights.missing.reliableSpeciesProfile',currentTemperature:'insights.missing.currentTemperature',currentHumidity:'insights.missing.currentHumidity',sufficientLightCoverage:'insights.missing.sufficientLightCoverage',historicalWateringCycles:'insights.missing.historicalWateringCycles'};
export function CareInsights({plant,revision,active}:{plant:Plant;revision?:number;active?:boolean}){
  const {t}=useI18n();
  const [data,setData]=useState<{recommendations:Recommendation[];dryDown:{estimatedHoursToTarget?:number;uncertaintyHours?:number}}>();
  const [error,setError]=useState("");
  useEffect(()=>{let active=true;setData(undefined);setError("");api<typeof data>(`plants/${plant.id}/care-engine`).then(v=>{if(active)setData(v)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[plant.id,plant._version,revision]);
  return <section className="detail-section care-insights"><h3>{t("insights.title")}</h3><p className="muted small-text">{t(active?"insights.textActive":"insights.text")}</p>{error && <p role="alert">{error}</p>}{!data && !error && <p className="muted">{t("insights.evaluating")}</p>}{data?.recommendations.map(r=><article key={r.domain}><div className="fact"><span>{t(domainKeys[r.domain] ?? "insights.title")}</span><strong>{t("insights.confidence",{percent:Math.round(r.confidence.value*100)})}</strong></div><p>{t(actionKeys[r.action] ?? "insights.action.observe")}</p>{r.domain==='light'&&r.components?.profileQuality!=null&&<p className="muted small-text">{t("insights.lightProfile",{percent:Math.round((r.components.profileQuality||0)*100)})}</p>}{r.safetyGate && <p className="muted small-text">{t(reasonKeys[r.safetyGate.code] ?? "insights.reason.generic")}</p>}{r.missingInputs.length>0 && <p className="muted small-text">{t("insights.addData",{items:r.missingInputs.map(m=>t(missingKeys[m] ?? "insights.reason.generic")).join(", ")})}</p>}</article>)}{data?.dryDown.estimatedHoursToTarget != null && <p className="muted small-text">{t("insights.dryEstimate",{hours:Math.round(data.dryDown.estimatedHoursToTarget),uncertainty:Math.round(data.dryDown.uncertaintyHours || 0)})}</p>}</section>
}
