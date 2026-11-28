/*
 * Pediatric dose engine.
 * Pure functions, no DOM. Works in the browser (window.PedsDose) and in Node (require).
 *
 * A drug file (data/drugs/*.json) holds:
 *   products  : the products available in Iran (strength per unit)
 *   regimens  : UpToDate rules, each with a population, a dose, a frequency, caps and a verbatim quote
 *   messages  : what to show for ages/weights that have no regimen
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.PedsDose = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const DAYS_PER = { d: 1, w: 7, m: 30.4375, y: 365.25 };
  const EPS = 1e-6;
  const MAX_AGE_DAYS = 19 * DAYS_PER.y;      // pediatric range: up to 18 years (inclusive)

  // ---------------------------------------------------------------- frequencies
  // perDay: fixed number of doses/day (needed when the dose is per day).
  // prnMaxPerDay: upper bound of administrations for "every X to Y hours" orders.
  const FREQ = {
    once:      { en: 'once (single dose)', fa: 'تک‌دوز', single: true },
    q48h:      { en: 'q48h', fa: 'هر ۴۸ ساعت', everyHours: 48 },
    q36h:      { en: 'q36h', fa: 'هر ۳۶ ساعت', everyHours: 36 },
    q24h:      { en: 'q24h', fa: 'روزی ۱ بار', perDay: 1 },
    q12h:      { en: 'q12h', fa: 'هر ۱۲ ساعت', perDay: 2 },
    q8h:       { en: 'q8h', fa: 'هر ۸ ساعت', perDay: 3 },
    q6h:       { en: 'q6h', fa: 'هر ۶ ساعت', perDay: 4 },
    'q6h-prn': { en: 'q6h PRN', fa: 'هر ۶ ساعت در صورت نیاز', prnMaxPerDay: 4 },
    q4h:       { en: 'q4h', fa: 'هر ۴ ساعت', perDay: 6 },
    bid:       { en: 'BID', fa: 'روزی ۲ بار', perDay: 2 },
    tid:       { en: 'TID', fa: 'روزی ۳ بار', perDay: 3 },
    qid:       { en: 'QID', fa: 'روزی ۴ بار', perDay: 4 },
    'tid-qid': { en: '3–4 times daily', fa: 'روزی ۳ تا ۴ بار', prnMaxPerDay: 4 },
    'q4-6h':   { en: 'q4–6h PRN', fa: 'هر ۴ تا ۶ ساعت در صورت نیاز', prnMaxPerDay: 6 },
    'q4-8h':   { en: 'q4–8h PRN', fa: 'هر ۴ تا ۸ ساعت در صورت نیاز', prnMaxPerDay: 6 },
    'q6-8h':   { en: 'q6–8h', fa: 'هر ۶ تا ۸ ساعت', prnMaxPerDay: 4 },
    'q6-12h':  { en: 'q6–12h PRN', fa: 'هر ۶ تا ۱۲ ساعت در صورت نیاز', prnMaxPerDay: 4 },
    'q1-4h':   { en: 'q1–4h PRN', fa: 'هر ۱ تا ۴ ساعت در صورت نیاز' },
    'q20min':  { en: 'q20min × 3 doses', fa: 'هر ۲۰ دقیقه، تا ۳ نوبت' },
    'q5-15min':{ en: 'q5–15min (usually up to 3 doses)', fa: 'هر ۵ تا ۱۵ دقیقه (معمولاً تا ۳ نوبت)' },
  };

  // ---------------------------------------------------------------- helpers
  function parseAge(s) {
    const m = /^(\d+(?:\.\d+)?)([dwmy])$/.exec(String(s));
    if (!m) throw new Error('bad age literal: ' + s);
    return Number(m[1]) * DAYS_PER[m[2]];
  }

  function ageToDays(value, unit) {
    const u = { day: 'd', days: 'd', d: 'd', week: 'w', w: 'w', month: 'm', months: 'm', m: 'm', year: 'y', years: 'y', y: 'y' }[unit];
    if (!u) throw new Error('bad age unit: ' + unit);
    return Number(value) * DAYS_PER[u];
  }

  // pop: object or array of objects (OR). Keys: ageGe/ageLt ('3m'), wtGe/wtGt/wtLe/wtLt (kg), gaGe/gaLt (weeks)
  function matchPop(pop, ctx) {
    if (!pop) return true;
    if (Array.isArray(pop)) return pop.some(p => matchPop(p, ctx));
    const a = ctx.ageDays, w = ctx.weightKg, ga = ctx.gaWeeks;
    // Missing/invalid GA must never match every GA/PMA band via NaN comparisons.
    if (Object.keys(pop).some(k => /^(ga|pma)/.test(k)) && !Number.isFinite(ga)) return false;
    if (pop.ageGe != null && a < parseAge(pop.ageGe) - EPS) return false;
    if (pop.ageLt != null && a >= parseAge(pop.ageLt) - EPS) return false;
    if (pop.ageGt != null && a <= parseAge(pop.ageGt) + EPS) return false;
    if (pop.wtGe != null && w < pop.wtGe - EPS) return false;
    if (pop.wtGt != null && w <= pop.wtGt + EPS) return false;
    if (pop.wtLe != null && w > pop.wtLe + EPS) return false;
    if (pop.wtLt != null && w >= pop.wtLt - EPS) return false;
    if (pop.gaGe != null && ga < pop.gaGe - EPS) return false;
    if (pop.gaLt != null && ga >= pop.gaLt - EPS) return false;
    const pma = ga + a / 7;   // postmenstrual age (weeks) = gestational age + postnatal age
    if (pop.pmaGe != null && pma < pop.pmaGe - EPS) return false;
    if (pop.pmaGt != null && pma <= pop.pmaGt + EPS) return false;
    if (pop.pmaLe != null && pma > pop.pmaLe + EPS) return false;
    if (pop.pmaLt != null && pma >= pop.pmaLt - EPS) return false;
    return true;
  }

  const fmtNum = (x) => {
    if (x == null || !isFinite(x)) return '—';
    const r = Number(x.toPrecision(8));
    return String(r).replace(/\.0+$/, '');
  };
  const fmtRange = (lo, hi, unit) => (Math.abs(lo - hi) < 1e-9 ? fmtNum(lo) : fmtNum(lo) + '–' + fmtNum(hi)) + (unit ? ' ' + unit : '');

  // ---------------------------------------------------------------- dose math
  // Returns per-administration amount (mg or mcg) [lo, hi] after caps, plus cap flags.
  function perDoseAmount(dose, max, freq, weightKg) {
    let lo = dose.min, hi = dose.max != null ? dose.max : dose.min;
    if (dose.perKg) { lo *= weightKg; hi *= weightKg; }
    if (dose.basis === 'day') {
      if (!freq.perDay) throw new Error('per-day dose needs a fixed frequency');
      lo /= freq.perDay; hi /= freq.perDay;
    }
    if (dose.floor != null) { lo = Math.max(lo, dose.floor); hi = Math.max(hi, dose.floor); }   // e.g. "minimum dose: 2.5 mg/dose"
    const raw = [lo, hi];
    const capped = [];
    let cap = Infinity;
    if (max) {
      if (max.perDose != null && max.perDose < cap) cap = max.perDose;
      const daily = dailyCap(max, weightKg);
      if (daily != null && freq.perDay) {
        const c = daily / freq.perDay;
        if (c < cap) cap = c;
      }
    }
    if (hi > cap + EPS) { hi = cap; capped.push('dose'); }
    if (lo > cap + EPS) { lo = cap; }
    return { lo, hi, raw, capped };
  }

  function dailyCap(max, weightKg) {
    if (!max) return null;
    let c = Infinity;
    if (max.perDay != null) c = Math.min(c, max.perDay);
    if (max.perKgDay != null) c = Math.min(c, max.perKgDay * weightKg);
    return c === Infinity ? null : c;
  }

  // ---------------------------------------------------------------- products
  function unitsPerAmount(product, amount) {
    return amount / product.strength * (product.per || 1);
  }

  function liquidStep(v, product) {
    if (product.step) return product.step;
    return v < 1 ? 0.05 : 0.1;
  }

  const clean = (x) => Math.round(x * 1e6) / 1e6;   // strip floating-point noise (6.300000000000001)

  // Offer only measurable amounts inside the prescribed interval. A fixed dose
  // that cannot be measured at this step needs another preparation/device, not
  // an invented rounding tolerance or a minimum volume that changes the dose.
  function roundLiquid(lo, hi, product) {
    const step = liquidStep(hi, product);
    const a = clean(Math.ceil(lo / step - 1e-9) * step);
    const b = clean(Math.floor(hi / step + 1e-9) * step);
    if (a > b + 1e-9 || b <= 0 || b > hi + 1e-9) return null;
    return [Math.max(a, step), b];
  }

  // Discrete units (tablets, packets, sprays): find whole (or half) counts inside [lo, hi].
  function roundDiscrete(lo, hi, product) {
    const q = product.half ? 0.5 : 1;
    const a = Math.ceil(lo / q - 1e-9) * q;
    const b = Math.floor(hi / q + 1e-9) * q;
    if (a <= b && b > 0) return [Math.max(a, q), b];
    return null;   // no whole-unit match
  }

  function productAmount(product, mgLo, mgHi) {
    if (product.verificationStatus === 'unverified') return { ok: false, reason: 'unverified' };
    if (product.mgOnly) {
      // Powder vials: reconstitution volume varies by route/protocol, so show the dose itself.
      const a = [mgLo, mgHi];
      return { ok: true, amount: a, unit: product.doseUnit || 'mg', mg: a };
    }
    const uLo = unitsPerAmount(product, mgLo), uHi = unitsPerAmount(product, mgHi);
    if (product.discrete) {
      const d = roundDiscrete(uLo, uHi, product);
      if (!d) return { ok: false, exact: [uLo, uHi] };
      return { ok: true, amount: d, unit: product.perUnit, mg: [d[0] * product.strength / (product.per || 1), d[1] * product.strength / (product.per || 1)] };
    }
    const r = roundLiquid(uLo, uHi, product);
    if (!r) return { ok: false, reason: 'unmeasurable', exact: [uLo, uHi], step: liquidStep(uHi, product) };
    return { ok: true, amount: r, unit: product.perUnit, mg: [r[0] * product.strength / (product.per || 1), r[1] * product.strength / (product.per || 1)] };
  }

  // ---------------------------------------------------------------- order text
  function orderText(dose, freq, max, extra) {
    const u = dose.unit || 'mg';
    let s = fmtRange(dose.min, dose.max != null ? dose.max : dose.min, '');
    s += ' ' + u + (dose.perKg ? '/kg' : '') + (dose.basis === 'day' ? '/day' : (dose.perKg ? '/dose' : ''));
    if (dose.of) s += ' (' + dose.of + ')';
    if (dose.site) s += ' ' + dose.site;
    s += (dose.basis === 'day' ? ' ÷ ' : ' ') + freq.en;
    const caps = [];
    if (max) {
      if (max.perDose != null) caps.push('max ' + fmtNum(max.perDose) + ' ' + u + '/dose');
      if (max.perDay != null) caps.push('max ' + fmtNum(max.perDay) + ' ' + u + '/day');
      if (max.perKgDay != null) caps.push('max ' + fmtNum(max.perKgDay) + ' ' + u + '/kg/day');
    }
    if (dose.floor != null) caps.unshift('min ' + fmtNum(dose.floor) + ' ' + u + '/dose');
    if (caps.length) s += '; ' + caps.join('; ');
    if (extra) s += '; ' + extra;
    return s;
  }

  // ---------------------------------------------------------------- main
  function validateInput(input, drug) {
    const errors = [];
    const w = Number(input.weightKg), av = Number(input.ageValue);
    if (!Number.isFinite(w) || !(w > 0)) errors.push('وزن نامعتبر است');
    if (!Number.isFinite(av) || !(av > 0)) errors.push('سن نامعتبر است');
    if (w > 200) errors.push('وزن بیش از ۲۰۰ کیلوگرم است');
    let ageDays = null;
    if (Number.isFinite(av) && av > 0) {
      try { ageDays = ageToDays(av, input.ageUnit || 'year'); }
      catch (e) { errors.push('واحد سن نامعتبر است'); }
      if (ageDays >= MAX_AGE_DAYS) errors.push('این ماشین‌حساب فقط برای سن زیر ۱۹ سال است');
    }
    const missingGA = input.gaWeeks == null || String(input.gaWeeks).trim() === '';
    const gaWeeks = missingGA ? null : Number(input.gaWeeks);
    if (!missingGA && (!Number.isFinite(gaWeeks) || gaWeeks < 22 || gaWeeks > 44)) {
      errors.push('سن حاملگی باید عددی بین ۲۲ تا ۴۴ هفته باشد');
    } else if (missingGA && needsGA(drug, ageDays)) {
      errors.push('برای محاسبهٔ این دارو، سن حاملگی هنگام تولد را وارد کنید');
    }
    return { errors, ctx: { ageDays, weightKg: w, gaWeeks } };
  }

  function calcSimple(drug, reg, ctx) {
    const stages = reg.stages || [{ label: null, dose: reg.dose, max: reg.max }];
    const out = [];
    for (const st of stages) {
      const dose = Object.assign({}, reg.dose || {}, st.dose || {});
      const max = st.max !== undefined ? st.max : reg.max;
      const freqs = st.freq || reg.freq || ['once'];
      for (const fc of freqs) {
        const freq = FREQ[fc];
        if (!freq) throw new Error(drug.id + '/' + reg.id + ': unknown freq ' + fc);
        const pd = perDoseAmount(dose, max, freq, ctx.weightKg);
        const daily = dailyCap(max, ctx.weightKg);
        const prods = [];
        for (const pid of reg.products || []) {
          const p = drug.products[pid];
          if (!p) throw new Error(drug.id + '/' + reg.id + ': unknown product ' + pid);
          const pa = productAmount(p, pd.lo, pd.hi);
          const row = { productId: pid, product: p.label, ok: pa.ok };
          if (pa.ok) {
            row.amount = pa.amount; row.unit = pa.unit; row.mg = pa.mg;
            row.amountText = fmtRange(pa.amount[0], pa.amount[1], pa.unit);
            if (p.mgOnly) row.mgOnly = true;
            if (daily != null && !p.mgOnly) {
              row.dailyMaxUnits = unitsPerAmount(p, daily);
              row.dailyMaxText = fmtNum(Math.floor(row.dailyMaxUnits * 10 + 1e-9) / 10) + ' ' + p.perUnit + '/day';
            }
          } else {
            row.reason = pa.reason || 'discrete';
            if (pa.exact) row.exact = pa.exact;
            row.amountText = pa.reason === 'unverified'
              ? 'ترکیب یا قدرت این فرآورده تأیید نشده است؛ حجم ارائه نمی‌شود.'
              : pa.reason === 'unmeasurable'
                ? 'با گام ' + fmtNum(pa.step) + ' ' + p.perUnit + ' قابل تنظیم نیست؛ ابزار دقیق‌تر یا فرآورده/رقیق‌سازی تأییدشده لازم است.'
                : 'با این فرآورده مقدار کامل قابل تنظیم نیست (' + fmtRange(pa.exact[0], pa.exact[1], p.perUnit) + ')';
          }
          prods.push(row);
        }
        const r = {
          stage: st.label || null,
          freq: fc, freqFa: freq.fa, freqEn: freq.en,
          order: orderText(dose, freq, max, st.orderNote || reg.orderNote),
          mgPerDose: [pd.lo, pd.hi], mgRaw: pd.raw,
          unit: dose.unit || 'mg',
          capped: pd.capped,
          dailyMax: daily,
          products: prods,
          schedule: st.schedule || reg.schedule || null,
        };
        if (freq.prnMaxPerDay || reg.maxDosesPerDay) {
          const n = reg.maxDosesPerDay || freq.prnMaxPerDay;
          r.maxDosesPerDay = daily != null && pd.lo > 0 ? Math.min(n, Math.floor(daily / pd.lo + 1e-9)) : n;
          if (daily != null && pd.hi > 0) r.maxDosesAtHigh = Math.min(n, Math.floor(daily / pd.hi + 1e-9));
          r.order += '; max ' + r.maxDosesPerDay + ' doses/24h';
        }
        if (r.schedule) r.order += '; ' + r.schedule.en;
        if (freq.perDay) r.mgPerDay = [pd.lo * freq.perDay, pd.hi * freq.perDay];
        out.push(r);
      }
    }
    return out;
  }

  // Combination product: each component has its own rule; the volume is limited by the most restrictive one.
  function calcCombo(drug, reg, ctx) {
    const freq = FREQ[reg.freq[0]];
    const out = [];
    for (const pid of reg.products) {
      const p = drug.products[pid];
      if (p.verificationStatus === 'unverified') {
        out.push({ stage: null, freq: reg.freq[0], freqFa: freq.fa, freqEn: freq.en,
          order: 'حجم فرآورده تا تأیید ترکیب و قدرت آن محاسبه نمی‌شود.', combo: true, capped: [],
          products: [{ productId: pid, product: p.label, ok: false, reason: 'unverified',
            amountText: 'ترکیب یا قدرت این فرآورده تأیید نشده است؛ حجم ارائه نمی‌شود.' }] });
        continue;
      }
      let vLo = 0, vHi = Infinity, dailyVol = Infinity;
      const comps = [];
      for (const c of reg.components) {
        const pc = p.components[c.name];
        const pd = perDoseAmount(c.dose, c.max, freq, ctx.weightKg);
        const lo = pd.lo / pc.strength * pc.per, hi = pd.hi / pc.strength * pc.per;
        vLo = Math.max(vLo, lo); vHi = Math.min(vHi, hi);
        const dc = dailyCap(c.max, ctx.weightKg);
        if (dc != null) dailyVol = Math.min(dailyVol, dc / pc.strength * pc.per);
        comps.push({ name: c.name, order: orderText(c.dose, freq, c.max), mgPerDose: [pd.lo, pd.hi], capped: pd.capped });
      }
      const r = roundLiquid(vLo, vHi, p);
      const comp2 = comps.map(c => {
        const pc = p.components[c.name];
        return Object.assign(c, r ? { mgAtVolume: [r[0] * pc.strength / pc.per, r[1] * pc.strength / pc.per] } : {});
      });
      const row = {
        productId: pid, product: p.label, ok: !!r, unit: p.perUnit,
        amountText: r ? fmtRange(r[0], r[1], p.perUnit) : 'با این فرآورده دوز همهٔ اجزا در بازهٔ مجاز قابل تنظیم نیست.',
      };
      if (r) { row.amount = r; row.components = comp2; }
      if (dailyVol !== Infinity) {
        row.dailyMaxUnits = dailyVol;
        row.dailyMaxText = fmtNum(Math.floor(dailyVol * 10 + 1e-9) / 10) + ' ' + p.perUnit + '/day';
      }
      const res = { stage: null, freq: reg.freq[0], freqFa: freq.fa, freqEn: freq.en, order: comps.map(c => c.name + ': ' + c.order).join(' | '), products: [row], combo: true, capped: comps.some(c => c.capped.length) ? ['dose'] : [] };
      if (freq.prnMaxPerDay) {
        res.maxDosesPerDay = freq.prnMaxPerDay;
        if (r && dailyVol !== Infinity && r[1] > 0) res.maxDosesAtHigh = Math.min(freq.prnMaxPerDay, Math.floor(dailyVol / r[1] + 1e-9));
      }
      out.push(res);
    }
    return out;
  }

  function calculate(drug, input) {
    const v = validateInput(input, drug);
    if (v.errors.length) return { errors: v.errors, regimens: [], messages: [] };
    const ctx = v.ctx;
    const regimens = [];
    for (const reg of drug.regimens) {
      if (!matchPop(reg.pop, ctx)) continue;
      const results = reg.components ? calcCombo(drug, reg, ctx) : calcSimple(drug, reg, ctx);
      const warnings = [];
      for (const w of [...(drug.warnIf || []), ...(reg.warnIf || [])]) if (matchPop(w.pop, ctx)) warnings.push(w.text);
      regimens.push({
        id: reg.id,
        indication: reg.indication,
        population: reg.population,
        route: reg.route || 'PO',
        duration: reg.duration || null,
        limitedData: !!reg.limitedData,
        notes: reg.notes || [],
        warnings,
        source: reg.source || drug.source,
        quotes: reg.quotes || (reg.quote ? [reg.quote] : []),
        results,
      });
    }
    const messages = [];
    for (const m of drug.messages || []) if (matchPop(m.pop, ctx)) messages.push(m.text);
    if (!regimens.length && !messages.length) messages.push('برای این سن/وزن در این نسخه رژیمی پیاده نشده است؛ برای بررسی دوز به منبع مراجعه کنید.');
    return { errors: [], ctx, regimens, messages, drugNotes: drug.notes || [] };
  }

  // The UI asks for gestational age only while it can change the result.
  function needsGA(drug, ageDays) {
    if (!drug || ageDays == null || ageDays >= parseAge(drug.gaAgeLt || '29d') - EPS) return false;
    const usesGA = (pop) => {
      if (Array.isArray(pop)) return pop.some(usesGA);
      if (!pop || !Object.keys(pop).some(k => /^(ga|pma)/.test(k))) return false;
      const agePop = Object.fromEntries(Object.entries(pop).filter(([k]) => k.startsWith('age')));
      return matchPop(agePop, { ageDays });
    };
    return [...drug.regimens, ...(drug.messages || [])].some(r => usesGA(r.pop));
  }

  return { calculate, matchPop, ageToDays, parseAge, needsGA, FREQ, _internal: { perDoseAmount, roundLiquid, roundDiscrete, productAmount, orderText, dailyCap } };
}));
