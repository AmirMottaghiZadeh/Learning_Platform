/* Exercise the actual shared reader CSS/JS in Chrome, including rowspan. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process'),assert=require('node:assert/strict');
const ts=require('typescript');
const root=path.resolve(__dirname,'..');const output=path.resolve(root,'../backend/exports');
const source=fs.readFileSync(path.join(root,'src/utils/uptodateTables.ts'),'utf8');
const moduleValue={exports:{}};
vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,{module:moduleValue,exports:moduleValue.exports});
const table=moduleValue.exports;
const styles=table.tableStyles({ink:'#14201d',prose:'#14201d',muted:'#647267',bg:'#fff',accent:'#0f5c52',rule:'#26382e',accentSoft:'#d4dcd3'},false);
const html=`<!doctype html><html><meta charset="utf-8"><style>body{font:16px sans-serif;margin:36px}main{max-width:1080px}${styles}</style><main><h2>UpToDate — original table layout fixture</h2><p>UI fixture only; no clinical recommendation.</p>
<table><thead><tr><th>Category</th><th>Value</th><th>Notes</th></tr></thead><tbody><tr><td id="first" rowspan="2">Source group</td><td>A</td><td rowspan="2">Merged source note</td></tr><tr><td id="neighbor" style="border:0!important">B</td></tr><tr><td>Follow-up</td><td colspan="2">Original merged source cell</td></tr></tbody></table></main>
<script>function __utdEmitOp(){};${table.TABLE_SCRIPT};__utdTablesInit({labels:${JSON.stringify(table.tableLabels(false))},context:'article'});
var cells=[...document.querySelectorAll('.utd-reference-table td,.utd-reference-table th')];var result={allRightBorders:cells.every(c=>getComputedStyle(c).borderRightWidth==='1px'),allBottomBorders:cells.every(c=>parseFloat(getComputedStyle(c).borderBottomWidth)>=1),neighborBorder:getComputedStyle(document.getElementById('neighbor')).borderRightColor,sourceSpan:document.getElementById('first').rowSpan,logicalFirst:document.getElementById('first').classList.contains('utd-table-label'),neighborNotFirst:!document.getElementById('neighbor').classList.contains('utd-table-label'),firstColor:getComputedStyle(document.getElementById('first')).backgroundColor};
var report=document.createElement('script');report.id='qa-result';report.type='application/json';report.textContent=JSON.stringify(result);document.body.appendChild(report);</script></html>`;
const file=path.join(output,'uptodate-table-grid.html');fs.writeFileSync(file,html,{mode:0o600});
const result=cp.spawnSync('/usr/bin/google-chrome',['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--hide-scrollbars','--window-size=1200,720','--virtual-time-budget=1000',`--screenshot=${path.join(output,'uptodate-table-grid.png')}`,'--dump-dom','file://'+file],{encoding:'utf8',maxBuffer:2000000});
assert.equal(result.status,0);const match=result.stdout.match(/<script id="qa-result" type="application\/json">([^<]+)<\/script>/);
assert.ok(match,'Browser layout report missing');const report=JSON.parse(match[1]);
assert.equal(report.allRightBorders,true);assert.equal(report.allBottomBorders,true);assert.equal(report.neighborBorder,'rgb(38, 56, 46)');
assert.equal(report.sourceSpan,2);assert.equal(report.logicalFirst,true);assert.equal(report.neighborNotFirst,true);assert.equal(report.firstColor,'rgb(212, 220, 211)');
console.log('Table grid passed: all cell edges visible, rowspan preserved, middle-column edge retained, inline border:none removed, selected first-column color.');
