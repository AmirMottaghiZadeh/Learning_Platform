/* Exercise the actual script shared by the web iframe and native WebView. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const ts = require("typescript");

const source = fs.readFileSync("src/components/article/ClinicalArticleReader.tsx", "utf8");
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
  addEventListener() {},
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

// Text nodes as delivered by a browser after its first entity-decoding pass.
// Exercise the actual reader function, including legacy package content.
class DomNode {
  constructor(tagName, value = "") {
    this.tagName = tagName;
    this.nodeValue = value;
    this.children = [];
    this.parentNode = null;
    this.nodeType = tagName === "#text" ? 3 : tagName === "#fragment" ? 11 : 1;
  }
  get parentElement() { return this.parentNode?.nodeType === 1 ? this.parentNode : null; }
  get textContent() { return this.nodeType === 3 ? this.nodeValue : this.children.map((n) => n.textContent).join(""); }
  appendChild(node) { this.children.push(node); node.parentNode = this; return node; }
  replaceChild(next, old) {
    const at = this.children.indexOf(old);
    assert.ok(at >= 0);
    const nodes = next.nodeType === 11 ? next.children : [next];
    this.children.splice(at, 1, ...nodes);
    for (const node of nodes) node.parentNode = this;
    old.parentNode = null;
  }
}
function descendants(node) { return [node, ...node.children.flatMap(descendants)]; }
function paragraph(parent, tag, text) {
  const element = parent.appendChild(new DomNode(tag));
  element.appendChild(new DomNode("#text", text));
  return element;
}
document.body = new DomNode("BODY");
const clinical = paragraph(document.body, "P", "Age <7; dose >5; ≤10 and ≥3.");
const reference = paragraph(document.body, "P", "A <em>versus</em> B; &lt;I&gt;H. pylori&lt;/I&gt;.");
const literal = paragraph(document.body, "PRE", "<i>literal code</i>");
const scriptNode = paragraph(document.body, "SCRIPT", "var value = '<b>script text</b>';");
const unsafe = paragraph(document.body, "P", '<img src=x onerror="alert(1)">');
const table = paragraph(document.body, "TABLE", "Preserved table");
document.createTreeWalker = (root) => {
  const nodes = descendants(root).filter((node) => node.nodeType === 3);
  let at = 0;
  return { nextNode: () => nodes[at++] ?? null };
};
document.createTextNode = (value) => new DomNode("#text", value);
document.createElement = (tag) => new DomNode(tag.toUpperCase());
document.createDocumentFragment = () => new DomNode("#fragment");
context.NodeFilter = { SHOW_TEXT: 4 };
context.__utdRepairInlineMarkup();
assert.equal(clinical.textContent, "Age <7; dose >5; ≤10 and ≥3.");
assert.equal(reference.textContent, "A versus B; H. pylori.");
assert.equal(descendants(reference).find((n) => n.tagName === "EM").textContent, "versus");
assert.equal(descendants(reference).find((n) => n.tagName === "I").textContent, "H. pylori");
assert.equal(literal.textContent, "<i>literal code</i>");
assert.equal(scriptNode.textContent, "var value = '<b>script text</b>';");
assert.equal(unsafe.textContent, '<img src=x onerror="alert(1)">');
assert.ok(!descendants(unsafe).some((n) => n.tagName === "IMG"));
assert.ok(document.body.children.includes(table));
// Table controls must not move saved highlight offsets or become search hits.
const beforeControls = context.__utdFullText(context.__utdTexts());
const tools = paragraph(document.body, "DIV", "View table full screen");
tools.hasAttribute = (name) => name === "data-utd-ui";
assert.equal(context.__utdSkipped(tools.children[0]), true);
assert.equal(context.__utdFullText(context.__utdTexts()), beforeControls);
assert.equal(context.__utdSearch("View table full screen").count, 0);
console.log("UpToDate search navigation and reader HTML checks passed");
