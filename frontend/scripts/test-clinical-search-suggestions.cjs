const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const source = fs.readFileSync(path.join(__dirname, '../src/data/clinicalSearchSuggestions.ts'), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const mod = { exports: {} };
vm.runInNewContext(compiled, { module: mod, exports: mod.exports });
const { CLINICAL_SEARCH_SUGGESTIONS: bank, pickClinicalSearchSuggestions: pick } = mod.exports;

test('the bilingual bank covers 16 clinical areas with no duplicate questions', () => {
  assert.equal(bank.length, 80);
  assert.equal(new Set(bank.map(q => q.category)).size, 16);
  for (const key of ['id', 'fa', 'en']) {
    assert.equal(new Set(bank.map(q => q[key])).size, bank.length);
    assert.ok(bank.every(q => q[key].trim()));
  }
});

test('each entry gets four different questions from four different areas', () => {
  const original = JSON.stringify(bank);
  for (const random of [() => 0, () => 0.5, () => 0.999999]) {
    const picked = pick(4, random);
    assert.equal(picked.length, 4);
    assert.equal(new Set(picked.map(q => q.id)).size, 4);
    assert.equal(new Set(picked.map(q => q.category)).size, 4);
    assert.ok(picked.every(q => bank.some(item => item.id === q.id && item.fa === q.fa && item.en === q.en)));
  }
  assert.equal(JSON.stringify(bank), original);
  assert.notEqual(JSON.stringify(pick(4, () => 0)), JSON.stringify(pick(4, () => 0.999999)));
});
