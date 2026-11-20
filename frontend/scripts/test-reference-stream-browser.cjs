/* Local UI fixture, zero model calls. Uses a private temporary app account. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { spawn } = require('node:child_process');
const WebSocket = require('ws');
const assert = require('node:assert/strict');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, timeout = 20000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { if (await fn()) return; await delay(50); }
  throw Error('UI_FIXTURE_TIMEOUT');
}
async function main() {
  const accountPath = path.resolve('../backend/.private/hybrid-ui-account.json');
  assert.equal(fs.statSync(accountPath).mode & 0o077, 0);
  const account = JSON.parse(fs.readFileSync(accountPath)).accounts[0];
  const root = '/tmp/pharmenta-hybrid-ui-export';
  const output = path.resolve('../backend/exports');
  const jobId = '00000000-0000-4000-8000-000000000001';
  const citation = { source_id: 'P1', source: 'uptodate', title: 'Source fixture', section: 'Source section',
    quote: 'Original reference text for UI transport verification.', summary_fa: '', content_hash: 'a'.repeat(64),
    context: [{ quote: 'Fixture indication:', source_anchor: 'fixture-context', ordinal: 1 }],
    verification: 'retrieved', target: { screen: 'uptodateArticle', params: { id: '2863' } },
    media: [{key:'table-fixture',kind:'table',title:'Sample table — UI fixture',article_id:'2863',content_hash:'a'.repeat(64)},
      {key:'image-fixture',kind:'image',title:'Sample image — UI fixture',article_id:'2863',content_hash:'a'.repeat(64)}] };
  const finding = { id: '0:2863:P1', sequence: 1, part_index: 0, question_fa: 'سؤال آزمایشی', article_id: '2863', citation };
  const excludedCitation = { ...citation, source_id: 'P2', title: 'Unused source fixture', quote: 'Excluded reference text.',
    target: { screen: 'uptodateArticle', params: { id: '2864' } } };
  const findings = [finding, { ...finding, id: '0:2864:P2', sequence: 2, article_id: '2864', citation: excludedCitation }];
  const initial = { status: 'running', stage: 'retrieving', findings: [], cancellable: true };
  const completed = { status: 'complete', cancellable: true, feedback_available: false, findings,
    result: { model: 'luna', pipeline: 'ui-fixture', warnings: [], stages: [], parts: [{ question_fa: 'سؤال آزمایشی',
      queries: ['fixture'], status: 'answered', overview_fa: 'پاسخ آزمایشی برای بررسی رابط استریم.',
      items: [{ ...citation, summary_fa: 'متن منبع آزمایشی', verification: 'verified' }] }] } };
  let finished = false, streamRequests = 0, askRequests = 0, purchase, creditBalance='100';
  const json = (res, value, status = 200) => { res.writeHead(status, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(value)); };
  const server = http.createServer((req, res) => {
    if (req.url.includes('/media/table-fixture/')) return json(res,{kind:'table',caption:'Sample table — UI fixture',
      html:'<table><thead><tr><th>Sample</th><th>Value</th><th>Note</th></tr></thead><tbody><tr><td rowspan="2">Source group</td><td>A</td><td rowspan="2">Merged note</td></tr><tr><td id="rowspan-neighbor">B</td></tr></tbody></table>',headers:[],rows:[]});
    if (req.url.includes('/media/image-fixture/')) return json(res,{kind:'image',caption:'Sample image — UI fixture',
      src:'data:image/svg+xml;base64,'+Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="180"><rect width="300" height="180" fill="#cbded4"/><circle cx="150" cy="90" r="45" fill="#0f5c52"/></svg>').toString('base64')});
    if (req.url.startsWith('/api/v1/ai-lab/')) {
      if (req.url.includes('/wallet/topups/')) {
        let body = ''; req.on('data', chunk => { body += chunk; });
        req.on('end', () => { purchase = JSON.parse(body); json(res, { order_id: 1, status: 'pending', payment_url: 'about:blank#credit-fixture' }, 201); });
        return;
      }
      if (req.url.includes('/wallet/history/')) return json(res, { transactions: [], pending: [], next_offset: null });
      if (req.url.includes('/wallet/')) return json(res, { balance: creditBalance, available: creditBalance, billing_enabled: true,
        pricing_ready: true, exhausted:Number(creditBalance)<=0,can_search: Number(creditBalance)>0, topups_enabled: true,
        packages: [{id:1,name:'بستهٔ ۱۰۰',credits:'100',price_toman:16200}, {id:2,name:'بستهٔ ۵۰۰',credits:'500',price_toman:81000},
          {id:3,name:'بستهٔ ۱۰۰۰',credits:'1000',price_toman:162000}], gateways: [{kind:'fake',name:'آزمون رابط'}], usage_30_days: { credits: '0' } });
      if (req.url.includes('/status/')) return json(res, { enabled: true, models: { luna: 'fixture' }, sources: { uptodate: 'UpToDate' } });
      if (req.url.includes('/active/')) return json(res, { active_job: null });
      if (req.url.includes('/ask/')) { askRequests++; req.resume(); return json(res, { job_id: jobId }, 202); }
      if (req.url.includes('/stream/')) {
        streamRequests++;
        res.writeHead(200, { 'Content-Type': 'application/x-ndjson', 'Cache-Control': 'no-store', 'Content-Encoding': 'identity' });
        res.write(JSON.stringify({ type: 'snapshot', sequence: 1, job: initial }) + '\n');
        const first = setTimeout(() => res.write(JSON.stringify({ type: 'sources', sequence: 2, findings }) + '\n'), 200);
        const final = setTimeout(() => { finished = true; res.end(JSON.stringify({ type: 'complete', sequence: 3, job: completed }) + '\n'); }, 4000);
        res.on('close', () => { clearTimeout(first); clearTimeout(final); });
        return;
      }
      return json(res, finished ? completed : { ...initial, findings });
    }
    if (req.url.startsWith('/api/')) {
      const upstream = http.request({ hostname: '127.0.0.1', port: 8000, path: req.url, method: req.method,
        headers: { ...req.headers, host: '127.0.0.1:8000' } }, response => { res.writeHead(response.statusCode, response.headers); response.pipe(res); });
      upstream.on('error', () => json(res, {}, 503)); req.pipe(upstream); return;
    }
    let file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname);
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(root, 'index.html');
    const mime = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.ttf': 'font/ttf', '.png': 'image/png', '.css': 'text/css' };
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' }); fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(8004, '127.0.0.1', resolve));
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'hybrid-ui-fixture-'));
  const chrome = spawn('/usr/bin/google-chrome', ['--headless=new', '--disable-dev-shm-usage', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
  let ws;
  let stage = 'CONNECT';
  let debugCapture;
  try {
    await until(() => fs.existsSync(path.join(profile, 'DevToolsActivePort')));
    const [port, endpoint] = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').trim().split('\n');
    ws = new WebSocket(`ws://127.0.0.1:${port}${endpoint}`);
    await new Promise(resolve => ws.once('open', resolve));
    let next = 0, session;
    const callbacks = new Map();
    const send = (method, params = {}, sid = session) => new Promise((resolve, reject) => {
      const id = ++next; const timer = setTimeout(() => { callbacks.delete(id); reject(Error('CDP_TIMEOUT')); }, 15000);
      callbacks.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params, ...(sid ? { sessionId: sid } : {}) }));
    });
    ws.on('message', raw => { const msg = JSON.parse(String(raw));
      if(msg.method==='Fetch.requestPaused'){
        void send('Fetch.fulfillRequest',{requestId:msg.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],
          body:Buffer.from(JSON.stringify({ok:true,id:jobId,target:'both',summary_fa:'پیشنهاد ویرایش آزمایشی',summary_en:'Edited UI fixture',notes:'پیشنهاد آزمایشی؛ دادهٔ واقعی نیست.'})).toString('base64')},msg.sessionId);
        return;
      }
      const cb = callbacks.get(msg.id); if (cb) {
      callbacks.delete(msg.id); clearTimeout(cb.timer); msg.error ? cb.reject(Error('CDP_FAILED')) : cb.resolve(msg.result);
    } });
    const target = await send('Target.createTarget', { url: 'about:blank' }, null);
    session = (await send('Target.attachToTarget', { targetId: target.targetId, flatten: true }, null)).sessionId;
    await send('Page.enable'); await send('Runtime.enable');
    await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    const authInjection = await send('Page.addScriptToEvaluateOnNewDocument', { source: `if(location.origin==='http://127.0.0.1:8004'){for(const [k,v] of Object.entries(${JSON.stringify({ 'pharmexa.access': account.access_token, 'pharmexa.refresh': account.refresh_token, 'pharmexa.session': account.session_id, 'pharmexa.toursSeen.v1': '["home","calculator"]' })}))localStorage.setItem(k,v);}` });
    const evaluate = async expression => (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result.value;
    const clickText = text => evaluate(`[...document.querySelectorAll('[role=button],button')].find(e=>e.textContent.includes(${JSON.stringify(text)}))?.click()`);
    debugCapture = async () => {
      const screenshot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(path.join(output, 'hybrid-ui-failed.png'), Buffer.from(screenshot.data, 'base64'), { mode: 0o600 });
      console.error(await evaluate(`JSON.stringify([...document.querySelectorAll('[role=button],button')].map(e=>e.textContent.slice(0,80)))`));
    };
    stage = 'HOME';
    await send('Page.navigate', { url: 'http://127.0.0.1:8004' });
    await until(() => evaluate(`Boolean([...document.querySelectorAll('[role=button],button')].find(e=>e.textContent.includes('سرچ هوشمند')))`));
    await evaluate(`[...document.querySelectorAll('[role=button],button')].find(e=>e.textContent.includes('سرچ هوشمند')).click()`);
    stage = 'SEARCH';
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-question]'))`));
    assert.equal(await evaluate(`Boolean(document.querySelector('[data-testid=smart-search-wallet]'))`), true);
    await until(() => evaluate(`document.querySelector('[data-testid=search-credit-balance]').textContent.includes('۱۰۰')`));
    assert.equal(await evaluate(`document.querySelector('[data-testid=smart-search-wallet]').textContent.includes('توکن')`), false);
    assert.equal(await evaluate(`getComputedStyle(document.querySelector('[data-testid=search-credit-manage]')).backgroundColor`), 'rgb(15, 92, 82)');
    await evaluate(`(()=>{const e=document.querySelector('[data-testid=reference-question]');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,'سؤال آزمایشی درباره منابع');e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
    await until(() => evaluate(`document.querySelector('[data-testid=reference-send]').getAttribute('aria-disabled')!=='true'`));
    await evaluate(`document.querySelector('[data-testid=reference-send]').click()`);
    stage = 'SOURCES';
    await until(() => evaluate(`document.querySelectorAll('[data-testid=reference-source]').length===2`));
    assert.equal(await evaluate(`Boolean(document.querySelector('[data-testid=reference-answer-skeleton]'))`), true);
    assert.equal(await evaluate(`Boolean(document.querySelector('[data-testid=reference-final-answer]'))`), false);
    assert.equal(await evaluate(`Boolean(document.querySelector('[data-testid=reference-citation]'))`), false);
    const shot = async name => { await delay(350); const screenshot = await send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(path.join(output, name), Buffer.from(screenshot.data, 'base64'), { mode: 0o600 }); };
    await shot('hybrid-ui-pending.png');
    stage = 'FINAL';
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-final-answer]'))`));
    assert.equal(await evaluate(`Boolean(document.querySelector('[data-testid=reference-answer-skeleton]'))`), false);
    assert.equal(await evaluate(`document.querySelectorAll('[data-testid=reference-source]').length`), 1);
    assert.equal(await evaluate(`document.querySelector('[data-testid=reference-sources-toggle]').getAttribute('aria-expanded')`), 'false');
    assert.equal(await evaluate(`Boolean(document.querySelector('[data-testid=reference-source-passages]'))`), false);
    assert.equal(await evaluate(`document.body.textContent.includes('Unused source fixture')`), false);
    assert.equal(await evaluate(`document.querySelector('[data-testid=reference-primary-media]').compareDocumentPosition(document.querySelector('[data-testid=reference-answer-summary]')) & Node.DOCUMENT_POSITION_FOLLOWING`),4);
    assert.equal(await evaluate(`document.querySelector('[data-testid=reference-answer-summary]').compareDocumentPosition(document.querySelector('[data-testid=reference-source-results]')) & Node.DOCUMENT_POSITION_FOLLOWING`),4);
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-media] iframe'))`));
    await evaluate(`document.querySelectorAll('[data-testid=reference-media] [role=tab]')[1].click()`);
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-media] img'))`));
    await shot('hybrid-ui-media-image.png');
    await evaluate(`document.querySelectorAll('[data-testid=reference-media] [role=tab]')[0].click()`);
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-media] iframe'))`));
    await shot('hybrid-ui-final-collapsed.png');
    await evaluate(`document.querySelector('[data-testid=reference-answer-summary]').scrollIntoView({block:'center'})`);
    await shot('hybrid-ui-answer-last.png');
    await evaluate(`[...document.querySelectorAll('*')].find(e=>e.textContent==='☾'&&!e.children.length)?.click()`);
    await delay(100);
    await shot('hybrid-ui-answer-dark.png');
    await evaluate(`[...document.querySelectorAll('*')].find(e=>e.textContent==='☀'&&!e.children.length)?.click()`);
    await evaluate(`document.querySelector('[data-testid=reference-sources-toggle]').click()`);
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-citation]'))`));
    assert.equal(await evaluate(`document.querySelector('[data-testid=reference-sources-toggle]').getAttribute('aria-expanded')`), 'true');
    assert.equal(await evaluate(`document.body.textContent.includes('Excluded reference text.')`), false);
    await evaluate(`document.querySelector('[data-testid=reference-citation] [role=button]').click()`);
    await until(() => evaluate(`document.querySelector('[data-testid=reference-citation]').textContent.includes('Fixture indication:')`));
    await shot('hybrid-ui-final.png');
    await evaluate(`document.querySelector('[data-testid=reference-sources-toggle]').click()`);
    await until(() => evaluate(`!document.querySelector('[data-testid=reference-source-passages]')`));
    await evaluate(`document.querySelector('[data-testid=search-credit-manage]').click()`);
    await until(() => evaluate(`Boolean(document.querySelector('[aria-label="بستن مدیریت اعتبار"]'))`));
    // React Native Web mounts before its 300 ms modal fade finishes.
    await delay(350);
    assert.equal(await evaluate(`document.querySelectorAll('[data-testid^=search-credit-package-]').length`),3);
    assert.equal(await evaluate(`document.querySelector('[aria-modal=true]').textContent.includes('توکن')`),false);
    await evaluate(`document.querySelector('[data-testid=search-credit-package-3]').click()`);
    await until(() => evaluate(`document.querySelector('[data-testid=search-credit-buy]').textContent.includes('۱٬۰۰۰')`));
    await shot('hybrid-ui-credit-wallet.png');
    await evaluate(`document.querySelector('[data-testid=search-credit-buy]').click()`);
    await until(() => Boolean(purchase));
    assert.equal(purchase.package_id,3);assert.equal(purchase.expected_price_toman,162000);
    await evaluate(`document.querySelector('[aria-label="بستن مدیریت اعتبار"]').click()`);
    stage='CREDIT_EXHAUSTED';
    await evaluate(`(()=>{const e=document.querySelector('[data-testid=reference-question]');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,'پرسش بعدی آزمایشی');e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
    await until(()=>evaluate(`document.querySelector('[data-testid=reference-send]').getAttribute('aria-disabled')!=='true'`));
    creditBalance='0.2';
    await evaluate(`document.querySelector('[data-testid=search-credit-manage]').click()`);await delay(350);
    await clickText('به‌روزرسانی');
    await until(()=>evaluate(`document.querySelector('[data-testid=search-credit-balance]').textContent.includes('۱')&&!document.querySelector('[data-testid=search-credit-balance]').textContent.includes('۱۰۰')`));
    assert.equal(await evaluate(`document.querySelector('[data-testid=search-credit-balance]').textContent.includes('٫')`),false);
    creditBalance='-0.2';await clickText('به‌روزرسانی');
    await until(()=>evaluate(`document.querySelector('[data-testid=reference-send]').getAttribute('aria-disabled')==='true'`));
    await evaluate(`document.querySelector('[aria-label="بستن مدیریت اعتبار"]').click()`);
    await until(()=>evaluate(`document.querySelector('[data-testid=search-credit-warning]').textContent.includes('تمام شده')`));
    await shot('smart-search-credit-exhausted.png');
    await evaluate(`document.querySelector('[data-testid=reference-send]').click()`);assert.equal(askRequests,1);
    creditBalance='100';await evaluate(`document.querySelector('[data-testid=search-credit-manage]').click()`);await delay(350);await clickText('به‌روزرسانی');
    await until(()=>evaluate(`document.querySelector('[data-testid=search-credit-balance]').textContent.includes('۱۰۰')`));
    await evaluate(`document.querySelector('[aria-label="بستن مدیریت اعتبار"]').click()`);
    stage = 'ARTICLE_PDF';
    await evaluate(`document.querySelector('[data-testid=reference-source]').click()`);
    await until(() => evaluate(`Boolean(document.querySelector('[aria-label="خروجی PDF مقاله"]'))`));
    await delay(500);
    await shot('uptodate-article-pdf-action.png');
    assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth+1`),true);
    const downloads = fs.mkdtempSync(path.join(os.tmpdir(),'pharmenta-pdf-fixture-'));
    try {
      await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloads},null);
      await evaluate(`document.querySelector('[aria-label="خروجی PDF مقاله"]').click()`);
      await until(() => fs.readdirSync(downloads).some(name => name.endsWith('.pdf')),20000);
      const pdf = fs.readFileSync(path.join(downloads,fs.readdirSync(downloads).find(name=>name.endsWith('.pdf'))));
      assert.equal(pdf.subarray(0,4).toString(),'%PDF');
    } finally { fs.rmSync(downloads,{recursive:true,force:true}); }
    await clickText('›');
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-question]'))`));
    stage = 'CLINICAL';
    await clickText('›');
    await clickText('رد شدن');
    stage = 'CLINICAL_HOME';
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=home-path-clinical]'))`));
    await shot('home-two-gateways.png');
    await evaluate(`document.querySelector('[data-testid=home-path-clinical]').click()`);
    stage = 'CLINICAL_HUB';
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=clinical-paths]'))`));
    assert.equal(await evaluate(`document.querySelectorAll('[data-testid=clinical-paths] [role=button]').length`),3);
    await shot('clinical-gateway.png');
    await clickText('ماشین‌حساب');
    stage = 'CLINICAL_CALCULATORS';
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=frequent-calculators]'))`));
    assert.equal(await evaluate(`document.querySelector('[data-testid=frequent-calculators]').textContent.includes('تنظیم دوز اطفال')`),true);
    assert.equal(await evaluate(`document.querySelector('[data-testid=frequent-calculators]').children.length`),4);
    await shot('frequent-calculators.png');
    assert.equal(askRequests, 1); assert.equal(streamRequests, 1);
    if (account.admin_cookie) {
      stage = 'ADMIN';
      await send('Network.setCookie', { name: account.admin_cookie.name, value: account.admin_cookie.value, url: 'http://127.0.0.1:8000/', httpOnly: true });
      await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1080, deviceScaleFactor: 1, mobile: false });
      await send('Page.navigate', { url: 'http://127.0.0.1:8000/manage/app/search-credit/' });
      await until(() => evaluate(`Boolean(document.querySelector('[data-testid=credit-settings-form]'))`));
      await until(() => evaluate(`getComputedStyle(document.querySelector('.credit-heading')).display==='flex'`));
      assert.equal(await evaluate(`document.querySelectorAll('[data-testid=credit-settings-form] input:not([type=hidden]):not([type=checkbox]):not(.fld)').length`),0);
      assert.equal(await evaluate(`document.querySelectorAll('.credit-package').length>=3`),true);
      assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth+1`),true);
      await shot('search-credit-admin-light.png');
      await evaluate(`document.documentElement.setAttribute('data-theme','dark')`);
      await delay(100);await shot('search-credit-admin-dark.png');
      await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
      assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth+1`),true);
      await shot('search-credit-admin-mobile.png');
      stage='DQC_AI';
      await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
      await send('Page.navigate',{url:'http://127.0.0.1:8000/manage/data/ai-settings/'});
      await until(()=>evaluate(`Boolean(document.querySelector('[data-testid=dqc-ai-settings]'))`));
      assert.equal(await evaluate(`document.querySelector('[name=config-api_key]').value`),'');
      await shot('dqc-ai-settings.png');
      await send('Page.navigate',{url:'http://127.0.0.1:8000/manage/data/drugs/'+account.dqc_slug+'/?field=dosage_and_administration'});
      await until(()=>evaluate(`document.getElementById('ai-editor')?.dataset.ready==='true'`));
      await send('Fetch.enable',{patterns:[{urlPattern:'*/manage/data/drugs/*/*/ai/',requestStage:'Request'}]});
      await evaluate(`document.querySelector('#ai-editor summary').click();document.getElementById('ai-instruction').value='ویرایش آزمایشی';document.getElementById('ai-run').click()`);
      await until(()=>evaluate(`document.getElementById('ai-preview').hidden===false`));
      assert.equal(await evaluate(`document.querySelector('[name=summary_fa]').value`),'خلاصهٔ اولیه');
      await shot('dqc-ai-preview.png');
      await evaluate(`document.getElementById('ai-apply').click()`);
      await until(()=>evaluate(`document.querySelector('[name=summary_fa]').value==='پیشنهاد ویرایش آزمایشی'`));
      await until(()=>evaluate(`document.getElementById('save-status').textContent.includes('پیش‌نویس خودکار ذخیره شد')`));
      await send('Fetch.disable');
      await shot('dqc-ai-draft.png');
      await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    }
    stage = 'EMAIL_LOGIN';
    await send('Page.removeScriptToEvaluateOnNewDocument', { identifier: authInjection.identifier });
    await send('Page.navigate',{url:'http://127.0.0.1:8004'});
    await until(() => evaluate(`document.readyState==='complete'`));
    await evaluate(`localStorage.removeItem('pharmexa.access');localStorage.removeItem('pharmexa.refresh');localStorage.removeItem('pharmexa.session');location.reload()`);
    await until(() => evaluate(`Boolean(document.querySelector('[data-testid=auth-methods]'))`));
    assert.equal(await evaluate(`document.querySelector('[data-testid=auth-method-mobile]').getAttribute('aria-selected')`),'true');
    await evaluate(`document.querySelector('[data-testid=auth-email-otp]').click()`);
    await until(() => evaluate(`document.body.textContent.includes('ارسال کد به ایمیل')`));
    await shot('email-otp-login.png');
    console.log('Browser fixture passed: original media then answer then sources, integer credit balance and negative-balance block, selected home/auth layouts, exactly three common calculators, PDF download, AI settings and reviewable quality draft; zero model calls and zero email sends.');
  } catch (error) {
    if (debugCapture) await debugCapture().catch(() => undefined);
    console.error('UI_FIXTURE_STAGE_' + stage);
    console.error(error.message);
    throw error;
  } finally {
    ws?.close(); chrome.kill('SIGTERM'); server.closeAllConnections(); server.close();
    await delay(300); fs.rmSync(profile, { recursive: true, force: true });
  }
}
main().catch(() => { console.error('REFERENCE_STREAM_BROWSER_FIXTURE_FAILED'); process.exitCode = 1; });
