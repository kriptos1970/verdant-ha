// Match CompleteCareSheet.completedNote without adding event fields or changing scheduling.
export const healthSymptoms=['Foglie gialle','Punte secche','Foglie cadenti','Macchie','Parassiti','Crescita lenta'];
export const healthAreas=['Foglie','Retro foglie','Fusto','Terreno','Radici','Drenaggio'];
export function healthCheckNote(note:string,symptoms:string[],areas:string[],problem:string,nextAction:string){
 return [note.trim(),symptoms.length?`Sintomi: ${[...symptoms].sort().join(', ')}`:'',areas.length?`Aree controllate: ${[...areas].sort().join(', ')}`:'',problem.trim()?`Possibile problema: ${problem.trim()}`:'',nextAction.trim()?`Azione consigliata: ${nextAction.trim()}`:''].filter(Boolean).join(' · ');
}
