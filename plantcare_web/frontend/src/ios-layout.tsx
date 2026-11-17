import {explicitProductDose} from './product-dose';
import {IOSIcon,adaptiveIcon} from './ios-icons';
import {useEffect,useState,useId,type ReactNode} from 'react';
import {useI18n} from './i18n';
import {useProductLabels} from './product-labels';
import {useCareLabels} from './care-labels';
import {ArrowLeft,Pencil,Search,Droplets,Sparkles,Sun,RotateCw,Scissors,Package,MapPin,CalendarDays,Ruler,TrendingUp,ShieldCheck,RefreshCw,BookOpen,FileText,SlidersHorizontal,Leaf,Camera,FlaskConical,ChevronRight} from 'lucide-react';
import type {Plant,Product} from './types';
import {photoURL,dueLabel} from './api';
import {Avatar,ProductPhoto,Modal} from './ui';

const PruneIcon=adaptiveIcon('scissors',Scissors), BookIcon=adaptiveIcon('book',BookOpen), NotesIcon=adaptiveIcon('notes',FileText), GrowthIcon=adaptiveIcon('chart',TrendingUp), SafetyIcon=adaptiveIcon('shield',ShieldCheck), CameraIcon=adaptiveIcon('camera',Camera), ProductIcon=adaptiveIcon('flask',FlaskConical), BrainIcon=adaptiveIcon('brain',Sparkles), ProfileIcon=adaptiveIcon('leaf',Leaf), WaterIcon=adaptiveIcon('water',Droplets), FeedIcon=adaptiveIcon('sparkles',Sparkles), RotationIcon=adaptiveIcon('rotate',RotateCw), PotIcon=adaptiveIcon('box',Package), LightIcon=adaptiveIcon('sun',Sun), PositionIcon=adaptiveIcon('pin',MapPin), DateIcon=adaptiveIcon('calendar',CalendarDays);

export function IOSPlantOverview({plant,products,openSection,sectionContent,onAction,onSection,onLabel}:{plant:Plant;products:Product[];openSection:string;sectionContent:ReactNode;onAction:(kind:string)=>void;onSection:(section:string)=>void;onLabel:()=>void}){
 const {t,plural,locale,formatDate,formatNumber}=useI18n();
 const {careValue,dueLabel}=useCareLabels();
 const [photoOpen,setPhotoOpen]=useState(false),[frequencies,setFrequencies]=useState(false);
 const image=photoURL(plant.photoPath)||(/^https:\/\//.test(plant.catalogImageURL||'')?plant.catalogImageURL:undefined);
 useEffect(()=>{setPhotoOpen(false);setFrequencies(false)},[plant.id,image]);
 const sectionID=useId();
 const product=products.find(p=>p.id===plant.fertilizerProductID);
 const next=plant._actions[0];
 const due=(kind:string)=>careValue(plant,kind,frequencies);
 const facts=[
  {label:t('ios.fact.water'),value:due('Annaffia'),icon:WaterIcon},
  {label:t('ios.fact.feed'),value:due('Concima'),icon:FeedIcon},
  {label:t('ios.fact.rotate'),value:due('Ruota'),icon:RotationIcon},
  ...(plant.inspectionInterval?[{label:t('ios.fact.inspect'),value:due('Controlla salute'),icon:ShieldCheck}]:[]),
  ...(plant.progressInterval?[{label:t('ios.fact.progress'),value:due('Aggiorna progressi'),icon:GrowthIcon}]:[]),
  {label:t('ios.fact.prune'),value:due('Pota'),icon:PruneIcon},
  {label:t('ios.fact.repot'),value:due('Rinvasa'),icon:PotIcon},
  {label:t('ios.fact.light'),value:plant.light,icon:LightIcon},
  {label:t('ios.fact.position'),value:plant.room,icon:PositionIcon},
  {label:t('ios.fact.since'),value:formatDate(plant.acquiredOn,{month:'short',year:'numeric'}),icon:DateIcon},
  {label:t('ios.fact.height'),value:plant.heightCM!=null?`${formatNumber(plant.heightCM)} cm`:t('ios.fact.toAdd'),icon:Ruler},
  {label:t('ios.fact.pot'),value:[plant.potMaterial,plant.potDiameterCM!=null?`${formatNumber(plant.potDiameterCM)} cm`:null].filter(Boolean).join(' · ')||t('ios.fact.toAdd'),icon:PotIcon},
 ];
 return <div className="ios-plant-overview">{photoOpen&&image&&<IOSPhotoViewer src={image} name={plant.name} credit={plant.photoPath?undefined:plant.catalogImageAttribution} onClose={()=>setPhotoOpen(false)}/>} <section className="ios-plant-hero"><Avatar plant={plant} large/>{image&&<button className="ios-open-photo" aria-label={t('ios.photoAria',{name:plant.name})} onClick={()=>setPhotoOpen(true)}/>}<div className="ios-plant-caption"><p className="ios-next-care">{next?dueLabel(next.daysUntil):t('ios.notScheduled')}</p><h2>{plant.name}</h2><p className="ios-plant-species">{plant.species||plant.category}</p><div className="ios-plant-actions"><button onClick={()=>onAction('Annaffia')}><IOSIcon name="water"/><span>{t('ios.action.water')}</span></button><button onClick={()=>onAction('Concima')}><IOSIcon name="sparkles"/><span>{t('ios.action.feed')}</span></button><button onClick={()=>onAction('Controlla salute')}><IOSIcon name="health"/><span>{t('ios.action.health')}</span></button><button onClick={()=>onSection('Misure')}><IOSIcon name="sun"/><span>{t('ios.action.light')}</span></button><button onClick={onLabel}><IOSIcon name="qr"/><span>{t('ios.action.qr')}</span></button></div></div></section>{plant.catalogImageURL&&!plant.photoPath&&plant.catalogImageAttribution&&<p className="ios-photo-credit">{plant.catalogImageAttribution}</p>}<section className="ios-summary"><h3><IOSIcon name="grid" size={21}/>{t('ios.summary')}</h3><button type="button" className="ios-summary-toggle" aria-label={t('ios.toggleAria')} aria-pressed={frequencies} onClick={()=>setFrequencies(v=>!v)}><span><IOSIcon name={frequencies?"rotate":"calendar"} size={16}/>{frequencies?t('ios.frequencies'):t('ios.deadlines')}</span><small><RefreshCw size={15}/>{t('ios.toggleHint')}</small></button><div className="ios-summary-grid" onClick={()=>setFrequencies(v=>!v)}>{facts.map(f=><div key={f.label}><i className="ios-fact-icon" data-fact={f.label}><f.icon size={20}/></i><span><small>{f.label}</small><strong>{f.value}</strong></span></div>)}</div></section><div className="ios-section-list">{[
 {label:t('ios.section.plan',{mode:plant.carePlanMode||'Manuale'}),desc:t('ios.section.planDesc'),section:'Piano',icon:SlidersHorizontal},
 {label:t('ios.section.insights'),desc:t('ios.section.insightsDesc'),section:'Consigli',icon:SafetyIcon},
 {label:t('ios.section.history'),desc:plural('ios.section.historyDesc',plant.history.filter(e=>!e.deletedAt).length),section:'Diario',icon:BookIcon},
 {label:t('ios.section.profile'),desc:plant.species||t('ios.section.profile'),section:'Guida',icon:ProfileIcon},
 {label:t('ios.section.growth'),desc:plural('ios.section.growthDesc',plant.growthEntries?.length||0),section:'Crescita',icon:GrowthIcon},
 {label:t('ios.section.measures'),desc:t('ios.section.measuresDesc'),section:'Misure',icon:LightIcon},
 {label:t('ios.section.safety'),desc:plant.safetyProfile?.sourceName||t('ios.section.safetyVerify'),section:'Sicurezza',icon:SafetyIcon},
 ...(product?[{label:t('ios.section.product'),desc:[product.name,product.brand].filter(Boolean).join(' · '),section:'Prodotto',icon:ProductIcon}]:[]),
 ...(plant.notes?[{label:t('ios.section.notes'),desc:t('ios.section.notesDesc'),section:'Note',icon:NotesIcon}]:[]),
 {label:t('ios.section.album'),desc:t('ios.section.albumDesc'),section:'Salute',icon:CameraIcon},
 {label:t('ios.section.treatments'),desc:t('ios.section.treatmentsDesc'),section:'Trattamenti',icon:ProductIcon},
 {label:t('ios.section.ai'),desc:t('ios.section.aiDesc'),section:'AI',icon:BrainIcon},
 ].map(s=>{const open=openSection===s.section;const contentID=`${sectionID}-${s.section}`;return <section className="ios-section-card" data-section={s.section} key={s.section}><button type="button" aria-expanded={open} aria-controls={open?contentID:undefined} onClick={()=>onSection(open?'':s.section)}><i className="ios-disclosure-icon"><s.icon size={24}/></i><span><strong>{s.label}</strong><small>{s.desc}</small></span><ChevronRight className={open?'expanded':''} size={19}/></button>{open&&<div id={contentID} className="ios-section-content" role="region" aria-label={s.label}>{s.section==='Note'?<p className="preserve">{plant.notes}</p>:s.section==='Prodotto'&&product?<><div className="ios-assigned-product"><ProductPhoto product={product}/><div><h3>{product.name}</h3><p>{product.brand}</p><small>{product.form}</small></div></div><h4>{t('ios.dose')}</h4><p>{explicitProductDose(product.dosage,plant.fertilizerDose)}</p>{product.applicationMethod&&<p>{product.applicationMethod}</p>}</>:sectionContent}</div>}</section>})}</div></div>
}

export function IOSProducts({products,onEdit,onCycle,onDelete}:{products:Product[];onEdit:(product:Product)=>void;onCycle:(product:Product)=>void;onDelete:(product:Product)=>void}){
 const {t,plural,locale}=useI18n();
 const {categoryLabel,formLabel}=useProductLabels();
 const [selected,setSelected]=useState<string>(),[search,setSearch]=useState(''),[category,setCategory]=useState(''),[photoOpen,setPhotoOpen]=useState(false);
 const product=products.find(p=>p.id===selected);
 const productImage=photoURL(product?.photoPath);
 useEffect(()=>setPhotoOpen(false),[selected]);
 const filtered=[...products].filter(p=>(!category||p.category===category)&&`${p.name} ${p.brand} ${p.suitableFor||''} ${p.category||''}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())).sort((a,b)=>a.name.localeCompare(b.name,'it'));
 return <div className="ios-products"><label className="search"><Search size={20}/><input aria-label={t("products.searchAria")} placeholder={t("products.searchPlaceholder")} value={search} onChange={e=>setSearch(e.target.value)}/></label><label className="ios-product-filter">{t("products.categoryFilter")}<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">{t("products.allCategories")}</option>{[...new Set(products.map(p=>p.category).filter(Boolean))].sort().map(c=><option key={c} value={c!}>{categoryLabel(c)}</option>)}</select></label><div className="ios-product-list">{filtered.map(p=><button key={p.id} onClick={()=>setSelected(p.id)}><IOSProductImage product={p}/><span><strong>{p.name}</strong><small>{p.brand||formLabel(p.form)||t("products.brandUnknown")}</small><small>{categoryLabel(p.category)||t("products.category")}{p.form?` · ${formLabel(p.form)}`:''}</small></span><ChevronRight size={20}/></button>)}</div>{!filtered.length&&<p className="gentle-empty">{products.length?t("products.noMatch"):t("products.first")}</p>}{product&&<section className="ios-product-detail"><header><button className="icon-button" aria-label={t("products.backAria")} onClick={()=>setSelected(undefined)}><ArrowLeft size={22}/></button><strong>{product.name}</strong><button className="icon-button" aria-label={t("products.editAria")} onClick={()=>onEdit(product)}><Pencil size={21}/></button></header><div className="ios-product-scroll"><div className="ios-product-photo">{productImage&&<button className="ios-open-photo" aria-label={t("products.photoAria", { name: product.name })} onClick={()=>setPhotoOpen(true)}/>}<ProductPhoto product={product}/></div><h2>{product.name}</h2><p className="muted">{product.brand||t("products.brandUnknown")}</p><p>{categoryLabel(product.category)||t("products.category")}{product.form?` · ${formLabel(product.form)}`:''}</p>{product.dosage&&<section><h3>{t("products.doseTitle")}</h3><p>{product.dosage}</p></section>}{product.applicationIntervalDays&&<section><h3>{t("products.frequency")}</h3><p>{plural("care.everyDays", product.applicationIntervalDays)}</p></section>}<section><h3>{t("products.notes")}</h3><p className="preserve">{product.notes||t("products.noNotes")}</p></section><button className="button primary" onClick={()=>onCycle(product)}>{t("products.planCycle")}</button><button className="button secondary" onClick={()=>onEdit(product)}>{t("products.edit")}</button><button className="text-button danger" onClick={()=>onDelete(product)}>{t("common.delete")}</button></div></section>}{photoOpen&&product&&productImage&&<IOSPhotoViewer src={productImage} name={product.name} onClose={()=>setPhotoOpen(false)}/>}</div>
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
