import { useState, useEffect } from "react";
import { Sprout, LoaderCircle } from "lucide-react";
import { api } from "./api";
import { Modal } from "./ui";
import type { Plant } from "./types";

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
const placements = ["Balcone riparato","Pieno sole","Ombra","Mezza ombra · balcone","Patio","Pianerottolo","Interno luminoso","Interno poco luminoso"];
export function AdaptiveEditor({plant,onClose,onApplied}:{plant:Plant;onClose:()=>void;onApplied:()=>Promise<void>}) {
  const old=plant.adaptivePlan;
  const [placement,setPlacement]=useState(old?.placement || "Interno luminoso");
  const [name,setName]=useState(old?.locationName || "");
  const [latitude,setLatitude]=useState(old?.latitude?.toString() || "");
  const [longitude,setLongitude]=useState(old?.longitude?.toString() || "");
  const [weather,setWeather]=useState(old?.weatherEnabled || false);
  const [temperature,setTemperature]=useState(old?.averageTemperature ?? 22);
  const [humidity,setHumidity]=useState(old?.relativeHumidity ?? 55);
  const [rain,setRain]=useState(old?.precipitationNextWeek ?? 0);
  const [preview,setPreview]=useState<{plan:AdaptivePlan;previewID:string;expectedVersion:number}>();
  const [busy,setBusy]=useState(false),[error,setError]=useState("");
  const [applied,setApplied]=useState(false);
  const [botanical,setBotanical]=useState<{previewID:string;profile:{scientificName:string;exactMatch:boolean;source:string;wateringDays:number;wateringLabel:string;fetchedAt:string}}>();
  const [useBotanical,setUseBotanical]=useState(false),[confirmMatch,setConfirmMatch]=useState(false),[botanicalBusy,setBotanicalBusy]=useState(false),[botanicalMessage,setBotanicalMessage]=useState('');
  return <Modal title="Il suo ritmo di cura" onClose={onClose}>
    <form className="editor" onChange={()=>setPreview(undefined)} onSubmit={async e=>{
      e.preventDefault();if(botanicalBusy)return;setBusy(true);setError("");
      try { setPreview(await api(`plants/${plant.id}/adaptive/preview?version=${plant._version}`,{method:"POST",body:JSON.stringify({placement,location:{name,latitude:Number(latitude),longitude:Number(longitude)},weatherEnabled:weather,...(useBotanical&&botanical?{botanicalPreviewID:botanical.previewID,confirmBotanicalMatch:confirmMatch}:{}),climate:{averageTemperature:temperature,relativeHumidity:humidity,precipitationNextWeek:rain}})})); }
      catch(e){setError((e as Error).message)} finally{setBusy(false)}
    }}>
      <fieldset disabled={busy || applied} className="adaptive-fields"><p className="muted">Specie, esposizione, stagione e cure registrate aiutano a trovare un ritmo adatto. Controlla il piano prima di applicarlo.</p>
      <div className="form-grid">
        <label>Posizione<select value={placement} onChange={e=>setPlacement(e.target.value)}>{placements.map(p=><option key={p}>{p}</option>)}</select></label>
        <label>Località<input required value={name} maxLength={200} onChange={e=>setName(e.target.value)} placeholder="La tua città"/></label>
        <label>Latitudine<input required type="number" step="any" min={-90} max={90} value={latitude} onChange={e=>setLatitude(e.target.value)}/></label>
        <label>Longitudine<input required type="number" step="any" min={-180} max={180} value={longitude} onChange={e=>setLongitude(e.target.value)}/></label>
      </div>
      <label className="check-label"><input type="checkbox" checked={weather} onChange={e=>setWeather(e.target.checked)}/> Usa il meteo e aggiorna il piano ogni giorno</label>
      <p className="muted small-text">{weather ? "Le coordinate indicate saranno inviate a Open-Meteo per le previsioni. Le piante e le foto restano in Home Assistant." : "Clima inserito manualmente: nessuna richiesta meteo. I valori iniziali sono un esempio e vanno verificati; il piano resta valido fino al prossimo ricalcolo."}</p>
      {!weather && <div className="form-grid">
        <label>Temperatura media · °C<input required type="number" step="0.1" min={-90} max={65} value={temperature} onChange={e=>setTemperature(Number(e.target.value))}/></label>
        <label>Umidità dell’aria · %<input required type="number" min={0} max={100} value={humidity} onChange={e=>setHumidity(Number(e.target.value))}/></label>
        <label>Pioggia in 7 giorni · mm<input required type="number" step="0.1" min={0} max={5000} value={rain} onChange={e=>setRain(Number(e.target.value))}/></label>
      </div>}
      <section className="botanical-plan-choice"><h3>Profilo botanico della specie</h3><p className="muted small-text">Consulta Open Plantbook o Perenual per usare il riferimento della specie nel pianificatore stagionale. Il collegamento viene applicato soltanto con il piano confermato; i dati dei sensori restano invariati.</p><button type="button" className="button secondary" disabled={botanicalBusy||!plant.species} onClick={async()=>{setBotanicalBusy(true);setBotanicalMessage('');setBotanical(undefined);setUseBotanical(false);setConfirmMatch(false);setPreview(undefined);try{const data=await api<{previewID:string;profile:NonNullable<typeof botanical>['profile']|null}>(`plants/${plant.id}/botanical/preview?version=${plant._version}`,{method:'POST'});if(data.profile)setBotanical({previewID:data.previewID,profile:data.profile});else setBotanicalMessage('Nessun profilo trovato per questa specie.')}catch(e){setBotanicalMessage((e as Error).message)}finally{setBotanicalBusy(false)}}}>{botanicalBusy?'Consulto la specie…':'Consulta riferimento botanico'}</button>{botanicalMessage&&<p role="status">{botanicalMessage}</p>}{botanical&&<div className="guide-tip"><strong>{botanical.profile.scientificName}</strong><p className="small-text">{botanical.profile.source} · {new Date(botanical.profile.fetchedAt).toLocaleDateString('it-IT')} · base acqua {botanical.profile.wateringDays} giorni</p><p className="small-text">{botanical.profile.wateringLabel}</p>{!botanical.profile.exactMatch&&<label className="check-label"><input type="checkbox" checked={confirmMatch} onChange={e=>{setConfirmMatch(e.target.checked);if(!e.target.checked)setUseBotanical(false);setPreview(undefined)}}/>Corrispondenza approssimativa: confermo che questa specie è quella della mia pianta.</label>}<label className="check-label"><input type="checkbox" checked={useBotanical} disabled={!botanical.profile.exactMatch&&!confirmMatch} onChange={e=>{setUseBotanical(e.target.checked);setPreview(undefined)}}/>Usa questo profilo nell’anteprima del piano</label></div>}</section>
      {error && <p className="error" role="alert">{error}</p>}
      {preview && <div className="plan-preview" aria-live="polite">
        <h3>{preview.plan.seasonName}</h3>
        <div className="plan-intervals"><span>Acqua<strong>{plant.wateringInterval} → {preview.plan.wateringDays} giorni</strong></span><span>Concime<strong>{plant.fertilizingInterval ?? "—"} → {preview.plan.fertilizingDays} giorni</strong></span></div>
        {preview.plan.botanicalScientificName && <p className="small-text">Profilo collegato: {preview.plan.botanicalScientificName} · {preview.plan.botanicalSource}</p>}
        {preview.plan.rationale.map((r,i)=><p className="small-text" key={i}>{r}</p>)}
        <p className="muted small-text">Il calendario verrà ricalcolato. Le cure registrate e i rinvii restano conservati.</p>
      </div>}
      <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Annulla</button><button className="button secondary" disabled={busy || botanicalBusy || applied}>{busy && <LoaderCircle size={16} className="spin"/>}Calcola anteprima</button>
      {preview && <button type="button" className="button primary" disabled={busy || botanicalBusy || applied} onClick={async()=>{
        setBusy(true);setError("");try{await api(`plants/${plant.id}/adaptive/apply?version=${preview.expectedVersion}&previewID=${encodeURIComponent(preview.previewID)}`,{method:"POST"});setApplied(true);await onApplied();onClose()}catch(e){setError((e as Error).message)}finally{setBusy(false)}
      }}><Sprout size={16}/>Applica piano</button>}</div>
    </fieldset></form>
  </Modal>
}

type Recommendation={domain:string;action:string;confidence:{value:number};safetyGate?:{code:string};missingInputs:string[];factors:{id:string;parameters:Record<string,string>}[]};
const domains:Record<string,string>={water:"Acqua",nutrition:"Nutrizione",light:"Luce",temperature:"Temperatura",humidity:"Umidità"};
const actions:Record<string,string>={waterNow:"Le misure indicano substrato asciutto",checkSubstrate:"Controlla il substrato",waitToWater:"Attendi prima di annaffiare",improveLight:"Migliora la luce",maintainLight:"Mantieni questa luce",monitorDirectSun:"Controlla il sole diretto",observe:"Continua a osservare",insufficientData:"Servono altri dati",fertilize:"Condizioni favorevoli alla concimazione",waitToFertilize:"Attendi prima di concimare",warmEnvironment:"Valuta un ambiente più caldo",coolEnvironment:"Valuta un ambiente più fresco",increaseHumidity:"Aumenta l’umidità",reduceHumidity:"Riduci l’umidità",maintainClimate:"Clima nella fascia consigliata"};
const reasons:Record<string,string>={"water.moisture_high":"Umidità del substrato elevata.","water.measurement_unreliable":"La misura richiede una verifica manuale.","water.profile_insufficient":"Manca un profilo idrico botanico sufficientemente affidabile.","water.drainage_risk":"Il drenaggio del vaso richiede attenzione.","water.measured_dry":"La misura ha raggiunto la soglia del profilo botanico.","water.approaching_dry_down":"Il substrato si avvicina alla soglia di asciugatura.","water.above_dry_down":"Il substrato è ancora sopra la soglia di asciugatura.","water.no_reliable_moisture":"Indicazione basata sul calendario: verifica il terriccio.","nutrition.recently_repotted":"Rinvaso negli ultimi 30 giorni.","nutrition.plant_stressed":"La pianta è in difficoltà o in recupero.","nutrition.high_ec":"Conducibilità del substrato elevata.","nutrition.profile_insufficient":"Manca un profilo nutrizionale affidabile.","nutrition.active_growth_unconfirmed":"Crescita attiva non documentata.","nutrition.recent_application":"Concimazione registrata da meno di 21 giorni.","nutrition.conditions_support_feeding":"Il profilo e lo stato di crescita sostengono la concimazione.","climate.measurement_missing":"Manca una lettura climatica.","climate.measurement_stale":"La lettura climatica ha più di 6 ore o una data futura.","climate.profile_insufficient":"Manca una fascia climatica botanica affidabile.","climate.fresh_profiled_observation":"Confronto con la fascia del profilo botanico.","light.insufficient_daytime_readings":"Servono letture di luce nelle ore diurne.","light.direct_sun_not_repeated":"Una lettura elevata isolata non dimostra stress da sole diretto."};
const missingLabels:Record<string,string>={substrateMoisture:"umidità del substrato",containerSetup:"dati del vaso",substrateProperties:"substrato",reliableSpeciesProfile:"profilo botanico affidabile",currentTemperature:"temperatura recente",currentHumidity:"umidità recente",sufficientLightCoverage:"letture diurne di luce",historicalWateringCycles:"cicli di annaffiatura"};
export function CareInsights({plant,revision}:{plant:Plant;revision?:number}){
  const [data,setData]=useState<{recommendations:Recommendation[];dryDown:{estimatedHoursToTarget?:number;uncertaintyHours?:number}}>();
  const [error,setError]=useState("");
  useEffect(()=>{let active=true;setData(undefined);setError("");api<typeof data>(`plants/${plant.id}/care-engine`).then(v=>{if(active)setData(v)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[plant.id,plant._version,revision]);
  return <section className="detail-section care-insights"><h3>Osservazioni per la sua cura</h3><p className="muted small-text">Queste indicazioni non modificano il calendario. Confidenza e dati disponibili aiutano a interpretarle.</p>{error && <p role="alert">{error}</p>}{!data && !error && <p className="muted">Valutazione in corso…</p>}{data?.recommendations.map(r=><article key={r.domain}><div className="fact"><span>{domains[r.domain]}</span><strong>{Math.round(r.confidence.value*100)}% confidenza</strong></div><p>{actions[r.action]}</p>{r.safetyGate && <p className="muted small-text">{reasons[r.safetyGate.code] || "Confronto con il profilo botanico e le letture disponibili."}</p>}{r.missingInputs.length>0 && <p className="muted small-text">Dati da aggiungere: {r.missingInputs.map(m=>missingLabels[m] || m).join(", ")}.</p>}</article>)}{data?.dryDown.estimatedHoursToTarget != null && <p className="muted small-text">Stima di asciugatura: {Math.round(data.dryDown.estimatedHoursToTarget)} ore ± {Math.round(data.dryDown.uncertaintyHours || 0)}. Verifica sempre il terriccio.</p>}</section>
}
