const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const { test } = require('node:test');

function timing() {
  let clock = 0;
  const measurements = [];
  const context = { exports: {}, performance: { now: () => clock, measure: (name, options) => measurements.push({ name, ...options }) } };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/api/referenceTiming.ts'), 'utf8'),
    { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText, context);
  return { api: context.exports, measurements, tick: value => { clock = value; } };
}
test('visible titles or partial citations never count as a complete rendered answer', () => {
  const { api, measurements, tick } = timing();
  api.startReferenceTiming('opaque-id'); tick(100);
  api.noteReferenceRender('opaque-id', { status: 'running', titles: true, citation: true, answerComplete: false });
  assert.equal(measurements.length, 2);
  tick(200); api.noteReferenceRender('opaque-id', { status: 'complete', titles: true, citation: true, answerComplete: false });
  assert.equal(measurements.at(-1).name, 'pharmenta.reference.finished');
  assert.equal(measurements.at(-1).detail.answer_complete, false);
});
test('finish uses click-to-render elapsed time and records no content or credentials', () => {
  const { api, measurements, tick } = timing();
  api.startReferenceTiming('opaque-id'); tick(1250);
  api.noteReferenceRender('opaque-id', { status: 'complete', titles: true, citation: true, answerComplete: true });
  assert.equal(measurements.at(-1).detail.elapsed_ms, 1250);
  assert.equal(measurements.at(-1).detail.answer_complete, true);
  assert.deepEqual(Object.keys(measurements.at(-1).detail).sort(), ['answer_complete', 'elapsed_ms', 'status', 'turn_id']);
  api.noteReferenceRender('opaque-id', { status: 'complete', answerComplete: true });
  assert.equal(measurements.length, 3);
});
test('a recovered or cancelled request has no invented fresh start time', () => {
  const { api, measurements } = timing();
  api.noteReferenceRender('restored-id', { status: 'complete', answerComplete: true });
  api.startReferenceTiming('cancelled'); api.cancelReferenceTiming('cancelled');
  api.noteReferenceRender('cancelled', { status: 'complete', answerComplete: true });
  assert.equal(measurements.length, 0);
});
