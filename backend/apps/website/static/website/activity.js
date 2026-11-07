/* Coordinates only: no element text, inputs, URLs, searches or message data. */
(() => {
  const config = document.querySelector('meta[name="activity-section"]');
  const csrf = document.querySelector('meta[name="activity-csrf"]')?.content;
  const known = new Set(["home", "blog", "post", "page", "plans", "download", "contact", "drugs", "drug", "account", "checkout", "login", "announcements", "category", "tag", "search", "announcement"]);
  if (!config || !known.has(config.content) || !csrf) return;
  let queue = [], sending = false, visible = !document.hidden, started = Date.now();
  const heartbeat = () => {
    const seconds = Math.min(120, Math.floor((Date.now() - started) / 1000));
    if (visible && seconds > 0 && crypto.randomUUID) {
      queue.push({ id: crypto.randomUUID(), section: config.content, action: "engagement", duration_seconds: seconds });
      queue = queue.slice(-100);
    }
    started = Date.now();
  };
  const flush = async () => {
    if (sending || !queue.length) return;
    sending = true; const batch = queue.slice(0, 20);
    try {
      const response = await fetch("/events/activity/", { method: "POST", credentials: "same-origin", keepalive: true, headers: { "Content-Type": "application/json", "X-CSRFToken": csrf }, body: JSON.stringify({ events: batch }) });
      if (response.ok) { const ids = new Set(batch.map(event => event.id)); queue = queue.filter(event => !ids.has(event.id)); }
    } catch { /* Retry the batch while this page remains open. */ }
    finally { sending = false; }
  };
  document.addEventListener("pointerup", event => {
    if (!event.isPrimary || document.hidden || !crypto.randomUUID) return;
    queue.push({ id: crypto.randomUUID(), section: config.content, action: "click", x: Math.round(Math.max(0, Math.min(100, event.clientX / innerWidth * 100))), y: Math.round(Math.max(0, Math.min(100, event.clientY / innerHeight * 100))), area: "screen", viewport: innerWidth <= 600 ? "mobile" : innerWidth <= 1100 ? "tablet" : "desktop" });
    queue = queue.slice(-100);
    if (queue.length >= 10) void flush();
  }, { passive: true });
  const timer = setInterval(() => { heartbeat(); void flush(); }, 10000);
  document.addEventListener("visibilitychange", () => {
    heartbeat(); visible = !document.hidden; void flush();
  });
  window.addEventListener("pagehide", () => { heartbeat(); visible = false; void flush(); clearInterval(timer); });
})();
