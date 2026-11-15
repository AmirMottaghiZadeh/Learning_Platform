const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs'),path = require('node:path'),vm = require('node:vm');
const ts = require('typescript');
const root=path.resolve(__dirname,'../src/utils');
function load(name) {
  const mod={exports:{}};
  const compiled=ts.transpileModule(fs.readFileSync(path.join(root,name+'.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
  vm.runInNewContext(compiled,{module:mod,exports:mod.exports,require(id){if(id==='./html')return load('html');throw Error('Unexpected import');}});
  return mod.exports;
}
const {classifyReferenceContent:classify}=load('referenceContent');
const {referenceCalculatorPage:page}=load('referenceCalculatorPage');
const link=(id,title)=>`<a data-topicid="${id}" onclick="doOperation({contentId:&quot;${id}&quot;})">${title}</a>`;
const topic=(body,title='Azelastine: Patient drug information')=>({title,body_html:`<div id="drugTitle">${title}</div><div id="topicText">${body}</div><div>Topic version and copyright outside content</div>`});

test('recognizes a split monograph with real source-style links and notice',()=>{
  const result=classify(topic(`<div><p>Information for this drug is presented separately based upon the following methods of administration:</p></div><div class="sec_xr rmolist"><ul><li>${link('10814','Azelastine (nasal)')}</li><li>${link('10890','Azelastine (ophthalmic)')}</li></ul></div>`));
  assert.equal(result.kind,'directory');assert.equal(result.links.length,2);assert.equal(result.links[0].id,'10814');
});
test('recognizes a link-only formulation directory, including operation-only destinations',()=>{
  const result=classify(topic(`<div><h2></h2></div><ul><li><a onclick="doOperation({contentId:'10066'})">Potassium citrate and citric acid</a></li><li>${link('9930','Sodium citrate and citric acid')}</li></ul>`,'Oral citrate formulations: Drug information'));
  assert.equal(result.kind,'directory');assert.equal(result.links[0].id,'10066');assert.equal(result.links[1].id,'9930');
});
test('retains short real articles, external-link lists and incomplete HTML as articles',()=>{
  for(const body of [
    `<p>Continue treatment and monitor symptoms.</p><ul><li>${link('10','Option one')}</li><li>${link('20','Option two')}</li></ul>`,
    '<ul><li><a href="https://outside.invalid">External reference</a></li><li>'+link('10','Source')+'</li></ul>',
    '<p>Body with two unrelated references.</p>'+link('10','One')+link('20','Two'),
  ])assert.equal(classify(topic(body)).kind,'article');
  assert.equal(classify({title:'Short article',body_html:'<div id="topicText"><ul><li>'+link('10','One')+'</li><li>'+link('20','Two')+'</li></ul>'}).kind,'article');
});
test('only explicit calculators with forms enter the calculator surface',()=>{
  assert.equal(classify(topic('<form><input></form>','Calculator: FIB-4 index')).kind,'calculator');
  assert.equal(classify(topic('<form><input></form>','Overview of a calculator')).kind,'article');
  assert.equal(classify(topic('<p>Form unavailable.</p>','Calculator: Missing form')).kind,'article');
});
test('calculator page keeps local equations and controls, blocks remote assets and uses app colors',()=>{
  const html=page('<body><script src="https://outside.invalid/code.js"></script><script>function calculate(){return 42}</script><form><input type="number" name="Age_param" onchange="calculate()"></form><script>undefined</script></body>',{
    cardBg:'#fff',ink:'#14201d',muted:'#5f6b68',accent:'#0f5c52',onAccent:'#fff',softBg:'#f7f5ef',trackBg:'#e0dbd1',
  });
  assert.match(html,/function calculate\(\)\{return 42\}/);assert.match(html,/onchange="calculate\(\)"/);
  assert.ok(!html.includes('https://outside.invalid'));assert.ok(!html.includes('<script>undefined</script>'));
  assert.match(html,/connect-src 'none'/);assert.match(html,/form-action 'none'/);assert.match(html,/frame-src 'none'/);
  assert.ok(!html.includes("'unsafe-eval'"));assert.ok(!html.includes('allow-same-origin'));
  assert.match(html,/background:#0f5c52/);
});
