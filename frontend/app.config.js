// Merges app.json with what depends on the build:
// - the version: app.json's `version` (SemVer, bumped by scripts/release.mjs)
//   is the only one written down; Android's versionCode and iOS's
//   buildNumber are derived from it -- 1.4.2 -> 10402 -- so they always
//   agree and always grow. A rebuild of a released version ships as the next
//   patch.
// - the Android build properties, per EAS profile (eas.json `env`):
//   ANDROID_ARCHS -- the CPU types built for: the phones' ARM ones by default,
//   never the emulator-only x86/x86_64 (37 of the old APK's 80 MB);
//   ANDROID_COMPRESS_NATIVE_LIBS=1 -- the native libraries stored compressed,
//   for an APK that is downloaded directly or from Bazaar/Myket (Google Play
//   compresses an app bundle itself, so its profile leaves this off);
//   release builds run R8 and drop unused resources, and refuse plain HTTP
//   (every endpoint is HTTPS; a debug build's own manifest still allows it,
//   to reach Metro).
// - for a GitHub Pages build, the sub-path base URL from EXPO_BASE_URL (e.g.
//   "/Learning_Platform") so exported asset paths resolve under
//   https://<user>.github.io/<repo>/. Local dev and native builds leave it unset.
const basePath = (process.env.EXPO_BASE_URL || "").replace(/\/+$/, "");

function versionCodeOf(version) {
  const parts = version.split(".").map(Number);
  if (parts.length !== 3 || parts.some((n) => !Number.isInteger(n) || n < 0) || parts[1] > 99 || parts[2] > 99) {
    throw new Error(`app.json version must be MAJOR.MINOR.PATCH with MINOR and PATCH under 100, not "${version}"`);
  }
  return parts[0] * 10000 + parts[1] * 100 + parts[2];
}

module.exports = ({ config }) => {
  const archs = (process.env.ANDROID_ARCHS || "arm64-v8a,armeabi-v7a").split(",").map((a) => a.trim());
  return {
    ...config,
    android: { ...config.android, versionCode: versionCodeOf(config.version) },
    ios: { ...config.ios, buildNumber: config.version },
    plugins: [
      ...(config.plugins || []),
      [
        "expo-build-properties",
        {
          android: {
            buildArchs: archs,
            enableMinifyInReleaseBuilds: true,
            enableShrinkResourcesInReleaseBuilds: true,
            useLegacyPackaging: process.env.ANDROID_COMPRESS_NATIVE_LIBS === "1",
            usesCleartextTraffic: false,
          },
        },
      ],
    ],
    experiments: {
      ...config.experiments,
      ...(basePath ? { baseUrl: basePath } : {}),
    },
  };
};
