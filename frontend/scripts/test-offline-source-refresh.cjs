/* Installing a new package must invalidate answers from the previous build. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const ts = require("typescript");
const { QueryClient } = require("@tanstack/react-query");

const queryClient = new QueryClient();
const keys = ["uptodate-search-page", "uptodate-topic", "uptodate-graphic-html"];
let state = { datasets: { uptodate: { installed: { manifest: { build: "old" } } }, lexicomp: { installed: null } } };
let subscription;
let forgotten = 0;
let network = 0;
const offlineStore = { getState: () => state, subscribe: (fn) => { subscription = fn; } };
const unavailable = () => { network++; throw new Error("Network is unavailable"); };
const stubs = {
  "@/api/endpoints": { uptodateApi: { search: unavailable, searchPage: unavailable, topic: unavailable, image: unavailable }, lexicompApi: {} },
  "@/api/client": { ApiError: class ApiError extends Error {} },
  "@/api/queryClient": { queryClient },
  "./store": { useOffline: offlineStore, isUsable: () => !!state.datasets.uptodate.installed, renewLicense: async () => {}, touch() {} },
  "./reader": { openReader: async (_dataset, manifest) => ({ manifest }) },
  "./uptodateLocal": { forgetUptodate: () => forgotten++, searchTopicsPage: async (reader) => ({ build: reader.manifest.build }) },
  "./uptodateSearchSupplement": { refreshSearchSupplement: async () => false },
  "./lexicompLocal": {},
};
const output = ts.transpileModule(fs.readFileSync("src/offline/sources.ts", "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText;
const loaded = { exports: {} };
new Function("require", "exports", "module", output)((name) => {
  assert.ok(Object.hasOwn(stubs, name), `unexpected dependency ${name}`);
  return stubs[name];
}, loaded.exports, loaded);

function seed() {
  for (const key of keys) queryClient.setQueryData([key, "cached"], { source: "old package" });
  queryClient.setQueryData(["calculator", "cached"], { source: "unchanged" });
}
function replace(build) {
  const previous = state;
  state = { ...state, datasets: { ...state.datasets, uptodate: { installed: build ? { manifest: { build } } : null } } };
  subscription(state, previous);
}
function assertInvalidated(expected) {
  for (const key of keys) assert.equal(queryClient.getQueryState([key, "cached"]).isInvalidated, expected, key);
  assert.equal(queryClient.getQueryState(["calculator", "cached"]).isInvalidated, false);
}
async function main() {
  seed(); replace("new"); assertInvalidated(true); assert.equal(forgotten, 1);
  assert.deepEqual(await loaded.exports.uptodateSource.searchPage("h pylori"), { build: "new" });
  seed(); replace("new"); assertInvalidated(false); assert.equal(forgotten, 1);
  seed(); replace(null); assertInvalidated(true); assert.equal(forgotten, 2);
  seed(); replace("installed-again"); assertInvalidated(true); assert.equal(forgotten, 3);
  seed();
  const previous = state;
  state = { ...state, datasets: { ...state.datasets, lexicomp: { installed: { manifest: { build: "lexi-new" } } } } };
  subscription(state, previous);
  assertInvalidated(false); assert.equal(forgotten, 3); assert.equal(network, 0);
  console.log("Offline package install, replacement, removal and search cache refresh passed without network");
}
main().catch((error) => { console.error(error); process.exitCode = 1; }).finally(() => queryClient.clear());
