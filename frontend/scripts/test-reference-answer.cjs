const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const { test } = require('node:test');
const context = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/utils/referenceAnswer.ts'), 'utf8'),
  { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText, context);
const { answerSegments, answerFollowOffset } = context.exports;
const segments = text => JSON.parse(JSON.stringify(answerSegments(text)));

test('Persian and English emphasis keeps exact content and becomes bold without delimiters', () => {
  assert.deepEqual(segments('داروی **Fixturemed** و **دوز مصرف**.'), [
    { text: 'داروی ', bold: false }, { text: 'Fixturemed', bold: true },
    { text: ' و ', bold: false }, { text: 'دوز مصرف', bold: true }, { text: '.', bold: false },
  ]);
});
test('unfinished emphasis remains visible while its closing delimiter is still streaming', () => {
  assert.deepEqual(segments('متن **بخش در حال'), [{ text: 'متن ', bold: false }, { text: 'بخش در حال', bold: true }]);
  assert.equal(segments('**').length, 0);
  assert.equal(segments('شروع **بخش** ادامه').map(s => s.text).join(''), 'شروع بخش ادامه');
});
test('escaped stars, arithmetic, line breaks and HTML-like strings remain literal text', () => {
  const value = '2 * 3\n\\*\\*literal\\*\\* <script>alert(1)</script>';
  assert.equal(segments(value).map(s => s.text).join(''), '2 * 3\n**literal** <script>alert(1)</script>');
  assert.ok(segments(value).every(s => !s.bold));
});
test('short answers stay at their beginning and long answers follow their own tail', () => {
  assert.equal(answerFollowOffset(200, 120, 600), 188);
  assert.equal(answerFollowOffset(200, 900, 600), 520);
  assert.equal(answerFollowOffset(0, 50, 600), 0);
  // Source-card height is deliberately absent from the calculation.
});
