import { lazy, Suspense, useEffect, useState } from "react";
import { Check, LoaderCircle, Sparkles, RotateCw } from "lucide-react";
import { api } from "./api";
import { useI18n, type MessageKey } from "./i18n";
import type { Plant, Settings } from "./types";

const Markdown = lazy(() => import("./markdown"));

type Advice = {contextVersion?:number;climateContext?:{generatedAt:string|null;currentWeather:false}|null;id:string;expectedVersion:number;provider:string;model:string;createdAt:string;summaryMarkdown:string;careNotes:string;wateringDays:number;fertilizingDays:number;inspectionDays:number;pruningDays:number;repottingDays:number;applied?:boolean;stale?:boolean};
type AdviceField = "wateringDays"|"fertilizingDays"|"inspectionDays"|"pruningDays"|"repottingDays";
type PlantField = "wateringInterval"|"fertilizingInterval"|"inspectionInterval"|"pruningInterval"|"repottingInterval";
const choices = [
  ["watering","assistant.choice.watering","wateringDays","wateringInterval"],
  ["fertilizing","assistant.choice.fertilizing","fertilizingDays","fertilizingInterval"],
  ["inspection","assistant.choice.inspection","inspectionDays","inspectionInterval"],
  ["pruning","assistant.choice.pruning","pruningDays","pruningInterval"],
  ["repotting","assistant.choice.repotting","repottingDays","repottingInterval"],
] as const satisfies ReadonlyArray<readonly [string, MessageKey, AdviceField, PlantField]>;
export function PlantAssistant({plant,settings,run}:{plant:Plant;settings?:Settings;run:(fn:()=>Promise<unknown>,message?:string)=>Promise<void>}){
  const { t, formatDate } = useI18n();
  const [question,setQuestion]=useState(()=>t("assistant.defaultQuestion")),[advice,setAdvice]=useState<Advice|null>(null);
  const [selection,setSelection]=useState<Record<string,boolean>>({watering:true,fertilizing:true,inspection:true,pruning:true,repotting:true});
  const [asking,setAsking]=useState(false),[applying,setApplying]=useState(false),[error,setError]=useState("");
  useEffect(()=>{let active=true;setAdvice(null);setError("");api<Advice|null>(`plants/${plant.id}/advice`).then(v=>{if(active)setAdvice(v)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[plant.id]);
  const stale=advice && !advice.applied && (advice.stale || advice.expectedVersion!==plant._version);
  const [preview,setPreview]=useState<Record<string,number|null>>();
  const [previewing,setPreviewing]=useState(false);
  useEffect(()=>{let active=true;setPreview(undefined);
    if(!advice || advice.applied || stale){setPreviewing(false);return}
    setPreviewing(true);api<Record<string,number|null>>(`plants/${plant.id}/advice/preview`,{method:"POST",body:JSON.stringify({adviceID:advice.id,...selection})}).then(v=>{if(active)setPreview(v)}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setPreviewing(false)});
    return()=>{active=false}
  },[advice?.id,advice?.applied,selection,plant._version,stale]);
  return <><div className="ai-detail-intro"><Sparkles size={26}/><h3>{t("assistant.title")}</h3><p>{t("assistant.intro")}</p></div>
    <form onSubmit={async e=>{e.preventDefault();setAsking(true);setError("");try{setAdvice(await api(`plants/${plant.id}/advice`,{method:"POST",body:JSON.stringify({question})}));setSelection({watering:true,fertilizing:true,inspection:true,pruning:true,repotting:true})}catch(e){setError((e as Error).message)}finally{setAsking(false)}}}>
      <label>{t("assistant.askLabel")}<textarea rows={4} required maxLength={4000} value={question} disabled={asking || applying} onChange={e=>setQuestion(e.target.value)}/></label>
      <p className="muted small-text">{t("assistant.privacy",{provider:settings?.aiProvider === "openai" ? "OpenAI" : settings?.aiProvider === "gemini" ? "Gemini" : t("assistant.providerNone")})}</p>
      <button className="button primary" disabled={asking || applying || !settings?.aiConfigured}>{asking ? <LoaderCircle className="spin" size={17} /> : <Sparkles size={17} />}{t("assistant.ask")}</button>
    </form>
    {!settings?.aiConfigured && <p className="muted small-text">{t("assistant.config")}</p>}
    {error && <p role="alert" className="form-error">{error}</p>}
    {advice && <div className="advice-proposal"><p className="muted small-text">{advice.provider} · {advice.model} · {formatDate(advice.createdAt, { dateStyle: "medium", timeStyle: "short" })}</p>{advice.climateContext && <p className="muted small-text">{t("assistant.climate",{date:advice.climateContext.generatedAt ? formatDate(advice.climateContext.generatedAt, { dateStyle: "medium", timeStyle: "short" }) : t("assistant.unknownDate")})}</p>}<div className="ai-answer">
        <Suspense fallback={<p>{advice.summaryMarkdown}</p>}>
          <Markdown>{advice.summaryMarkdown}</Markdown>
        </Suspense>
      </div>
      <h3>{t("assistant.frequenciesTitle")}</h3><p className="muted small-text">{t("assistant.frequenciesText")}</p>
      <fieldset className="advice-options" disabled={!!stale || advice.applied || asking || applying}>{choices.map(([key,labelKey,value,field])=><label key={key}><input type="checkbox" checked={selection[key] || false} onChange={e=>setSelection(s=>({...s,[key]:e.target.checked}))}/><span>{t(labelKey)}<small>{plant[field] ?? "—"} → {t("assistant.days",{days:advice[value]})}</small></span></label>)}</fieldset>
      {!advice.applied && <div className="plan-preview" aria-live="polite"><h4>{t("assistant.previewTitle")}</h4>{previewing ? <p>{t("assistant.previewBusy")}</p> : preview && choices.map(([key,labelKey,,field])=><p className="small-text" key={key}>{t(labelKey)}: {plant[field] ?? t("assistant.notSet")} → {preview[field]!=null ? t("assistant.days",{days:preview[field]}) : t("assistant.notSet")}</p>)}</div>}
      {advice.careNotes && <><h4>{t("assistant.careNotesTitle")}</h4><p className="preserve small-text">{advice.careNotes}</p><p className="muted small-text">{t("assistant.careNotesHint")}</p></>}
      {stale && <p className="danger" role="alert">{t("assistant.stale")}</p>}
      {advice.applied ? <p className="success-message"><Check size={16}/>{t("assistant.applied")}</p> : <button className="button primary" disabled={!!stale || asking || applying || previewing || !preview} onClick={async()=>{setApplying(true);setError("");try{await run(()=>api(`plants/${plant.id}/advice/apply`,{method:"POST",body:JSON.stringify({adviceID:advice.id,...selection})}),t("assistant.appliedToast"));setAdvice(a=>a?{...a,applied:true}:a)}catch(e){setError((e as Error).message)}finally{setApplying(false)}}}><Check size={16}/>{Object.values(selection).some(Boolean)?t("assistant.applySelected"):t("assistant.applyNotes")}</button>}
    </div>}
  </>
}

export function AIModelCatalog({settings,onChanged}:{settings?:Settings;onChanged:()=>Promise<void>}){
  const { t } = useI18n();
  const [models,setModels]=useState<string[]>([]),[model,setModel]=useState(settings?.aiModel || ""),[busy,setBusy]=useState(false),[error,setError]=useState("");
  useEffect(()=>{setModel(settings?.aiModel || "");setModels([])},[settings?.aiProvider,settings?.aiModel]);
  return <details className="ai-catalog"><summary>{t("assistant.modelsTitle")}</summary><p className="muted small-text">{t("assistant.modelsText")}</p>
    <button className="button secondary" disabled={busy || !settings?.aiConfigured} onClick={async()=>{setBusy(true);setError("");try{const data=await api<{models:string[];selectedModel:string}>("ai/models",{method:"POST"});setModels(data.models);setModel(data.selectedModel)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}>{busy?<LoaderCircle className="spin" size={16}/>:<RotateCw size={16}/>}{t("assistant.loadModels")}</button>
    {models.length>0 && <div className="model-choice"><label>{t("assistant.model")}<select value={model} disabled={busy} onChange={e=>setModel(e.target.value)}>{!models.includes(model) && <option value={model}>{t("assistant.notInCatalog",{model})}</option>}{models.map(m=><option key={m}>{m}</option>)}</select></label><button className="button secondary" disabled={busy || !models.includes(model)} onClick={async()=>{setBusy(true);setError("");try{await api("ai/model",{method:"PUT",body:JSON.stringify({model})});await onChanged()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}>{t("assistant.useModel")}</button></div>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </details>
}
