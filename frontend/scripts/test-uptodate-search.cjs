/* Behavioral checks against the actual TypeScript search, including old packages. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

const modules = new Map();
let supplement = null;
const disk = new Map();
let fetchCount = 0;
let remoteSupplement;
function load(filename) {
  const absolute = path.resolve(filename);
  if (modules.has(absolute)) return modules.get(absolute).exports;
  const module = { exports: {} };
  modules.set(absolute, module);
  const code = ts.transpileModule(fs.readFileSync(absolute, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  function localRequire(name) {
    if (name === "./uptodateSearchSupplement") return { loadSearchSupplement: async () => supplement };
    if (name === "@/api/client") return { apiClient: { get: async () => {
      fetchCount++;
      if (remoteSupplement instanceof Error) throw remoteSupplement;
      return { data: new TextEncoder().encode(JSON.stringify(remoteSupplement)).buffer };
    } } };
    if (name === "./files") return {
      partSize: async (_dataset, build) => disk.get(build)?.length ?? 0,
      readRange: async (_dataset, build) => disk.get(build),
      writePart: async (_dataset, build, _name, bytes) => disk.set(build, bytes),
    };
    const target = name.startsWith("@/") ? path.resolve("src", name.slice(2)) : path.resolve(path.dirname(absolute), name);
    return load(target + ".ts");
  }
  new Function("require", "exports", "module", code)(localRequire, module.exports, module);
  return module.exports;
}

const search = load("src/offline/uptodateLocal.ts");
const { stripHtml } = load("src/utils/html.ts");
const catalog = {
  queries: [["h pylori", "1", 100], ["helicobacter pylori", "1", 90], ["h pylori treatment", "2", 150], ["h pylori diagnosis", "3", 60]],
  topics: { "1": ["t,d,p,missing", "t,d", "p,d", ""], "2": ["t,p", "t", "p", ""], "3": ["d,p", "d", "p", ""] },
};
const index = {
  version: "202607", search_schema: 1, search: catalog,
  sections: ["Family Medicine", "Gastroenterology", "Pediatrics"],
  topics: {
    ids: ["t", "d", "p", "bad"],
    titles: ["Treatment of <i>Helicobacter pylori</i> in adults", "Diagnosis of Helicobacter pylori in adults",
      "Helicobacter pylori in children", "Infantile hypertrophic pyloric stenosis"],
    sections: [0, 1, 2, 2], memberships: [[0, 1, 1], [1], [1, 2], [2]], updated: [],
  },
  articles: { ids: ["t"], locs: [0, 0, 1] }, images: { ids: [], types: [], locs: [] },
};
const reader = (data, build) => ({ manifest: { build }, index: async () => structuredClone(data), json: async () => ({ title: "Treatment of <i>H. pylori</i>", body_html: "<p>Text</p>" }) });

async function main() {
  const current = reader(index, "new");
  for (const q of ["h pylori", "H. pylori", "helicobacter pylori"]) {
    const result = await search.searchTopicsPage(current, q);
    assert.equal(result.results[0].id, "t");
    assert.ok(!result.results.some((r) => ["bad", "missing"].includes(r.id)));
    assert.ok(!result.results[0].title.includes("<"));
  }
  const filtered = await search.searchTopicsPage(current, "h pylori", { section: "Gastroenterology", limit: 1 });
  assert.equal(filtered.results[0].id, "t");
  assert.equal(filtered.results[0].section, "Gastroenterology");
  assert.equal(filtered.sections.find((s) => s.name === "Gastroenterology").count, 3);
  assert.equal(filtered.suggestions[0].query, "h pylori treatment");
  assert.equal(filtered.suggestions[0].kind, "treatment");
  assert.equal(filtered.suggestions[0].count, 2);
  const { SearchCatalog } = load("src/offline/uptodateSearchCatalog.ts");
  const guided = new SearchCatalog({ queries: [["h pylori test of cure", "c", 20], ["h pylori treatment", "t", 100],
    ["h pylori diagnosis", "d", 50], ["h pylori treatment adult", "t", 30]],
    topics: { c: ["18,18,missing", "", "", ""], t: ["140619,18", "140619", "", ""], d: ["18,missing", "", "", ""] } });
  assert.deepEqual(guided.suggest("h py", new Map([["18", 0], ["140619", 1]])).map(s => [s.kind, s.count]),
    [["treatment", 2], ["diagnosis", 1], ["followup", 1]]);
  assert.equal((await search.searchTopicsPage(current, "h pylori zzzzzz")).total, 0);
  assert.deepEqual((await search.searchTopicsPage(current, "h pylori children")).results.map((r) => r.id), ["p"]);
  const pages = await Promise.all([0, 1, 2].map((offset) => search.searchTopicsPage(current, "h pylori", { limit: 1, offset })));
  assert.deepEqual(pages.flatMap((page) => page.results.map((r) => r.id)), ["t", "d", "p"]);

  const old = structuredClone(index);
  delete old.search_schema; delete old.search; delete old.topics.memberships;
  const legacy = reader(old, "legacy");
  assert.equal((await search.searchTopicsPage(legacy, "pylori")).results.length, 4);
  supplement = { schema: 1, version: "202607", search: catalog, memberships: { t: ["Family Medicine", "Gastroenterology"], d: ["Gastroenterology"], p: ["Pediatrics"] } };
  search.forgetUptodate();
  assert.equal((await search.searchTopicsPage(legacy, "h pylori", { section: "Gastroenterology" })).results[0].id, "t");
  assert.equal((await search.getTopic(legacy, "t")).title, "Treatment of H. pylori");
  for (const input of ["Age <7 and dose >5", "Age &lt;7 and dose &gt;5", "Age &amp;lt;7 and dose &amp;gt;5"])
    assert.equal(stripHtml(input), "Age <7 and dose >5");
  assert.equal(stripHtml("&amp;lt;i&amp;gt;H. pylori&amp;lt;/i&amp;gt;&nbsp;≥5"), "H. pylori ≥5");
  assert.doesNotThrow(() => stripHtml("&#99999999; and &#xFFFFFFFF;"));

  const upgrade = load("src/offline/uptodateSearchSupplement.ts");
  remoteSupplement = supplement;
  const upgradeReader = (build, schema) => ({ manifest: { build }, index: async () => ({ version: "202607", search_schema: schema }),
    decodeJson: async (bytes) => JSON.parse(new TextDecoder().decode(bytes)) });
  const installed = upgradeReader("old-package-upgrade");
  assert.equal(await upgrade.refreshSearchSupplement(installed), true);
  assert.deepEqual(await upgrade.loadSearchSupplement(installed, "202607"), supplement);
  const alreadyFetched = fetchCount;
  assert.equal(await upgrade.refreshSearchSupplement(installed), false);
  assert.equal(fetchCount, alreadyFetched);
  assert.equal(await upgrade.refreshSearchSupplement(upgradeReader("new-package", 1)), false);
  assert.equal(fetchCount, alreadyFetched);
  remoteSupplement = { ...supplement, version: "wrong-snapshot" };
  assert.equal(await upgrade.refreshSearchSupplement(upgradeReader("mismatch")), false);
  assert.equal(disk.has("mismatch"), false);
  remoteSupplement = new Error("offline");
  assert.equal(await upgrade.refreshSearchSupplement(upgradeReader("offline-package")), false);
  remoteSupplement = supplement;
  disk.set("corrupt", new TextEncoder().encode("broken record"));
  assert.equal(await upgrade.refreshSearchSupplement(upgradeReader("corrupt")), true);

  // Optional large fixture produced by the Python real-snapshot validation.
  if (process.env.UPTODATE_PARITY_FIXTURE) {
    const fixture = JSON.parse(fs.readFileSync(process.env.UPTODATE_PARITY_FIXTURE, "utf8"));
    supplement = null;
    const real = reader(fixture.index, "real-snapshot");
    for (const { query, args, expected } of fixture.cases) {
      const actual = await search.searchTopicsPage(real, query, args);
      assert.deepEqual(actual, expected, `online/offline parity: ${query} / ${args.section || "all"}`);
    }
    console.log(`Real-snapshot online/offline parity passed (${fixture.cases.length} cases)`);
  }
  console.log("UpToDate concept, specialty, pagination, legacy-package and title checks passed");
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
