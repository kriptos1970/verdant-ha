import {explicitProductDose} from './product-dose';
import {iosCareValue} from './ios-summary';
import {IOSIcon,adaptiveIcon} from './ios-icons';
import {useEffect,useState,useId,type ReactNode} from 'react';
import {ArrowLeft,Pencil,Search,Droplets,Sparkles,Sun,RotateCw,Scissors,Package,MapPin,CalendarDays,Ruler,TrendingUp,ShieldCheck,RefreshCw,BookOpen,FileText,SlidersHorizontal,Leaf,Camera,FlaskConical,ChevronRight} from 'lucide-react';
import type {Plant,Product} from './types';
import {photoURL,dueLabel} from './api';
import {Avatar,ProductPhoto,Modal} from './ui';

const PruneIcon=adaptiveIcon('scissors',Scissors), BookIcon=adaptiveIcon('book',BookOpen), NotesIcon=adaptiveIcon('notes',FileText), GrowthIcon=adaptiveIcon('chart',TrendingUp), SafetyIcon=adaptiveIcon('shield',ShieldCheck), CameraIcon=adaptiveIcon('camera',Camera), ProductIcon=adaptiveIcon('flask',FlaskConical), BrainIcon=adaptiveIcon('brain',Sparkles), ProfileIcon=adaptiveIcon('leaf',Leaf), WaterIcon=adaptiveIcon('water',Droplets), FeedIcon=adaptiveIcon('sparkles',Sparkles), RotationIcon=adaptiveIcon('rotate',RotateCw), PotIcon=adaptiveIcon('box',Package), LightIcon=adaptiveIcon('sun',Sun), PositionIcon=adaptiveIcon('pin',MapPin), DateIcon=adaptiveIcon('calendar',CalendarDays);

export function IOSPlantOverview({plant,products,openSection,sectionContent,onAction,onSection,onLabel}:{plant:Plant;products:Product[];openSection:string;sectionContent:ReactNode;onAction:(kind:string)=>void;onSection:(section:string)=>void;onLabel:()=>void}){
 const [photoOpen,setPhotoOpen]=useState(false),[frequencies,setFrequencies]=useState(false);
 const image=photoURL(plant.photoPath)||(/^https:\/\//.test(plant.catalogImageURL||'')?plant.catalogImageURL:undefined);
 useEffect(()=>{setPhotoOpen(false);setFrequencies(false)},[plant.id,image]);
 const sectionID=useId();
 const product=products.find(p=>p.id===plant.fertilizerProductID);
 const next=plant._actions[0];
 const due=(kind:string)=>iosCareValue(plant,kind,frequencies);
 const facts=[
  {label:'Annaffiatura',value:due('Annaffia'),icon:WaterIcon},
  {label:'Concimazione',value:due('Concima'),icon:FeedIcon},
  {label:'Rotazione',value:due('Ruota'),icon:RotationIcon},
  ...(plant.inspectionInterval?[{label:'Controllo',value:due('Controlla salute'),icon:ShieldCheck}]:[]),
  ...(plant.progressInterval?[{label:'Diario crescita',value:due('Aggiorna progressi'),icon:GrowthIcon}]:[]),
  {label:'Potatura',value:due('Pota'),icon:PruneIcon},
  {label:'Rinvaso',value:due('Rinvasa'),icon:PotIcon},
  {label:'Luce',value:plant.light,icon:LightIcon},
  {label:'Posizione',value:plant.room,icon:PositionIcon},
  {label:'Con te dal',value:new Date(plant.acquiredOn).toLocaleDateString('it-IT',{month:'short',year:'numeric'}),icon:DateIcon},
  {label:'Altezza',value:plant.heightCM!=null?`${plant.heightCM.toLocaleString('it-IT')} cm`:'Da aggiungere',icon:Ruler},
  {label:'Vaso',value:[plant.potMaterial,plant.potDiameterCM!=null?`${plant.potDiameterCM.toLocaleString('it-IT')} cm`:null].filter(Boolean).join(' · ')||'Da aggiungere',icon:PotIcon},
 ];
 return <div className="ios-plant-overview">{photoOpen&&image&&<IOSPhotoViewer src={image} name={plant.name} credit={plant.photoPath?undefined:plant.catalogImageAttribution} onClose={()=>setPhotoOpen(false)}/>} <section className="ios-plant-hero"><Avatar plant={plant} large/>{image&&<button className="ios-open-photo" aria-label={`Mostra foto di ${plant.name} a schermo intero`} onClick={()=>setPhotoOpen(true)}/>}<div className="ios-plant-caption"><p className="ios-next-care">{next?dueLabel(next.daysUntil):'Nessuna cura programmata'}</p><h2>{plant.name}</h2><p className="ios-plant-species">{plant.species||plant.category}</p><div className="ios-plant-actions"><button onClick={()=>onAction('Annaffia')}><IOSIcon name="water"/><span>Acqua</span></button><button onClick={()=>onAction('Concima')}><IOSIcon name="sparkles"/><span>Concime</span></button><button onClick={()=>onAction('Controlla salute')}><IOSIcon name="health"/><span>Salute</span></button><button onClick={()=>onSection('Misure')}><IOSIcon name="sun"/><span>Luce</span></button><button onClick={onLabel}><IOSIcon name="qr"/><span>QR/NFC</span></button></div></div></section>{plant.catalogImageURL&&!plant.photoPath&&plant.catalogImageAttribution&&<p className="ios-photo-credit">{plant.catalogImageAttribution}</p>}<section className="ios-summary"><h3><IOSIcon name="grid" size={21}/>In sintesi</h3><button type="button" className="ios-summary-toggle" aria-label="Cambia rappresentazione del riepilogo" aria-pressed={frequencies} onClick={()=>setFrequencies(v=>!v)}><span><IOSIcon name={frequencies?"rotate":"calendar"} size={16}/>{frequencies?"Frequenze":"Scadenze"}</span><small><RefreshCw size={15}/>Tocca per cambiare</small></button><div className="ios-summary-grid" onClick={()=>setFrequencies(v=>!v)}>{facts.map(f=><div key={f.label}><i className="ios-fact-icon" data-fact={f.label}><f.icon size={20}/></i><span><small>{f.label}</small><strong>{f.value}</strong></span></div>)}</div></section><div className="ios-section-list">{[
 {label:`Piano ${plant.carePlanMode||'Manuale'} · Attivo`,desc:'Frequenze e attività',section:'Piano',icon:SlidersHorizontal},
 {label:'Osservazioni per la sua cura',desc:'Indicazioni e dati disponibili',section:'Consigli',icon:SafetyIcon},
 {label:'Andamento e cronologia',desc:`${plant.history.filter(e=>!e.deletedAt).length} attività ${plant.history.filter(e=>!e.deletedAt).length===1?'registrata':'registrate'}`,section:'Diario',icon:BookIcon},
 {label:'Profilo e cura',desc:plant.species||'Esigenze della pianta',section:'Guida',icon:ProfileIcon},
 {label:'Diario di crescita',desc:`${plant.growthEntries?.length||0} ${(plant.growthEntries?.length||0)===1?'aggiornamento':'aggiornamenti'}`,section:'Crescita',icon:GrowthIcon},
 {label:'Misure e sensori',desc:'Osservazioni della pianta',section:'Misure',icon:LightIcon},
 {label:'Sicurezza',desc:plant.safetyProfile?.sourceName||'Dati da verificare',section:'Sicurezza',icon:SafetyIcon},
 ...(product?[{label:'Prodotto per la concimazione',desc:[product.name,product.brand].filter(Boolean).join(' · '),section:'Prodotto',icon:ProductIcon}]:[]),
 ...(plant.notes?[{label:'Note',desc:'Osservazioni e indicazioni salvate sulla pianta',section:'Note',icon:NotesIcon}]:[]),
 {label:'Album salute',desc:'Fotografie e osservazioni',section:'Salute',icon:CameraIcon},
 {label:'Trattamenti',desc:'Prodotti e cicli',section:'Trattamenti',icon:ProductIcon},
 {label:'Assistente AI',desc:'Proposte e consigli',section:'AI',icon:BrainIcon},
 ].map(s=>{const open=openSection===s.section;const contentID=`${sectionID}-${s.section}`;return <section className="ios-section-card" data-section={s.section} key={s.section}><button type="button" aria-expanded={open} aria-controls={open?contentID:undefined} onClick={()=>onSection(open?'':s.section)}><i className="ios-disclosure-icon"><s.icon size={24}/></i><span><strong>{s.label}</strong><small>{s.desc}</small></span><ChevronRight className={open?'expanded':''} size={19}/></button>{open&&<div id={contentID} className="ios-section-content" role="region" aria-label={s.label}>{s.section==='Note'?<p className="preserve">{plant.notes}</p>:s.section==='Prodotto'&&product?<><div className="ios-assigned-product"><ProductPhoto product={product}/><div><h3>{product.name}</h3><p>{product.brand}</p><small>{product.form}</small></div></div><h4>Dose da usare</h4><p>{explicitProductDose(product.dosage,plant.fertilizerDose)}</p>{product.applicationMethod&&<p>{product.applicationMethod}</p>}</>:sectionContent}</div>}</section>})}</div></div>
}

export function IOSProducts({products,onEdit,onCycle,onDelete}:{products:Product[];onEdit:(product:Product)=>void;onCycle:(product:Product)=>void;onDelete:(product:Product)=>void}){
 const [selected,setSelected]=useState<string>(),[search,setSearch]=useState(''),[category,setCategory]=useState(''),[photoOpen,setPhotoOpen]=useState(false);
 const product=products.find(p=>p.id===selected);
 const productImage=photoURL(product?.photoPath);
 useEffect(()=>setPhotoOpen(false),[selected]);
 const filtered=[...products].filter(p=>(!category||p.category===category)&&`${p.name} ${p.brand} ${p.suitableFor||''} ${p.category||''}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())).sort((a,b)=>a.name.localeCompare(b.name,'it'));
 return <div className="ios-products"><label className="search"><Search size={20}/><input aria-label="Cerca un prodotto" placeholder="Cerca prodotto, marca o utilizzo" value={search} onChange={e=>setSearch(e.target.value)}/></label><label className="ios-product-filter">Categoria<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">Tutti i prodotti</option>{[...new Set(products.map(p=>p.category).filter(Boolean))].sort().map(c=><option key={c} value={c!}>{c}</option>)}</select></label><div className="ios-product-list">{filtered.map(p=><button key={p.id} onClick={()=>setSelected(p.id)}><IOSProductImage product={p}/><span><strong>{p.name}</strong><small>{p.brand||p.form||'Marca non indicata'}</small><small>{p.category||'Prodotto'}{p.form?` · ${p.form}`:''}</small></span><ChevronRight size={20}/></button>)}</div>{!filtered.length&&<p className="gentle-empty">{products.length?'Nessun prodotto con questi filtri.':'Aggiungi il primo prodotto con il pulsante +.'}</p>}{product&&<section className="ios-product-detail"><header><button className="icon-button" aria-label="Torna ai prodotti" onClick={()=>setSelected(undefined)}><ArrowLeft size={22}/></button><strong>{product.name}</strong><button className="icon-button" aria-label="Modifica prodotto" onClick={()=>onEdit(product)}><Pencil size={21}/></button></header><div className="ios-product-scroll"><div className="ios-product-photo">{productImage&&<button className="ios-open-photo" aria-label={`Mostra foto di ${product.name} a schermo intero`} onClick={()=>setPhotoOpen(true)}/>}<ProductPhoto product={product}/></div><h2>{product.name}</h2><p className="muted">{product.brand||'Marca non indicata'}</p><p>{product.category||'Prodotto'}{product.form?` · ${product.form}`:''}</p>{product.dosage&&<section><h3>Dose</h3><p>{product.dosage}</p></section>}{product.applicationIntervalDays&&<section><h3>Frequenza</h3><p>Ogni {product.applicationIntervalDays} giorni</p></section>}<section><h3>Note</h3><p className="preserve">{product.notes||'Nessuna nota.'}</p></section><button className="button primary" onClick={()=>onCycle(product)}>Pianifica ciclo</button><button className="button secondary" onClick={()=>onEdit(product)}>Modifica prodotto</button><button className="text-button danger" onClick={()=>onDelete(product)}>Elimina prodotto</button></div></section>}{photoOpen&&product&&productImage&&<IOSPhotoViewer src={productImage} name={product.name} onClose={()=>setPhotoOpen(false)}/>}</div>
}
function IOSProductImage({product}:{product:Product}){const src=photoURL(product.photoPath);const [failed,setFailed]=useState(false);useEffect(()=>setFailed(false),[src]);return <span className="ios-product-image">{src&&!failed?<img src={photoURL(product.photoPath,true)} alt={product.name} loading="lazy" onError={()=>setFailed(true)}/>:<IOSIcon name="flask" size={32}/>}</span>}

function IOSPhotoViewer({src,name,credit,onClose}:{src:string;name:string;credit?:string;onClose:()=>void}){
 const [failed,setFailed]=useState(false);
 useEffect(()=>setFailed(false),[src]);
 return <Modal title={name} onClose={onClose}><div className="ios-photo-viewer">{failed?<p role="alert">Fotografia non disponibile. Chiudi e riprova.</p>:<img src={src} alt={`Fotografia di ${name}`} onError={()=>setFailed(true)}/>}{credit&&<p>{credit}</p>}<a href={src} target="_blank" rel="noreferrer">Apri originale</a></div></Modal>;
}
export function useIOSLayout(){
 const [phone,setPhone]=useState(()=>window.matchMedia('(max-width:760px)').matches);
 useEffect(()=>{const media=window.matchMedia('(max-width:760px)');const update=()=>setPhone(media.matches);update();media.addEventListener('change',update);return()=>media.removeEventListener('change',update)},[]);
 return phone;
}
