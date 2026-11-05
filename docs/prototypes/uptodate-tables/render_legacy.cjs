// Evaluate the real reader wrapper with unused React imports stubbed. The
// resulting iframe is the current app's output, not a recreated approximation.
const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");

const root = path.resolve(__dirname, "../../..");
const frontendRequire = createRequire(path.join(root, "frontend/package.json"));
const ts = frontendRequire("typescript");
const source = fs.readFileSync(path.join(root, "frontend/src/screens/UptodateArticleScreen.tsx"), "utf8");
const output = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.React },
}).outputText;
const wrappedModule = { exports: {} };
new Function("require", "exports", "module", output + "\nmodule.exports.wrap = wrap;")(
  (name) => name === "@/store/library" ? { HIGHLIGHT_COLORS: [], HIGHLIGHT_PAINT: {} } : {},
  wrappedModule.exports, wrappedModule,
);
const colors = { ink:"#192a24", prose:"#24362f", muted:"#52665d", bg:"#ffffff", accent:"#126b51",
  accentSoft:"#eaf4ef", onAccent:"#ffffff", rule:"#dde5e0" };
const samples = JSON.parse(fs.readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(Object.fromEntries(samples.map((s) => [s.id, wrappedModule.exports.wrap(s.body, colors)]))));
