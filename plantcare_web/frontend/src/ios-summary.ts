import type {Plant} from './types';
const intervals:Record<string,keyof Plant>={Annaffia:'wateringInterval',Concima:'fertilizingInterval',Ruota:'rotationInterval',Pota:'pruningInterval',Rinvasa:'repottingInterval','Controlla salute':'inspectionInterval','Aggiorna progressi':'progressInterval'};
export function iosDeadline(days:number){
 if(days===0)return 'Oggi';
 if(days>0)return days===1?'Tra 1 giorno':`Tra ${days} giorni`;
 return days===-1?'Scaduta da 1 giorno':`Scaduta da ${-days} giorni`;
}
export function iosCareValue(plant:Plant,kind:string,frequencies=false){
 const interval=plant[intervals[kind]];
 if(typeof interval!=='number'||interval<=0)return ['Annaffia','Concima'].includes(kind)?'Non pianificata':'Non prevista';
 if(frequencies)return interval===1?'Ogni giorno':`Ogni ${interval} giorni`;
 // Operational actions group water+fertilizer and may omit the separate feed row.
 // The ungrouped server schedule preserves both dates and all postponements.
 const action=plant._schedule.find(a=>a.kind===kind);
 return action?iosDeadline(action.daysUntil):'Non pianificata';
}
