// node --test tests/
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../../src/pediatricDose/engine.js');

const DRUGS = Object.fromEntries(require('../../../backend/apps/calculators/data/pediatric-dose.json').drugs.map(d => [d.id,d]));

// Fixtures default to an explicitly known term birth; missing GA is tested separately.
const calc = (id, age, unit, wt, ga = 40) => E.calculate(DRUGS[id], { ageValue: age, ageUnit: unit, weightKg: wt, gaWeeks: ga });
const reg = (r, id) => r.regimens.find(x => x.id === id);
const prod = (res, pid) => res.products.find(p => p.productId === pid);
const ids = (r) => r.regimens.map(x => x.id);

// ---------------------------------------------------------------- data integrity
test('50 drugs, every regimen has quote, products exist, freq known', () => {
  assert.equal(Object.keys(DRUGS).length, 50);
  for (const d of Object.values(DRUGS)) {
    assert.ok(d.source && d.source.contentId, d.id + ' source');
    for (const r of d.regimens) {
      assert.ok(r.quote || (r.quotes && r.quotes.length), `${d.id}/${r.id} quote`);
      for (const p of r.products) assert.ok(d.products[p], `${d.id}/${r.id} product ${p}`);
      for (const f of r.freq || []) assert.ok(E.FREQ[f], `${d.id}/${r.id} freq ${f}`);
      for (const s of r.stages || []) for (const f of s.freq || []) assert.ok(E.FREQ[f], `${d.id}/${r.id} stage freq ${f}`);
    }
  }
});

// Every number in the structured rule must appear in the verbatim UpToDate quote(s),
// unless explicitly listed as derived. Catches transcription errors (45 vs 54, etc.).
const DERIVED = {
  'ketotifen/c5_18_initial_bid': [0.5],
  'nasal_sprays/flup_4_11': [50],
  'nasal_sprays/flup_12': [50, 100],   // "2 sprays" / "1 or 2 sprays" of 50 mcg
  'nasal_sprays/fluf_2_11': [27.5, 55],
  'nasal_sprays/fluf_12': [27.5, 55],
  'ondansetron_amp/age_iv': [],
  'ampicillin/gen_iv': [8000],         // "8 g/day"
  'ampicillin/meningitis': [12000],    // "12 g/day"
};
test('structured numbers appear in the source quote', () => {
  const problems = [];
  for (const d of Object.values(DRUGS)) {
    for (const r of d.regimens) {
      const text = (r.quotes || [r.quote]).join(' ').replace(/(\d),(\d{3})/g, '$1$2');
      const nums = new Set((text.match(/\d+(?:\.\d+)?/g) || []).map(Number));
      const want = [];
      const addDose = (x) => { if (!x) return; want.push(x.min); if (x.max != null) want.push(x.max); if (x.floor != null) want.push(x.floor); };
      const addMax = (m) => { if (!m) return; ['perDose', 'perDay', 'perKgDay'].forEach(k => m[k] != null && want.push(m[k])); };
      addDose(r.dose); addMax(r.max);
      for (const s of r.stages || []) { addDose(s.dose); addMax(s.max); }
      for (const c of r.components || []) { addDose(c.dose); addMax(c.max); }
      const allowed = DERIVED[`${d.id}/${r.id}`] || [];
      for (const n of want) if (!nums.has(n) && !allowed.includes(n)) problems.push(`${d.id}/${r.id}: ${n}`);
    }
  }
  assert.deepEqual(problems, []);
});

// ---------------------------------------------------------------- safety fixes vs reference site
test('acetaminophen: 100 kg capped at 1000 mg/dose and 4000 mg/day', () => {
  const r = calc('acetaminophen', 10, 'year', 100);
  const res = reg(r, 'weight_directed').results[0];
  assert.equal(res.mgPerDose[1], 1000);
  assert.equal(res.dailyMax, 4000);
  assert.equal(res.maxDosesAtHigh, 4);
  assert.equal(prod(res, 'syr120').ok, false);   // a fixed 1000 mg is not exactly measurable at 0.1 mL
  assert.equal(prod(res, 'syr120').reason, 'unmeasurable');
  assert.deepEqual(prod(res, 'tab500').amount, [2, 2]);
});

test('acetaminophen: 18 kg child', () => {
  const res = reg(calc('acetaminophen', 5, 'year', 18), 'weight_directed').results[0];
  assert.deepEqual(res.mgPerDose, [180, 270]);
  assert.deepEqual(prod(res, 'syr120').amount, [7.5, 11.2]);
  assert.deepEqual(prod(res, 'drop100').amount, [1.8, 2.7]);
});

test('acetaminophen neonates follow GA/PNA bands', () => {
  assert.deepEqual(ids(calc('acetaminophen', 5, 'day', 3, 40)), ['neo_ga33_36_or_term_lt10d']);
  assert.deepEqual(ids(calc('acetaminophen', 15, 'day', 3.5, 40)), ['neo_term_ge10d']);
  assert.deepEqual(ids(calc('acetaminophen', 15, 'day', 1.5, 30)), ['neo_ga28_32']);
  const r = calc('acetaminophen', 15, 'day', 1, 26);
  assert.equal(r.regimens.length, 0);
  assert.match(r.messages[0], /۲۸ هفته/);
});

test('amoxicillin: neonate gets neonatal dosing, not 80-90 mg/kg/day', () => {
  const r = calc('amoxicillin', 1, 'day', 3.5);
  assert.deepEqual(ids(r).sort(), ['neo_high_ge2kg', 'neo_traditional']);
  assert.deepEqual(reg(r, 'neo_traditional').results[0].mgPerDose, [52.5, 52.5]);
});

test('amoxicillin: standard dose capped at 500 mg/dose; AOM standard capped at 1500 mg/day', () => {
  const r = calc('amoxicillin', 10, 'year', 40);
  assert.deepEqual(reg(r, 'gen_standard').results[0].mgPerDose, [500, 500]);
  assert.deepEqual(reg(r, 'aom_standard').results[0].mgPerDose, [750, 750]);
  assert.deepEqual(reg(r, 'gen_high').results[0].mgPerDose, [1600, 1800]);
});

test('azithromycin: neonate gets 10 mg/kg; strep regimen only ≥1 year', () => {
  const r = calc('azithromycin', 10, 'day', 3.5);
  assert.deepEqual(ids(r), ['neo_general']);
  assert.ok(!ids(calc('azithromycin', 5, 'month', 7)).includes('strep_5day'));
  const big = calc('azithromycin', 15, 'year', 60);
  assert.deepEqual(reg(big, 'strep_5day').results[0].mgPerDose, [500, 500]);
  assert.deepEqual(reg(big, 'strep_3day').results[0].mgPerDose, [1000, 1000]);
});

test('ondansetron ampoule 8 mg/4 mL: 3 mg = 1.5 mL (site used 8 mg/2 mL)', () => {
  const res = reg(calc('ondansetron_amp', 6, 'year', 20), 'age_iv').results[0];
  assert.deepEqual(prod(res, 'amp8').amount, [1.5, 1.5]);
});

test('ketotifen: no dosing under 5 years', () => {
  const r = calc('ketotifen', 2, 'year', 12);
  assert.equal(r.regimens.length, 0);
  assert.match(r.messages[0], /۵ سال/);
});

test('levetiracetam neonate: initial 10-30 mg/kg/day, not 8-120', () => {
  const res = reg(calc('levetiracetam', 10, 'day', 3.5), 'neo_oral').results[0];
  assert.deepEqual(res.mgPerDose, [17.5, 52.5]);
});

// ---------------------------------------------------------------- other behaviour
test('cefixime: 400 mg/day cap', () => {
  const r = calc('cefixime', 10, 'year', 60);
  const qd = reg(r, 'general').results.find(x => x.freq === 'q24h');
  assert.deepEqual(qd.mgPerDose, [400, 400]);
  assert.deepEqual(prod(qd, 's100').amount, [20, 20]);
});

test('co-trimoxazole: nothing under 2 months', () => {
  const r = calc('co_trimoxazole', 1, 'month', 4);
  assert.equal(r.regimens.length, 0);
});

test('esomeprazole infant weight bands', () => {
  const r = calc('esomeprazole', 5, 'month', 6);
  assert.ok(ids(r).includes('ee_inf_5_7_5'));
  assert.deepEqual(prod(reg(r, 'ee_inf_5_7_5').results[0], 'gr5').amount, [1, 1]);
});

test('fexofenadine 10.5 kg threshold', () => {
  assert.deepEqual(ids(calc('fexofenadine', 1, 'year', 10)), ['inf_lt10_5']);
  assert.deepEqual(ids(calc('fexofenadine', 1, 'year', 11)), ['inf_ge10_5']);
});

test('ibuprofen: fever needs ≥3 months and ≥5 kg; caps 600 mg/dose', () => {
  assert.ok(!ids(calc('ibuprofen', 4, 'month', 4.5)).includes('fever_weight'));
  assert.ok(ids(calc('ibuprofen', 4, 'month', 6)).includes('fever_weight'));
  const res = reg(calc('ibuprofen', 16, 'year', 120), 'fever_weight').results[0];
  assert.deepEqual(res.mgPerDose, [600, 600]);
  assert.equal(res.dailyMax, 2400);
});

test('cold products: under 4 blocked; unverified composition never yields a volume', () => {
  assert.equal(calc('cold_products', 1, 'year', 10).regimens.length, 0);
  assert.equal(calc('cold_products', 3, 'year', 12.7).regimens.length, 0);
  const p8 = reg(calc('cold_products', 8, 'year', 26), 'c6_12').results[0].products[0];
  assert.equal(p8.ok, false);
  assert.equal(p8.reason, 'unverified');
  assert.equal(p8.amount, undefined);
});

test('levetiracetam 4-16 y: target capped at 1500 mg/dose (3000 mg/day)', () => {
  const r = calc('levetiracetam', 12, 'year', 60);
  const target = reg(r, 'c4_16_weight').results[1];
  assert.deepEqual(target.mgPerDose, [1500, 1500]);
});

test('discrete products: no fake fractions', () => {
  // 30 kg, amox standard 400-450 mg/dose: 500 mg capsule is out of range -> not offered as a match
  const res = reg(calc('amoxicillin', 8, 'year', 30), 'gen_standard').results[0];
  assert.equal(prod(res, 'cap500').ok, false);
  assert.equal(prod(res, 'cap250').ok, false);
});

test('input validation', () => {
  assert.ok(calc('amoxicillin', 0, 'year', 10).errors.length);
  assert.ok(calc('amoxicillin', 5, 'year', 0).errors.length);
  assert.ok(calc('amoxicillin', 20, 'year', 60).errors.length);
});

// ---------------------------------------------------------------- property sweep
test('sweep: no crash, no NaN, never above caps, volumes positive', () => {
  const ages = [];
  for (const d of [1, 5, 9, 10, 14, 28, 29, 35, 60, 126, 127]) ages.push([d, 'day']);
  for (const m of [1, 2, 3, 4, 5, 6, 9, 11, 12, 18, 23]) ages.push([m, 'month']);
  for (let y = 2; y <= 18; y++) ages.push([y, 'year']);
  const weights = [0.35, 0.5, 0.8, 1.2, 1.8, 2.5, 3.5, 5, 7.5, 10, 10.5, 15, 20, 30, 40, 41, 55, 80, 120];
  let rows = 0;
  for (const d of Object.values(DRUGS)) {
    for (const [a, u] of ages) for (const w of weights) for (const ga of [30, 35, 40]) {
      const r = calc(d.id, a, u, w, ga);
      assert.equal(r.errors.length, 0);
      assert.ok(r.regimens.length || r.messages.length, `${d.id} ${a}${u} ${w}kg: nothing shown`);
      for (const g of r.regimens) {
        const def = d.regimens.find(x => x.id === g.id);
        for (const res of g.results) {
          for (const p of res.products) {
            rows++;
            if (!p.ok) continue;
            assert.ok(p.amount.every(x => isFinite(x) && x > 0), `${d.id}/${g.id} amount ${p.amount}`);
            assert.ok(p.amount[0] <= p.amount[1] + 1e-9);
          }
          if (res.combo) continue;
          assert.ok(res.mgPerDose.every(isFinite));
          const st = (def.stages || []).find(s => s.label === res.stage);
          const max = st && st.max !== undefined ? st.max : def.max;
          if (max && max.perDose != null) assert.ok(res.mgPerDose[1] <= max.perDose + 1e-9, `${d.id}/${g.id} perDose cap`);
          if (res.mgPerDay && res.dailyMax != null) assert.ok(res.mgPerDay[1] <= res.dailyMax + 1e-6, `${d.id}/${g.id} daily cap`);
          // every product amount (converted back to mg) must not exceed the capped dose
          for (const p of res.products) if (p.ok && p.mg) {
            assert.ok(p.mg[1] <= res.mgPerDose[1] + 1e-6, `${d.id}/${g.id}/${p.productId} rounded above dose`);
            assert.ok(p.mg[0] >= res.mgPerDose[0] - 1e-6, `${d.id}/${g.id}/${p.productId} rounded below dose`);
          }
        }
      }
    }
  }
  assert.ok(rows > 10000);
});

// ---------------------------------------------------------------- batch 2 (drugs 26-50)
test('gentamicin neonatal GA x PNA table', () => {
  const a = calc('gentamicin', 5, 'day', 1.0, 28);
  assert.deepEqual(ids(a).filter(x => x.startsWith('neo')), ['neo_lt30_le14']);
  assert.equal(reg(a, 'neo_lt30_le14').results[0].freq, 'q48h');
  assert.deepEqual(prod(reg(a, 'neo_lt30_le14').results[0], 'a10').amount, [0.5, 0.5]);
  assert.deepEqual(ids(calc('gentamicin', 20, 'day', 1.8, 32)).filter(x => x.startsWith('neo')), ['neo_30_35_11_60']);
  const t = reg(calc('gentamicin', 3, 'day', 3.5, 39), 'neo_ge35_le7').results[0];
  assert.deepEqual(t.mgPerDose, [14, 14]);
  // GA input still matters at 45 days for gentamicin, not for amoxicillin
  assert.equal(E.needsGA(DRUGS.gentamicin, 45), true);
  assert.equal(E.needsGA(DRUGS.amoxicillin, 45), false);
});

test('ampicillin neonatal GA bands', () => {
  assert.equal(reg(calc('ampicillin', 5, 'day', 2, 33), 'neo_ga_lt35_le7').results[0].freq, 'q12h');
  assert.equal(reg(calc('ampicillin', 5, 'day', 3.2, 38), 'neo_ga_ge35').results[0].freq, 'q8h');
  const m = reg(calc('ampicillin', 10, 'year', 40), 'meningitis').results.find(x => x.freq === 'q6h');
  assert.deepEqual(m.mgPerDose, [3000, 3000]);   // 300-400 mg/kg/day capped at 12 g/day
});

test('ceftriaxone: neonatal calcium warning; daily caps', () => {
  const n = calc('ceftriaxone', 3, 'day', 3);
  assert.ok(reg(n, 'neo_general').warnings[0].includes('IV calcium'));
  const g = reg(calc('ceftriaxone', 8, 'year', 40), 'general').results.find(x => x.freq === 'q24h');
  assert.deepEqual(g.mgPerDose, [2000, 2000]);
  assert.equal(g.products[0].amountText, '2000 mg');
  const men = reg(calc('ceftriaxone', 14, 'year', 50), 'meningitis_ca').results.find(x => x.freq === 'q24h');
  assert.deepEqual(men.mgPerDose, [4000, 4000]);
});

test('oseltamivir weight bands and neonatal PMA', () => {
  assert.ok(ids(calc('oseltamivir', 2, 'year', 14)).includes('tx_le15'));
  assert.ok(ids(calc('oseltamivir', 6, 'year', 20)).includes('tx_15_23'));
  assert.ok(ids(calc('oseltamivir', 12, 'year', 45)).includes('tx_gt40'));
  assert.deepEqual(ids(calc('oseltamivir', 7, 'day', 2.2, 34)), ['neo_pma_lt38']);
  assert.deepEqual(ids(calc('oseltamivir', 10, 'day', 3.4, 40)), ['neo_term']);
});

test('epinephrine IM anaphylaxis caps 0.3 / 0.5 mg', () => {
  const c = reg(calc('epinephrine', 10, 'year', 40), 'anaph_prepubertal').results[0];
  assert.deepEqual(c.mgPerDose, [0.3, 0.3]);
  assert.deepEqual(prod(c, 'amp1').amount, [0.3, 0.3]);
  const a = reg(calc('epinephrine', 15, 'year', 60), 'anaph_adolescent').results[0];
  assert.deepEqual(a.mgPerDose, [0.5, 0.5]);
  const small = reg(calc('epinephrine', 1, 'year', 9), 'anaph_prepubertal').results[0];
  assert.deepEqual(prod(small, 'amp1').amount, [0.09, 0.09]);
});

test('salbutamol nebulized exacerbation: 2.5 mg floor and 5 mg cap', () => {
  const s10 = reg(calc('salbutamol', 1, 'year', 10), 'exac_neb').results[0];
  assert.deepEqual(s10.mgPerDose, [2.5, 2.5]);
  const s40 = reg(calc('salbutamol', 12, 'year', 40), 'exac_neb').results[0];
  assert.deepEqual(s40.mgPerDose, [5, 5]);
  assert.equal(s40.freq, 'q20min');
});

test('promethazine blocked under 2 years', () => {
  const r = calc('promethazine', 18, 'month', 11);
  assert.equal(r.regimens.length, 0);
  assert.match(r.messages[0], /۲ سال/);
});

test('nystatin preterm vs term neonate', () => {
  assert.deepEqual(ids(calc('nystatin', 5, 'day', 1.5, 32)), ['neo_preterm']);
  assert.deepEqual(ids(calc('nystatin', 5, 'day', 3.4, 39)), ['neo_term']);
  assert.deepEqual(prod(reg(calc('nystatin', 5, 'day', 3.4, 39), 'neo_term').results[0], 's100k').amount, [2, 2]);
});

test('iron: elemental mg only; treatment initial capped at 120 mg/day', () => {
  const r = calc('ferrous_sulfate', 6, 'year', 25);
  const t = reg(r, 'tx_initial').results[0];
  assert.deepEqual(t.mgPerDose, [75, 75]);
  assert.equal(t.products[0].amountText, '75 mg Fe');
  assert.deepEqual(reg(calc('ferrous_sulfate', 15, 'year', 50), 'tx_initial').results[0].mgPerDose, [120, 120]);
});

test('dexamethasone croup capped at 16 mg', () => {
  const c = reg(calc('dexamethasone', 8, 'year', 30), 'croup').results[0];
  assert.deepEqual(c.mgPerDose, [16, 16]);
  assert.deepEqual(prod(c, 'amp4').amount, [4, 4]);
});

test('domperidone: 30 mg/day limits number of doses', () => {
  const d = reg(calc('domperidone', 4, 'year', 15), 'lt35').results[0];
  assert.deepEqual(d.mgPerDose, [4.5, 9]);
  assert.equal(d.maxDosesAtHigh, 3);
});
