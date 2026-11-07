const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");
const cache = new Map();
function load(file) {
  file = path.resolve(file);
  if (cache.has(file)) return cache.get(file);
  const exports = {};
  cache.set(file, exports);
  const source = ts.transpileModule(fs.readFileSync(file, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
  vm.runInNewContext(source, { exports, Map, Set, require(name) {
    if (name === "@/api/endpoints") return { medscapeApi: {} };
    if (name === "@/api/queryClient") return { queryClient: {} };
    if (name.startsWith("@/")) return load(path.resolve("src", name.slice(2)) + ".ts");
    if (name.startsWith(".")) return load(path.resolve(path.dirname(file), name) + ".ts");
    return require(name);
  } }, { filename: file });
  return exports;
}
const { groupInteractions } = load("src/utils/lexicompGroups.ts");
const base = { drug_ids: [1, 2], object_generic_id: 1, precipitant_generic_id: 2, object_name: "Drug A", precipitant_name: "Drug B", severity: "minor", reliability: "", summary: "First distinct rule", management: "First action", discussion: "", footnotes: "" };
const rows = [
  { ...base, monograph_id: 1 },
  { ...base, monograph_id: 2, severity: "major", summary: "Different rule", management: "Different action", object_generic_id: 2, precipitant_generic_id: 1, object_name: "Drug B", precipitant_name: "Drug A" },
  { ...base, monograph_id: 1 },
  { ...base, monograph_id: 3, precipitant_generic_id: 3, precipitant_name: "Drug C" },
];
const groups = groupInteractions(rows);
assert.equal(groups.length, 2, "one card per unordered pair");
assert.equal(groups[0].interactions.length, 2, "preserve both distinct rules and remove only duplicated monographs");
assert.equal(groups[0].severity, "major");
assert.equal(groups[0].interactions[0].management, "Different action");
assert.equal(rows.length, 4, "source response is not mutated");
const { drugName } = load("src/utils/drugName.ts");
assert.equal(drugName({ name: "Aspirin", name_fa: "آسپرین" }, true), "آسپرین");
assert.equal(drugName({ name: "Aspirin", name_fa: "آسپرین" }, false), "Aspirin");
assert.equal(drugName({ name: "Aspirin" }, true), "Aspirin", "old cached data remains usable");
const { medscapeDocument } = load("src/utils/medscapeReader.ts");
const article = { slug: "sample-guideline", title: "Reference", kind: "guideline", categories: [], latest_update: null, sections: [{ heading: "Overview", blocks: [{ type: "paragraph", text: '<script>alert("bad")</script> & care' }, { type: "table", headers: ["Name", "Value"], rows: [["Example", "1"]] }], children: [{ heading: "References", blocks: [{ type: "list", ordered: true, items: ["Source A", "Source B"] }], children: [] }] }] };
const rendered = medscapeDocument(article);
assert.ok(rendered.body_html.includes('id="med-0.0"'));
assert.ok(rendered.body_html.includes("<table>"));
assert.ok(rendered.body_html.includes("<ol><li>Source A"));
assert.ok(!rendered.body_html.includes("<script>"), "upstream plain text cannot execute script");
assert.ok(rendered.body_html.includes("&lt;script&gt;"));
const { numberedOutline } = load("src/utils/uptodateOutline.ts");
const outline = numberedOutline(rendered.outline_html);
assert.equal(outline.length, 2);
assert.equal(outline[1].id, "med-0.0");
assert.equal(outline[1].depth, 1);
console.log("Reference update checks passed: paired interactions, localized names, shared-reader conversion and outline anchors.");
