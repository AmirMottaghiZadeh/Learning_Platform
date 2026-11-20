'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../../src/pediatricDose/engine.js');
const DRUGS = require('../../../backend/apps/calculators/data/pediatric-dose.json').drugs;
const load = id => DRUGS.find(d => d.id === id);
const calc = (id, age, weight, ga) => E.calculate(load(id), { ageValue: age, ageUnit: 'day', weightKg: weight, gaWeeks: ga });
const find = (r, id) => r.regimens.find(g => g.id === id);

test('oseltamivir: term birth at 37 weeks gets 3 mg/kg, not the premature PMA dose', () => {
  for (const ga of [37, 38, 39, 40, 44]) {
    const r = calc('oseltamivir', 1, 3, ga);
    assert.deepEqual(r.errors, []);
    assert.deepEqual(r.regimens.map(g => g.id), ['neo_term']);
    assert.deepEqual(r.regimens[0].results[0].mgPerDose, [9, 9]);
  }
});

test('oseltamivir: preterm PMA rules survive day 28 and remain exclusive at every boundary', () => {
  for (const ga of [22, 26, 30, 34, 36, 36.5, 37, 40]) {
    for (const age of [1, 7, 14, 28, 29, 35, 56, 70, 98, 112, 126, 127]) {
      const r = calc('oseltamivir', age, 2, ga);
      assert.deepEqual(r.errors, []);
      const treatment = r.regimens.filter(g => /^(neo_|tx_)/.test(g.id));
      assert.equal(treatment.length, 1, `GA ${ga}, PNA ${age}`);
      const pma = ga + age / 7;
      const expected = ga < 37 && pma <= 40 ? (pma < 38 ? 1 : 1.5) : 3;
      assert.deepEqual(treatment[0].results[0].mgPerDose, [expected * 2, expected * 2]);
    }
  }
  assert.deepEqual(find(calc('oseltamivir', 35, 2, 30), 'neo_pma_lt38').results[0].mgPerDose, [2, 2]);
  assert.deepEqual(find(calc('oseltamivir', 56, 2, 30), 'neo_pma_38_40').results[0].mgPerDose, [3, 3]);
  assert.deepEqual(find(calc('oseltamivir', 70, 2, 30), 'neo_pma_38_40').results[0].mgPerDose, [3, 3]);
  assert.deepEqual(find(calc('oseltamivir', 71, 2, 30), 'tx_inf_lt9m').results[0].mgPerDose, [6, 6]);
});

test('GA is required only when relevant; blanks, invalid values and impossible weeks cannot select bands', () => {
  for (const ga of [undefined, null, '', '  ', 'bad', NaN, Infinity, 0, 21.9, 44.1, 100]) {
    const r = calc('oseltamivir', 5, 3, ga);
    assert.ok(r.errors.length, `GA ${String(ga)} must fail`);
    assert.deepEqual(r.regimens, []);
  }
  assert.equal(E.needsGA(load('oseltamivir'), 126), true);
  assert.equal(E.needsGA(load('oseltamivir'), 127), false);
  assert.equal(E.needsGA(load('amoxicillin'), 1), false);
  assert.deepEqual(calc('amoxicillin', 1, 3).errors, []);
  assert.deepEqual(calc('oseltamivir', 127, 3).errors, []);
  assert.equal(E.matchPop({ pmaLt: 38 }, { ageDays: 1, gaWeeks: NaN }), false);
  assert.equal(E.matchPop({ gaGe: 37 }, { ageDays: 1, gaWeeks: null }), false);
  assert.ok(E.calculate(load('amoxicillin'), { ageValue: 1, ageUnit: 'bad', weightKg: 3 }).errors.length);
});

test('small liquid volumes cannot be forced upward or quietly rounded below the dose', () => {
  const r = find(calc('oseltamivir', 1, 0.5, 26), 'neo_pma_lt38').results[0];
  assert.deepEqual(r.mgPerDose, [0.5, 0.5]);
  for (const p of r.products) {
    assert.equal(p.ok, false);
    assert.equal(p.reason, 'unmeasurable');
    assert.equal(p.amount, undefined);
  }
  assert.equal(E._internal.roundLiquid(0.02, 0.02, {}), null);
  assert.equal(E._internal.roundLiquid(0.0833333333, 0.0833333333, {}), null);
  assert.deepEqual(E._internal.roundLiquid(0.083, 0.14, {}), [0.1, 0.1]);
  assert.deepEqual(E._internal.roundLiquid(0.05, 0.1, {}), [0.05, 0.1]);
  assert.deepEqual(E._internal.roundLiquid(7.51, 11.25, {}), [7.6, 11.2]);
  const epi = calc('epinephrine', 40, 1.5).regimens[0].results[0];
  assert.equal(epi.products[0].ok, false);  // 0.015 mL cannot become 0.01 or 0.02 mL
});

test('iron: all dosage-range frequency options apply the usual 200 mg/day upper limit', () => {
  for (const weight of [25, 50, 80, 120]) {
    const r = E.calculate(load('ferrous_sulfate'), { ageValue: 15, ageUnit: 'year', weightKg: weight });
    const g = find(r, 'tx_range');
    assert.match(g.quotes.join(' '), /usual maximum daily dose: 150 to 200/);
    assert.ok(g.notes.length);
    assert.equal(g.results.length, 3);
    for (const s of g.results) {
      assert.equal(s.dailyMax, 200);
      assert.ok(s.mgPerDay[1] <= 200);
    }
  }
});

test('acetaminophen: keep 1000 mg extra-strength dose and limit administrations to 3 per 24h', () => {
  const r = E.calculate(load('acetaminophen'), { ageValue: 15, ageUnit: 'year', weightKg: 60 });
  const s = find(r, 'adol_extra').results[0];
  assert.deepEqual(s.mgPerDose, [1000, 1000]);
  assert.deepEqual(s.products[0].amount, [2, 2]);
  assert.equal(s.dailyMax, 3000);
  assert.equal(s.maxDosesPerDay, 3);
  assert.equal(s.maxDosesAtHigh, 3);
  assert.equal(s.mgPerDay, undefined); // PRN does not imply four scheduled administrations
  assert.match(s.order, /max 3 doses\/24h/);
  const child = find(calc('acetaminophen', 365.25 * 5, 18), 'weight_directed').results[0];
  assert.equal(child.maxDosesPerDay, 5);
  assert.match(child.order, /max 5 doses\/24h/);
});

test('PJP prophylaxis: each alternative has its own weekday plan, including q12h only 2-3 days/week', () => {
  const r = E.calculate(load('co_trimoxazole'), { ageValue: 5, ageUnit: 'year', weightKg: 20 });
  const g = find(r, 'pjp_ppx');
  assert.equal(g.results.length, 3);
  const daily = g.results.find(s => s.schedule.pattern === 'daily');
  assert.equal(daily.freq, 'q24h');
  assert.deepEqual(daily.schedule.daysPerWeek, [7]);
  const consecutive = g.results.find(s => s.schedule.pattern === 'consecutive');
  assert.equal(consecutive.freq, 'q24h');
  assert.deepEqual(consecutive.schedule.daysPerWeek, [3]);
  const bid = g.results.find(s => s.freq === 'q12h');
  assert.deepEqual(bid.schedule.daysPerWeek, [2, 3]);
  assert.deepEqual(bid.mgPerDose, [50, 50]);
  assert.match(bid.order, /selected days only/);
  assert.match(g.notes.join(' '), /هم‌زمان اجرا نشوند/);
});

test('ceftriaxone neonatal calcium warning accompanies every neonatal regimen', () => {
  for (const age of [3, 14, 28]) for (const g of calc('ceftriaxone', age, 3).regimens) {
    assert.ok(g.warnings.some(w => w.includes('IV calcium')), g.id);
  }
});

test('combination products require a feasible intersection of all component doses', () => {
  const d = load('cold_products');
  d.products.grippe.verificationStatus = 'verified';
  const g = d.regimens.find(r => r.id === 'c6_12');
  // At the documented ratio, both components require the same 15 mL.
  let r = E.calculate(d, { ageValue: 8, ageUnit: 'year', weightKg: 26 });
  assert.deepEqual(find(r, g.id).results[0].products[0].amount, [15, 15]);
  // A changed ratio cannot be dealt with by underdosing one component.
  d.products.grippe.components.chlorpheniramine.strength = 1;
  r = E.calculate(d, { ageValue: 8, ageUnit: 'year', weightKg: 26 });
  assert.equal(find(r, g.id).results[0].products[0].ok, false);
});

test('fallback messages describe missing implementation, not absence of a dose in UpToDate', () => {
  const r = calc('albendazole', 1, 3);
  assert.equal(r.regimens.length, 0);
  assert.ok(r.messages.length);
  assert.ok(!r.messages.some(m => m.includes('در UpToDate دوزی')));
});
