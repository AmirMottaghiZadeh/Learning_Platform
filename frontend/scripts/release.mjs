#!/usr/bin/env node
/**
 * Cuts an app release: `npm run release -- patch|minor|major [--dry-run]`.
 *
 * 1. Bumps the SemVer in app.json -- the version's only source: app.config.js
 *    derives Android's versionCode and iOS's buildNumber from it -- and the
 *    same number in package.json and package-lock.json.
 * 2. Adds a CHANGELOG.md section listing the commit subjects since the last
 *    app-v* tag.
 * 3. Commits "Release app vX.Y.Z" and tags it app-vX.Y.Z.
 *
 * Nothing is pushed or built; the next steps are printed. --dry-run prints
 * the new version and its changelog section and changes nothing.
 */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = join(dirname(fileURLToPath(import.meta.url)), "..");
const git = (...args) => execFileSync("git", args, { cwd: frontend, encoding: "utf8" }).trim();
const file = (name) => join(frontend, name);
const readJson = (name) => JSON.parse(readFileSync(file(name), "utf8"));
const writeJson = (name, data) => writeFileSync(file(name), JSON.stringify(data, null, 2) + "\n");

function fail(message) {
  console.error(`release: ${message}`);
  process.exit(1);
}

const CHANGELOG_HEAD = `# Changelog

The app's releases, newest first. \`npm run release\` writes each section from
the commit subjects since the previous release; reword it before pushing if
needed. The update message the app shows is written separately, in Persian,
on the release's row in the Django admin (docs/08-deployment.md).
`;

// As in app.config.js: 1.4.2 -> 10402.
const versionCode = (version) => version.split(".").reduce((code, n) => code * 100 + Number(n), 0);

const [kind, ...flags] = process.argv.slice(2);
const dryRun = flags.includes("--dry-run");
if (!["patch", "minor", "major"].includes(kind)) fail("usage: npm run release -- patch|minor|major [--dry-run]");
if (!dryRun && git("status", "--porcelain")) fail("the working tree has uncommitted changes; commit or stash them first");

const appJson = readJson("app.json");
const current = appJson.expo.version;
const [major, minor, patch] = current.split(".").map(Number);
const next =
  kind === "major" ? `${major + 1}.0.0` : kind === "minor" ? `${major}.${minor + 1}.0` : `${major}.${minor}.${patch + 1}`;
const [, nextMinor, nextPatch] = next.split(".").map(Number);
// The versionCode only grows while these stay two digits.
if (nextMinor > 99 || nextPatch > 99) fail(`${next}: minor and patch must stay under 100; release a new major instead`);
const tag = `app-v${next}`;
if (git("tag", "--list", tag)) fail(`tag ${tag} already exists`);

// The newest release tag behind HEAD; none before the first release.
const previous = git("tag", "--list", "app-v*", "--merged", "HEAD", "--sort=-v:refname").split("\n")[0];
const subjects = previous
  ? git("log", `${previous}..HEAD`, "--no-merges", "--pretty=format:%s")
      .split("\n")
      .filter((s) => s && !s.startsWith("Release app v"))
  : [];
const lines = !previous ? ["- First tagged release."] : subjects.length ? subjects.map((s) => `- ${s}`) : ["- No changes."];
const now = new Date();
const today = [now.getFullYear(), now.getMonth() + 1, now.getDate()].map((n) => String(n).padStart(2, "0")).join("-");
const section = [`## ${next} (${today})`, "", ...lines, ""].join("\n");

console.log(`${current} -> ${next} (versionCode ${versionCode(current)} -> ${versionCode(next)})\n`);
console.log(section);
if (dryRun) process.exit(0);

appJson.expo.version = next;
writeJson("app.json", appJson);
const pkg = readJson("package.json");
pkg.version = next;
writeJson("package.json", pkg);
const lock = readJson("package-lock.json");
lock.version = next;
if (lock.packages?.[""]) lock.packages[""].version = next;
writeJson("package-lock.json", lock);

const old = existsSync(file("CHANGELOG.md")) ? readFileSync(file("CHANGELOG.md"), "utf8") : CHANGELOG_HEAD;
const at = old.indexOf("\n## ");
writeFileSync(file("CHANGELOG.md"), at < 0 ? `${old.trimEnd()}\n\n${section}` : `${old.slice(0, at + 1)}${section}\n${old.slice(at + 1)}`);

git("add", "app.json", "package.json", "package-lock.json", "CHANGELOG.md");
git("commit", "-m", `Release app v${next}`);
git("tag", "-a", tag, "-m", `Pharmenta app ${next}`);

console.log(`Committed "Release app v${next}" and tagged ${tag}. Nothing is pushed yet. Next:
  1. To reword frontend/CHANGELOG.md: edit it, then
       git add CHANGELOG.md && git commit --amend --no-edit && git tag -f -a ${tag} -m "Pharmenta app ${next}"
  2. git push && git push origin ${tag}
  3. npx eas-cli build -p android --profile production   (APK for Bazaar, Myket and the site)
     npx eas-cli build -p android --profile play         (app bundle for Google Play)
  4. Once the build is downloadable: Django admin -> نسخه‌های اپ -> add ${next} for Android with its
     Persian notes and download link, and tick «منتشر شده». Installed apps offer the update on opening.`);
