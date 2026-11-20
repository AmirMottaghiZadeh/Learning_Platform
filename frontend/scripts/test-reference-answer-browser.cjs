/* Actual web export + synthetic streaming API. No accounts, DB or model calls. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { spawn } = require('node:child_process');
const WebSocket = require('ws');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, timeout = 20000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { const value = await fn(); if (value) return value; await delay(50); }
  throw Error('ANSWER_UI_TIMEOUT');
}
async function main() {
  const root = path.resolve('dist');
  const output = path.resolve('../backend/exports/reference-answer-ui');
  fs.mkdirSync(output, { recursive: true, mode: 0o700 });
  const jobId = '00000000-0000-4000-8000-000000000001';
  const question = 'پرسش آزمایشی برای بررسی نمایش پاسخ';
  const parts = ['**بخش برجسته**\n\n', ...Array.from({ length: 40 }, (_, i) => `متن آزمایشی شماره ${i + 1} برای بررسی دنبال‌کردن پاسخ در حال تولید و نمایش لحظه‌ای آن.\n\n`)];
  const citations = Array.from({ length: 16 }, (_, i) => ({ source_id: `P${i + 1}`, source: 'uptodate', title: `Source fixture ${i + 1}`,
    section: 'Fixture', quote: 'UI fixture source text.', summary_fa: '', content_hash: 'a'.repeat(64), verification: 'retrieved',
    target: { screen: 'uptodateArticle', params: { id: String(i + 1) } } }));
  const findings = citations.map((citation, i) => ({ id: `0:${i + 1}:P${i + 1}`, sequence: i + 1, part_index: 0, question_fa: question, article_id: String(i + 1), citation }));
  let finished = false;
  const initial = { status: 'running', stage: 'answering', findings: [], cancellable: true };
  const complete = { status: 'complete', result: { model: 'luna', pipeline: 'ui-fixture', warnings: [], stages: [], parts: [{
    question_fa: question, status: 'answered', overview_fa: parts.join(''), items: [{ ...citations[0], verification: 'verified' }],
  }] } };
  const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', '*');
    res.setHeader('Access-Control-Allow-Methods', '*');
    if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
    const json = value => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(value)); };
    if (req.url.includes('/api/v1/')) {
      if (req.url.includes('/auth/me/')) return json({ id: 900001, username: 'ui-fixture', has_password: true, roles: ['superuser'],
        profile: { display_name: 'آزمون رابط', is_onboarded: true, language: 'fa', study_field: 'medicine', study_goal: 'clinical', study_level: 'advanced' } });
      if (req.url.includes('/me/dashboard/')) return json({ greeting_name: 'آزمون', streak_days: 0, xp: 0, next_chapter: null, focus_session: { rows: [], total_minutes: 0 } });
      if (req.url.includes('/me/plan/')) return json({ mode: 'none' });
      if (req.url.includes('/announcements/')) return json([]);
      if (req.url.includes('/billing/me/')) return json({ features: [], current: null, modules: [] });
      if (req.url.includes('/wallet/')) return json({ balance: '100', available: '100', can_search: true, billing_enabled: false, packages: [], gateways: [], usage_30_days: { credits: '0' } });
      if (req.url.includes('/ai-lab/status/')) return json({ enabled: true });
      if (req.url.includes('/ai-lab/active/')) return json({ active_job: null });
      if (req.url.includes('/ai-lab/ask/')) { finished = false; req.resume(); res.statusCode = 202; return json({ job_id: jobId }); }
      if (req.url.includes('/stream/')) {
        res.setHeader('Content-Type', 'application/x-ndjson');
        res.setHeader('Cache-Control', 'no-store');
        let sequence = 0, index = 0;
        const write = event => res.write(JSON.stringify({ ...event, sequence: ++sequence }) + '\n');
        write({ type: 'snapshot', job: initial });
        write({ type: 'sources', findings });
        const timer = setInterval(() => {
          if (index < parts.length) write({ type: 'answer_delta', part_index: 0, text: parts[index++] });
          else { clearInterval(timer); finished = true; write({ type: 'complete', job: complete }); res.end(); }
        }, 180);
        res.on('close', () => clearInterval(timer));
        return;
      }
      if (req.url.includes('/ai-lab/results/')) return json(finished ? complete : initial);
      return json({ results: [] });
    }
    let file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname);
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(root, 'index.html');
    const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.ttf': 'font/ttf' };
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'answer-ui-'));
  const chrome = spawn('/usr/bin/google-chrome', ['--headless=new', '--disable-dev-shm-usage', '--disable-background-timer-throttling',
    '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
  let ws, send, evaluate, session;
  try {
    await until(() => fs.existsSync(path.join(profile, 'DevToolsActivePort')));
    const [port, endpoint] = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').trim().split('\n');
    ws = new WebSocket(`ws://127.0.0.1:${port}${endpoint}`);
    await new Promise((resolve, reject) => { ws.once('open', resolve); ws.once('error', reject); });
    let sequence = 0;
    const waiting = new Map();
    send = (method, params = {}, sid = session) => new Promise((resolve, reject) => {
      const id = ++sequence;
      const timer = setTimeout(() => { waiting.delete(id); reject(Error('CDP_TIMEOUT')); }, 20000);
      waiting.set(id, { resolve, reject, timer });
      ws.send(JSON.stringify({ id, method, params, ...(sid ? { sessionId: sid } : {}) }));
    });
    ws.on('message', raw => {
      const msg = JSON.parse(String(raw));
      if (msg.method === 'Fetch.requestPaused') {
        const url = new URL(msg.params.request.url);
        void send('Fetch.continueRequest', { requestId: msg.params.requestId, url: origin + url.pathname + url.search }, msg.sessionId);
      }
      const item = waiting.get(msg.id);
      if (item) { waiting.delete(msg.id); clearTimeout(item.timer); msg.error ? item.reject(Error('CDP_FAILED')) : item.resolve(msg.result); }
    });
    const target = await send('Target.createTarget', { url: 'about:blank' }, null);
    session = (await send('Target.attachToTarget', { targetId: target.targetId, flatten: true }, null)).sessionId;
    await send('Page.enable'); await send('Runtime.enable');
    await send('Fetch.enable', { patterns: [{ urlPattern: '*/api/v1/*' }] });
    evaluate = async expression => {
      const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (r.exceptionDetails) throw Error('UI_EVALUATION_FAILED');
      return r.result.value;
    };
    await send('Page.addScriptToEvaluateOnNewDocument', { source: `if(location.origin===${JSON.stringify(origin)}){
      localStorage.setItem('pharmexa.access','fixture-access');localStorage.setItem('pharmexa.refresh','fixture-refresh');
      localStorage.setItem('pharmexa.session','fixture-session');localStorage.setItem('pharmexa.toursSeen.v1','["home","calculator"]');}` });
    const geometry = `(()=>{const e=document.querySelector('[data-testid=reference-answer-draft]');let p=e;
      while(p&&!(p.scrollHeight>p.clientHeight+10&&/auto|scroll/.test(getComputedStyle(p).overflowY)))p=p.parentElement;
      if(!e||!p)return null;const a=e.getBoundingClientRect(),b=p.getBoundingClientRect();return {tail:a.bottom,top:b.top,bottom:b.bottom,scroll:p.scrollTop,height:p.clientHeight};})()`;
    for (const [name, width, height] of [['iphone', 390, 844], ['mobile', 390, 844], ['desktop', 1280, 900]]) {
      const ios = name === 'iphone';
      await send('Emulation.setUserAgentOverride', { userAgent: ios
        ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1'
        : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36', platform: ios ? 'iPhone' : 'Linux x86_64' });
      await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: name !== 'desktop' });
      await send('Page.navigate', { url: origin });
      await until(() => evaluate(`Boolean([...document.querySelectorAll('[role=button],button')].find(e=>e.textContent.includes('سرچ هوشمند')))`));
      await evaluate(`[...document.querySelectorAll('[role=button],button')].find(e=>e.textContent.includes('سرچ هوشمند')).click()`);
      await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-question]'))`));
      const inputSize = await evaluate(`parseFloat(getComputedStyle(document.querySelector('[data-testid=reference-question]')).fontSize)`);
      assert.equal(inputSize, ios ? 16 : 14);
      assert.equal(await evaluate(`/maximum-scale|user-scalable/.test(document.querySelector('meta[name=viewport]').content)`), false);

      await evaluate(`(()=>{const e=document.querySelector('[data-testid=reference-question]');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(question)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
      await until(() => evaluate(`document.querySelector('[data-testid=reference-send]').getAttribute('aria-disabled')!=='true'`));
      await evaluate(`document.querySelector('[data-testid=reference-send]').click()`);
      await until(() => evaluate(`document.querySelector('[data-testid=reference-answer-draft]')?.textContent.length>600`));
      assert.equal(await evaluate(`document.querySelector('[data-testid=reference-answer-draft]').textContent.includes('**')`), false);
      assert.equal(await evaluate(`Boolean([...document.querySelector('[data-testid=reference-answer-draft]').children].find(e=>getComputedStyle(e).fontFamily.includes('700Bold')))`), true);
      // A streamed chunk can render just before the frame that follows it.
      const visibleTail = async () => {
        const box = await evaluate(geometry);
        return box && box.tail <= box.bottom + 1 && box.tail > box.top && box;
      };
      const box = await until(visibleTail, 600);
      await send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: width / 2, y: box.top + 100, deltaX: 0, deltaY: -240 });
      await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-follow-answer]'))`));
      await evaluate(`document.querySelector('[data-testid=reference-follow-answer]').click()`);
      await until(visibleTail, 600);
      const shot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(path.join(output, `${name}-stream.png`), Buffer.from(shot.data, 'base64'), { mode: 0o600 });
      await until(() => evaluate(`Boolean(document.querySelector('[data-testid=reference-final-answer]'))`));
      assert.equal(await evaluate(`document.querySelector('[data-testid=reference-answer-text]').textContent.includes('**')`), false);
      console.log(JSON.stringify({ surface: name, input_font_size: inputSize, streaming_tail_visible: true, bold_rendered: true, pause_resume: true }));
    }
  } catch (error) {
    if (send && session) {
      const shot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(path.join(output, 'failed.png'), Buffer.from(shot.data, 'base64'), { mode: 0o600 });
    }
    throw error;
  } finally {
    ws?.close(); chrome.kill(); server.closeAllConnections(); server.close();
    await delay(150); fs.rmSync(profile, { recursive: true, force: true });
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
