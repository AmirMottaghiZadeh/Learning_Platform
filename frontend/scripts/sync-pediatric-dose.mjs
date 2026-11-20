// Import the owner's audited source snapshot; do not rewrite clinical rules.
// node scripts/sync-pediatric-dose.mjs [--source /path/to/peds_dose] [--check]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const args = process.argv.slice(2);
const sourceIndex = args.indexOf('--source');
const source = path.resolve(sourceIndex >= 0 ? args[sourceIndex + 1] : '/home/amir/Documents/Medscape/peds_dose');
const check = args.includes('--check');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const files = fs.readdirSync(path.join(source, 'data/drugs')).filter(file => file.endsWith('.json')).sort();
const drugs = files.map(file => JSON.parse(fs.readFileSync(path.join(source, 'data/drugs', file), 'utf8'))).sort((a, b) => (a.order || 999) - (b.order || 999));
if (!drugs.length || new Set(drugs.map(d => d.id)).size !== drugs.length) throw new Error('Missing or duplicate drug definitions');
for (const drug of drugs) {
  if (!drug.source?.contentId || !Array.isArray(drug.regimens) || !drug.products) throw new Error(`Invalid source definition: ${drug.id}`);
  for (const regimen of drug.regimens) {
    if (!regimen.quote && !regimen.quotes?.length) throw new Error(`Missing source quote: ${drug.id}/${regimen.id}`);
    for (const product of regimen.products) if (!drug.products[product]) throw new Error(`Unknown preparation: ${drug.id}/${product}`);
  }
}
const engine = fs.readFileSync(path.join(source, 'src/engine.js'));
const engineTarget = path.join(root, 'frontend/src/pediatricDose/engine.js');
const dataTarget = path.join(root, 'backend/apps/calculators/data/pediatric-dose.json');
const sourceDescription = 'UpToDate local monographs; source references retained per regimen';
const dataset = { source: sourceDescription, drugs, engine_sha256: sha(engine) };
if (check) {
  if (!engine.equals(fs.readFileSync(engineTarget))) throw new Error('Engine differs from the source snapshot');
  if (!isDeepStrictEqual(dataset, JSON.parse(fs.readFileSync(dataTarget, 'utf8')))) throw new Error('Dataset differs from the source snapshot');
  if (!fs.readFileSync(path.join(root, 'frontend/src/pediatricDose/version.ts'), 'utf8').includes(sha(engine))) throw new Error('Client engine version differs from source');
  console.log(`Source match: ${drugs.length} entries, ${drugs.reduce((n, d) => n + d.regimens.length, 0)} regimens; unchanged engine.`);
} else {
  const sourceFiles = { 'src/engine.js': sha(engine) };
  for (const file of files) sourceFiles['data/drugs/' + file] = sha(fs.readFileSync(path.join(source, 'data/drugs', file)));
  const payload = JSON.stringify(dataset) + '\n';
  const provenance = { source_directory: source, imported_at: new Date().toISOString().slice(0, 10), drug_entries: drugs.length,
    regimens: drugs.reduce((n, d) => n + d.regimens.length, 0), source_files: sourceFiles, bundle_sha256: sha(payload) };
  fs.writeFileSync(engineTarget, engine);
  fs.writeFileSync(path.join(root, 'frontend/src/pediatricDose/version.ts'), `export const PEDIATRIC_ENGINE_SHA256 = "${sha(engine)}";\n\nexport function isCompatibleDataset(data: { schema_version?: unknown; engine_sha256?: unknown }) {\n  return data.schema_version === 1 && data.engine_sha256 === PEDIATRIC_ENGINE_SHA256;\n}\n`);
  fs.writeFileSync(dataTarget, payload);
  fs.writeFileSync(path.join(root, 'frontend/src/pediatricDose/provenance.json'), JSON.stringify(provenance, null, 2) + '\n');
  console.log(`Imported ${drugs.length} entries and the source engine. Run the pediatric regression suite and rebuild backend and app together.`);
}
