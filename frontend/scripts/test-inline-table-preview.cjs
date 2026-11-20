/* Run the real shared table code in Chrome, including resizing and full viewer. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const cp=require('node:child_process'),assert=require('node:assert/strict'),ts=require('typescript');
const root=path.resolve(__dirname,'..');
const output=path.resolve(root,'../backend/exports');fs.mkdirSync(output,{recursive:true});
const mod={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(root,'src/utils/uptodateTables.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:mod,exports:mod.exports});
const tables=mod.exports;
const styles=tables.tableStyles({ink:'#14201d',prose:'#14201d',muted:'#5f6b68',bg:'#fff',accent:'#0f5c52',rule:'#26382e',accentSoft:'#d4dcd3'},false);
const table=`<table><thead><tr><th>Section</th><th>Content</th><th>Reference</th></tr></thead><tbody><tr><td rowspan="2" id="merged">Source group</td><td><a id="source-link" href="#reference">Original link</a></td><td>Source note</td></tr><tr><td colspan="2">Original merged cell</td></tr>${Array.from({length:28},(_,i)=>`<tr><td>Section ${i+1}</td><td>Original reference text retained in its source DOM.</td><td>Source ${i+1}</td></tr>`).join('')}</tbody></table>`;
const html=`<!doctype html><html><meta charset="utf-8"><style>body{font:16px sans-serif;margin:16px}main{width:330px;max-width:100%}${styles}</style><main>${table}</main><script>
var originalText=document.querySelector('table').textContent;var operations=[];
function __utdEmitOp(op){operations.push(op);}
${tables.TABLE_SCRIPT}
__utdTablesInit({labels:${JSON.stringify(tables.tableLabels(false))},context:'article'});
setTimeout(function(){
  var main=document.querySelector('main'),t=document.querySelector('table'),preview=document.querySelector('.utd-table-preview');
  function fits(){var a=preview.getBoundingClientRect(),b=t.getBoundingClientRect();return b.left>=a.left-1&&b.right<=a.right+1&&b.top>=a.top-1&&b.bottom<=a.bottom+1&&a.height<=562;}
  var small=fits();main.style.width='700px';window.dispatchEvent(new Event('resize'));var resized=fits();
  preview.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));
  var opened=operations.length===1&&operations[0].type==='table'&&operations[0].index===0&&operations[0].context==='article';
  document.getElementById('source-link').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
  var linkPreserved=operations.length===1;
  var result={small:small,resized:resized,opened:opened,linkPreserved:linkPreserved,textPreserved:originalText===t.textContent,rowspan:document.getElementById('merged').rowSpan,accessible:preview.getAttribute('role')==='button'&&preview.getAttribute('aria-haspopup')==='dialog'};
  var viewer=document.createElement('iframe');viewer.id='viewer';viewer.style.cssText='width:390px;height:700px';document.body.appendChild(viewer);
  var d=viewer.contentDocument;d.open();d.write('<html><head><style>'+${JSON.stringify(styles)}+'</style></head><body>'+${JSON.stringify(table)}+'</body></html>');d.close();
  viewer.contentWindow.__utdEmitOp=function(){};
  viewer.contentWindow.eval(${JSON.stringify(tables.TABLE_SCRIPT)});
  viewer.contentWindow.__utdTablesInit({labels:${JSON.stringify(tables.tableLabels(false))},context:'article',viewer:{index:0,title:'Fixture table'}});
  var view=viewer.contentWindow.__utdTableView;
  result.viewerOpened=!!view&&!!d.getElementById('utdTableViewer');
  result.viewerHasNoPreview=!!d.querySelector('.utd-table-canvas > table')&&!d.querySelector('.utd-table-preview');
  result.readByDefault=view.state().mode==='read'&&view.state().scale===1;
  view.fit('all');
  result.wholeTableFits=view.state().mode==='all'&&view.state().scale<1;
  view.fit('read');
  var stage=d.querySelector('.utd-table-stage');
  result.canScrollToMoreColumns=view.state().scale===1&&stage.scrollWidth>stage.clientWidth;
  var r=document.createElement('script');r.id='qa-result';r.type='application/json';r.textContent=JSON.stringify(result);document.body.appendChild(r);
},150);
</script></html>`;
const file=path.join(output,'inline-table-preview.html');fs.writeFileSync(file,html,{mode:0o600});
const result=cp.spawnSync('/usr/bin/google-chrome',['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--window-size=820,960','--virtual-time-budget=1200','--dump-dom','file://'+file],{encoding:'utf8',maxBuffer:3000000});
assert.equal(result.status,0);
const match=result.stdout.match(/<script id="qa-result" type="application\/json">([^<]+)<\/script>/);assert.ok(match,'Browser report missing');
const report=JSON.parse(match[1]);
for(const key of ['small','resized','opened','linkPreserved','textPreserved','accessible','viewerOpened','viewerHasNoPreview','readByDefault','wholeTableFits','canScrollToMoreColumns'])assert.equal(report[key],true,key);
assert.equal(report.rowspan,2);
console.log('Inline table preview passed: full table fits, resize works, original text/links/spans remain, keyboard opens original full viewer.');
