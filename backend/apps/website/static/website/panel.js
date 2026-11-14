(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var FA = "۰۱۲۳۴۵۶۷۸۹";
  var fa = function (n) { return String(n).replace(/\d/g, function (d) { return FA[d]; }); };
  var csrf = function () { var i = $("input[name=csrfmiddlewaretoken]"); return i ? i.value : ""; };

  /* ---- dialogs ---- */
  document.addEventListener("click", function (e) {
    var close = e.target.closest("[data-close]");
    if (close) { var d = close.closest("dialog"); if (d) d.close(); }
  });

  /* ---- confirm before dangerous actions ---- */
  var confirmDlg = $("#confirm"), pending = null;
  function ask(text, then) {
    if (!confirmDlg || !confirmDlg.showModal) { if (window.confirm(text)) then(); return; }
    $("#confirm-text").textContent = text;
    pending = then;
    confirmDlg.showModal();
  }
  if (confirmDlg) {
    $("#confirm-yes").addEventListener("click", function () { confirmDlg.close(); var f = pending; pending = null; if (f) f(); });
    $("#confirm-no").addEventListener("click", function () { pending = null; confirmDlg.close(); });
  }
  document.addEventListener("submit", function (e) {
    var form = e.target, sub = e.submitter;
    if (form.__ok) { form.__ok = false; return; }
    var text = (sub && sub.getAttribute("data-confirm")) || form.getAttribute("data-confirm");
    if (!text && sub && sub.hasAttribute("data-confirm-bulk")) {
      var n = $$("input[name=ids]:checked", form).length;
      if (!n) { e.preventDefault(); alert("ابتدا چند مورد را انتخاب کنید."); return; }
      text = "برای " + fa(n) + " مورد انتخاب‌شده اجرا شود؟";
    }
    if (!text) return;
    e.preventDefault();
    ask(text, function () { form.__ok = true; if (form.requestSubmit) form.requestSubmit(sub || undefined); else form.submit(); });
  }, true);

  /* ---- select all ---- */
  $$("[data-all]").forEach(function (box) {
    box.addEventListener("change", function () {
      $$("input[name=ids]", box.closest("table")).forEach(function (c) { c.checked = box.checked; });
    });
  });

  /* ---- comment reply ---- */
  var replyDlg = $("#reply-dialog");
  $$("[data-reply]").forEach(function (b) {
    b.addEventListener("click", function () {
      $("#reply-id").value = b.getAttribute("data-reply");
      $("#reply-title").textContent = "پاسخ به " + b.getAttribute("data-name");
      replyDlg.showModal();
      $("#reply-text").focus();
    });
  });

  /* ---- media drop zone ---- */
  var drop = $("#drop");
  if (drop) {
    ["dragenter", "dragover"].forEach(function (n) { drop.addEventListener(n, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (n) { drop.addEventListener(n, function (e) { e.preventDefault(); drop.classList.remove("over"); }); });
    drop.addEventListener("drop", function (e) {
      var input = $("input[type=file]", drop);
      if (e.dataTransfer && e.dataTransfer.files.length) { input.files = e.dataTransfer.files; drop.submit(); }
    });
  }

  /* ---- media picker (cover + editor images) ---- */
  var picker = $("#picker"), pickGrid = $("#pick-grid"), pickCb = null;
  function loadPicker() {
    fetch(window.PANEL.picker + "?type=image", { credentials: "same-origin" }).then(function (r) { return r.json(); }).then(function (d) {
      pickGrid.innerHTML = "";
      d.items.forEach(function (m) {
        var b = document.createElement("button"), img = document.createElement("img");
        b.type = "button"; b.title = m.title; img.src = m.url; img.alt = m.alt || m.title; img.loading = "lazy";
        b.appendChild(img);
        b.addEventListener("click", function () { picker.close(); if (pickCb) pickCb(m); });
        pickGrid.appendChild(b);
      });
      if (!d.items.length) pickGrid.textContent = "هنوز تصویری بارگذاری نشده است.";
    });
  }
  function openPicker(cb) { if (!picker) return; pickCb = cb; loadPicker(); picker.showModal(); }
  function uploadFiles(files) {
    var fd = new FormData();
    Array.prototype.forEach.call(files, function (f) { fd.append("files", f); });
    fd.append("csrfmiddlewaretoken", csrf());
    fetch(window.PANEL.upload, { method: "POST", body: fd, credentials: "same-origin", headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (r) { return r.json(); }).then(function (d) {
        if (d.errors && d.errors.length) alert(d.errors.join("\n"));
        if (d.items && d.items.length) { picker.close(); if (pickCb) pickCb(d.items[0]); }
      });
  }
  var pickFile = $("#pick-file"), pickDrop = $("#pick-drop");
  if (pickFile) pickFile.addEventListener("change", function () { if (pickFile.files.length) uploadFiles(pickFile.files); });
  if (pickDrop) {
    pickDrop.addEventListener("dragover", function (e) { e.preventDefault(); pickDrop.classList.add("over"); });
    pickDrop.addEventListener("dragleave", function () { pickDrop.classList.remove("over"); });
    pickDrop.addEventListener("drop", function (e) { e.preventDefault(); pickDrop.classList.remove("over"); if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files); });
  }

  /* ---- visual editor ---- */
  function buildEditor(ta) {
    var wrap = document.createElement("div");
    var tools = document.createElement("div"); tools.className = "ed-tools"; tools.setAttribute("role", "toolbar"); tools.setAttribute("aria-label", "ابزار ویرایش");
    var body = document.createElement("div"); body.className = "ed-body"; body.contentEditable = "true"; body.setAttribute("role", "textbox"); body.setAttribute("aria-multiline", "true"); body.setAttribute("aria-label", "متن مطلب");
    var src = document.createElement("textarea"); src.className = "ed-src"; src.hidden = true; src.setAttribute("aria-label", "کد HTML");
    body.innerHTML = ta.value || "<p><br></p>";
    ta.hidden = true; ta.parentNode.insertBefore(wrap, ta); wrap.appendChild(tools); wrap.appendChild(body); wrap.appendChild(src); wrap.appendChild(ta);
    var sourceMode = false;
    function exec(cmd, val) { body.focus(); document.execCommand(cmd, false, val || null); sync(); }
    function block(tag) { exec("formatBlock", tag); }
    function wrapBlock(cls, html) {
      body.focus();
      var sel = window.getSelection(), text = sel && sel.toString() ? sel.toString() : "متن را اینجا بنویسید";
      document.execCommand("insertHTML", false, '<div class="' + cls + '">' + (html || "<p>" + text + "</p>") + "</div><p><br></p>"); sync();
    }
    function align(cls) {
      var sel = window.getSelection(); if (!sel.rangeCount) return;
      var node = sel.anchorNode; if (node.nodeType === 3) node = node.parentNode;
      while (node && node !== body && !/^(P|H2|H3|H4)$/.test(node.nodeName)) node = node.parentNode;
      if (!node || node === body) return;
      ["ta-center", "ta-right", "ta-left"].forEach(function (c) { node.classList.remove(c); });
      if (cls) node.classList.add(cls); sync();
    }
    var cmds = [
      ["H2", "عنوان بخش", function () { block("h2"); }], ["H3", "زیرعنوان", function () { block("h3"); }], ["¶", "پاراگراف", function () { block("p"); }], "|",
      ["B", "پررنگ", function () { exec("bold"); }], ["I", "کج", function () { exec("italic"); }], ["U", "زیرخط", function () { exec("underline"); }], "|",
      ["•", "فهرست نقطه‌ای", function () { exec("insertUnorderedList"); }], ["۱.", "فهرست شماره‌دار", function () { exec("insertOrderedList"); }], ["❝", "نقل‌قول", function () { block("blockquote"); }], "|",
      ["⟷", "وسط‌چین", function () { align("ta-center"); }], ["⇥", "راست‌چین", function () { align(""); }], "|",
      ["پیوند", "افزودن پیوند", function () { var u = prompt("نشانی پیوند (https://…):"); if (u) exec("createLink", u); }],
      ["تصویر", "درج تصویر", function () { openPicker(function (m) { exec("insertHTML", '<figure><img src="' + m.url + '" alt="' + (m.alt || m.title).replace(/"/g, "&quot;") + '"></figure><p><br></p>'); }); }],
      ["جدول", "جدول ۳×۳", function () { var r = "<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>"; exec("insertHTML", "<table><tbody>" + r + r + r + "</tbody></table><p><br></p>"); }],
      ["—", "خط جداکننده", function () { exec("insertHorizontalRule"); }], "|",
      ["نکته", "کادر نکته", function () { wrapBlock("callout"); }],
      ["دکمهٔ اپ", "بلوک دانلود اپ", function () { wrapBlock("cta-app", '<p>فارمنتا را نصب کنید</p><p><a href="/download/">دانلود اپ</a></p>'); }], "|",
      ["↶", "واگرد", function () { exec("undo"); }], ["↷", "ازنو", function () { exec("redo"); }], ["پاک", "پاک کردن قالب", function () { exec("removeFormat"); }], "|",
      ["HTML", "نمایش کد", function () { toggleSource(); }]
    ];
    cmds.forEach(function (c) {
      if (c === "|") { var s = document.createElement("span"); s.className = "sp"; tools.appendChild(s); return; }
      var b = document.createElement("button"); b.type = "button"; b.textContent = c[0]; b.title = c[1]; b.setAttribute("aria-label", c[1]);
      b.addEventListener("mousedown", function (e) { e.preventDefault(); });
      b.addEventListener("click", function () { c[2](); });
      if (c[0] === "HTML") b.dataset.src = "1";
      tools.appendChild(b);
    });
    function sync() {
      ta.value = sourceMode ? src.value : body.innerHTML;
      var text = (body.textContent || "").trim(), words = text ? text.split(/\s+/).length : 0;
      var wc = $("#wc"), rt = $("#rt");
      if (wc) wc.textContent = fa(words) + " کلمه";
      if (rt) rt.textContent = fa(Math.max(1, Math.ceil(words / 180))) + " دقیقه مطالعه";
      document.dispatchEvent(new CustomEvent("editor-change"));
    }
    function toggleSource() {
      sourceMode = !sourceMode;
      var btn = $("[data-src]", tools);
      if (sourceMode) { src.value = body.innerHTML; src.hidden = false; body.hidden = true; if (btn) btn.classList.add("on"); }
      else { body.innerHTML = src.value || "<p><br></p>"; src.hidden = true; body.hidden = false; if (btn) btn.classList.remove("on"); }
      sync();
    }
    body.addEventListener("input", sync);
    src.addEventListener("input", sync);
    body.addEventListener("paste", function (e) {
      var cd = e.clipboardData; if (!cd) return;
      var text = cd.getData("text/plain"); if (!text) return;
      e.preventDefault();
      var html = text.split(/\n{2,}/).map(function (p) { return "<p>" + p.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/\n/g, "<br>") + "</p>"; }).join("");
      document.execCommand("insertHTML", false, html); sync();
    });
    ta.form && ta.form.addEventListener("submit", function () { ta.value = sourceMode ? src.value : body.innerHTML; });
    sync();
    return { body: body };
  }
  $$("textarea[data-editor]").forEach(buildEditor);

  /* ---- post form: cover, slug, SEO ---- */
  var form = $("#postform");
  if (form) {
    var coverBox = $("#cover-box"), coverInput = $("#id_cover"), clear = $("#cover-clear");
    function setCover(m) {
      coverInput.value = m ? m.id : "";
      coverBox.style.backgroundImage = m ? "url('" + m.url + "')" : "";
      coverBox.textContent = m ? "" : "انتخاب یا بارگذاری تصویر";
      document.dispatchEvent(new CustomEvent("editor-change"));
    }
    if (coverBox) {
      coverBox.addEventListener("click", function () { openPicker(setCover); });
      coverBox.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openPicker(setCover); } });
    }
    if (clear) clear.addEventListener("click", function () { setCover(null); });

    var title = $("[name=title]", form), slug = $("[name=slug]", form), desc = $("[name=seo_description]", form), stitle = $("[name=seo_title]", form), excerpt = $("[name=excerpt]", form);
    var slugTouched = !!(slug && slug.value);
    function slugify(t) { return t.replace(/‌/g, "-").replace(/[^؀-ۿa-zA-Z0-9\s-]/g, "").trim().replace(/\s+/g, "-").toLowerCase().slice(0, 100); }
    if (slug) slug.addEventListener("input", function () { slugTouched = true; });
    if (title && slug) title.addEventListener("input", function () { if (!slugTouched) slug.value = slugify(title.value); });

    var snT = $("#sn-title"), snU = $("#sn-url"), snD = $("#sn-desc"), score = $("#seo-score"), bar = $("#seo-bar"), list = $("#seo-checks");
    function plain() { var d = $(".ed-body"); return d ? d.textContent : ""; }
    function seo() {
      var t = (stitle && stitle.value) || (title && title.value) || "", d = (desc && desc.value) || (excerpt && excerpt.value) || plain().trim().slice(0, 160);
      if (snT) snT.textContent = t || "عنوان مطلب";
      if (snU) snU.textContent = "pharmenta.ir › blog › " + ((slug && slug.value) || "…");
      if (snD) snD.textContent = d || "توضیح مطلب اینجا نمایش داده می‌شود.";
      var bodyEl = $(".ed-body"), html = bodyEl ? bodyEl.innerHTML : "", words = plain().trim().split(/\s+/).filter(Boolean).length;
      var imgs = bodyEl ? $$("img", bodyEl) : [];
      var checks = [
        [t.length >= 25 && t.length <= 65, "عنوان بین ۲۵ تا ۶۵ نویسه (اکنون " + fa(t.length) + ")", 20],
        [d.length >= 70 && d.length <= 160, "توضیح سئو بین ۷۰ تا ۱۶۰ نویسه (اکنون " + fa(d.length) + ")", 20],
        [words >= 300, "متن حداقل ۳۰۰ کلمه (اکنون " + fa(words) + ")", 20],
        [/<h2/i.test(html), "حداقل یک عنوان بخش (H2)", 15],
        [!!(coverInput && coverInput.value), "تصویر شاخص انتخاب شده", 15],
        [/<a [^>]*href/i.test(html), "حداقل یک پیوند در متن", 5],
        [imgs.every(function (i) { return i.getAttribute("alt"); }), "همهٔ تصویرها متن جایگزین دارند", 5]
      ];
      var total = 0; if (list) list.innerHTML = "";
      checks.forEach(function (c) {
        if (c[0]) total += c[2];
        if (list) { var li = document.createElement("li"); if (c[0]) li.className = "ok"; li.textContent = c[1]; list.appendChild(li); }
      });
      if (score) score.textContent = fa(total) + " / ۱۰۰";
      if (bar) { bar.style.width = total + "%"; bar.style.background = total >= 80 ? "var(--ok)" : total >= 50 ? "var(--amber)" : "var(--bad)"; }
    }
    ["input", "change"].forEach(function (ev) { form.addEventListener(ev, seo); });
    document.addEventListener("editor-change", seo);
    seo();
  }
})();
