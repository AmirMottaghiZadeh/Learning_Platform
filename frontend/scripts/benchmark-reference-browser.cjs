/* Real Chromium/Chrome UI timing via CDP. The account file and outputs stay private. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { createHash } = require('node:crypto');
const WebSocket = require('ws');
const args = Object.fromEntries(process.argv.slice(2).map(value => { const i = value.indexOf('='); return [value.slice(0, i), value.slice(i + 1)]; }));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, timeout = 30000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { const value = await fn(); if (value) return value; await delay(100); }
  throw Error('BROWSER_WAIT_TIMEOUT');
}
async function main() {
  const accountPath = args['--accounts'];
  if ((fs.statSync(accountPath).mode & 0o077) !== 0) throw Error('PRIVATE_ACCOUNT_FILE_REQUIRED');
  const accounts = JSON.parse(fs.readFileSync(accountPath, 'utf8')).accounts;
  const account = accounts[Number(args['--account-index'] ?? accounts.length - 1)];
  if (!account?.access_token?.startsWith('phx_access_') || !account.refresh_token) throw Error('INVALID_ACCOUNT_FILE');
  const app = new URL(args['--app']); const api = new URL(args['--api']);
  for (const url of [app, api]) if (!['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)) throw Error('LOCAL_BROWSER_DIAGNOSTIC_ONLY');
  const dataset = JSON.parse(fs.readFileSync(path.join(__dirname, '../../backend/apps/ai_lab/benchmark/cases.json'), 'utf8'));
  const plans = JSON.parse(fs.readFileSync(path.join(__dirname, '../../backend/apps/ai_lab/benchmark/lexical_cases.json'), 'utf8')).plans;
  const selected = plans.slice(0, Number(args['--limit'] ?? 10)).map(plan => dataset.cases.find(c => c.id === plan.case_id));
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'reference-browser-'));
  const chrome = spawn(args['--chrome'] || '/usr/bin/google-chrome', ['--headless=new', '--disable-dev-shm-usage',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--remote-debugging-port=0',
    `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
  let ws; let debugEvaluate; let stage = 'CONNECT';
  try {
    const portFile = path.join(profile, 'DevToolsActivePort');
    await until(() => fs.existsSync(portFile), 15000);
    const [port, endpoint] = fs.readFileSync(portFile, 'utf8').trim().split('\n');
    ws = new WebSocket(`ws://127.0.0.1:${port}${endpoint}`);
    await new Promise((resolve, reject) => { ws.once('open', resolve); ws.once('error', reject); });
    let sequence = 0; const waiting = new Map(); let session; let job = null; let epoch = 0; const pendingBodies = new Set();
    function send(method, params = {}, sid = session) {
      return new Promise((resolve, reject) => {
        const id = ++sequence; const timer = setTimeout(() => { waiting.delete(id); reject(Error('CDP_TIMEOUT')); }, 30000);
        waiting.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params, ...(sid ? { sessionId: sid } : {}) }));
      });
    }
    ws.on('message', async raw => {
      const data = JSON.parse(String(raw));
      if (data.id && waiting.has(data.id)) { const callback = waiting.get(data.id); waiting.delete(data.id); clearTimeout(callback.timer);
        if (data.error) callback.reject(Error('CDP_COMMAND_FAILED')); else callback.resolve(data.result); return; }
      if (data.sessionId !== session) return;
      if (data.method === 'Network.responseReceived' && data.params.response.url.startsWith(api.href.replace(/\/$/, '') + '/ai-lab/results/')) pendingBodies.add(data.params.requestId);
      if (data.method === 'Network.loadingFinished' && pendingBodies.delete(data.params.requestId)) {
        const responseEpoch = epoch;
        try { const response = await send('Network.getResponseBody', { requestId: data.params.requestId });
          const value = JSON.parse(response.base64Encoded ? Buffer.from(response.body, 'base64').toString() : response.body);
          if (responseEpoch === epoch && ['complete', 'failed'].includes(value.status)) job = value;
        } catch { /* A missing body is recorded as missing evidence, never fabricated. */ }
      }
    });
    const target = await send('Target.createTarget', { url: 'about:blank' }, null);
    session = (await send('Target.attachToTarget', { targetId: target.targetId, flatten: true }, null)).sessionId;
    await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
    const stored = { 'pharmexa.access': account.access_token, 'pharmexa.refresh': account.refresh_token, 'pharmexa.session': account.session_id };
    await send('Page.addScriptToEvaluateOnNewDocument', { source: `if(location.origin===${JSON.stringify(app.origin)}&&!localStorage.getItem('pharmexa.refresh')){for(const [k,v] of Object.entries(${JSON.stringify(stored)}))localStorage.setItem(k,v);}` });
    const evaluate = async expression => (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result.value;
    debugEvaluate = evaluate;
    const runtimeResponse = await fetch(api.href.replace(/\/$/, '') + '/ai-lab/status/?diagnostics=1', { headers: { Authorization: `Bearer ${account.access_token}` }, redirect: 'error' });
    const runtime = (await runtimeResponse.json()).runtime;
    const reservation = runtime?.max_provider_requests ?? 12;
    if (!Number.isInteger(reservation) || reservation < 1 || reservation > 1000) throw Error('INVALID_SERVER_BUDGET');
    const runs = []; const journal = args['--output'] + '.progress.jsonl'; let coldAnswered = false; let used = 0; let bundleDigest;
    fs.writeFileSync(journal, '', { flag: 'wx', mode: 0o600 });
    for (const test of selected) for (const scenario of ['cold', 'hit']) {
      if (scenario === 'cold') coldAnswered = false;
      if (scenario === 'hit' && !coldAnswered) {
        runs.push({case_id:test.id,scenario,browser_elapsed_ms:0,rendered_answer_complete:false,job:{status:'skipped',error:{code:'NO_COMPLETE_COLD_ANSWER'}}});
        continue;
      }
      if (used + reservation > Number(args['--max-requests'] ?? 72)) break;
      job = null; epoch++; pendingBodies.clear();
      stage = 'NAVIGATE';
      await send('Page.navigate', { url: app.href });
      await until(async () => evaluate(`Boolean([...document.querySelectorAll('[role=button],button')].find(e=>e.textContent.includes('سرچ هوشمند')))`));
      if (!bundleDigest) {
        const bundleUrl = await evaluate(`[...document.scripts].map(s=>s.src).find(s=>s.includes('/_expo/static/js/web/index-'))`);
        const bundle = await fetch(bundleUrl, { redirect: 'error' });
        bundleDigest = createHash('sha256').update(Buffer.from(await bundle.arrayBuffer())).digest('hex');
      }
      await evaluate(`[...document.querySelectorAll('[role=button],button')].find(e=>e.textContent.includes('سرچ هوشمند')).click()`);
      stage = 'OPEN_SEARCH';
      await until(async () => evaluate(`Boolean(document.querySelector('[data-testid=reference-question]'))`));
      await evaluate(`(()=>{const e=document.querySelector('[data-testid=reference-question]');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(test.question)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
      stage = 'DRAFT';
      await until(async () => evaluate(`(()=>{const e=document.querySelector('[data-testid=reference-send]');return e&&e.getAttribute('aria-disabled')!=='true';})()`));
      if (args['--probe-only'] === 'true') { console.log('REFERENCE_BROWSER_UI_READY'); return; }
      await evaluate(`performance.clearMeasures('pharmenta.reference.finished');document.querySelector('[data-testid=reference-send]').click()`);
      stage = 'WAIT_RESULT';
      const measurement = await until(async () => evaluate(`(()=>{const m=performance.getEntriesByName('pharmenta.reference.finished').at(-1);return m?{elapsed:m.duration,detail:m.detail,citations:document.querySelectorAll('[data-testid=reference-final-answer] [data-testid=reference-citation]').length}:null;})()`), 40000);
      await until(() => job, 3000).catch(() => null);
      runs.push({ case_id: test.id, scenario, browser_elapsed_ms: measurement.elapsed,
        rendered_answer_complete: measurement.detail.answer_complete === true && measurement.citations > 0,
        rendered_citations: measurement.citations, job: job || { status: 'failed', error: { code: 'BROWSER_JOB_EVIDENCE_MISSING' } } });
      used += Number.isInteger(job?.metrics?.provider_requests) ? job.metrics.provider_requests : reservation;
      if (scenario === 'cold') coldAnswered = measurement.detail.answer_complete === true && job?.status === 'complete';
      const serialized = JSON.stringify(runs.at(-1));
      if(serialized.includes(account.access_token)||/sk-[A-Za-z0-9_-]{16,}/.test(serialized))throw Error('UNSAFE_BROWSER_REPORT');
      fs.appendFileSync(journal, serialized + '\n');
      console.log(`Measured ${test.id} ${scenario}`);
    }
    const output = JSON.stringify({ schema: 1, kind: 'reference_browser_measurements', served_bundle_digest:bundleDigest,runtime_profile_digest: runtime?.profile_digest,provider_request_upper_bound_used:used, runs }, null, 2);
    if (output.includes(account.access_token) || /sk-[A-Za-z0-9_-]{16,}/.test(output)) throw Error('UNSAFE_BROWSER_REPORT');
    fs.writeFileSync(args['--output'], output + '\n', { flag: 'wx', mode: 0o600 });
  } catch (error) {
    if (debugEvaluate) {
      try { const text = await debugEvaluate('document.body.innerText');
        if (typeof text === 'string' && !text.includes(account.access_token) && !/sk-[A-Za-z0-9_-]{16,}/.test(text))
          fs.writeFileSync(args['--output'] + '.diagnostic.txt', stage + '\n' + text, { flag: 'wx', mode: 0o600 });
      } catch { /* Keep debugging output private and optional. */ }
    }
    throw Error(`REFERENCE_BROWSER_${stage}_FAILED`);
  } finally {
    if (ws) ws.close(); chrome.kill('SIGTERM');
    await delay(300); fs.rmSync(profile, { recursive: true, force: true });
  }
}
main().catch(error => { console.error(/^[A-Z_]+$/.test(error.message) ? error.message : 'REFERENCE_BROWSER_FAILED'); process.exitCode = 1; });
