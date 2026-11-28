const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const { test } = require('node:test');
const src = path.join(__dirname, '../src');
function load(file, modules = {}, globals = {}) {
  const context = { exports: {}, require: name => {
    if (!(name in modules)) throw Error(`Unexpected dependency: ${name}`);
    return modules[name];
  }, ...globals };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(src, file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.React },
  }).outputText, context);
  return context.exports;
}
const helpers = load('utils/webInput.ts');
const iphone = { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)', platform: 'iPhone', maxTouchPoints: 5 };
const ipad = { userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)', platform: 'MacIntel', maxTouchPoints: 5 };
const android = { userAgent: 'Mozilla/5.0 (Linux; Android 14)', platform: 'Linux armv8l', maxTouchPoints: 5 };
const mac = { userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X)', platform: 'MacIntel', maxTouchPoints: 0 };
function flatten(style) {
  return Object.assign({}, ...(Array.isArray(style) ? style : [style]).filter(Boolean).map(value => Array.isArray(value) ? flatten(value) : value));
}
function render(device, props) {
  const native = { TextInput: function NativeInput() {}, StyleSheet: { flatten } };
  const { TextInput } = load('components/primitives/TextInput.web.tsx', {
    react: React, 'react-native': native, '@/utils/webInput': helpers,
  }, device ? { navigator: device } : {});
  const ref = { current: null };
  const element = TextInput.render(props, ref);
  assert.equal(element.type, native.TextInput);
  assert.equal(element.props.ref, ref);
  return element.props;
}

test('all iPhone browsers and desktop-mode iPads get the fix, other platforms do not', () => {
  assert.equal(helpers.hasIosInputZoom(iphone), true);
  assert.equal(helpers.hasIosInputZoom(ipad), true);
  for (const device of [android, mac, undefined]) assert.equal(helpers.hasIosInputZoom(device), false);
});
test('the effective nested style is clamped before focus while props and refs survive', () => {
  const onChangeText = () => {};
  const props = render(iphone, { style: [{ fontSize: 20, color: 'green' }, [false, { fontSize: 14 }]],
    multiline: true, autoFocus: true, editable: false, onChangeText, accessibilityLabel: 'پیام' });
  assert.equal(flatten(props.style).fontSize, 16);
  assert.equal(flatten(props.style).color, 'green');
  assert.equal(props.onChangeText, onChangeText);
  assert.equal(props.multiline, true);
  assert.equal(props.autoFocus, true);
  assert.equal(props.editable, false);
  assert.equal(props.accessibilityLabel, 'پیام');
});
test('large OTP fonts stay large and unstyled inputs get a readable default on iOS', () => {
  assert.equal(flatten(render(iphone, { style: { fontSize: 20, letterSpacing: 8 } }).style).fontSize, 20);
  assert.equal(flatten(render(ipad, {}).style).fontSize, 16);
});
test('desktop, Android web and server rendering retain the exact original style', () => {
  const style = [{ fontSize: 14, color: 'green' }];
  for (const device of [mac, android, undefined]) assert.equal(render(device, { style }).style, style);
});
test('all app text fields pass through the boundary and native uses the original input', () => {
  const boundary = ['components/primitives/TextInput.tsx', 'components/primitives/TextInput.web.tsx'];
  function check(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) check(file);
      else if (/\.tsx?$/.test(file) && !boundary.includes(path.relative(src, file))) {
        const ast = ts.createSourceFile(file, fs.readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true);
        for (const statement of ast.statements) {
          if (ts.isImportDeclaration(statement) && statement.moduleSpecifier.text === 'react-native') {
            const bindings = statement.importClause?.namedBindings;
            if (bindings && ts.isNamedImports(bindings)) {
              assert.ok(!bindings.elements.some(e => (e.propertyName ?? e.name).text === 'TextInput'), file);
            }
          }
        }
      }
    }
  }
  check(src);
  const nativeInput = {};
  assert.equal(load('components/primitives/TextInput.tsx', { 'react-native': { TextInput: nativeInput } }).TextInput, nativeInput);
});
test('viewport still permits pinch zoom and has no forced reset after focus', () => {
  const html = fs.readFileSync(path.join(__dirname, '../public/index.html'), 'utf8');
  const viewport = html.match(/<meta name="viewport"[^>]+>/)[0];
  assert.doesNotMatch(viewport, /maximum-scale|user-scalable/i);
});
