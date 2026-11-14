'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const Module=require('node:module');
const crypto=require('node:crypto');
const ts=require('typescript');
const root=path.resolve(__dirname,'../..');
const modules=new Map();
function load(relative){
 const file=path.join(root,'src',relative);
 if(modules.has(file))return modules.get(file).exports;
 const instance=new Module(file,module);instance.filename=file;instance.paths=Module._nodeModulePaths(path.dirname(file));modules.set(file,instance);
 const native=instance.require.bind(instance);
 instance.require=specifier=>{
  let target=specifier.startsWith('@/')?specifier.slice(2):specifier.startsWith('./')?path.relative(path.join(root,'src'),path.resolve(path.dirname(file),specifier)):null;
  if(target && fs.existsSync(path.join(root,'src',target+'.ts')))return load(target+'.ts');
  return native(specifier);
 };
 instance._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,esModuleInterop:true}}).outputText,file);
 return instance.exports;
}
const {includePediatricDose,PEDIATRIC_DOSE_SLUG}=load('pediatricDose/catalog.ts');
const {groupByMainCategory}=load('utils/calculatorCategories.ts');
const {emptyDraft,patientInput,validatePatient,needsFrequency,selectedResults,formatDoseRange}=load('pediatricDose/model.ts');
const E=require('../../src/pediatricDose/engine.js');
const drugs=require('../../../backend/apps/calculators/data/pediatric-dose.json').drugs;
const provenance=require('../../src/pediatricDose/provenance.json');

test('the runtime engine is the exact reviewed upstream engine',()=>{
 const hash=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'src/pediatricDose/engine.js'))).digest('hex');
 assert.equal(hash,provenance.source_files['src/engine.js']);
});
test('tool joins the real Pediatrics domain without changing other calculators or hardcoding its database id',()=>{
 const pediatrics={id:917,name:'Pediatrics',name_fa:'کودکان',is_main_category:true,parent_id:null};
 const cardiology={...pediatrics,id:49,name:'Cardiology'};
 const original=[{slug:'apgar',name:'APGAR',name_fa:'آپگار',description:'',description_fa:'',categories:[pediatrics]},{slug:'other',name:'Other',name_fa:'',description:'',description_fa:'',categories:[cardiology]}];
 const result=includePediatricDose(original,[pediatrics,cardiology]);
 const groups=groupByMainCategory(result.items,result.categories);
 assert.equal(groups.filter(g=>g.name==='Pediatrics').length,1);
 const group=groups.find(g=>g.id===917);
 const section=group.subgroups.find(s=>s.name==='Pediatric Dose Adjustment');
 assert.deepEqual(section.calculators.map(c=>c.slug),[PEDIATRIC_DOSE_SLUG]);
 assert.equal(result.items.find(c=>c.slug==='other'),original[1]);assert.equal(original.length,2);
 const again=includePediatricDose(result.items,result.categories);
 assert.equal(again.items.filter(c=>c.slug===PEDIATRIC_DOSE_SLUG).length,1);
});
test('tool remains available in an empty snapshot with a dedicated Pediatrics domain',()=>{
 const catalog=includePediatricDose([],[]),groups=groupByMainCategory(catalog.items,catalog.categories);
 assert.equal(groups.length,1);assert.equal(groups[0].name,'Pediatrics');assert.equal(groups[0].subgroups.length,1);
});
test('new patients start empty and Persian decimal input reaches the unchanged validator',()=>{
 const blank=emptyDraft();assert.ok(validatePatient(blank).errors.length>=2);assert.equal(blank.ga,'');assert.equal(blank.drugId,'');
 const draft={...blank,age:'۵',weight:'۲۰٫۵'};const input=patientInput(draft);
 assert.equal(input.ageValue,5);assert.equal(input.weightKg,20.5);assert.equal(input.gaWeeks,undefined);assert.deepEqual(validatePatient(draft).errors,[]);
});
test('regimen, preparation and alternative frequency must be explicitly selected',()=>{
 const drug=drugs.find(d=>d.id==='amoxicillin'),draft={...emptyDraft(),age:'5',weight:'20',regimenId:'strep_pharyngitis'};
 const regimen=E.calculate(drug,patientInput(draft)).regimens.find(r=>r.id===draft.regimenId),raw=drug.regimens.find(r=>r.id===draft.regimenId);
 assert.equal(needsFrequency(raw,regimen),true);assert.deepEqual(selectedResults(raw,regimen,draft),[]);
 draft.productId='s250';assert.deepEqual(selectedResults(raw,regimen,draft),[]);
 draft.frequency='q12h';const result=selectedResults(raw,regimen,draft);assert.equal(result.length,1);assert.deepEqual(result[0].mgPerDose,[500,500]);
});
test('staged regimens retain every stage instead of selecting one and dropping the others',()=>{
 const drug=drugs.find(d=>d.id==='co_trimoxazole'),draft={...emptyDraft(),age:'5',weight:'20'};
 const output=E.calculate(drug,patientInput(draft));
 const regimen=output.regimens.find(r=>drug.regimens.find(raw=>raw.id===r.id)?.stages);
 const raw=drug.regimens.find(r=>r.id===regimen.id);draft.productId=raw.products[0];
 assert.equal(needsFrequency(raw,regimen),false);
 assert.equal(selectedResults(raw,regimen,draft).length,regimen.results.length);
});
test('unverified combination preparations remain blocked in the selected output',()=>{
 const drug=drugs.find(d=>d.id==='cold_products'),draft={...emptyDraft(),age:'5',weight:'20'};
 const regimen=E.calculate(drug,patientInput(draft)).regimens[0],raw=drug.regimens.find(r=>r.id===regimen.id);draft.productId=raw.products[0];
 assert.equal(needsFrequency(raw,regimen),false);
 const result=selectedResults(raw,regimen,draft);assert.ok(result.length);
 for(const r of result)for(const p of r.products){assert.equal(p.ok,false);assert.equal(p.amount,undefined);}
});
test('tiny nonzero doses do not get formatted as zero',()=>{
 assert.equal(formatDoseRange([0.0000001,0.0000001],false),'0.0000001');
 assert.equal(formatDoseRange([10,10],false),'10');
 assert.equal(formatDoseRange([7.6,11.2],false),'7.6–11.2');
});

const {isCompatibleDataset,PEDIATRIC_ENGINE_SHA256}=load('pediatricDose/version.ts');
test('mismatched engine/data versions cannot enter the dose calculator',()=>{
 const dataset=require('../../../backend/apps/calculators/data/pediatric-dose.json');
 assert.equal(isCompatibleDataset({...dataset,schema_version:1}),true);
 assert.equal(dataset.engine_sha256,PEDIATRIC_ENGINE_SHA256);
 assert.equal(isCompatibleDataset({schema_version:1,engine_sha256:'old-engine'}),false);
 assert.equal(isCompatibleDataset({schema_version:2,engine_sha256:PEDIATRIC_ENGINE_SHA256}),false);
 assert.equal(isCompatibleDataset({schema_version:1}),false);
});
