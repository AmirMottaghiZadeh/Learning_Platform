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
const errorContext = { exports: {} };
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/utils/referenceFailure.ts'), 'utf8'),
  { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText, errorContext);
const { referenceFailure } = errorContext.exports;
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

test('plan, quota and credit failures give different actions without blaming the connection', () => {
  assert.match(referenceFailure('PREMIUM_REQUIRED'), /پلن/);
  assert.match(referenceFailure('QUOTA_EXCEEDED'), /سهمیه/);
  assert.match(referenceFailure('AI_CREDIT_INSUFFICIENT'), /شارژ/);
  for (const code of ['PREMIUM_REQUIRED', 'QUOTA_EXCEEDED', 'AI_CREDIT_INSUFFICIENT']) {
    assert.doesNotMatch(referenceFailure(code), /اتصال/);
  }
});
test('invalid provider format is a response-processing problem, independent of HTTP status', () => {
  assert.match(referenceFailure('INVALID_PROVIDER_RESPONSE', 0), /قابل پردازش نبود/);
  assert.match(referenceFailure('INVALID_SEARCH_TOOL_ARGUMENTS'), /قابل پردازش نبود/);
  assert.doesNotMatch(referenceFailure('INVALID_PROVIDER_RESPONSE', 0), /اتصال/);
});
test('unknown errors do not expose upstream content or invent a connection cause', () => {
  const untrusted = 'private-provider-body-and-credential';
  const message = referenceFailure(untrusted);
  assert.ok(!message.includes(untrusted));
  assert.doesNotMatch(message, /اتصال/);
});
