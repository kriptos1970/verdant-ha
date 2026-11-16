import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
if(process.argv.includes('--legacy-intl')){
 const NativeNumberFormat=Intl.NumberFormat;
 Intl.NumberFormat=function(locale,options={}){const {roundingMode,...legacy}=options;return new NativeNumberFormat(locale,legacy)};
}
const {explicitProductDose}=await import('../plantcare_web/frontend/src/product-dose.ts');
const source=readFileSync(new URL('../../PlantCare2.0/VerdantMultiplatform/Sources/Verdant/Models.swift',import.meta.url),'utf8');
function block(marker){const start=source.indexOf(marker);assert(start>=0);let depth=0;for(let i=source.indexOf('{',start);i<source.length;i++){if(source[i]==='{')depth++;if(source[i]==='}'&&!--depth)return source.slice(start,i+1);}throw Error(marker);}
const inputs=[];
for(const text of ['','  10 ml per 1 litro  ','10–20 ml / 2 l','3 a 6 g per litro','7,5 ml','Seguire etichetta','2.5 - 7.5 g / 10 l','Dose 1000 ml'])for(const dose of ['Dose intera','¾ di dose','½ dose','⅓ di dose','¼ di dose'])inputs.push([text,dose]);
const folder=mkdtempSync(join(tmpdir(),'plantcare-dose-'));
try{
 const encoded=Buffer.from(JSON.stringify(inputs)).toString('base64');
 const code=`import Foundation\n${block('enum FertilizerDose:')}\nstruct Product { var dosage:String\n${block('func explicitDosage(for dose:')}\n}\nlet cases = try JSONDecoder().decode([[String]].self, from: Data(base64Encoded: "${encoded}")!)\nlet answers = cases.map { Product(dosage: $0[0]).explicitDosage(for: FertilizerDose(rawValue: $0[1])!) }\nprint(String(data: try JSONEncoder().encode(answers), encoding: .utf8)!)`;
 const path=join(folder,'dose.swift');writeFileSync(path,code);
 const expected=JSON.parse(execFileSync('swift',['-module-cache-path',join(folder,'cache'),path],{encoding:'utf8'}));
 inputs.forEach(([text,dose],i)=>assert.equal(explicitProductDose(text,dose),expected[i],JSON.stringify([text,dose])));
 console.log(`OK: ${inputs.length} dosaggi confrontati con la funzione Swift originale${process.argv.includes('--legacy-intl')?' (fallback Intl)':''}.`);
}finally{rmSync(folder,{recursive:true,force:true});}
