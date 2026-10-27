// Focused regression checks without a DOM or a new test dependency.
// Run: node --test scripts/announcement-calculator.test.cjs
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

function load(file, mocks = {}, globals = {}) {
  const filename = path.resolve(__dirname, "../src", file);
  const exports = {};
  const source = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, esModuleInterop: false },
  }).outputText;
  vm.runInNewContext(source, {
    exports, ...globals,
    require: (name) => {
      if (Object.hasOwn(mocks, name)) return mocks[name];
      if (name.startsWith(".")) return load(path.relative(path.resolve(__dirname, "../src"), path.resolve(path.dirname(filename), `${name}.ts`)), mocks, globals);
      throw new Error(`Unmocked import: ${name}`);
    },
  }, { filename });
  return exports;
}
const { calculatorLabel, choiceLabels } = load("utils/calculatorLabels.ts");
const choice = (primary, secondary, fa = primary, secondaryFa = secondary) => ({
  title_primary: primary, title_secondary: secondary,
  title_primary_fa: fa, title_secondary_fa: secondaryFa, answer_factor: "3",
});

test("Child-Pugh shows both original albumin units and their thresholds", () => {
  const input = choice("&lt;28 g/L", "&lt;2.8 g/dL");
  const before = JSON.stringify(input);
  assert.equal(choiceLabels(input, true).join("\n"), "کمتر از 28 g/L\nکمتر از 2.8 g/dL");
  assert.equal(choiceLabels(input, false).join("\n"), "less than 28 g/L\nless than 2.8 g/dL");
  assert.equal(JSON.stringify(input), before); // display must never change scoring data
});
test("both bounds and equality are preserved in Persian and English", () => {
  assert.equal(calculatorLabel("&ge;150 g/L", true), "بیشتر یا مساوی 150 g/L");
  assert.equal(calculatorLabel("&le;1.5 mg/dL", false), "less than or equal to 1.5 mg/dL");
  assert.equal(calculatorLabel(">= 5", false), "greater than or equal to 5");
  assert.equal(calculatorLabel("<= ۰", true), "کمتر یا مساوی ۰");
  assert.equal(calculatorLabel("28-35 g/L", true), "28 تا 35 g/L");
  assert.equal(calculatorLabel("2.8–3.5 g/dL", false), "2.8 to 3.5 g/dL");
});
test("HTML stripping keeps raw inequalities, decimals, fractions, units and negatives", () => {
  assert.equal(calculatorLabel("<5 and >10", false), "less than 5 and greater than 10");
  assert.equal(calculatorLabel("<i>Cr</i> &lt; 1.2 mg/dL<br />OR urine <500 mL/day", false), "Cr less than 1.2 mg/dL OR urine less than 500 mL/day");
  assert.equal(calculatorLabel("&gt; -0.5 °C", true), "بیشتر از -0.5 °C");
  assert.equal(calculatorLabel("<½ the time", false), "less than ½ the time");
  assert.equal(calculatorLabel("10 m<sup>2</sup>", false), "10 m2");
});
test("fallbacks retain secondary explanations and avoid duplicate labels", () => {
  assert.equal(choiceLabels(choice("Yes", "Hgb &lt;130 g/L", "بله", null), true).join("; "), "بله; Hgb کمتر از 130 g/L");
  assert.equal(choiceLabels(choice("None", "", "هیچ", null), true).join(""), "هیچ");
  assert.equal(choiceLabels(choice("2 mg/dL", "2 mg/dL "), false).length, 1);
});

function browser({ ios = false, standalone = false, stored = false } = {}) {
  const window = new EventTarget();
  const storage = new Map(stored ? [["pharmenta:pwa-installed", "1"]] : []);
  window.localStorage = { getItem: (key) => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key) };
  window.matchMedia = () => ({ matches: standalone, addEventListener() {} });
  const install = load("pwa/install.web.ts", {}, {
    window, navigator: { userAgent: ios ? "iPhone" : "Chrome", platform: ios ? "iPhone" : "Linux", maxTouchPoints: 1 },
  });
  install.initializeInstall();
  function offer(outcome = "accepted", throws = false) {
    let calls = 0;
    const event = new Event("beforeinstallprompt", { cancelable: true });
    event.prompt = async () => { calls++; if (throws) throw new Error("blocked"); };
    event.userChoice = Promise.resolve({ outcome });
    window.dispatchEvent(event);
    return () => calls;
  }
  return { ...install, window, storage, offer };
}
test("captures install before home mounts; prompts synchronously once per browser offer", async () => {
  const app = browser();
  const calls = app.offer();
  const result = app.requestInstall();
  assert.equal(calls(), 1); // still in the original click, before an await
  assert.equal(await result, "accepted");
  assert.equal(await app.requestInstall(), "manual");
  assert.equal(app.getInstallState().environment, "browser");
  app.window.dispatchEvent(new Event("appinstalled"));
  assert.equal(app.getInstallState().environment, "standalone");
  assert.equal(app.storage.get("pharmenta:pwa-installed"), "1");
});
test("cancellation and prompt failures leave installation available via browser instructions", async () => {
  const app = browser();
  app.offer("dismissed");
  assert.equal(await app.requestInstall(), "dismissed");
  assert.equal(app.getInstallState().environment, "browser");
  assert.equal(app.getInstallState().busy, false);
  app.offer("accepted", true);
  assert.equal(await app.requestInstall(), "error");
  assert.equal(app.getInstallState().busy, false);
});
test("iOS provides manual installation; standalone and remembered installs are excluded", async () => {
  const ios = browser({ ios: true });
  assert.equal(ios.getInstallState().manual, "ios");
  assert.equal(await ios.requestInstall(), "manual");
  assert.equal(browser({ standalone: true }).getInstallState().environment, "standalone");
  const installed = browser({ stored: true });
  assert.equal(installed.getInstallState().environment, "standalone");
  installed.offer(); // browser says the app was uninstalled
  assert.equal(installed.getInstallState().environment, "browser");
});
test("native builds do not offer PWA installation", () => {
  assert.equal(load("pwa/install.ts").getInstallState().environment, "native");
});
test("offline dismissal survives restart, retries, and is isolated by account", async () => {
  const storage = new Map();
  let online = false;
  let userId = 1;
  const calls = [];
  const mocks = {
    "@react-native-async-storage/async-storage": { default: { getItem: async (key) => storage.get(key) ?? null, setItem: async (key, value) => storage.set(key, value) } },
    "@/api/endpoints": { announcementsApi: { event: async (id, event) => { if (!online) throw new Error("offline"); calls.push({ userId, id, event }); } } },
    "@/store/auth": { useAuth: { getState: () => ({ user: { id: userId } }) } },
  };
  let store = load("components/announcements/dismissals.ts", mocks);
  await Promise.all([store.rememberDismissal(1, 12), store.rememberDismissal(1, 13)]);
  await store.syncDismissals(1);
  store = load("components/announcements/dismissals.ts", mocks);
  assert.equal((await store.loadDismissals(1)).join(","), "12,13");
  assert.equal((await store.loadDismissals(2)).length, 0);
  online = true;
  userId = 2;
  await store.syncDismissals(1);
  assert.equal(calls.length, 0); // never submit another account's receipts
  userId = 1;
  await store.syncDismissals(1);
  await store.syncDismissals(1);
  assert.equal(calls.length, 2);
  assert.equal((await store.loadDismissals(1)).join(","), "12,13");
});
