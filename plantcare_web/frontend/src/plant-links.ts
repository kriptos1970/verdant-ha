const UUID='[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}';
export function routePlant(path:unknown):string|null {if(typeof path!=='string')return null;return new RegExp(`^/plant/(${UUID})/?$`).exec(path)?.[1].toUpperCase()||null}
export function labelLink(origin:string,id:string,ingress:boolean,slug='local_plantcare_web'):string {
 if(!new RegExp(`^${UUID}$`).test(id))throw new Error('Identificativo pianta non valido.');
 const base=new URL(origin);if(!['http:','https:'].includes(base.protocol)||base.username||base.password)throw new Error('Indirizzo non valido.');
 return ingress?`${base.origin}/app/${encodeURIComponent(slug)}/plant/${id}`:`${base.origin}/#plant=${id}`;
}
export function parsePlantLabel(value:string):string|null {
 try{const u=new URL(value.trim());if(u.protocol==='verdant:'&&u.hostname==='plant')return routePlant('/plant'+u.pathname);if(!['https:','http:'].includes(u.protocol))return null;return routePlant(u.pathname.replace(/^\/app\/[^/]+/,''))||routePlant(u.pathname.replace(/^\/local_plantcare_web/,''))||routePlant('/plant/'+new URLSearchParams(u.hash.slice(1)).get('plant'))}catch{return null}
}
