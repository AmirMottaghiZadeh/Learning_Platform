/* Exercise the actual script shared by the web iframe and native WebView. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const ts = require("typescript");

const source = fs.readFileSync("src/screens/UptodateArticleScreen.tsx", "utf8");
const ast = ts.createSourceFile("screen.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
let initializer;
function walk(node) {
  if (ts.isVariableDeclaration(node) && node.name.getText(ast) === "FIND_SCRIPT") initializer = node.initializer;
  ts.forEachChild(node, walk);
}
walk(ast);
assert.ok(initializer, "reader script must exist");
const expression = ts.transpileModule(`var result = ${initializer.getText(ast)};`, {
  compilerOptions: { target: ts.ScriptTarget.ES2020 },
}).outputText;
const script = vm.runInNewContext(expression + "\nresult;");
let matches = [];
let ids = [];
let scrolled = 0;
let highlighted = false;
const element = {
  id: "H1",
  scrollIntoView() { scrolled++; },
  classList: { add(value) { if (value === "utd-search-flash") highlighted = true; }, remove() {} },
};
const document = {
  querySelectorAll(selector) { return selector === "[id]" ? ids : matches; },
  getElementById() { return null; },
};
const window = { addEventListener() {} };
const context = vm.createContext({ window, document, setTimeout() {}, requestAnimationFrame() {} });
vm.runInContext(script, context);
const anchor = "utd-" + "a".repeat(32);
matches = [element];
assert.equal(context.__utdGotoSearch(anchor), true);
assert.equal(scrolled, 1);
assert.equal(highlighted, true);
matches = [element, element];
assert.equal(context.__utdGotoSearch(anchor), false);
assert.equal(context.__utdGotoSearch('bad"]'), false);
ids = [element, element];
assert.equal(context.__utdGotoSearchSection("H1"), false);
ids = [element];
assert.equal(context.__utdGotoSearchSection("H1"), true);
assert.equal(scrolled, 2);
console.log("UpToDate search navigation checks passed");
