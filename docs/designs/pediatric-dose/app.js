/* Design review only. All amounts come from the unchanged upstream engine. */
(async function () {
  'use strict';
  const E = window.PedsDose;
  const params = new URLSearchParams(location.search);
  const design = [1, 2, 3].includes(Number(params.get('design'))) ? Number(params.get('design')) : 1;
  const state = { lang: params.get('lang') === 'en' ? 'en' : 'fa', entry: params.has('entry'), step: Number(params.get('step')) || 1,
    drug: 'amoxicillin', regimen: 'strep_pharyngitis', result: 1, product: 's250', age: '5', weight: '20', ageUnit: 'year', ga: '', search: '', choosing: false, tab: 'dose', editing: false };
  const names = {
    acetaminophen:'استامینوفن', amoxicillin:'آموکسی‌سیلین', co_amoxiclav:'کوآموکسی‌کلاو', azithromycin:'آزیترومایسین', cephalexin:'سفالکسین', cefixime:'سفیکسیم', cefuroxime:'سفوروکسیم', ceftriaxone:'سفتریاکسون', penicillin_v:'پنی‌سیلین وی', ampicillin:'آمپی‌سیلین', clindamycin:'کلیندامایسین', co_trimoxazole:'کوتریموکسازول', metronidazole:'مترونیدازول', erythromycin:'اریترومایسین', clarithromycin:'کلاریترومایسین', gentamicin:'جنتامایسین', nitrofurantoin:'نیتروفورانتوئین', acyclovir:'آسیکلوویر', oseltamivir:'اوسلتامیویر', nystatin:'نیستاتین', albendazole:'آلبندازول', ibuprofen:'ایبوپروفن', prednisolone:'پردنیزولون', dexamethasone:'دگزامتازون', cetirizine:'ستیریزین', loratadine:'لوراتادین', desloratadine:'دسلوراتادین', fexofenadine:'فکسوفنادین', hydroxyzine:'هیدروکسی‌زین', diphenhydramine:'دیفن‌هیدرامین', chlorpheniramine:'کلرفنیرامین', ketotifen:'کتوتیفن', montelukast:'مونته‌لوکاست', salbutamol:'سالبوتامول', ipratropium:'ایپراتروپیوم', epinephrine:'اپی‌نفرین', bromhexine:'برم‌هگزین', omeprazole:'امپرازول', esomeprazole:'ازومپرازول', famotidine:'فاموتیدین', metoclopramide:'متوکلوپرامید', domperidone:'دومپریدون', ondansetron_syr:'اندانسترون خوراکی', ondansetron_amp:'اندانسترون تزریقی', dicyclomine:'دی‌سیکلومین', promethazine:'پرومتازین', ferrous_sulfate:'فروس سولفات', levetiracetam:'لووتیراستام', nasal_sprays:'اسپری‌های بینی', cold_products:'فرآورده‌های سرماخوردگی'
  };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const t = (fa, en) => state.lang === 'fa' ? fa : en;
  const n = value => new Intl.NumberFormat(state.lang === 'fa' ? 'fa-IR' : 'en-US', { maximumFractionDigits: 4 }).format(value);
  const normal = value => String(value).replace(/[۰-۹]/g, c => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(c))).replace(/[٠-٩]/g, c => String('٠١٢٣٤٥٦٧٨٩'.indexOf(c))).replace(/٫/g,'.');
  const num = v => Number(Number(v).toPrecision(8));
  const range = (pair, unit = '') => pair ? `${n(num(pair[0]))}${Math.abs(pair[0]-pair[1]) > 1e-7 ? '–'+n(num(pair[1])) : ''}${unit ? ' '+esc(unit) : ''}` : '—';
  const title = drug => state.lang === 'fa' ? names[drug.id] || drug.name : drug.name;
  const unitLabel = () => ({day:t('روز','days'),month:t('ماه','months'),year:t('سال','years')})[state.ageUnit];
  let drugs;
  document.body.classList.add(`design-${design}`);
  if (params.has('embed')) document.body.classList.add('embed');

  function calculate() {
    const drug = drugs.find(d => d.id === state.drug);
    const out = E.calculate(drug, { ageValue: normal(state.age), ageUnit: state.ageUnit, weightKg: normal(state.weight), gaWeeks: normal(state.ga) });
    const regimen = out.regimens.find(r => r.id === state.regimen) || out.regimens[0];
    if (regimen) state.regimen = regimen.id;
    const result = regimen?.results[state.result] || regimen?.results[0];
    if (regimen && !regimen.results[state.result]) state.result = 0;
    const product = result?.products.find(p => p.productId === state.product) || result?.products.find(p => p.ok) || result?.products[0];
    if (product) state.product = product.productId;
    return { drug, out, regimen, result, product };
  }
  function field(label, body, cls='') { return `<label class="field ${cls}"><span>${label}</span>${body}</label>`; }
  function patient(compact=false) {
    return `<section class="${compact?'compact-patient':'panel'}"><div class="panel-head"><h2>${t('مشخصات کودک','Patient details')}</h2><button type="button" class="text-button" data-action="clear">${t('بیمار جدید','New patient')}</button></div><div class="patient-fields">
      ${field(t('وزن · کیلوگرم','Weight · kg'),`<input id="weight" name="weight" inputmode="decimal" autocomplete="off" value="${esc(state.weight)}" aria-label="${t('وزن کودک','Child weight')}">`)}
      ${field(t('سن کودک','Age'),`<input id="age" name="age" inputmode="decimal" autocomplete="off" value="${esc(state.age)}" aria-label="${t('سن کودک','Child age')}">`)}
      <div class="age-unit segmented" role="group" aria-label="${t('واحد سن','Age unit')}">${['day','month','year'].map(unit=>`<button type="button" data-unit="${unit}" class="${unit===state.ageUnit?'active':''}" aria-pressed="${unit===state.ageUnit}">${({day:t('روز','Days'),month:t('ماه','Months'),year:t('سال','Years')})[unit]}</button>`).join('')}</div>
      <label class="field ga" id="ga-field"><span>${t('سن حاملگی هنگام تولد · هفته','Gestational age at birth · weeks')}</span><input id="ga" name="ga" inputmode="decimal" autocomplete="off" value="${esc(state.ga)}"><small>${t('برای رژیم‌های وابسته به GA / PMA الزامی است.','Required for GA / PMA dependent regimens.')}</small></label>
    </div></section>`;
  }
  function drugPicker() {
    const drug=drugs.find(d=>d.id===state.drug);
    return `<section class="panel"><div class="panel-head"><h2>${t('دارو و اندیکاسیون','Drug and indication')}</h2><small>${n(drugs.length)} ${t('مدخل دارویی','drug entries')}</small></div>
      <div class="selected-drug"><div class="drug-mark" aria-hidden="true">Rx</div><div><h2>${esc(title(drug))}</h2><small class="ltr">${esc(drug.name)}</small></div><button type="button" class="text-button" data-action="choose">${t('تغییر دارو','Change')}</button></div>
      <div class="search-wrap" ${state.choosing?'':'hidden'}><input id="search" class="search-input" value="${esc(state.search)}" placeholder="${t('نام فارسی یا انگلیسی دارو…','Search drug name…')}" aria-label="${t('جستجوی دارو','Search drug')}"><div id="drug-results" class="drug-results"></div></div>
      <div id="selection-fields" class="selector-grid">${selection(calculate())}</div></section>`;
  }
  function selection({out,regimen,result}) {
    if(out.errors.length || !regimen) return `<div class="full note">${t('ابتدا اطلاعات معتبر کودک را وارد کنید.','Enter valid patient details first.')}</div>`;
    return `${field(t('اندیکاسیون / رژیم','Indication / regimen'),`<select id="regimen" dir="ltr">${out.regimens.map(r=>`<option value="${esc(r.id)}" ${r.id===state.regimen?'selected':''}>${esc(r.indication)}</option>`).join('')}</select>`,'full')}
      ${field(t('گزینه / مرحلهٔ مصرف','Schedule / stage'),`<select id="result-choice">${regimen.results.map((r,i)=>`<option value="${i}" ${i===state.result?'selected':''}>${esc(r.stage || '')}${r.stage?' · ':''}${esc(t(r.freqFa,r.freqEn))}</option>`).join('')}</select>`)}
      ${field(t('فرآورده','Preparation'),`<select id="product" dir="ltr">${result.products.map(p=>`<option value="${esc(p.productId)}" ${p.productId===state.product?'selected':''}>${esc(p.product)}</option>`).join('')}</select>`)}`;
  }
  function summary(edit=false) {return `<div class="patient-summary"><div class="facts"><span>${t('سن','Age')} <strong>${esc(state.age)} ${unitLabel()}</strong></span><span>${t('وزن','Weight')} <strong>${esc(state.weight)} kg</strong></span></div>${edit?`<button type="button" class="text-button" data-step="1">${t('ویرایش','Edit')}</button>`:''}</div>`;}
  function notices({out,regimen}) {
    if(out.errors.length) return out.errors.map(x=>`<p class="notice error" role="alert">${esc(x)}</p>`).join('');
    return [...out.messages,...(out.drugNotes||[]),...(regimen?.warnings||[]),...(regimen?.notes||[])].map(x=>`<p class="notice">${esc(x)}</p>`).join('')+(regimen?.limitedData?`<p class="notice">${t('دادهٔ محدود برای این رژیم · یادداشت منبع را بررسی کنید.','Limited data for this regimen · review source notes.')}</p>`:'');
  }
  function source(regimen) {
    if(!regimen) return '';
    return `<details class="source"><summary>${t('منبع و متن پشتوانه','Source and supporting text')} · UpToDate</summary><p dir="ltr">${esc(regimen.source.title)} · Topic ${esc(regimen.source.contentId)}</p>${regimen.quotes.map(q=>`<blockquote lang="en">${esc(q)}</blockquote>`).join('')}</details>`;
  }
  function dose({result:r,product:p}) {
    if(!r||!p) return '';
    if(!p.ok) return `<div class="dose-card"><span class="dose-label">${t('این فرآورده قابل ارائه نیست','Preparation unavailable')}</span><p class="notice">${esc(p.amountText)}</p>${r.mgPerDose?`<p>${t('دوز محاسباتی دارو','Calculated drug amount')}: <b class="ltr">${range(r.mgPerDose,r.unit)}</b></p>`:''}</div>`;
    return `<div class="dose-card"><span class="dose-label">${t('مقدار هر نوبت · فرآوردهٔ انتخابی','Per administration · selected preparation')}</span><strong class="dose-value number">${range(p.amount)} <span class="unit">${esc(p.unit)}</span></strong><span class="frequency">${esc(t(r.freqFa,r.freqEn))}</span>${p.mg?`<span class="small">${t('معادل','Equivalent to')} <b class="ltr">${range(p.mg,r.unit||'mg')}</b></span>`:''}<div class="preparation">${esc(p.product)}</div></div>`;
  }
  function detailRows({regimen:r,result:s}) {
    if(!r||!s) return '';
    const rows=[[t('راه مصرف','Route'),r.route],[t('جمعیت منبع','Source population'),r.population]];
    if(s.mgPerDay) rows.unshift([t(s.schedule?'مجموع در روز مصرف':'مجموع روزانه','Total per treatment day'),range(s.mgPerDay,s.unit)]);
    if(s.dailyMax!=null) rows.push([t('سقف روزانه','Daily maximum'),`${n(s.dailyMax)} ${esc(s.unit)}`]);
    if(r.duration) rows.push([t('مدت درمان','Duration'),r.duration]);
    let html=rows.map(([k,v])=>`<div class="meta-row"><span class="muted">${k}</span><b dir="auto">${esc(v)}</b></div>`).join('');
    if(s.capped.length) html+=`<p class="notice">${t('سقف دوز در محاسبه اعمال شده است.','A maximum dose cap was applied.')}</p>`;
    if(s.schedule) html+=`<p class="notice">${esc(t(s.schedule.fa,s.schedule.en))}</p>`;
    if(s.maxDosesPerDay!=null) html+=`<p class="notice">${t('حداکثر تعداد نوبت در ۲۴ ساعت','Maximum administrations in 24 hours')}: ${n(s.maxDosesPerDay)}</p>`;
    if(s.maxDosesAtHigh!=null && s.maxDosesAtHigh!==s.maxDosesPerDay) html+=`<p class="notice">${t('با دوز بالای بازه، حداکثر نوبت در ۲۴ ساعت','At the upper dose, maximum administrations in 24 hours')}: ${n(s.maxDosesAtHigh)}</p>`;
    html+=`<details class="source"><summary>${t('قاعدهٔ محاسبه و مراحل منبع','Calculation rule and source stages')}</summary><p class="ltr">${esc(s.order)}</p>${r.results.length>1?r.results.map((v,i)=>`<p class="note ltr">${i+1}. ${esc(v.stage||'')} ${esc(v.order)}</p>`).join(''):''}</details>`;
    return html;
  }
  function products({result}) {
    if(!result) return '';
    return `<table class="products-table"><thead><tr><th>${t('فرآورده','Preparation')}</th><th>${t('مقدار هر نوبت','Per administration')}</th></tr></thead><tbody>${result.products.map(p=>`<tr><td dir="ltr">${esc(p.product)}</td><td dir="auto">${p.ok?`<span class="number ltr">${range(p.amount,p.unit)}</span>`:`<span class="note">${esc(p.amountText)}</span>`}${p.components?p.components.map(c=>`<p class="note ltr">${esc(c.name)}: ${range(c.mgAtVolume,'mg')}</p>`).join(''):''}${p.dailyMaxText?`<p class="note">${t('سقف','Max')}: <span class="ltr">${esc(p.dailyMaxText)}</span></p>`:''}</td></tr>`).join('')}</tbody></table>`;
  }
  function output() {
    const d=calculate();
    const message=notices(d);
    if(!d.regimen||d.out.errors.length) return `<section class="stack">${message}</section>`;
    if(design===3) return `<section class="panel compact-result">${message}<div class="tabbar" role="group">${[['dose',t('پاسخ','Dose')],['products',t('فرآورده‌ها','Preparations')],['source',t('منبع','Source')]].map(([key,label])=>`<button type="button" data-tab="${key}" class="${state.tab===key?'active':''}" aria-pressed="${state.tab===key}">${label}</button>`).join('')}</div>${state.tab==='dose'?dose(d)+detailRows(d):state.tab==='products'?products(d):source(d.regimen)}</section>`;
    return `<section class="${design===2?'stack result-panel':'panel result-panel'}"><div class="panel-head"><h2>${t('نتیجهٔ تنظیم دوز','Dose adjustment result')}</h2><span class="pill">${esc(d.regimen.route)}</span></div>${message}${dose(d)}<div class="${design===2?'panel':''}">${detailRows(d)}${source(d.regimen)}</div>${design===1?`<details class="source"><summary>${t('مقایسهٔ فرآورده‌های این رژیم','Compare preparations for this regimen')}</summary>${products(d)}</details>`:''}</section>`;
  }
  function entry() {
    return `<div class="entry-intro"><img src="../../../frontend/assets/icons/spec-pediatrics.png" alt=""><div><h2>${t('کودکان','Pediatrics')}</h2><p class="small">${t('ماشین‌حساب‌های بالینی','Clinical calculators')}</p></div></div><section class="entry-card"><small>${t('ابزار مستقل تنظیم دوز','Dedicated dosing tool')}</small><div><h2>${t('تنظیم دوز اطفال','Pediatric Dose Adjustment')}</h2><span aria-hidden="true">${t('‹','›')}</span></div><p class="small" dir="ltr">${t('Pediatric Dose Adjustment','تنظیم دوز اطفال')}</p><p>${t('محاسبه بر اساس سن، وزن، اندیکاسیون و فرآوردهٔ دارویی','Calculate by age, weight, indication and preparation')}</p><small>${n(drugs.length)} ${t('مدخل دارویی','drug entries')} · UpToDate</small><button type="button" class="primary" data-action="open">${t('باز کردن ابزار','Open calculator')}</button></section><h2>${t('سایر ابزارهای کودکان','Other pediatric tools')}</h2><div class="entry-list"><div>${t('آپگار','APGAR')}</div><div>${t('معیارهای Boston برای شیرخواران تب‌دار','Boston Criteria for Febrile Infants')}</div><div>${t('صدک‌های قد و وزن کودک','Pediatric growth percentiles')}</div></div><p class="note">${t('جایگاه پیشنهادی: ماشین‌حساب‌های بالینی ← کودکان ← تنظیم دوز اطفال','Proposed location: Clinical calculators → Pediatrics → Pediatric Dose Adjustment')}</p>`;
  }
  function syncHeader() {
    document.documentElement.lang=state.lang; document.documentElement.dir=state.lang==='fa'?'rtl':'ltr';
    document.querySelector('#title').textContent=state.entry?t('کودکان','Pediatrics'):t('تنظیم دوز اطفال','Pediatric Dose Adjustment');
    document.querySelector('#subtitle').textContent=state.entry?t('Pediatrics','کودکان'):t('Pediatric Dose Adjustment','تنظیم دوز اطفال');
    document.querySelector('[data-action=language]').textContent=t('EN','FA');
    for(const [key,label] of Object.entries({home:t('خانه','Home'),formulary:t('دارونامه','Formulary'),profile:t('پروفایل','Profile')}))document.querySelector(`[data-label=${key}]`).textContent=label;
  }
  function render() {
    syncHeader();
    const root=document.querySelector('#app');
    if(state.entry) {root.innerHTML=entry();return;}
    let html='';
    if(design===1) html=`${patient()}${drugPicker()}<div id="output" class="stack">${output()}</div>`;
    if(design===2) {
      html=`<nav class="stepper" aria-label="${t('مراحل تنظیم دوز','Dose adjustment steps')}">${[t('کودک','Patient'),t('دارو','Drug'),t('نتیجه','Result')].map((label,i)=>`<button type="button" data-step="${i+1}" class="${state.step===i+1?'active':''}"><span class="step-num">${n(i+1)}</span>${label}</button>`).join('')}</nav>`;
      if(state.step===1)html+=`<div><h2 class="step-title">${t('ابتدا مشخصات کودک','Start with the patient')}</h2><p class="step-intro">${t('سن و وزن، مبنای انتخاب رژیم هستند.','Age and weight determine applicable regimens.')}</p></div>${patient()}<div id="output" class="stack"></div><button type="button" class="primary" data-action="next">${t('ادامه · انتخاب دارو','Continue · select a drug')}</button>`;
      if(state.step===2)html+=`${summary(true)}${drugPicker()}<div id="output" class="stack">${notices(calculate())}</div><button type="button" class="primary" data-action="next">${t('محاسبه و مشاهدهٔ نتیجه','Calculate and review')}</button>`;
      if(state.step===3)html+=`${summary(true)}<div class="panel-head"><h2>${esc(title(calculate().drug))}</h2><button type="button" class="text-button" data-step="2">${t('تغییر دارو / رژیم','Change drug / regimen')}</button></div><p class="small ltr">${esc(calculate().regimen?.indication||'')}</p><div id="output" class="stack">${output()}</div>`;
    }
    if(design===3)html=`${state.editing?patient(true)+`<button type="button" class="secondary" data-action="edit-patient">${t('اعمال مشخصات','Apply details')}</button>`:`<div class="patient-summary"><div class="facts"><span>${t('سن','Age')} <strong>${esc(state.age)} ${unitLabel()}</strong></span><span>${t('وزن','Weight')} <strong>${esc(state.weight)} kg</strong></span></div><button type="button" class="text-button" data-action="edit-patient">${t('ویرایش','Edit')}</button></div>`}${drugPicker()}<div id="output" class="stack">${output()}</div>`;
    root.innerHTML=html; syncGA(); renderDrugList();
  }
  function syncGA() {
    const field=document.querySelector('#ga-field');if(!field)return;
    let days=null;try{days=E.ageToDays(Number(normal(state.age)),state.ageUnit);}catch{}
    field.hidden=!E.needsGA(drugs.find(d=>d.id===state.drug),days);
  }
  function renderDrugList() {
    const root=document.querySelector('#drug-results');if(!root)return;
    const q=state.search.trim().toLowerCase();
    const matches=drugs.filter(d=>!q||`${d.name} ${names[d.id]||''}`.toLowerCase().includes(q));
    root.innerHTML=matches.map(d=>`<button type="button" class="drug-row ${state.drug===d.id?'active':''}" data-drug="${esc(d.id)}"><span>${esc(title(d))}<small>${esc(d.name)}</small></span><span aria-hidden="true">${state.drug===d.id?'✓':''}</span></button>`).join('')||`<p class="note">${t('دارویی پیدا نشد.','No drugs found.')}</p>`; // taste-skill-ignore: existing app theme/selection glyph
  }
  function updateResult() {
    syncGA();
    const d=calculate(), fields=document.querySelector('#selection-fields');
    if(fields)fields.innerHTML=selection(d);
    const root=document.querySelector('#output');
    if(root)root.innerHTML=design===2&&state.step!==3?notices(d):output();
  }
  document.addEventListener('input',event=>{
    if(event.target.id==='search'){state.search=event.target.value;renderDrugList();return;}
    if(['weight','age','ga'].includes(event.target.id)){state[event.target.id]=event.target.value;updateResult();}
  });
  document.addEventListener('change',event=>{
    const id=event.target.id;
    if(id==='regimen'){state.regimen=event.target.value;state.result=0;state.product='';updateResult();}
    if(id==='result-choice'){state.result=Number(event.target.value);state.product='';updateResult();}
    if(id==='product'){state.product=event.target.value;updateResult();}
  });
  document.addEventListener('click',event=>{
    const b=event.target.closest('button');if(!b)return;
    if(b.dataset.drug){state.drug=b.dataset.drug;state.regimen='';state.result=0;state.product='';state.choosing=false;state.search='';render();return;}
    if(b.dataset.unit){state.ageUnit=b.dataset.unit;render();return;}
    if(b.dataset.tab){state.tab=b.dataset.tab;updateResult();return;}
    if(b.dataset.step){const step=Number(b.dataset.step);if(step>1&&calculate().out.errors.length){const root=document.querySelector('#output');if(root)root.innerHTML=notices(calculate());return;}state.step=step;render();return;}
    switch(b.dataset.action){
      case 'theme':document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';b.textContent=document.documentElement.dataset.theme==='dark'?'☀':'☾';break; // taste-skill-ignore: existing app theme/selection glyph
      case 'language':state.lang=state.lang==='fa'?'en':'fa';render();break;
      case 'edit-patient':state.editing=!state.editing;render();break;
      case 'choose':state.choosing=!state.choosing;render();document.querySelector('#search')?.focus();break;
      case 'open':state.entry=false;state.step=1;render();break;
      case 'back':if(design===2&&state.step>1)state.step--;else state.entry=true;render();break;
      case 'clear':state.age='';state.weight='';state.ga='';state.step=1;state.editing=true;render();break;
      case 'next':if(calculate().out.errors.length){document.querySelector('#output').innerHTML=notices(calculate());return;}state.step=Math.min(3,state.step+1);render();break;
    }
  });
  try {
    const response=await fetch('vendor/drugs.json');if(!response.ok)throw new Error('Dataset loading failed');
    drugs=(await response.json()).drugs;
    render();window.__pediatricPreview={state,calculate,render,drugs};
  } catch(error) {
    document.querySelector('#app').innerHTML=`<p class="notice error" role="alert">${t('دریافت داده‌ها ممکن نشد؛ صفحه را دوباره بارگذاری کنید.','Unable to load data; reload the page.')}</p><button type="button" class="primary" id="retry">${t('تلاش دوباره','Retry')}</button>`;
    document.querySelector('#retry').onclick=()=>location.reload();
  }
}());
