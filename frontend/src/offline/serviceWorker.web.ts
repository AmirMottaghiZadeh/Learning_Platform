/** Registers public/sw.js, which keeps the web app's own files so the
 * installed PWA opens without internet. Production builds only: under the
 * dev server it would serve stale bundles. Relative URL, so it also works
 * under a sub-path deploy. */
export function registerServiceWorker() {
  if (__DEV__ || typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  const register = () => navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(() => undefined);
  if (document.readyState === "complete") register();
  else window.addEventListener("load", register, { once: true });
}
