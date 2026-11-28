const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const React = require("react");
const ts = require("typescript");

function renderGlyph(progress, active, tab) {
  const source = path.join(__dirname, "../src/components/TabGlyph.tsx");
  const { outputText } = ts.transpileModule(fs.readFileSync(source, "utf8"), {
    compilerOptions: { jsx: ts.JsxEmit.React, module: ts.ModuleKind.CommonJS, esModuleInterop: true },
  });
  const colors = { accent: "#0F5C52", muted: "#5C6964", onAccent: "#FFFFFF" };
  const worklets = [];
  const modules = {
    react: { ...React, useRef: (current) => ({ current }), useEffect: () => undefined },
    "react-native-svg": { __esModule: true, default: "Svg", Path: "Path" },
    "react-native-reanimated": {
      __esModule: true,
      default: { createAnimatedComponent: () => "AnimatedPath" },
      ReduceMotion: { System: "system" },
      useSharedValue: () => ({ value: progress }),
      withSpring: (value) => value,
      useAnimatedProps: (worklet, _deps, adapter) => {
        const props = worklet();
        adapter?.(props);
        worklets.push(props);
        return props;
      },
      createAnimatedPropAdapter: (adapter) => adapter,
      interpolateColor: () => colors.accent,
      processColor: () => -15770542,
    },
    "@/theme/ThemeProvider": { useTheme: () => ({ colors }) },
    "@/theme/tokens": { navigationGlyphSpring: {} },
  };
  const exports = {};
  new Function("require", "exports", outputText)((name) => modules[name], exports);
  return { tree: exports.TabGlyph({ tab, active }), worklets, colors };
}

test("native navigation never sends SVG color brushes through Reanimated worklets", () => {
  for (const tab of ["dashboard", "lessons", "clinical", "profile"]) {
    const frames = [0, 0.5, 1].map((progress) => renderGlyph(progress, progress > 0, tab));
    for (const [index, { tree, worklets, colors }] of frames.entries()) {
      assert.equal(worklets.length, 1);
      assert.deepEqual(Object.keys(worklets[0]).sort(), ["d", "fillOpacity"]);
      assert.equal(worklets[0].fillOpacity, index / 2);
      assert.equal(tree.props.children[0].props.stroke, index === 0 ? colors.muted : colors.accent);
    }
    assert.equal(new Set(frames.map(({ worklets }) => worklets[0].d)).size, 3);
  }
});
