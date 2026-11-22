import { lazy, Suspense, useEffect, useState } from "react";
import { Check, LoaderCircle, Sparkles, RotateCw } from "lucide-react";
import { api } from "./api";
import { useI18n } from "./i18n";
import type { Plant, Settings } from "./types";

const Markdown = lazy(() => import("./markdown"));

type Advice = {contextVersion?:number;climateContext?:{generatedAt:string|null;currentWeather:false}|null;id:string;expectedVersion:number;provider:string;model:string;createdAt:string;summaryMarkdown:string;careNotes:string;wateringDays:number;fertilizingDays:number;inspectionDays:number;pruningDays:number;repottingDays:number;applied?:boolean;stale?:boolean};
const choices = [
  ["watering","Annaffiatura","wateringDays","wateringInterval"],
  ["fertilizing","Concimazione","fertilizingDays","fertilizingInterval"],
  ["inspection","Controllo salute","inspectionDays","inspectionInterval"],
  ["pruning","Potatura","pruningDays","pruningInterval"],
  ["repotting","Rinvaso","repottingDays","repottingInterval"],
] as const;
export function PlantAssistant({plant,settings,run}:{plant:Plant;settings?:Settings;run:(fn:()=>Promise<unknown>,message?:string)=>Promise<void>}){
  const [question,setQuestion]=useState("Come posso prendermi cura di questa pianta?"),[advice,setAdvice]=useState<Advice|null>(null);
  const [selection,setSelection]=useState<Record<string,boolean>>({watering:true,fertilizing:true,inspection:true,pruning:true,repotting:true});
  const [asking,setAsking]=useState(false),[applying,setApplying]=useState(false),[error,setError]=useState("");
  const { formatDate, formatNumber } = useI18n();
  useEffect(()=>{let active=true;setAdvice(null);setError("");api<Advice|null>(`plants/${plant.id}/advice`).then(v=>{if(active)setAdvice(v)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[plant.id]);
  const stale=advice && !advice.applied && (advice.stale || advice.expectedVersion!==plant._version);
  const [preview,setPreview]=useState<Record<string,number|null>>();
  const [previewing,setPreviewing]=useState(false);
  useEffect(()=>{let active=true;setPreview(undefined);
    if(!advice || advice.applied || stale){setPreviewing(false);return}
    setPreviewing(true);api<Record<string,number|null>>(`plants/${plant.id}/advice/preview`,{method:"POST",body:JSON.stringify({adviceID:advice.id,...selection})}).then(v=>{if(active)setPreview(v)}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setPreviewing(false)});
    return()=>{active=false}
  },[advice?.id,advice?.applied,selection,plant._version,stale]);
  return <><div className="ai-detail-intro"><Sparkles size={26}/><h3>Conosciamola meglio.</h3><p>Consigli basati sui dati della pianta. Le fotografie non vengono analizzate dall’assistente testuale.</p></div>
    <form onSubmit={async e=>{e.preventDefault();setAsking(true);setError("");try{setAdvice(await api(`plants/${plant.id}/advice`,{method:"POST",body:JSON.stringify({question})}));setSelection({watering:true,fertilizing:true,inspection:true,pruning:true,repotting:true})}catch(e){setError((e as Error).message)}finally{setAsking(false)}}}>
      <label>Chiedi all’assistente<textarea rows={4} required maxLength={4000} value={question} disabled={asking || applying} onChange={e=>setQuestion(e.target.value)}/></label>
      <p className="muted small-text">La domanda e il contesto testuale della pianta saranno inviati al provider configurato: {settings?.aiProvider === "openai" ? "OpenAI" : settings?.aiProvider === "gemini" ? "Gemini" : "non configurato"}. La richiesta può consumare credito API.</p>
      <button className="button primary" disabled={asking || applying || !settings?.aiConfigured}>{asking ? <LoaderCircle className="spin" size={17}/> : <Sparkles size={17}/>}Chiedi consiglio</button>
    </form>
    {!settings?.aiConfigured && <p className="muted small-text">Configura provider e chiave nelle opzioni dell’add-on Home Assistant.</p>}
    {error && <p role="alert" className="form-error">{error}</p>}
    {advice && <div className="advice-proposal"><p className="muted small-text">{advice.provider} · {advice.model} · {formatDate(advice.createdAt, { dateStyle: "medium", timeStyle: "short" })}</p>{advice.climateContext && <p className="muted small-text">Clima del piano salvato: {advice.climateContext.generatedAt ? formatDate(advice.climateContext.generatedAt, { dateStyle: "medium", timeStyle: "short" }) : "data sconosciuta"}. Questi dati non rappresentano il meteo attuale.</p>}<div className="ai-answer">
        <Suspense fallback={<p>{advice.summaryMarkdown}</p>}>
          <Markdown>{advice.summaryMarkdown}</Markdown>
        </Suspense>
      </div>
      <h3>Le frequenze proposte</h3><p className="muted small-text">Scegli quali attività aggiornare. Irrigazione, controlli, potatura e rinvaso seguono i riferimenti stabili del piano nativo. La concimazione resta coerente con la modalità di cura e con il ciclo dell’acqua.</p>
      <fieldset className="advice-options" disabled={!!stale || advice.applied || asking || applying}>{choices.map(([key,label,value,field])=><label key={key}><input type="checkbox" checked={selection[key] || false} onChange={e=>setSelection(s=>({...s,[key]:e.target.checked}))}/><span>{label}<small>{plant[field] ?? "—"} → {advice[value]} giorni</small></span></label>)}</fieldset>
      {!advice.applied && <div className="plan-preview" aria-live="polite"><h4>Il piano dopo l’applicazione</h4>{previewing ? <p>Calcolo delle attività selezionate…</p> : preview && choices.map(([key,label,,field])=><p className="small-text" key={key}>{label}: {plant[field] ?? "non impostata"} → {preview[field] ?? "non impostata"}{preview[field]!=null ? " giorni" : ""}</p>)}</div>}
      {advice.careNotes && <><h4>Indicazioni per la scheda</h4><p className="preserve small-text">{advice.careNotes}</p><p className="muted small-text">Applicando il consiglio, queste indicazioni saranno aggiunte alle note.</p></>}
      {stale && <p className="danger" role="alert">Piano, cronologia o contesto AI cambiati: richiedi un nuovo consiglio.</p>}
      {advice.applied ? <p className="success-message"><Check size={16}/>Consiglio applicato</p> : <button className="button primary" disabled={!!stale || asking || applying || previewing || !preview} onClick={async()=>{setApplying(true);setError("");try{await run(()=>api(`plants/${plant.id}/advice/apply`,{method:"POST",body:JSON.stringify({adviceID:advice.id,...selection})}),"Consiglio AI applicato");setAdvice(a=>a?{...a,applied:true}:a)}catch(e){setError((e as Error).message)}finally{setApplying(false)}}}><Check size={16}/>{Object.values(selection).some(Boolean)?"Applica attività selezionate":"Aggiungi solo le note"}</button>}
    </div>}
  </>
}

export function AIModelCatalog({settings,onChanged}:{settings?:Settings;onChanged:()=>Promise<void>}){
  const [models,setModels]=useState<string[]>([]),[model,setModel]=useState(settings?.aiModel || ""),[busy,setBusy]=useState(false),[error,setError]=useState("");
  useEffect(()=>{setModel(settings?.aiModel || "");setModels([])},[settings?.aiProvider,settings?.aiModel]);
  return <details className="ai-catalog"><summary>Modello dell’assistente</summary><p className="muted small-text">Provider e chiavi si configurano nelle opzioni dell’add-on. L’elenco mostra i modelli testuali disponibili al tuo account; la compatibilità con le risposte strutturate viene verificata alla richiesta.</p>
    <button className="button secondary" disabled={busy || !settings?.aiConfigured} onClick={async()=>{setBusy(true);setError("");try{const data=await api<{models:string[];selectedModel:string}>("ai/models",{method:"POST"});setModels(data.models);setModel(data.selectedModel)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}>{busy?<LoaderCircle className="spin" size={16}/>:<RotateCw size={16}/>}Carica modelli disponibili</button>
    {models.length>0 && <div className="model-choice"><label>Modello<select value={model} disabled={busy} onChange={e=>setModel(e.target.value)}>{!models.includes(model) && <option value={model}>{model} · non presente nel catalogo</option>}{models.map(m=><option key={m}>{m}</option>)}</select></label><button className="button secondary" disabled={busy || !models.includes(model)} onClick={async()=>{setBusy(true);setError("");try{await api("ai/model",{method:"PUT",body:JSON.stringify({model})});await onChanged()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}>Usa questo modello</button></div>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </details>
}
