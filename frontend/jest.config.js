module.exports = {
  preset: "jest-expo",
  setupFilesAfterEnv: ["<rootDir>/src/test/setup.ts"],
  testPathIgnorePatterns: ["/node_modules/", "/dist/"],
  collectCoverageFrom: [
    "App.tsx",
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/test/**",
  ],
};
