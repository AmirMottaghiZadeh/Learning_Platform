(() => {
  const root = document.getElementById("support-chat");
  if (!root) return;
  const list = document.getElementById("support-messages"), form = document.getElementById("support-form"), input = document.getElementById("support-text"), error = document.getElementById("support-error"), older = document.getElementById("support-older");
  const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;
  let sending = false, polling = false, clientId = crypto.randomUUID(), pendingText = "";
  const ids = () => [...list.querySelectorAll("[data-id]")].map(el => Number(el.dataset.id));
  // Advance only across messages fetched from the server. A local staff reply
  // can have a higher ID than a concurrent user message we have not fetched yet.
  let receivedThrough = Math.max(0, ...ids());
  const post = async (url, body) => {
    const response = await fetch(url, { method: "POST", credentials: "same-origin", headers: { "X-CSRFToken": csrf }, body: new URLSearchParams(body) });
    if (!response.ok) throw new Error("ارسال انجام نشد؛ اتصال یا اعتبار ورود را بررسی کنید.");
    return response.json();
  };
  function append(message) {
    if (list.querySelector('[data-id="' + message.id + '"]')) return;
    document.getElementById("support-empty")?.remove();
    const article = document.createElement("article");
    article.className = "sp-message" + (message.from_staff ? " from-staff" : ""); article.dataset.id = message.id;
    const p = document.createElement("p"), time = document.createElement("time"); p.textContent = message.text;
    const parts = Object.fromEntries(new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Tehran", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(new Date(message.created_at)).map(part => [part.type, part.value]));
    time.textContent = `${parts.month}/${parts.day} ${parts.hour}:${parts.minute} · ` + (message.from_staff ? "پشتیبانی" : "کاربر");
    article.append(p, time);
    const next = [...list.querySelectorAll("[data-id]")].find(node => Number(node.dataset.id) > message.id);
    if (next) next.before(article); else list.append(article);
  }
  async function acknowledge() {
    const last = receivedThrough;
    if (last && !document.hidden) await post(root.dataset.read, { through: last });
  }
  async function poll() {
    if (document.hidden || polling) return;
    polling = true;
    try {
      const response = await fetch(root.dataset.list + "?after=" + receivedThrough, { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("دریافت پیام‌های تازه انجام نشد؛ دوباره تلاش می‌شود.");
      const data = await response.json(), atBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 100;
      data.messages.forEach(message => append(message));
      receivedThrough = Math.max(receivedThrough, ...data.messages.map(message => message.id));
      if (atBottom) list.scrollTop = list.scrollHeight;
      await acknowledge(); error.textContent = "";
    } catch (e) { error.textContent = e.message; }
    finally { polling = false; }
  }
  form.addEventListener("submit", async event => {
    event.preventDefault(); if (sending || !input.value.trim()) return;
    const draft = input.value.trim();
    if (pendingText !== draft) { pendingText = draft; clientId = crypto.randomUUID(); }
    sending = true; form.querySelector("button").disabled = true;
    try {
      const message = await post(form.action, { text: draft, client_id: clientId });
      append(message); if (input.value.trim() === draft) input.value = "";
      pendingText = ""; clientId = crypto.randomUUID(); error.textContent = ""; list.scrollTop = list.scrollHeight;
    } catch (e) { error.textContent = e.message; }
    finally { sending = false; form.querySelector("button").disabled = false; }
  });
  older.addEventListener("click", async () => {
    const first = Math.min(...ids()); if (!Number.isFinite(first)) { older.hidden = true; return; }
    older.disabled = true;
    try {
      const response = await fetch(root.dataset.list + "?before=" + first, { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("پیام‌های قدیمی دریافت نشدند.");
      const data = await response.json(), height = list.scrollHeight;
      data.messages.forEach(message => append(message));
      older.hidden = !data.has_older; list.scrollTop += list.scrollHeight - height;
    } catch (e) { error.textContent = e.message; }
    finally { older.disabled = false; }
  });
  list.scrollTop = list.scrollHeight; void poll();
  const timer = setInterval(poll, 3000);
  window.addEventListener("pagehide", () => clearInterval(timer));
  document.addEventListener("visibilitychange", () => { if (!document.hidden) void poll(); });
})();
