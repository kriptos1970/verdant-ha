import {useEffect,useRef,useState} from 'react';
import {Camera,Leaf,LoaderCircle,Search,Sparkles} from 'lucide-react';
import {api} from './api';
import {Modal} from './ui';
import {useI18n,type MessageKey} from './i18n';
import type {Plant,Settings} from './types';

type Candidate={scientificName:string;commonName:string;family:string;score:number;category:string};
type Profile={ranges?:{title:string;minimum:number|null;maximum:number|null;unit:string}[];scientificName:string;exactMatch:boolean;wateringDays:number;wateringLabel:string;sunlight:string[];soil:string[];careLevel:string;summary:string;source:string;sourceURL:string;fetchedAt:string;poisonousToPets:boolean|null;poisonousToHumans:boolean|null};
export type PlantSeed={draft:Partial<Plant>;file?:File};
const organKeys:Record<string,MessageKey>={leaf:'knowledge.organ.leaf',flower:'knowledge.organ.flower',fruit:'knowledge.organ.fruit',bark:'knowledge.organ.bark',auto:'knowledge.organ.all'};
export function BotanicalLookup({scientificName,configured}:{scientificName:string;configured:boolean}){
  const {t,formatDate}=useI18n();
  const [profile,setProfile]=useState<Profile|null>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const generation=useRef(0);
  const toxicity=(v:boolean|null)=>v===true?t('knowledge.toxicYes'):v===false?t('knowledge.toxicNo'):t('knowledge.unavailable');
  useEffect(()=>{generation.current++;setProfile(undefined);setError('');setBusy(false)},[scientificName]);
  return <section className="botanical-reference"><h3>{t('knowledge.lookupTitle')}</h3><p className="muted small-text">{t('knowledge.lookupIntro')}</p>
    <button type="button" className="button secondary" disabled={!configured||busy||!scientificName.trim()} onClick={async()=>{const request=++generation.current;setBusy(true);setError('');try{const p=await api<Profile|null>('knowledge/profile',{method:'POST',body:JSON.stringify({scientificName})});if(request===generation.current)setProfile(p)}catch(e){if(request===generation.current)setError((e as Error).message)}finally{if(request===generation.current)setBusy(false)}}}>{busy?<LoaderCircle className="spin" size={16}/>:<Search size={16}/>}{t('knowledge.lookupAction')}</button>
    {!configured&&<p className="muted small-text">{t('knowledge.lookupConfig')}</p>}
    {error&&<p role="alert" className="form-error">{error}</p>}{profile===null&&<p>{t('knowledge.notFound')}</p>}
    {profile&&<article className="reference-profile"><h4>{profile.scientificName}</h4>{!profile.exactMatch&&<p className="form-error">{t('knowledge.approximate')}</p>}<p className="muted small-text">{profile.source} · {t('knowledge.lookupDate',{date:formatDate(profile.fetchedAt,{dateStyle:'medium'})})}</p><dl><dt>{t('knowledge.water')}</dt><dd>{profile.wateringLabel||t('knowledge.notStated')} · {t('knowledge.aboutDays',{days:profile.wateringDays})}</dd><dt>{t('knowledge.light')}</dt><dd>{profile.sunlight.join(', ')||t('knowledge.unavailable')}</dd><dt>{t('knowledge.soil')}</dt><dd>{profile.soil.join(', ')||t('knowledge.unavailable')}</dd><dt>{t('knowledge.difficulty')}</dt><dd>{profile.careLevel||t('knowledge.unavailable')}</dd><dt>{t('knowledge.pets')}</dt><dd>{toxicity(profile.poisonousToPets)}</dd><dt>{t('knowledge.people')}</dt><dd>{toxicity(profile.poisonousToHumans)}</dd></dl>{profile.ranges?.map(r=><p key={r.title}>{r.title}: {r.minimum ?? "—"}–{r.maximum ?? "—"} {r.unit}</p>)}{profile.summary&&<p>{profile.summary}</p>}<a href={profile.sourceURL} target="_blank" rel="noreferrer">{t('knowledge.openSource')}</a></article>}
  </section>
}

export function IdentificationTool({settings,onPrepare}:{settings?:Settings;onPrepare:(seed:PlantSeed)=>void}){
  const {t}=useI18n();
  const [file,setFile]=useState<File>(),[preview,setPreview]=useState(''),[organ,setOrgan]=useState('leaf'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[candidates,setCandidates]=useState<Candidate[]|null>(null),[consent,setConsent]=useState(false);
  useEffect(()=>{if(!file){setPreview('');return}const url=URL.createObjectURL(file);setPreview(url);return()=>URL.revokeObjectURL(url)},[file]);
  const choose=(f?:File)=>{setFile(f);setCandidates(null);setError('');setConsent(false)};
  const identify=async()=>{setConsent(false);setBusy(true);setCandidates(null);setError('');try{const form=new FormData();form.append('file',file!);form.append('organ',organ);form.append('consent','true');const result=await api<{candidates:Candidate[]}>('identify',{method:'POST',body:form});setCandidates(result.candidates)}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
  return <section className="panel knowledge-panel"><div className="section-heading"><div><h2>{t('knowledge.identifyTitle')}</h2><p className="muted">{t('knowledge.identifyIntro')}</p></div><Camera size={28}/></div>
    <label className="recognition-dropzone" onDragOver={e=>{if(!busy)e.preventDefault()}} onDrop={e=>{e.preventDefault();if(!busy)choose(e.dataTransfer.files[0])}}>{preview?<img src={preview} alt={t('knowledge.identifyAlt')}/>:<><Camera size={48}/><strong>{t('knowledge.choosePhoto')}</strong><span>{t('knowledge.identifyHint')}</span></>}<input type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={e=>choose(e.target.files?.[0])}/></label>
    <p className="muted small-text">{t('knowledge.identifyPrivacy')}</p>
    <div className="recognition-controls"><label>{t('knowledge.organ')}<select value={organ} disabled={busy} onChange={e=>{setOrgan(e.target.value);setCandidates(null)}}>{Object.entries(organKeys).map(([v,key])=><option value={v} key={v}>{t(key)}</option>)}</select></label><button type="button" className="button primary" disabled={!file||busy||!settings?.services?.plantnet} onClick={()=>setConsent(true)}>{busy?<LoaderCircle className="spin" size={17}/>:<Sparkles size={17}/>} {busy?t('knowledge.identifyBusy'):t('knowledge.identifyAction')}</button></div>
    {!settings?.services?.plantnet&&<p className="muted">{t('knowledge.identifyConfig')}</p>}
    {error&&<p role="alert" className="form-error">{error}</p>}{candidates&&<div aria-live="polite"><h3>{t('knowledge.candidates')}</h3>{!candidates.length&&<p>{t('knowledge.noCandidates')}</p>}{candidates.map(c=><article className="identification-candidate" key={c.scientificName}><div className="candidate-title"><Leaf size={25}/><div><strong>{c.commonName}</strong><em>{c.scientificName}</em><small>{c.family||t('catalog.familyUnknown')}</small></div><b>{Math.floor(c.score*100)}%</b><button type="button" className="button secondary" onClick={()=>onPrepare({draft:{name:c.commonName.slice(0,200),species:c.scientificName,family:c.family,category:c.category,notes:t('knowledge.identifiedNote',{percent:Math.floor(c.score*100)})},file})}>{t('catalog.prepare')}</button></div><details><summary>{t('knowledge.consultSpecies')}</summary><BotanicalLookup scientificName={c.scientificName} configured={!!(settings?.services?.perenual||settings?.services?.openplantbook)}/></details></article>)}<p className="muted small-text">{t('knowledge.identifyDisclaimer')}</p></div>}
    {consent&&<Modal title={t('knowledge.consentTitle')} onClose={()=>setConsent(false)}><p>{t('knowledge.consentText')}</p><div className="button-row"><button className="button secondary" onClick={()=>setConsent(false)}>{t('common.cancel')}</button><button className="button primary" onClick={()=>void identify()}>{t('knowledge.consentSend')}</button></div></Modal>}
  </section>
}

type SavedSpecies={id:string;scientificName:string;family:string;genus:string;synonyms:string[];updatedAt?:string};
export function SpeciesLibrary({settings,onPrepare}:{settings?:Settings;onPrepare:(seed:PlantSeed)=>void}){
  const {t}=useI18n();
  const [species,setSpecies]=useState<SavedSpecies[]>([]),[search,setSearch]=useState(''),[error,setError]=useState(''),[loading,setLoading]=useState(true);
  useEffect(()=>{let active=true;api<SavedSpecies[]>('knowledge/species').then(v=>{if(active)setSpecies(v)}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[]);
  const filtered=species.filter(p=>[p.scientificName,p.family,...p.synonyms].some(v=>v.toLocaleLowerCase().includes(search.toLocaleLowerCase())));
  return <section className="panel knowledge-panel"><h2>{t('knowledge.libraryTitle')}</h2><p className="muted">{t('knowledge.libraryIntro')}</p><label>{t('knowledge.librarySearch')}<input value={search} maxLength={300} placeholder={t('knowledge.librarySearchPlaceholder')} onChange={e=>setSearch(e.target.value)}/></label>{error&&<p role="alert">{error}</p>}{loading?<p>{t('knowledge.libraryLoading')}</p>:<p className="muted small-text">{t('knowledge.libraryCount',{count:filtered.length})}</p>}{filtered.map(p=><article className="identification-candidate" key={p.id}><h3>{p.scientificName}</h3><p>{p.family}{p.genus&&` · ${p.genus}`}</p>{p.synonyms.length>0&&<p className="muted small-text">{t('knowledge.synonyms',{list:p.synonyms.join(', ')})}</p>}<div className="button-row"><button className="button secondary" onClick={()=>onPrepare({draft:{name:p.scientificName.slice(0,200),species:p.scientificName,family:p.family}})}>{t('catalog.prepare')}</button></div><details><summary>{t('knowledge.cultivation')}</summary><BotanicalLookup scientificName={p.scientificName} configured={!!(settings?.services?.perenual||settings?.services?.openplantbook)}/></details></article>)}{!loading&&!filtered.length&&<p>{t('knowledge.libraryEmpty')}</p>}</section>
}
