/* Local design review only. No provider, authentication or payment requests. */
const icons = {
  search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/>',
  arrow:'<path d="M20 12H4m6-6-6 6 6 6"/>',
  chevron:'<path d="m14 6-6 6 6 6"/>',
  down:'<path d="m6 9 6 6 6-6"/>',
  home:'<path d="m3 10 9-7 9 7v10H3zM9 20v-7h6v7"/>',
  book:'<path d="M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1v15"/>',
  user:'<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  send:'<path d="m3 11 18-8-8 18-2-8-8-2zM11 13l10-10"/>',
  wallet:'<path d="M20 7H4V4h14v3M3 7v13h18V7H3m18 5h-6v4h6"/>',
  file:'<path d="M14 3H5v18h14V8l-5-5zm0 0v6h5M8 13h8M8 17h6"/>',
  folder:'<path d="M3 6h7l2 3h9v11H3V6z"/>',
  calculator:'<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 5h8v4H8zM8 13h1m6 0h1m-8 4h1m6 0h1"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  grid:'<rect x="3" y="3" width="18" height="18" rx="1"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
  expand:'<path d="M9 3H3v6m12-6h6v6M3 15v6h6m6 0h6v-6"/>',
  like:'<path d="M7 10 11 3c2 0 3 1 2 4l-1 3h7c2 0 2 2 1 4l-2 6H7zM3 10h4v11H3z"/>',
  dislike:'<path d="m7 14 4 7c2 0 3-1 2-4l-1-3h7c2 0 2-2 1-4l-2-6H7zM3 3h4v11H3z"/>',
  heart:'<path d="M21 8c0 5-9 12-9 12S3 13 3 8a5 5 0 0 1 9-3 5 5 0 0 1 9 3z"/>',
  bookmark:'<path d="M6 3h12v18l-6-4-6 4V3z"/>',
  close:'<path d="m6 6 12 12M6 18 18 6"/>',
  signal:'<path d="M4 19v-3m5 3v-7m5 7V8m5 11V4"/>',
  battery:'<rect x="2" y="7" width="18" height="10" rx="2"/><path d="M22 10v4M5 10h10v4H5z"/>',
};
const icon = (name, cls='') => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.file}</svg>`;
const escapeHtml = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const titles = {
  home: [
    ['کارت هم‌خانواده','کارت سفید، هم‌تراز با منابع و ورودی مشخص برای جست‌وجو.'],
    ['پرسش مستقیم','نوشتن سؤال از خود خانه؛ ادامه در صفحهٔ سرچ.'],
    ['ردیف فشرده','ورودی کم‌ارتفاع با تمرکز بیشتر روی سایر بخش‌های خانه.'],
    ['دعوت به پرسیدن','متن شاخص و یک دکمهٔ سبز، بدون کادر جست‌وجوی نمایشی.'],
    ['میان‌برهای بالینی','شروع با پرسش دلخواه یا یک نمونهٔ کوتاه از خانه.'],
  ],
  search: [
    ['گفت‌وگوی آرام','پرسش‌ها در یک کارت؛ پاسخ و منابع در حباب‌های خوانا.'],
    ['میز کار منابع','چهار کارت پیشنهادی؛ رسانه و پاسخ روی زمینهٔ باز.'],
    ['برگهٔ مطالعه','سطح سفید و متن پیوسته؛ کمترین تعداد کادر در نتیجه.'],
    ['پرسش در مرکز','کادر بزرگ در ابتدا؛ نتیجه در یک برگهٔ متمرکز.'],
    ['یادداشت بالینی','پرسش‌های مستقل و پاسخ به شکل یادداشت با منابع جمع‌شده.'],
  ],
  content: [
    ['صفحهٔ اختصاصی','نوع محتوا از ابتدا روشن است؛ فهرست یا ابزار، صفحهٔ خود را دارد.'],
    ['برگهٔ از پایین','ابزار یا فهرست روی صفحهٔ قبلی باز می‌شود؛ بازگشت سریع.'],
    ['پنل موضوعی','زیرموضوع‌ها به شکل کارت انتخاب؛ ورودی ابزار در یک پنل مستقل.'],
    ['راهنمای مسیر','ساختار شاخه‌ای برای فهرست؛ فرم عمودی و خوانا برای ابزار.'],
  ],
};
const suggestions = [
  'دارودرمانی بزرگی خوش‌خیم پروستات با چه داروها و دوزهایی انجام می‌شود؟',
  'عوارض مهم آریپیپرازول و نحوهٔ پایش آن‌ها چیست؟',
  'در کودک مبتلا به تب بدون کانون، ارزیابی اولیه چیست؟',
  'الگوریتم ارزیابی کم‌خونی میکروسیتیک را پیدا کن.',
];
const params = new URLSearchParams(location.search);
let group = params.get('group') || 'home';
if (!['home','search','content','table'].includes(group)) group = 'home';
let searchState = params.get('state') || 'empty';
let contentState = params.get('kind') || 'directory';
const single = Number(params.get('variant') || 0);
const board = params.get('board') === '1';
if (single) document.body.classList.add('single');
if (board) document.body.classList.add('board');
if (params.get('theme') === 'dark') document.documentElement.dataset.theme = 'dark';
const drafts = new Map();

function statusbar() {
  return `<div class="statusbar"><span>9:41</span><span class="status-icons">${icon('signal')}${icon('battery')}</span></div>`;
}
function chrome() {
  return `<div class="chrome"><button data-action="theme" aria-label="تغییر تم">${icon('sun')}</button><button data-action="language" aria-label="زبان پیش‌نمایش">EN</button></div>`;
}
function header(title='سرچ هوشمند') {
  return `${statusbar()}<header class="app-top search-top"><div class="row"><button class="back" data-action="back" aria-label="بازگشت">${icon('chevron')}</button><h1>${title}</h1>${chrome()}</div></header>`;
}
function homeHeader() {
  return `${statusbar()}<header class="app-top"><div class="row between"><span class="brand">${icon('book')}فارمنتا</span>${chrome()}</div><h2>دانش بالینی، در دسترس</h2><p>مرور منابع، یادگیری و تصمیم‌گیری بالینی</p></header>`;
}
function nav() {
  return `<nav class="bottom-nav" aria-label="ناوبری اپ"><button class="active" data-action="home">${icon('home')}خانه</button><button data-action="demo" data-message="این دکمه در اپ، دارونامه را باز می‌کند.">${icon('book')}دارونامه</button><button data-action="demo" data-message="این دکمه در اپ، پروفایل را باز می‌کند.">${icon('user')}پروفایل</button></nav>`;
}
function wallet() {
  return `<div class="wallet">${icon('wallet')}<span>اعتبار شما</span><strong>۱۰۰</strong><button data-action="wallet">مدیریت و شارژ</button></div>`;
}
function homeCard(v) {
  const heading = `<div class="row between"><h3>سرچ هوشمند</h3>${icon('search','icon-lg')}</div>`;
  if (v === 1) return `<button class="home-search home-v1 card" data-action="open-search">${heading}<p class="card-note">پرسش از منابع معتبر بالینی</p><div class="search-affordance">سؤال بالینی خود را بپرسید${icon('arrow')}</div></button>`;
  if (v === 2) return `<div class="home-search home-v2 card">${heading}<label class="sr-label" for="home-draft-${v}"><span class="card-note">سؤال بالینی شما</span></label><textarea id="home-draft-${v}" placeholder="مثلاً: ارزیابی بیمار با کم‌خونی…" aria-label="سؤال بالینی شما"></textarea><button class="primary" data-action="open-search">ادامه در سرچ هوشمند${icon('arrow')}</button></div>`;
  if (v === 3) return `<button class="home-search home-v3 card" data-action="open-search"><div class="grow"><h3>سرچ هوشمند</h3><p class="card-note">سؤال بالینی ← پاسخ همراه منبع</p></div><span class="open-round">${icon('arrow')}</span></button>`;
  if (v === 4) return `<div class="home-search home-v4"><span class="source-label">سرچ هوشمند · منابع بالینی</span><h3>سؤال از شما،<br>پاسخ در متن منبع</h3><p class="card-note">از سؤال تا بخش مرتبط مقاله</p><div class="footer-action"><button class="primary" data-action="open-search">پرسش بالینی جدید${icon('arrow')}</button></div></div>`;
  return `<div class="home-search home-v5 card"><button class="row between" data-action="open-search" style="width:100%;padding:0;min-height:44px">${heading}${icon('chevron')}</button><p class="card-note">سؤال خودت یا یک شروع پیشنهادی</p><div class="prompt-pair"><button data-action="open-search" data-question="عوارض مهم آریپیپرازول چیست؟">عوارض مهم آریپیپرازول${icon('arrow')}</button><button data-action="open-search" data-question="درمان اولیهٔ آسم در بزرگسالان چیست؟">درمان اولیهٔ آسم در بزرگسالان${icon('arrow')}</button></div></div>`;
}
function homePhone(v) {
  return `<div class="phone home-phone">${homeHeader()}<div class="phone-main">${homeCard(v)}<div class="card reference-card"><div class="reference-symbol">U<span style="font-size:16px">TD</span></div><div class="grow"><h3>UpToDate</h3><p>مرجع موضوعات و مقالات بالینی</p></div>${icon('chevron')}</div><div class="section-title">مسیرهای شما</div><div class="entry-grid"><button data-action="demo" data-message="مسیر آموزش در اپ باز می‌شود.">${icon('book')}آموزش</button><button data-action="demo" data-message="مسیر بالینی در اپ باز می‌شود.">${icon('heart')}بالینی</button></div><div class="card"><div class="row between"><h3>ادامهٔ مطالعه</h3>${icon('bookmark')}</div><p class="card-note">مقاله‌های ذخیره‌شده را در کتابخانه دنبال کنید.</p></div></div>${nav()}</div>`;
}
function composer(v, inline=false) {
  const saved = escapeHtml(drafts.get(v) || '');
  if (inline) return `<div class="focus-question"><label for="question-${v}">سؤال بالینی شما</label><textarea id="question-${v}" placeholder="سؤال، سناریوی بالینی یا نام موضوع…">${saved}</textarea><div class="row between"><small class="muted">پاسخ همراه ارجاع به متن اصلی</small><button class="primary" data-action="search" aria-label="جست‌وجوی نمونه">${icon('arrow')}</button></div></div>`;
  return `<form class="composer ${v === 3 || v === 5 ? 'composer-compact' : ''}"><textarea id="question-${v}" placeholder="سؤال خود را بنویسید…" aria-label="سؤال بالینی شما">${saved}</textarea><button type="submit" class="primary" aria-label="جست‌وجوی نمونه">${icon('send')}</button></form>`;
}
function suggestionButtons(v) {
  return suggestions.map((q,i) => `<button class="suggestion" data-action="suggestion" data-question="${escapeHtml(q)}">${v === 3 ? `<span class="question-index">${['۰۱','۰۲','۰۳','۰۴'][i]}</span>` : ''}<span>${q}</span>${icon('arrow')}</button>`).join('');
}
function searchEmpty(v) {
  if (v === 4) return `<div class="phone-main search-v4"><div class="search-intro"><h2>چه سؤالی دارید؟</h2><p>پرسش را بنویسید؛ متن مرتبط در منابع پیدا می‌شود.</p></div>${composer(v,true)}<div class="section-title">برای شروع، یک سؤال انتخاب کنید</div><div class="suggestion-list">${suggestionButtons(v)}</div></div>`;
  const heads = {
    1:['پرسش شما، متن اصلی منبع','پرسش بالینی‌تان را بنویسید و پاسخ را کنار منبع بخوانید.'],
    2:['امروز دنبال چه موضوعی هستید؟','درمان، دارو، سناریوی بالینی یا یک جدول در منابع.'],
    3:['از سؤال شروع کنید.','بخش مرتبط منبع، همراه یک پاسخ کوتاه فارسی.'],
    5:['یک سؤال بالینی بپرسید','پاسخ مستند را در قالب یادداشت، همراه منبع مرور کنید.'],
  };
  const [title,description] = heads[v];
  return `<div class="phone-main search-v${v}"><div class="search-intro"><h2>${title}</h2><p>${description}</p></div>${v === 5 ? '<div class="prompt-head">چند پیشنهاد برای شروع</div>' : '<div class="question-label">پرسش‌های پیشنهادی</div>'}<div class="${v === 2 ? 'suggestion-grid' : 'suggestion-list'}">${suggestionButtons(v)}</div><p class="small muted">با انتخاب پیشنهاد، فقط کادر سؤال پر می‌شود.</p></div>${composer(v)}`;
}
function miniTable() {
  return `<table class="mini-table"><thead><tr><th>Source section</th><th>What to read</th><th>Related material</th></tr></thead><tbody><tr><td>Selection and dosing</td><td>Initial pharmacologic agents</td><td>Table 5</td></tr><tr><td>Alternatives</td><td>Patient-specific considerations</td><td>Related topics</td></tr><tr><td>Special considerations</td><td>Exceptions and prescribing considerations</td><td>Original article</td></tr></tbody></table>`;
}
function media() {
  return `<section class="media"><div class="row">${icon('grid')}<span>رسانهٔ منبع · نمونهٔ طراحی</span></div><button class="media-open" data-action="table" aria-label="باز کردن جدول کامل">${miniTable()}</button><div class="media-foot"><span>جدول کامل؛ برای مشاهدهٔ جزئیات باز کنید</span>${icon('expand')}</div></section>`;
}
function sources() {
  return `<details class="source-disclosure"><summary>بخش‌های مرتبط در منابع${icon('down')}</summary><div class="source-item"><span>UpToDate · عنوان نمایشی</span><p class="ltr">Medical treatment of benign prostatic hyperplasia</p><button data-action="source">باز کردن بخش Selection and dosing${icon('arrow')}</button></div></details>`;
}
function feedback() {
  return `<div class="feedback"><span>این پاسخ مفید بود؟</span><button data-action="feedback" aria-label="پاسخ مفید بود" aria-pressed="false">${icon('like')}</button><button data-action="feedback" aria-label="پاسخ مفید نبود" aria-pressed="false">${icon('dislike')}</button></div>`;
}
function answerBlock(v, loading) {
  return `<section class="answer"><h3>${v === 5 ? 'یادداشت پاسخ' : 'پاسخ فارسی'}</h3>${loading ? '<div class="skeleton" role="status" aria-label="در حال آماده‌سازی پاسخ"><i></i><i></i><i></i></div>' : '<p>در متن نمونه، مسدودکننده‌های گیرندهٔ آلفا به‌عنوان درمان دارویی اولیه مطرح شده‌اند. انتخاب گزینه‌های دیگر به علائم همراه و شرایط بیمار وابسته است؛ جزئیات در بخش «انتخاب و دوز» آمده است.</p><p class="preview-only">بازنویسی متن ارسالی شما برای نمایش طراحی؛ راهنمای درمان نیست.</p>'}</section>`;
}
function resultBody(v) {
  const loading = searchState === 'loading';
  return `<div class="phone-main search-v${v}"><div class="${v === 5 ? 'turn-heading' : 'question-label'}">${v === 5 ? icon('file') : ''}پرسش شما</div><div class="user-question">${escapeHtml(drafts.get(v) || 'دارودرمانی بزرگی خوش‌خیم پروستات چیست؟')}</div>${loading ? '' : media()}${answerBlock(v,loading)}${loading ? `<div class="loading-note"><span class="loading-dot"></span>متن مرتبط پیدا شد؛ پاسخ در حال آماده‌سازی است</div><div class="stream-source"><small>UpToDate · منبع پیدا‌شده</small><p class="ltr">Medical treatment of benign prostatic hyperplasia</p><small>Selection and dosing</small></div>` : `${sources()}${feedback()}`}</div>${composer(v)}`;
}
function searchPhone(v) {
  return `<div class="phone search-phone" data-variant="${v}">${header()}${wallet()}${searchState === 'empty' ? searchEmpty(v) : resultBody(v)}</div>`;
}
function contentHeading() {
  const calc = contentState === 'calculator';
  return `<div class="topic-heading"><div class="content-tag">${icon(calc ? 'calculator' : 'folder')}${calc ? 'ابزار محاسبه' : 'فهرست موضوعی'} · UpToDate</div><h2>${calc ? 'کلیرانس کراتینین' : 'بیماری‌های پروستات'}</h2><p>${calc ? 'فرم اختصاصی ابزار، به‌جای صفحهٔ مقاله' : 'این عنوان، راهنمای ورود به زیرموضوع‌هاست.'}</p></div>`;
}
function directory(v) {
  return `<div class="directory-list">${[
    ['بزرگی خوش‌خیم پروستات','ارزیابی علائم، تشخیص و درمان','Benign prostatic hyperplasia'],
    ['سرطان پروستات','غربالگری، تشخیص و درمان','Prostate cancer'],
  ].map(([title,sub,en],i) => `<button class="topic-row" data-action="topic" data-title="${title}">${v === 4 ? `<span class="branch-index">${i ? '۲' : '۱'}</span>` : ''}<div class="grow"><strong>${title}</strong><small>${sub}</small><small class="ltr">${en}</small></div>${icon('chevron')}${v === 3 ? `<span class="kind">${icon('folder')}ورود به زیرموضوع</span>` : ''}</button>`).join('')}</div><p class="topic-context">انتخاب هر شاخه، زیرموضوع‌های همان بخش را باز می‌کند. ابزار و فهرست، با صفحهٔ مقاله اشتباه گرفته نمی‌شوند.</p>`;
}
function calculator(v) {
  return `<form class="tool-form"><p class="tool-caption">نمونهٔ طراحی فرم؛ در این پیش‌نمایش محاسبهٔ پزشکی انجام نمی‌شود.</p><div class="tool-fields"><label>سن<div class="unit-field"><input type="number" min="18" max="120" inputmode="numeric" placeholder="—" aria-label="سن"><span>سال</span></div></label><label>وزن<div class="unit-field"><input type="number" min="1" inputmode="decimal" placeholder="—" aria-label="وزن"><span>kg</span></div></label><label class="full">کراتینین سرم<div class="unit-field"><input type="number" min="0.1" step="0.1" inputmode="decimal" placeholder="—" aria-label="کراتینین سرم"><span>mg/dL</span></div></label><label class="full">جنسیت<select aria-label="جنسیت"><option value="">انتخاب کنید</option><option>زن</option><option>مرد</option></select></label></div><button class="primary" type="submit">مشاهدهٔ نتیجه${icon('arrow')}</button><div class="tool-output" role="status"></div></form>`;
}
function contextActions() {
  return `<div class="context-actions"><button data-action="source">${icon('book')}توضیحات منبع</button><button data-action="bookmark">${icon('bookmark')}ذخیره</button></div>`;
}
function contentPhone(v) {
  const inner = `${contentHeading()}${contentState === 'calculator' ? calculator(v) : directory(v)}${contextActions()}`;
  if (v === 2) return `<div class="phone content-phone">${header('منابع بالینی')}<div class="phone-main content-v2"><div class="underlay"><h3>موضوع‌های مرتبط</h3><p>مرور منابع و محتوای بالینی</p><div class="faux-text"></div><div class="faux-text" style="width:84%"></div><div class="faux-text" style="width:92%"></div></div><div class="sheet-backdrop"></div><section class="bottom-sheet"><div class="sheet-handle"></div>${inner}</section></div></div>`;
  return `<div class="phone content-phone">${header(contentState === 'calculator' ? 'ابزارهای بالینی' : 'موضوع‌های بالینی')}<div class="phone-main content-v${v}">${inner}</div>${v === 1 || v === 3 ? nav() : ''}</div>`;
}
function tablePhone() {
  return `<article class="design table-demo"><div class="design-heading"><span class="design-number">جدول</span><div><h2>کل جدول در عرض مقاله</h2><p>پیش‌نمایش کوچک و کامل؛ لمس برای نمایش بزرگ. نسخهٔ اصلی سلول‌ها حفظ می‌شود.</p></div></div><div class="phone">${header('مطالعهٔ مقاله')}<div class="phone-main"><h2 class="ltr">Selection and dosing</h2><p>نمونهٔ چیدمان مقاله. جدول در همان عرض متن دیده می‌شود و جزئیات آن با باز کردن نمای تمام‌صفحه در دسترس است.</p><div class="table-original"><button class="media-open" data-action="table" aria-label="باز کردن جدول کامل">${miniTable()}</button><button class="plain-link" data-action="table">${icon('expand')}نمایش تمام‌صفحهٔ جدول</button><p class="sample-caption">این جدول فقط برای بررسی چیدمان است.</p></div><p>مطالعهٔ متن مقاله پس از جدول ادامه دارد. همهٔ لبه‌های سلول‌ها، از جمله مرز بین ستون‌های میانی، حفظ می‌شوند.</p></div></div></article>`;
}
function render() {
  document.querySelectorAll('[data-group]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.group === group)));
  document.getElementById('search-state-label').hidden = group !== 'search';
  document.getElementById('content-state-label').hidden = group !== 'content';
  document.getElementById('search-state').value = searchState;
  document.getElementById('content-state').value = contentState;
  document.getElementById('group-hint').textContent = group === 'home' ? 'روی هر کارت بزنید تا صفحهٔ پرسش باز شود.' : group === 'search' ? 'پیشنهادها فقط کادر را پر می‌کنند؛ ارسال در این صفحه، نمایش نمونهٔ طراحی است.' : group === 'content' ? 'از انتخاب‌گر، هر چهار طرح را با فهرست موضوعی و ابزار مقایسه کنید.' : 'پیش‌نمایش رفتار جدول؛ دادهٔ نمایشی، بدون توصیهٔ پزشکی.';
  const gallery = document.getElementById('gallery');
  gallery.classList.toggle('content-board', group === 'content');
  if (group === 'table') { gallery.innerHTML = tablePhone(); return; }
  gallery.innerHTML = titles[group].map(([title,desc],i) => {
    const v = i + 1;
    if (single && single !== v) return '';
    return `<article class="design" data-design="${group}-${v}"><div class="design-heading"><span class="design-number">${['۱','۲','۳','۴','۵'][i]}</span><div><h2>${title}</h2><p>${desc}</p></div></div>${group === 'home' ? homePhone(v) : group === 'search' ? searchPhone(v) : contentPhone(v)}</article>`;
  }).join('');
}
function announce(text) {
  const el = document.getElementById('announcement');
  el.textContent = text; el.classList.add('visible');
  clearTimeout(announce.timer); announce.timer = setTimeout(() => el.classList.remove('visible'), 3500);
}
function dialog(html) {
  document.getElementById('dialog-content').innerHTML = html;
  document.getElementById('preview-dialog').showModal();
}
document.addEventListener('click', event => {
  const b = event.target.closest('button'); if (!b) return;
  if (b.dataset.group) { group = b.dataset.group; render(); return; }
  const action = b.dataset.action;
  const design = b.closest('.design');
  const v = Number(design?.dataset.design?.split('-')[1] || 1);
  if (action === 'theme' || b.id === 'theme') document.documentElement.dataset.theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  if (action === 'language') announce('این پیش‌نمایش برای انتخاب طراحی فارسی است؛ اپ، حالت انگلیسی را هم دارد.');
  if (action === 'suggestion') {
    const input = design.querySelector('textarea');
    input.value = b.dataset.question; drafts.set(v,input.value); input.focus();
    announce('سؤال داخل کادر قرار گرفت؛ هنوز ارسال نشده است.');
  }
  if (action === 'open-search') {
    const value = b.dataset.question || design.querySelector('textarea')?.value || '';
    drafts.set(v,value); group = 'search'; searchState = 'empty'; render();
    document.querySelector(`[data-design="search-${v}"] textarea`)?.focus();
  }
  if (action === 'back' || action === 'home') { group = 'home'; render(); }
  if (action === 'search') {
    const q = design.querySelector('textarea')?.value?.trim();
    if (!q) { announce('ابتدا یک سؤال بنویسید.'); return; }
    drafts.set(v,q); searchState = 'answer'; render(); announce('پاسخ نمونهٔ طراحی؛ هیچ درخواستی به سرویس ارسال نشده است.');
  }
  if (action === 'table') dialog(`<h2>پیش‌نمایش جدول کامل</h2><p>چیدمان بزرگ جدول؛ برای جابه‌جایی، داخل کادر پیمایش کنید.</p><div class="table-dialog-stage">${miniTable()}</div><p class="small">در اپ، بزرگ‌نمایی، کوچک‌نمایی، لمس دو انگشتی و تمام‌صفحه فعال است.</p>`);
  if (action === 'wallet') dialog('<h2>مدیریت و شارژ اعتبار</h2><p>۱۰۰ اعتبار · موجودی نمونه برای طراحی</p><div class="stack">'+['۱۰۰','۵۰۰','۱۰۰۰'].map(n=>`<button class="secondary" data-action="demo" data-message="پیش‌نمایش طراحی؛ پرداختی انجام نمی‌شود.">بستهٔ ${n} اعتباری</button>`).join('')+'</div><p class="small">قیمت و ماندهٔ واقعی از حساب کاربر در اپ دریافت می‌شود.</p>');
  if (action === 'feedback') {
    b.closest('.feedback').querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',String(el===b)));
    announce('بازخورد در پیش‌نمایش انتخاب شد؛ در پایگاه داده ثبت نمی‌شود.');
  }
  if (action === 'topic') dialog(`<h2>${escapeHtml(b.dataset.title)}</h2><p>در نسخهٔ نهایی، زیرموضوع‌های واقعی همین شاخه اینجا نمایش داده می‌شوند.</p><p class="small">این طرح، مسیر ورود به محتوا را نشان می‌دهد؛ فهرستِ کوتاه به شکل مقاله باز نمی‌شود.</p>`);
  if (action === 'source') dialog('<h2>ارجاع به منبع</h2><p>در اپ، این اقدام شما را به محل مرتبط در متن اصلی می‌برد. اینجا فقط پیش‌نمایش طراحی است.</p>');
  if (action === 'bookmark') announce('ذخیره در پیش‌نمایش انتخاب شد؛ تغییری در حساب شما ایجاد نشده است.');
  if (action === 'demo') announce(b.dataset.message);
  if (b.id === 'close-dialog') document.getElementById('preview-dialog').close();
});
document.addEventListener('input',event=>{
  if (event.target.matches('.search-phone textarea')) drafts.set(Number(event.target.closest('.search-phone').dataset.variant),event.target.value);
});
document.addEventListener('submit',event=>{
  event.preventDefault();
  const form = event.target;
  const design = form.closest('.design');
  if (form.classList.contains('composer')) {
    const v = Number(design.dataset.design.split('-')[1]); const q=form.querySelector('textarea').value.trim();
    if (!q) { announce('ابتدا یک سؤال بنویسید.'); return; }
    drafts.set(v,q); searchState='answer'; render(); announce('پاسخ نمونهٔ طراحی؛ هیچ درخواستی ارسال نشده است.');
  }
  if (form.classList.contains('tool-form')) form.querySelector('.tool-output').textContent='جای نمایش نتیجهٔ ابزار در طراحی. این نمونه محاسبهٔ پزشکی انجام نمی‌دهد.';
});
document.getElementById('search-state').addEventListener('change',e=>{searchState=e.target.value;render();});
document.getElementById('content-state').addEventListener('change',e=>{contentState=e.target.value;render();});
render();
