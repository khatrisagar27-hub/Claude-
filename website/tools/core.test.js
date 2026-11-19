// Known-answer tests for core.js. No dependencies: node website/tools/core.test.js
'use strict';
var assert = require('assert');
var S = require('./core.js');
var D = S.data;
var failures = 0, passed = 0;
function test(name, fn) {
  try { fn(); passed++; }
  catch (e) { failures++; console.error('FAIL ' + name + '\n  ' + (e && e.message)); }
}
function near(a, b, tol, msg) { assert.ok(Math.abs(a - b) <= (tol || 0.005), (msg || '') + ' expected ' + b + ', got ' + a); }
var d = S.utc;

// ── formatting ──
test('inr uses Indian grouping', function () {
  assert.strictEqual(S.inr(123456.78), '₹1,23,456.78');
  assert.strictEqual(S.inr(1234567, 0), '₹12,34,567');
  assert.strictEqual(S.inr(-999.5), '-₹999.50');
  assert.strictEqual(S.inr(100), '₹100.00');
});
test('num reads commas, rupee signs and brackets', function () {
  assert.strictEqual(S.num('1,23,456.50'), 123456.5);
  assert.strictEqual(S.num('₹ 2,000'), 2000);
  assert.strictEqual(S.num('(1,500)'), -1500);
  assert.ok(isNaN(S.num('abc')));
  assert.ok(isNaN(S.num('')));
});
test('amount in words, lakh and crore', function () {
  assert.strictEqual(S.amountInWords(123456.78), 'Rupees One Lakh Twenty-Three Thousand Four Hundred Fifty-Six and Paise Seventy-Eight Only');
  assert.strictEqual(S.amountInWords(10000000), 'Rupees One Crore Only');
  assert.strictEqual(S.amountInWords(0), 'Rupees Zero Only');
  assert.strictEqual(S.amountInWords(1005), 'Rupees One Thousand Five Only');
  assert.strictEqual(S.amountInWords(1234567890), 'Rupees One Hundred Twenty-Three Crore Forty-Five Lakh Sixty-Seven Thousand Eight Hundred Ninety Only');
});
test('dates parse in Indian formats and reject impossible ones', function () {
  assert.strictEqual(S.iso(S.parseDate('15/06/2026')), '2026-06-15');
  assert.strictEqual(S.iso(S.parseDate('2026-06-15')), '2026-06-15');
  assert.strictEqual(S.iso(S.parseDate('15-Jun-2026')), '2026-06-15');
  assert.strictEqual(S.parseDate('31/02/2026'), null);
  assert.strictEqual(S.monthsOrPart(d(2026, 1, 20), d(2026, 2, 8)), 2);
  assert.strictEqual(S.iso(S.addMonths(d(2026, 3, 31), 6)), '2026-09-30');
  assert.strictEqual(S.iso(S.addMonths(d(2026, 1, 31), 1)), '2026-02-28');
});
test('pasted table detects tabs and quoted CSV', function () {
  assert.deepStrictEqual(S.parseTable('a\tb\n1\t2'), [['a', 'b'], ['1', '2']]);
  assert.deepStrictEqual(S.parseTable('"x, y",3\nz,4'), [['x, y', '3'], ['z', '4']]);
});

// ── GST ──
test('GST exclusive, intra-State splits CGST and SGST', function () {
  var r = S.gstCalc({ amount: 10000, rate: 18, inclusive: false, interState: false });
  assert.strictEqual(r.cgst, 900); assert.strictEqual(r.sgst, 900); assert.strictEqual(r.total, 11800);
});
test('GST inclusive, inter-State', function () {
  var r = S.gstCalc({ amount: 11800, rate: 18, inclusive: true, interState: true });
  assert.strictEqual(r.taxable, 10000); assert.strictEqual(r.igst, 1800); assert.strictEqual(r.total, 11800);
});
test('GSTIN check character', function () {
  assert.strictEqual(S.gstinCheckChar('27AAPFU0939F1Z'), 'V');
  assert.ok(S.checkGSTIN('27AAPFU0939F1ZV').valid);
  var bad = S.checkGSTIN('27AAPFU0939F1ZW');
  assert.ok(!bad.valid && /Check character should be V/.test(bad.issues[0]));
});
test('identify picks the identifier from its shape', function () {
  assert.strictEqual(S.identify('ABCPE1234F').type, 'PAN');
  assert.strictEqual(S.identify('ABCPE1234F').fields[0][1], 'Individual');
  assert.strictEqual(S.identify('MUMA12345B').type, 'TAN');
  assert.strictEqual(S.identify('U72200GJ2022PTC123456').type, 'CIN');
  assert.ok(S.identify('U72200GJ2022PTC123456').valid);
  assert.strictEqual(S.identify('AAB-1234').type, 'LLPIN');
  assert.strictEqual(S.identify('12345678').type, 'DIN');
  assert.ok(!S.identify('ABCXE1234F').valid);
});
test('GST late fee caps by turnover', function () {
  var r = S.gstLateFee({ type: 'monthly', due: d(2026, 5, 20), filed: d(2026, 8, 20), turnover: 10000000 });
  assert.strictEqual(r.days, 92); assert.strictEqual(r.uncapped, 4600); assert.strictEqual(r.fee, 2000);
  assert.strictEqual(S.gstLateFee({ type: 'monthly', nil: true, due: d(2026, 5, 20), filed: d(2026, 6, 4), turnover: 1 }).fee, 300);
  var a = S.gstLateFee({ type: 'annual', due: d(2026, 12, 31), filed: d(2027, 3, 31), turnover: 30000000 });
  assert.strictEqual(a.days, 90); assert.strictEqual(a.fee, 4500); assert.strictEqual(a.cap, 12000);
});
test('GST interest at 18% a year by days', function () {
  var r = S.gstInterest({ tax: 100000, due: d(2026, 5, 20), paid: d(2026, 6, 19) });
  assert.strictEqual(r.days, 30); near(r.interest, 1479.45);
});

// ── TDS ──
function row(id) { return D.tds.rows.filter(function (r) { return r.id === id; })[0]; }
test('194C: single payment above Rs 30,000', function () {
  var r = S.tdsCompute(row('contractor-oth'), { amount: 35000, prior: 0 });
  assert.ok(r.applies); assert.strictEqual(r.tds, 700);
});
test('194C: below both limits', function () {
  assert.ok(!S.tdsCompute(row('contractor-ind'), { amount: 25000, prior: 50000 }).applies);
});
test('194C: crossing the aggregate takes in earlier untaxed payments', function () {
  var r = S.tdsCompute(row('contractor-ind'), { amount: 25000, prior: 90000, priorTaxed: false });
  assert.strictEqual(r.base, 115000); assert.strictEqual(r.tds, 1150);
  assert.strictEqual(S.tdsCompute(row('contractor-ind'), { amount: 25000, prior: 90000, priorTaxed: true }).tds, 250);
});
test('194Q: only the excess over Rs 50 lakh, 5% without PAN', function () {
  var r = S.tdsCompute(row('goods'), { amount: 2000000, prior: 4000000 });
  assert.strictEqual(r.base, 1000000); assert.strictEqual(r.tds, 1000);
  assert.strictEqual(S.tdsCompute(row('goods'), { amount: 2000000, prior: 4000000, hasPan: false }).tds, 50000);
});
test('no PAN: 20% unless the rate is higher', function () {
  assert.strictEqual(S.tdsCompute(row('professional'), { amount: 100000, hasPan: false }).rate, 0.20);
});
test('TDS deposit due date', function () {
  assert.strictEqual(S.iso(S.tdsDepositDue(d(2026, 3, 10))), '2026-04-30');
  assert.strictEqual(S.iso(S.tdsDepositDue(d(2026, 12, 10))), '2027-01-07');
  assert.strictEqual(S.iso(S.tdsDepositDue(d(2026, 6, 10))), '2026-07-07');
});
test('TDS interest, month or part of a month', function () {
  // deductible 15 Apr, deducted 10 May (2 months at 1%); due 7 Jun, paid 8 Jun: May and June (2 months at 1.5%)
  var r = S.tdsInterest({ tds: 10000, deductible: d(2026, 4, 15), deducted: d(2026, 5, 10), deposited: d(2026, 6, 8) });
  assert.strictEqual(r.lateDeductionInterest, 200); assert.strictEqual(r.lateDepositInterest, 300); assert.strictEqual(r.total, 500);
  assert.strictEqual(S.tdsInterest({ tds: 10000, deductible: d(2026, 4, 15), deducted: d(2026, 4, 15), deposited: d(2026, 5, 7) }).total, 0);
});
test('TDS statement late fee capped at the tax', function () {
  var r = S.tdsLateFee({ due: d(2026, 7, 31), filed: d(2026, 8, 30), tds: 5000 });
  assert.strictEqual(r.days, 30); assert.strictEqual(r.fee, 5000); assert.ok(r.capped);
});

// ── INCOME-TAX ──
test('new regime: salary 12.75 lakh is nil after rebate', function () {
  var r = S.incomeTax({ salary: 1275000, other: 0, deductions: 0, age: 'below60' }).newRegime;
  assert.strictEqual(r.taxable, 1200000); assert.strictEqual(r.slabTax, 60000); assert.strictEqual(r.total, 0);
});
test('new regime: marginal relief just above 12 lakh', function () {
  var r = S.incomeTax({ salary: 0, other: 1210000, age: 'below60' }).newRegime;
  assert.strictEqual(r.rebateRelief, 51500); assert.strictEqual(r.total, 10400);
});
test('new regime: surcharge marginal relief just above 50 lakh', function () {
  var r = S.incomeTax({ salary: 0, other: 5010000, age: 'below60' }).newRegime;
  assert.strictEqual(r.surchargeRelief, 101300); assert.strictEqual(r.total, 1133600);
});
test('old regime: rebate up to 5 lakh and senior slab', function () {
  assert.strictEqual(S.incomeTax({ salary: 0, other: 500000, age: 'below60' }).oldRegime.total, 0);
  var r = S.incomeTax({ salary: 1000000, other: 0, deductions: 150000, age: 'below60' }).oldRegime;
  assert.strictEqual(r.taxable, 800000); assert.strictEqual(r.total, 75400);
  assert.strictEqual(S.incomeTax({ salary: 0, other: 800000, age: 'senior' }).oldRegime.total, 72800);
});
test('advance tax instalments are cumulative', function () {
  var r = S.advanceTax({ liability: 100000, credits: 20000, fyStart: 2026 });
  assert.deepStrictEqual(r.rows.map(function (x) { return x.instalment; }), [12000, 24000, 24000, 20000]);
  assert.strictEqual(S.iso(r.rows[3].date), '2027-03-15');
  assert.ok(!S.advanceTax({ liability: 9000, fyStart: 2026 }).payable);
});

// ── ACCOUNTING ──
test('SLM depreciation: full years end at residual', function () {
  var r = S.depreciation({ cost: 100000, residualPct: 5, life: 5, method: 'SLM', putToUse: d(2025, 4, 1) });
  assert.strictEqual(r.rows.length, 5);
  r.rows.forEach(function (x) { assert.strictEqual(x.depreciation, 19000); });
  assert.strictEqual(r.rows[4].closing, 5000);
});
test('SLM depreciation: part first year, remainder in the last', function () {
  var r = S.depreciation({ cost: 100000, residualPct: 5, life: 5, method: 'SLM', putToUse: d(2025, 10, 1) });
  assert.strictEqual(r.rows[0].days, 182); near(r.rows[0].depreciation, 9473.97);
  assert.strictEqual(r.rows.length, 6); assert.strictEqual(r.rows[5].closing, 5000);
});
test('WDV depreciation reaches residual at the end of the life', function () {
  var r = S.depreciation({ cost: 100000, residualPct: 5, life: 5, method: 'WDV', putToUse: d(2025, 4, 1) });
  near(r.rate, 0.450720, 0.000001);
  assert.strictEqual(r.rows.length, 5); assert.strictEqual(r.rows[4].closing, 5000);
});
test('loan EMI and schedule close at zero', function () {
  var r = S.loanSchedule({ principal: 1000000, annualRate: 9, months: 60, firstEmi: d(2026, 5, 5) });
  near(r.emi, 20758.36, 0.01);
  assert.strictEqual(r.rows[59].balance, 0);
  var sumP = r.years.reduce(function (s, y) { return s + y.principal; }, 0);
  near(sumP, 1000000, 0.05);
  assert.strictEqual(r.years[0].fy, 'FY 2026-27');
  near(r.years[0].nonCurrent + r.years[0].current, r.years[0].closing, 0.01);
});

// ── AUDIT ──
test('attribute sample sizes match the AICPA table', function () {
  assert.strictEqual(S.attributeSampleSize({ confidence: 0.95, tolerable: 0.05, expected: 0 }).size, 59);
  assert.strictEqual(S.attributeSampleSize({ confidence: 0.95, tolerable: 0.05, expected: 0.01 }).size, 93);
  assert.strictEqual(S.attributeSampleSize({ confidence: 0.90, tolerable: 0.05, expected: 0 }).size, 45);
  assert.strictEqual(S.attributeSampleSize({ confidence: 0.95, tolerable: 0.10, expected: 0.02 }).size, 46);
  assert.strictEqual(S.attributeSampleSize({ confidence: 0.95, tolerable: 0.05, expected: 0.0125 }).size, 124);
  assert.ok(S.attributeSampleSize({ confidence: 0.95, tolerable: 0.05, expected: 0.05 }).error);
});
test('MUS sample size', function () {
  var r = S.musSampleSize({ population: 50000000, tolerable: 2500000, expected: 500000, confidence: 0.95 });
  assert.strictEqual(r.size, 89);
});
test('seeded selections repeat exactly and stay in range', function () {
  var a = S.selectRandom(1000, 25, 42), b = S.selectRandom(1000, 25, 42);
  assert.deepStrictEqual(a, b);
  assert.strictEqual(new Set(a).size, 25);
  a.forEach(function (x) { assert.ok(x >= 1 && x <= 1000); });
  var s = S.selectSystematic(100, 10, 7);
  assert.strictEqual(s.items.length, 10); assert.strictEqual(s.interval, 10);
});
test('MUS selection makes items above the interval certain', function () {
  var r = S.selectMUS([500000, 100, 200, 300, 400, 50000, 600, 700], 5, 1);
  var big = r.picks.filter(function (p) { return p.item === 1; })[0];
  assert.ok(big && big.certain && big.hits >= 4);
});
test('Benford on a Benford-distributed set conforms', function () {
  var nums = [];
  for (var i = 0; i < 5000; i++) nums.push(Math.pow(10, (i + 0.5) / 5000 * 4));
  var r = S.benford(nums);
  assert.strictEqual(r.n, 5000); assert.ok(r.mad < 0.006, 'mad ' + r.mad); assert.ok(!r.exceeds5pc);
  var flat = S.benford([1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33, 44, 55, 66, 77, 88, 99]);
  assert.strictEqual(flat.verdict, 'Nonconformity');
});
test('duplicates and gaps by series', function () {
  var r = S.dupesAndGaps(['INV/001', 'INV/002', 'INV/002', 'INV/005', 'CN/01', 'CN/03', 'inv/001']);
  assert.strictEqual(r.duplicates.length, 2);
  var inv = r.series.filter(function (s) { return s.prefix === 'INV/'; })[0];
  assert.deepStrictEqual(inv.missing, ['INV/003 to INV/004']);
  var cn = r.series.filter(function (s) { return s.prefix === 'CN/'; })[0];
  assert.deepStrictEqual(cn.missing, ['CN/02']);
});
test('ageing uses Schedule III month buckets from the due date', function () {
  var b = D.scheduleIII.receivableBuckets;
  var r = S.ageing([
    { party: 'A', date: d(2026, 3, 1), amount: 100 },     // 0 to 6 months
    { party: 'A', date: d(2025, 9, 30), amount: 200 },    // exactly 6 months: next bucket
    { party: 'B', date: d(2024, 3, 31), amount: 300 },    // 2 to 3 years
    { party: 'B', date: d(2026, 4, 30), amount: 50 }      // not yet due
  ], d(2026, 3, 31), b);
  assert.deepStrictEqual(r.totals, [100, 200, 0, 300, 0]); assert.strictEqual(r.notDue, 50); assert.strictEqual(r.grand, 650);
  assert.strictEqual(r.parties[0].party, 'B');
});
test('reconciliation matches loosely and nets repeated keys', function () {
  var r = S.reconcile(
    [{ key: 'INV-0001', amount: 100 }, { key: 'INV-0002', amount: 50 }, { key: 'INV-0002', amount: 50 }, { key: 'X9', amount: 7 }],
    [{ key: 'inv/1', amount: 100 }, { key: 'INV 2', amount: 90 }, { key: 'Y1', amount: 3 }], { loose: true });
  assert.strictEqual(r.matched.length, 1); assert.strictEqual(r.mismatched.length, 1); assert.strictEqual(r.mismatched[0].difference, 10);
  assert.strictEqual(r.onlyA.length, 1); assert.strictEqual(r.onlyB.length, 1);
});
test('Schedule III ratios flag a change above 25%', function () {
  var base = { currentAssets: 200, currentLiabilities: 100, debt: 100, equity: 200, equityOpening: 200, pat: 30, nonCash: 10, interest: 10, leasePayments: 0,
    principalRepaid: 20, prefDividend: 0, cogs: 400, inventory: 100, inventoryOpening: 100, creditSales: 600, receivables: 100, receivablesOpening: 100,
    creditPurchases: 300, payables: 50, payablesOpening: 50, sales: 600, ebit: 40, capitalEmployed: 300, investmentIncome: 5, avgInvestments: 50 };
  var cy = Object.assign({}, base, { currentAssets: 300 });
  var r = S.ratios(cy, base);
  var cur = r.filter(function (x) { return x.id === 'current'; })[0];
  assert.strictEqual(cur.cy, 3); assert.strictEqual(cur.py, 2); assert.ok(cur.explain);
  assert.ok(!r.filter(function (x) { return x.id === 'netProfit'; })[0].explain);
});
test('MSME: 45-day cap and compound interest', function () {
  var r = S.msme({ amount: 100000, acceptance: d(2026, 4, 1), agreedDays: 60, bankRate: 6, asAt: d(2026, 7, 16) });
  assert.strictEqual(r.creditDays, 45); assert.ok(r.capped); assert.strictEqual(S.iso(r.due), '2026-05-16');
  assert.strictEqual(r.months, 2); near(r.interest, 3022.5, 0.01);
  assert.strictEqual(S.msme({ amount: 1000, acceptance: d(2026, 4, 1), agreedDays: NaN, bankRate: 6, asAt: d(2026, 4, 10) }).interest, 0);
});
test('company and LLP due dates', function () {
  var r = S.rocDates({ entity: 'company', fyEnd: d(2026, 3, 31), agm: d(2026, 9, 30) });
  assert.deepStrictEqual(r.map(function (x) { return S.iso(x.date); }), ['2026-09-30', '2026-10-14', '2026-10-29', '2026-11-28']);
  var l = S.rocDates({ entity: 'llp', fyEnd: d(2026, 3, 31) });
  assert.deepStrictEqual(l.map(function (x) { return S.iso(x.date); }), ['2026-05-30', '2026-10-30']);
});
test('calendar covers the year in date order', function () {
  var c = S.calendar(2026);
  for (var i = 1; i < c.length; i++) assert.ok(c[i - 1].date <= c[i].date);
  assert.ok(c.every(function (x) { return x.date >= d(2026, 4, 1) && x.date <= d(2027, 3, 31); }), 'all dates inside FY 2026-27');
  assert.ok(!c.some(function (x) { return S.iso(x.date) === '2026-04-07' && x.law === 'TDS'; }), 'no 7 April TDS entry');
  assert.ok(c.some(function (x) { return S.iso(x.date) === '2026-04-30' && /March/.test(x.what); }));
});

console.log(passed + ' passed, ' + failures + ' failed');
process.exit(failures ? 1 : 0);
