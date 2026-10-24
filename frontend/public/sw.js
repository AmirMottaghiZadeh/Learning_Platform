/* Pharmenta web app service worker: keeps the app's own files so the
 * installed PWA opens without internet (and can then read the offline
 * UpToDate/Lexicomp packages). API calls go to another origin and are never
 * touched here; the offline packages live in the origin-private file
 * system, not in these caches.
 *
 * - The page itself: network first, so a deploy shows up as soon as the
 *   app is opened online; the last copy when offline.
 * - Content-hashed bundles and assets (_expo/, assets/): cache first --
 *   their names change whenever their content does.
 * - The few unhashed files (icons, manifest): network first, cached copy
 *   when offline.
 */

const CACHE = "pharmenta-shell-v1";
const SCOPE = new URL(self.registration.scope);
const INDEX = new URL("index.html", SCOPE).href;
const MAX_HASHED = 400;

const inScope = (url) => url.origin === SCOPE.origin && url.pathname.startsWith(SCOPE.pathname);
const isHashed = (url) => {
  const path = url.pathname.slice(SCOPE.pathname.length);
  return path.startsWith("_expo/") || path.startsWith("assets/");
};

/** The bundles an index.html names, so the shell is complete offline even
 * before the app has been opened twice. */
function referencedFiles(html) {
  const found = new Set();
  for (const match of html.matchAll(/(?:src|href)="([^"]+)"/g)) {
    const url = new URL(match[1], SCOPE);
    if (inScope(url)) found.add(url.href);
  }
  return [...found];
}

async function storeShell(response) {
  const cache = await caches.open(CACHE);
  const html = await response.clone().text();
  await cache.put(INDEX, response.clone());
  const files = referencedFiles(html);
  await Promise.all(files.map((href) => cache.add(href).catch(() => undefined)));
  // Drop bundles of earlier deploys the new page no longer names.
  const keep = new Set(files);
  for (const request of await cache.keys()) {
    const url = new URL(request.url);
    if (url.pathname.includes("/_expo/static/") && !keep.has(url.href)) await cache.delete(request);
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    fetch(INDEX, { cache: "no-store" })
      .then((res) => (res.ok ? storeShell(res) : undefined))
      .catch(() => undefined)
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) => Promise.all(names.filter((n) => n.startsWith("pharmenta-shell-") && n !== CACHE).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

async function trim(cache) {
  const keys = await cache.keys();
  for (const request of keys.slice(0, Math.max(0, keys.length - MAX_HASHED))) await cache.delete(request);
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (!inScope(url)) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((res) => {
          if (res.ok) event.waitUntil(storeShell(res.clone()));
          return res;
        })
        .catch(async () => (await caches.match(INDEX)) || Response.error()),
    );
    return;
  }

  if (isHashed(url)) {
    event.respondWith(
      caches.match(request).then(
        (hit) =>
          hit ||
          fetch(request).then((res) => {
            if (res.ok) {
              const copy = res.clone();
              event.waitUntil(caches.open(CACHE).then((c) => c.put(request, copy).then(() => trim(c))));
            }
            return res;
          }),
      ),
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          event.waitUntil(caches.open(CACHE).then((c) => c.put(request, copy)));
        }
        return res;
      })
      .catch(async () => (await caches.match(request)) || Response.error()),
  );
});
