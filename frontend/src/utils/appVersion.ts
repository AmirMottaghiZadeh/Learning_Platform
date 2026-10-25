import Constants from "expo-constants";

/** This build's version, app.json's SemVer ("1.4.2"). */
export const APP_VERSION: string = Constants.expoConfig?.version ?? "0.0.0";

/** 1.4.2 -> 10402: the number Android installs by, derived the same way in
 * app.config.js (the build's versionCode) and on the server
 * (apps.releases.models.version_code). */
export function versionCodeOf(version: string): number {
  const [major = 0, minor = 0, patch = 0] = version.split(".").map((n) => parseInt(n, 10) || 0);
  return major * 10000 + minor * 100 + patch;
}
