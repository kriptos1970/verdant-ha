import {useEffect,useState} from 'react';
import {BookOpen,Check,Leaf,ShieldCheck,Hand, Droplet,ArrowDownToLine,Ruler,Waves,Sun,RotateCw,Focus,Package, CircleDashed,Scissors,Eye,Search,Grid2X2,Pencil,Camera,RefreshCw,NotebookPen,Sunrise,Move,CheckCircle,Layers,Sparkles,Lightbulb} from 'lucide-react';
import type {Plant} from './types';
import {api} from './api';
import guidesIt from './data/care-guides.json';
import guidesEn from './data/care-guides.en.json';
import {useI18n,type MessageKey} from './i18n';
import {dateFormatter} from './intl-cache';
import {useCareLabels} from './care-labels';
import {useDomainLabels} from './domain-labels';
const guideImages=import.meta.glob('./assets/care-guides/*.webp',{eager:true,query:'?url',import:'default'}) as Record<string,string>;
const stepIcons:Record<string,typeof Leaf>={'hand.point.down.fill':Hand,'drop.fill':Droplet,'tray.and.arrow.down.fill':ArrowDownToLine,'ruler.fill':Ruler,'water.waves':Waves,'drop.circle.fill':Droplet,'sun.max.fill':Sun,'rotate.right.fill':RotateCw,'scope':Focus,'shippingbox.fill':Package,'circle.dotted':CircleDashed,'leaf.fill':Leaf,'cross.vial.fill':ShieldCheck,'eye.fill':Eye,'scissors':Scissors,'magnifyingglass':Search,'circle.hexagongrid.fill':Grid2X2,'square.and.pencil':Pencil,'camera.fill':Camera,'leaf.arrow.triangle.circlepath':RefreshCw,'note.text':NotebookPen,'sun.horizon.fill':Sunrise,'figure.strengthtraining.traditional':Move,'checkmark.circle.fill':CheckCircle,'rectangle.3.group.fill':Layers,'shield.lefthalf.filled':ShieldCheck,'sparkles':Sparkles};
const metricKeys:Record<string,MessageKey>={
  Luce:'guide.metric.light',Temperatura:'guide.metric.temperature',Umidità:'guide.metric.humidity',
};
const tileKeys:Record<string,MessageKey>={
  Terreno:'guide.tile.soil',Concimazione:'guide.tile.fertilize',Potatura:'guide.tile.prune',
  Rinvaso:'guide.tile.repot',Propagazione:'guide.tile.propagate',Difficoltà:'guide.tile.difficulty',
};
const symptomKeys:Record<string,MessageKey>={
  'Foglie gialle':'health.symptom.yellowLeaves',
  'Punte secche':'health.symptom.dryTips',
  'Foglie cadenti':'health.symptom.droopingLeaves',
  Macchie:'health.symptom.spots',
  Insetti:'health.symptom.insects',
  'Crescita lenta':'health.symptom.slowGrowth',
};

export function ActionGuide({kind,expanded=false}:{kind:string;expanded?:boolean}){
 const {t,locale}=useI18n();
 const {kindLabel}=useCareLabels();
 const guides=locale==='en'?guidesEn:guidesIt;
 const guide=guides.find(g=>g.kind===kind);
 return guide?<details className="action-guide" data-kind={kind} open={expanded||undefined}><summary><BookOpen size={18}/>{t('guides.quick')}</summary><img className="action-guide-image" src={guideImages[`./assets/care-guides/${guide.image}`]} alt={t('guides.imageAlt',{kind:kindLabel(kind)})} decoding="async"/><ol>{guide.steps.map((s,index)=>{const Icon=stepIcons[s.icon]||Leaf;return <li key={s.title}><span className="guide-step-symbol"><Icon size={19}/><b>{index+1}</b></span><div><strong>{s.title}</strong><p>{s.detail}</p></div></li>})}</ol><p className="guide-tip"><Lightbulb size={18}/><span>{guide.tip}</span></p></details>:null;
}

type Practical={ranges:{title:string;ideal:string;tolerable:string}[];tiles:{title:string;value:string;tip:string}[];seasonal:{month:number;days:number}[]};
export function PlantKnowledge({plant}:{plant:Plant}){
 const {t,locale}=useI18n();
 const {categoryLabel}=useDomainLabels();
 const [guide,setGuide]=useState<Practical>(),[error,setError]=useState('');
 useEffect(()=>{let active=true;setGuide(undefined);setError('');api<Practical>(`knowledge/plants/${plant.id}/guide?language=${locale}`).then(v=>{if(active)setGuide(v)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[plant.id,plant._version]);
 const months=Array.from({length:12},(_,i)=>dateFormatter(locale,{month:'short'}).format(new Date(2026,i,1)));
 return <section className="practical-guide"><h3><BookOpen size={19}/> {t('guides.practical')}</h3><p className="muted small-text">{t('guides.categoryIntro',{category:categoryLabel(plant.category).toLocaleLowerCase(locale)})}</p>{error&&<p role="alert">{error}</p>}{!guide&&!error&&<p>{t('guides.loading')}</p>}{guide&&<><div className="guide-ranges">{guide.ranges.map(r=><article key={r.title}><h4>{metricKeys[r.title]?t(metricKeys[r.title]):r.title}</h4><small>{t('guides.ideal')}</small><strong>{r.ideal}</strong><hr/><p>{t('guides.tolerable',{value:r.tolerable})}</p></article>)}</div><div className="guide-tiles">{guide.tiles.map(tile=><article key={tile.title}><h4>{tileKeys[tile.title]?t(tileKeys[tile.title]):tile.title}</h4><strong>{tile.value}</strong><p>{tile.tip}</p></article>)}</div><section className="seasonal-guide"><h4>{t('guides.seasonal')}</h4><p className="small-text">{t('guides.seasonalInterval')}</p><div className="seasonal-bars" role="img" aria-label={guide.seasonal.map(p=>t('guides.daysAria',{month:months[p.month-1],days:p.days})).join('; ')}>{guide.seasonal.map(p=><div key={p.month}><span>{p.days}</span><i style={{height:`${Math.max(4,p.days/Math.max(...guide.seasonal.map(item=>item.days))*100)}px`}}/><small>{months[p.month-1]}</small></div>)}</div><p className="muted small-text">{t('guides.seasonalNote')}</p></section></>}</section>
}
export function GuidesTool({plants}:{plants:Plant[]}){
 const {t,locale}=useI18n();
 const {kindLabel}=useCareLabels();
 const guides=locale==='en'?guidesEn:guidesIt;
 const [kind,setKind]=useState(guidesIt[0].kind),[chosen,setChosen]=useState('');
 const plant=plants.find(p=>p.id===chosen);
 return <section className="panel knowledge-panel"><h2>{t('guides.toolTitle')}</h2><p className="muted">{t('guides.toolText')}</p><label>{t('guides.activity')}<select value={kind} onChange={e=>setKind(e.target.value)}>{guides.map(g=><option key={g.kind} value={g.kind}>{kindLabel(g.kind)}</option>)}</select></label><ActionGuide key={kind} kind={kind} expanded/><hr/><label>{t('guides.plantGuide')}<select value={chosen} onChange={e=>setChosen(e.target.value)}><option value="">{t('guides.choosePlant')}</option>{plants.map(p=><option key={p.id} value={p.id}>{p.name} · {p.species}</option>)}</select></label>{plant&&<PlantKnowledge plant={plant}/>}</section>
}
const symptoms=['Foglie gialle','Punte secche','Foglie cadenti','Macchie','Insetti','Crescita lenta'];
export function DiagnosisTool({plants,onOpen}:{plants:Plant[];onOpen:(id:string)=>void}){
 const {t,locale}=useI18n();
 const [chosen,setChosen]=useState(''),[selected,setSelected]=useState<string[]>([]),[advice,setAdvice]=useState(''),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 useEffect(()=>{let active=true;setAdvice('');setError('');setLoading(false);if(!chosen||!selected.length||!plants.some(p=>p.id===chosen))return;setLoading(true);api<{plantID:string;advice:string}>('knowledge/diagnosis',{method:'POST',body:JSON.stringify({plantID:chosen,symptoms:selected,language:locale})}).then(v=>{if(active)setAdvice(v.advice)}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[chosen,selected,plants,locale]);
 return <section className="panel knowledge-panel"><h2>{t('diagnosis.title')}</h2><p className="muted">{t('diagnosis.text')}</p><h3>{t('diagnosis.stepPlant')}</h3><label>{t('diagnosis.plant')}<select value={chosen} onChange={e=>setChosen(e.target.value)}><option value="">{t('diagnosis.select')}</option>{plants.map(p=><option key={p.id} value={p.id}>{p.name} · {p.species}</option>)}</select></label>{!plants.length&&<p>{t('diagnosis.addPlant')}</p>}<h3>{t('diagnosis.stepSymptoms')}</h3><div className="symptoms-grid">{symptoms.map(s=><button key={s} type="button" aria-pressed={selected.includes(s)} className={selected.includes(s)?'selected':''} onClick={()=>setSelected(v=>v.includes(s)?v.filter(x=>x!==s):[...v,s])}><Leaf size={18}/>{t(symptomKeys[s])}{selected.includes(s)&&<Check size={18}/>}</button>)}</div><div aria-live="polite">{error&&<p role="alert">{error}</p>}{loading&&<p>{t('diagnosis.loading')}</p>}{advice&&<article className="diagnosis-result"><h3><ShieldCheck size={20}/> {t('diagnosis.result')}</h3><p>{advice}</p><p className="small-text">{t('diagnosis.hint')}</p><p className="muted small-text">{t('diagnosis.disclaimer')}</p><button className="button secondary" onClick={()=>onOpen(chosen)}>{t('diagnosis.open')}</button></article>}</div></section>
}
