const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const { test } = require('node:test');

function client(chunks) {
  const requested = [];
  const bytes = new TextEncoder().encode(chunks);
  const context = { exports: {}, AbortController, TextDecoder, setTimeout, clearTimeout,
    require(name) {
      assert.equal(name, './client');
      return { apiClient: {}, authenticatedStream: async (url, signal) => {
        requested.push(url);
        return { headers: new Headers({ 'content-type': 'application/x-ndjson' }),
          body: new ReadableStream({ start(controller) {
            // Split even inside Persian UTF-8 characters and JSON tokens.
            for (let n = 0; n < bytes.length; n++) controller.enqueue(bytes.slice(n, n + 1));
            controller.close();
          } }) };
      } };
    } };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/api/aiLab.ts'), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText, context);
  return { api: context.exports.aiLabApi, requested };
}

test('incremental NDJSON preserves split Persian UTF-8 and resumes with GET on the same job', async () => {
  const rows = [{ type: 'answer_delta', sequence: 2, part_index: 0, text: 'پاسخ فارسی' },
    { type: 'complete', sequence: 3, job: { status: 'complete', result: { parts: [] } } }];
  const { api, requested } = client(rows.map(row => JSON.stringify(row)).join('\n') + '\n');
  const received = [];
  await api.stream('existing-job', 1, new AbortController().signal, row => received.push(row));
  assert.deepEqual(JSON.parse(JSON.stringify(received)), rows);
  assert.deepEqual(requested, ['/ai-lab/results/existing-job/stream/?after_sequence=1']);
});

test('an incomplete disconnected event cannot become an answer or start a paid POST', async () => {
  const { api, requested } = client('{"type":"complete","sequence":1');
  const received = [];
  await assert.rejects(api.stream('existing-job', undefined, new AbortController().signal, row => received.push(row)), /Incomplete stream event/);
  assert.equal(received.length, 0);
  assert.equal(requested.length, 1);
});

test('invalid event sequence is rejected before applying it to conversation state', async () => {
  const { api } = client('{"type":"heartbeat","sequence":-1}\n');
  let applied = false;
  await assert.rejects(api.stream('existing-job', 0, new AbortController().signal, () => { applied = true; }), /Invalid stream event/);
  assert.equal(applied, false);
});
