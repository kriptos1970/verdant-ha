const formatOptions={minimumFractionDigits:0,maximumFractionDigits:2,roundingMode:'halfEven'} as Intl.NumberFormatOptions & {roundingMode:'halfEven'};
const formatters=new Map<string,Intl.NumberFormat>();
function formatterFor(locale:string){
 let formatter=formatters.get(locale);
 if(!formatter){formatter=new Intl.NumberFormat(locale,formatOptions);formatters.set(locale,formatter)}
 return formatter;
}
function supportsHalfEven(locale:string){
 return (formatterFor(locale).resolvedOptions() as Intl.ResolvedNumberFormatOptions & {roundingMode?:string}).roundingMode==='halfEven';
}
function nativeNumber(value:number,locale:string){
 if(supportsHalfEven(locale))return formatterFor(locale).format(value);
 // Older WebKit: preserve Swift's ties-to-even rounding at two decimal places.
 const scaled=value*100,lower=Math.floor(scaled),fraction=scaled-lower;
 const tie=Math.abs(fraction-.5)<=Number.EPSILON*Math.max(1,Math.abs(scaled))*2;
 const rounded=(tie?(lower%2===0?lower:lower+1):Math.round(scaled))/100;
 return rounded.toLocaleString(locale,{minimumFractionDigits:0,maximumFractionDigits:2});
}
type DoseTranslate=(key:'productDose.notIndicated'|'productDose.partial',params?:Record<string,string|number>)=>string;
const italianDose:DoseTranslate=(key,params)=>key==='productDose.notIndicated'?'Dose non indicata':`${params!.dose} della dose indicata: ${params!.source}`;
// FertilizerProduct.explicitDosage(for:) from Verdant Models.swift.
export function explicitProductDose(dosage:string|undefined,dose:string|undefined,locale='it',t:DoseTranslate=italianDose){
 const source=(dosage||'').trim();
 if(!source||!dose||dose==='Dose intera')return source||t('productDose.notIndicated');
 const factor:Record<string,number>={'¾ di dose':.75,'½ dose':.5,'⅓ di dose':1/3,'¼ di dose':.25};
 if(!(dose in factor))return t('productDose.partial',{dose,source});
 const matches=[...source.matchAll(/\d+(?:[.,]\d+)?/g)];
 if(!matches.length)return t('productDose.partial',{dose,source});
 const selected=[matches[0]];
 if(matches[1]&&['-','–','—','a'].includes(source.slice(matches[0].index!+matches[0][0].length,matches[1].index).trim().toLowerCase()))selected.push(matches[1]);
 let result=source;
 for(const m of selected.reverse()){
  const value=Number(m[0].replace(',','.'))*factor[dose];
  result=result.slice(0,m.index)+nativeNumber(value,locale)+result.slice(m.index!+m[0].length);
 }
 return result;
}
