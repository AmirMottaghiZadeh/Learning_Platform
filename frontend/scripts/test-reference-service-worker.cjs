const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

function worker() {
  const listeners = {};
  const context = { URL, self: { registration: { scope: 'http://localhost/' },
    addEventListener: (name, callback) => { listeners[name] = callback; } } };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../public/sw.js'), 'utf8'), context);
  return listeners;
}

test('same-origin APIs, authenticated responses and NDJSON bypass shell caching', () => {
  const listeners = worker();
  for (const request of [
    new Request('http://localhost/api/v1/auth/me/'),
    new Request('http://localhost/api/v1/ai-lab/results/fixture/stream/', { headers: { Accept: 'application/x-ndjson' } }),
    new Request('http://localhost/private-reference', { headers: { Authorization: 'Bearer test-placeholder' } }),
    new Request('http://localhost/custom-stream', { headers: { Accept: 'application/x-ndjson' } }),
  ]) {
    let intercepted = false;
    listeners.fetch({ request, respondWith() { intercepted = true; } });
    assert.equal(intercepted, false);
  }
});
