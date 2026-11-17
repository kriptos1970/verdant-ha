import fs from 'node:fs';
import ts from '../plantcare_web/frontend/node_modules/typescript/lib/typescript.js';

const catalogDir = new URL('../plantcare_web/frontend/src/i18n/', import.meta.url);

async function load(name) {
  const source = fs.readFileSync(new URL(name, catalogDir), 'utf8');
  const code = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  return (await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'))).default;
}

function placeholders(value) {
  return [...value.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort().join(',');
}

const it = await load('it.ts');
const en = await load('en.ts');
const italianKeys = Object.keys(it).sort();
const englishKeys = Object.keys(en).sort();

const problems = [];
for (const key of italianKeys) {
  if (!(key in en)) problems.push(`manca in inglese: ${key}`);
}
for (const key of englishKeys) {
  if (!(key in it)) problems.push(`manca in italiano: ${key}`);
}
for (const key of new Set([...italianKeys, ...englishKeys])) {
  const italian = it[key];
  const english = en[key];
  if (typeof italian !== 'string' || !italian.trim()) problems.push(`valore italiano vuoto: ${key}`);
  if (typeof english !== 'string' || !english.trim()) problems.push(`valore inglese vuoto: ${key}`);
  if (typeof italian === 'string' && typeof english === 'string' && placeholders(italian) !== placeholders(english)) {
    problems.push(`segnaposto diversi: ${key} (${placeholders(italian) || 'nessuno'} / ${placeholders(english) || 'nessuno'})`);
  }
}

if (problems.length) {
  console.error('Cataloghi di traduzione non allineati:');
  for (const problem of problems) console.error(' - ' + problem);
  process.exit(1);
}

console.log(`i18n OK: ${italianKeys.length} chiavi, italiano e inglese allineati (chiavi e segnaposto).`);
