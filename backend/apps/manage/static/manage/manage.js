(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var root = document.documentElement;

  /* ---- light / dark ---- */
  var themeBtn = $("#mg-theme");
  function paintTheme() {
    if (!themeBtn) return;
    var dark = root.getAttribute("data-theme") === "dark";
    themeBtn.setAttribute("aria-pressed", dark ? "true" : "false");
    themeBtn.setAttribute("aria-label", dark ? "حالت روشن" : "حالت تیره");
  }
  if (themeBtn) {
    paintTheme();
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("manage-theme", next); } catch (e) {}
      paintTheme();
    });
  }

  /* ---- on a phone the rail and the page column are bars: show where you are ---- */
  if (window.matchMedia && window.matchMedia("(max-width: 900px)").matches) {
    [".mg-mod.on", ".mg-page.on"].forEach(function (s) {
      var on = $(s);
      if (on && on.scrollIntoView) on.scrollIntoView({ block: "nearest", inline: "center" });
    });
    window.scrollTo(0, 0);
  }

  /* ---- the command window: pages and actions here, the rest from the server ---- */
  var pal = $("#mg-pal"), input = $("#mg-pal-q"), list = $("#mg-pal-list");
  if (!pal || !input || !list) return;
  var jumpEl = document.getElementById("mg-jump");
  var jump = jumpEl ? JSON.parse(jumpEl.textContent) : [];
  var results = [], active = 0, timer = null, opener = null;

  function local(q) {
    q = q.trim();
    return jump.filter(function (j) { return !q || j.label.indexOf(q) !== -1 || j.group.indexOf(q) !== -1; })
      .map(function (j) { return { label: j.label, type: j.group, url: j.url }; });
  }
  function paint() {
    list.innerHTML = "";
    results.forEach(function (r, i) {
      var li = document.createElement("li"), a = document.createElement("a"), t = document.createElement("span"), s = document.createElement("small");
      a.href = r.url;
      a.id = "mg-opt-" + i;
      a.setAttribute("role", "option");
      a.setAttribute("aria-selected", i === active ? "true" : "false");
      if (i === active) a.className = "on";
      t.textContent = r.label;
      s.textContent = r.type;
      a.appendChild(t); a.appendChild(s); li.appendChild(a); list.appendChild(li);
    });
    if (!results.length) {
      var li = document.createElement("li");
      li.className = "none";
      li.textContent = "چیزی پیدا نشد. نام صفحه، عنوان مطلب، شمارهٔ تلفن کاربر یا نام دارو را امتحان کن.";
      list.appendChild(li);
    }
    input.setAttribute("aria-activedescendant", results.length ? "mg-opt-" + active : "");
    var on = $("#mg-opt-" + active);
    if (on && on.scrollIntoView) on.scrollIntoView({ block: "nearest" });
  }
  function open() {
    opener = document.activeElement;
    results = local("");
    active = 0;
    input.value = "";
    paint();
    if (pal.showModal) pal.showModal(); else pal.setAttribute("open", "");
    input.focus();
  }
  pal.addEventListener("close", function () { if (opener && opener.focus) opener.focus(); });
  pal.addEventListener("click", function (e) { if (e.target === pal) pal.close(); });

  var openBtn = $("#mg-open-cmd");
  if (openBtn) openBtn.addEventListener("click", open);
  document.addEventListener("keydown", function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); open(); }
    else if (e.key === "/" && !typing && !pal.open) { e.preventDefault(); open(); }
  });

  input.addEventListener("input", function () {
    var q = input.value;
    results = local(q);
    active = 0;
    paint();
    clearTimeout(timer);
    if (q.trim().length < 2 || !window.MANAGE) return;
    timer = setTimeout(function () {
      fetch(window.MANAGE.search + "?q=" + encodeURIComponent(q.trim()), { credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (input.value !== q) return;
          results = local(q).concat(d.results || []);
          paint();
        })
        .catch(function () {});
    }, 220);
  });
  input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown") { e.preventDefault(); active = Math.min(active + 1, results.length - 1); paint(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); active = Math.max(active - 1, 0); paint(); }
    else if (e.key === "Enter" && results[active]) { e.preventDefault(); window.location = results[active].url; }
    // a search field's first Escape would only clear it
    else if (e.key === "Escape") { e.preventDefault(); pal.close(); }
  });
})();
