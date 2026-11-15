// Screenshot the local review gallery; no app/backend/provider is contacted.
import { createServer } from 'node:http';
import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve, join, extname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { homedir } from 'node:os';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import vm from 'node:vm';

const directory = dirname(fileURLToPath(import.meta.url));
const repo = resolve(directory, '../../..');
const skill = process.env.TASTE_SKILL_ROOT || join(homedir(), '.agents/skills/design-taste-frontend');
const { Browser } = await import(pathToFileURL(join(skill, 'scripts/lib/cdp.mjs')).href);
const screenshots = join(directory, 'screenshots');
mkdirSync(screenshots, { recursive: true });
const mime = { '.html':'text/html; charset=utf-8', '.css':'text/css', '.js':'text/javascript', '.ttf':'font/ttf', '.png':'image/png' };
const server = createServer((req,res)=>{
  const url = new URL(req.url, 'http://localhost');
  const requested = decodeURIComponent(url.pathname);
  const allowed = requested.startsWith('/docs/designs/smart-search-2026-11/') || requested.startsWith('/frontend/node_modules/@expo-google-fonts/vazirmatn/');
  const file = resolve(repo, '.' + requested);
  if (!allowed || !file.startsWith(repo + '/') || !existsSync(file)) {res.writeHead(404);res.end();return;}
  res.writeHead(200, {'Content-Type':mime[extname(file)] || 'application/octet-stream','Cache-Control':'no-store'});
  res.end(readFileSync(file));
});
await new Promise(r=>server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}/docs/designs/smart-search-2026-11/index.html`;
let browser;
const report = { sample_data:true, provider_requests:0, variants:[], checks:[] };
try {
  browser = await Browser.launch();
  const page = await browser.newPage({width:390,height:844});
  const errors=[];
  browser.on(page.sessionId, 'Runtime.exceptionThrown', p=>errors.push(p.exceptionDetails.text));
  for (const group of ['home','search','content']) {
    const count = group === 'content' ? 4 : 5;
    for (let variant=1; variant<=count; variant++) {
      await page.goto(`${base}?group=${group}&variant=${variant}`, {settleMs:40});
      await page.eval('document.fonts.ready');
      assert.equal(await page.eval('document.fonts.check("600 14px Vazirmatn")'), true, 'Brand font unavailable');
      assert.equal(await page.eval('document.documentElement.scrollWidth <= innerWidth'), true, 'Page overflow');
      const result = await page.eval(() => ({
        suggestions:document.querySelectorAll('.suggestion').length,
        clipped:[...document.querySelectorAll('.phone-main')].map(el=>el.scrollHeight>el.clientHeight),
      }));
      if(group==='search') assert.equal(result.suggestions,4);
      await page.screenshot({path:join(screenshots, `${group}-${variant}.png`),format:'png'});
      report.variants.push({group,variant,...result});
      if (group === 'search') {
        const prefill = await page.eval(() => {
          const text = document.querySelector('.suggestion').dataset.question;
          document.querySelector('.suggestion').click();
          return {textMatches:document.querySelector('textarea').value===text, noAnswer:!document.querySelector('.answer')};
        });
        assert.deepEqual(prefill,{textMatches:true,noAnswer:true});
        await page.goto(`${base}?group=search&variant=${variant}&state=answer`, {settleMs:30});
        await page.eval('document.fonts.ready');
        assert.deepEqual(await page.eval(() => [...document.querySelector('.phone-main').children].filter(el=>el.matches('.media,.answer,.source-disclosure')).map(el=>el.className)), ['media','answer','source-disclosure']);
        const extra = await page.eval(() => {const el=document.querySelector('.phone-main');return Math.max(0,el.scrollHeight-el.clientHeight);});
        await page.setViewport({width:390,height:844+extra+8});
        await page.eval('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
        await page.screenshot({path:join(screenshots, `search-${variant}-answer.png`),format:'png'});
        await page.setViewport({width:390,height:844});
      }
      if (group === 'content') {
        await page.goto(`${base}?group=content&variant=${variant}&kind=calculator`, {settleMs:30});
        await page.eval('document.fonts.ready');
        await page.screenshot({path:join(screenshots, `content-${variant}-calculator.png`),format:'png'});
      }
    }
  }
  for (const [group,state,kind,name,width] of [
    ['home','empty','directory','home-comparison',1936],
    ['search','empty','directory','search-comparison',1936],
    ['search','answer','directory','search-answer-comparison',1936],
    ['content','empty','directory','content-comparison',1556],
    ['content','empty','calculator','calculator-comparison',1556],
  ]) {
    await page.setViewport({width,height:1020});
    await page.goto(`${base}?group=${group}&state=${state}&kind=${kind}&board=1`, {settleMs:40});
    await page.eval('document.fonts.ready');
    if(group === 'search' && state === 'answer') {
      const height=await page.eval(() => {
        const extra=Math.max(...[...document.querySelectorAll('.phone-main')].map(el=>Math.max(0,el.scrollHeight-el.clientHeight)));
        document.querySelectorAll('.phone').forEach(el=>el.style.height=(820+extra+8)+'px');
        return Math.ceil(document.getElementById('gallery').getBoundingClientRect().height);
      });
      await page.setViewport({width,height});
    }
    await page.eval('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    await page.screenshot({path:join(screenshots,`${name}.png`),format:'png'});
    assert.ok(readFileSync(join(screenshots,`${name}.png`)).length>20000, 'Blank comparison screenshot');
  }
  for (const width of [390,768,1440]) {
    for (const group of ['home','search','content']) {
      await page.setViewport({width,height:900});
      await page.goto(`${base}?group=${group}`,{settleMs:30});
      assert.equal(await page.eval('document.documentElement.scrollWidth <= innerWidth'),true,`${group}: ${width}px overflow`);
    }
  }
  await page.setViewport({width:390,height:844});
  for (const state of ['empty','answer','loading']) {
    await page.goto(`${base}?group=search&variant=1&state=${state}&theme=dark`,{settleMs:30});
    await page.eval('document.fonts.ready');
    await page.screenshot({path:join(screenshots,`search-1-${state}-dark.png`),format:'png'});
  }
  await page.goto(`${base}?group=search&variant=1&state=answer`,{settleMs:30});
  const interaction = await page.eval(() => {
    document.querySelector('.source-disclosure summary').click();
    const expanded=document.querySelector('.source-disclosure').open;
    document.querySelector('[data-action=feedback]').click();
    const feedback=document.querySelector('[data-action=feedback]').getAttribute('aria-pressed')==='true';
    document.querySelector('[data-action=table]').click();
    const table=document.querySelector('dialog').open;
    document.getElementById('close-dialog').click();
    document.querySelector('[data-action=wallet]').click();
    const packages=document.querySelector('dialog').querySelectorAll('[data-action=demo]').length;
    return {expanded,feedback,table,packages};
  });
  assert.deepEqual(interaction,{expanded:true,feedback:true,table:true,packages:3});
  // Capture before/after using the actual table renderer, with layout fixtures.
  const require=createRequire(join(repo,'frontend/package.json'));
  const ts=require('typescript');
  const before=execFileSync('rtk',['proxy','git','show','HEAD:frontend/src/utils/uptodateTables.ts'],{cwd:repo,encoding:'utf8'});
  const after=readFileSync(join(repo,'frontend/src/utils/uptodateTables.ts'),'utf8');
  for(const [name,source,viewer] of [['table-before',before,false],['table-after',after,false],['table-viewer',after,true]]) {
    const mod={exports:{}};
    vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{module:mod,exports:mod.exports});
    const t=mod.exports;
    const colors={ink:'#14201d',prose:'#2a3936',muted:'#5f6b68',bg:'#fff',accent:'#0f5c52',rule:'#26382e',accentSoft:'#d4dcd3'};
    const table='<table><thead><tr><th>Source section</th><th>Content</th><th>Related topic</th><th>Reference</th></tr></thead><tbody>'+Array.from({length:8},(_,i)=>`<tr><td>Section ${i+1}</td><td>Original text in the source</td><td>Related material</td><td>${i+1}</td></tr>`).join('')+'</tbody></table>';
    const options={labels:t.tableLabels(true),context:'article',...(viewer?{viewer:{index:0,title:'Source table'}}:{})};
    await page.setViewport({width:390,height:844});
    await page.goto('about:blank',{settleMs:10});
    await page.eval(({css,script,table,options})=>{
      document.open();
      document.write('<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><style>body{font:16px/1.8 sans-serif;padding:20px;margin:0;background:#fff;color:#14201d}h1{font-size:20px}p{font-size:13px}'+css+'</style><body><h1>نمایش جدول در مقاله</h1><p>نمونهٔ چیدمان؛ جدول درمانی نیست.</p>'+table+'<p>متن مقاله بعد از جدول ادامه دارد.</p><script>function __utdEmitOp(){};'+script+';__utdTablesInit('+JSON.stringify(options)+');</scr'+'ipt></body></html>');
      document.close();
    },{css:t.tableStyles(colors,false),script:t.TABLE_SCRIPT,table,options});
    await page.eval('document.fonts.ready');
    await page.eval('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    await page.screenshot({path:join(screenshots,`${name}.png`),format:'png'});
  }
  assert.deepEqual(errors,[]);
  report.checks=['14 design variants rendered with Vazirmatn', '4 suggestions per search variant', 'Suggestion selection only prefills input', 'Media → Persian answer → collapsed sources', 'Home/search/content layouts at 390, 768, 1440px', 'Source disclosure, feedback, table and wallet interactions', 'Dark empty/answer/loading states', 'No browser script exceptions'];
  writeFileSync(join(directory,'browser-check.json'),JSON.stringify(report,null,2)+'\n');
  console.log('Rendered 14 variants, answer/tool states and 5 comparison boards. All interaction checks passed.');
} finally {
  if(browser) await browser.close();
  await new Promise(r=>server.close(r));
}
