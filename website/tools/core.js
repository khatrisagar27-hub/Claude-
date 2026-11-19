// Calculation library for the firm's tools. Pure functions, no DOM, no network.
// Every figure a tool shows is computed here, and every statutory rate comes from
// statutory-data.js, so a reviewer can read and challenge both.
// Runs in the browser (window.SKA) and in Node (require) for the tests.
(function (root, factory) {
  'use strict';
  var isNode = typeof module !== 'undefined' && module.exports;
  var api = factory(isNode ? require('./statutory-data.js') : root.SKA_DATA);
  if (isNode) module.exports = api; else root.SKA = api;
})(typeof self !== 'undefined' ? self : this, function (DATA) {
  'use strict';

  // ── NUMBERS ──
  function num(v) {
    if (typeof v === 'number') return v;
    if (v == null) return NaN;
    var s = String(v).trim();
    if (!s) return NaN;
    var neg = /^\(.*\)$/.test(s) || /^-/.test(s);
    s = s.replace(/₹|,|\s|Rs\.?|INR/gi, '').replace(/^\((.*)\)$/, '$1').replace(/^-/, '');
    if (!/^(\d+\.?\d*|\.\d+)$/.test(s)) return NaN;
    var n = parseFloat(s);
    return neg ? -n : n;
  }
  function round(n, dp) {
    var f = Math.pow(10, dp || 0);
    return Math.round((n + (n >= 0 ? 1 : -1) * 1e-9) * f) / f;
  }
  function roundTo(n, step) { return Math.round((n + 1e-9) / step) * step; }
  function inr(n, dp) {
    if (n == null || isNaN(n)) return '';
    if (!isFinite(n)) return 'No limit';
    dp = dp == null ? 2 : dp;
    var neg = n < 0;
    var parts = Math.abs(round(n, dp)).toFixed(dp).split('.');
    var int = parts[0];
    var last3 = int.slice(-3), rest = int.slice(0, -3);
    if (rest) last3 = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + last3;
    return (neg ? '-' : '') + '₹' + last3 + (dp ? '.' + parts[1] : '');
  }
  function pct(n, dp) { return isFinite(n) ? round(n * 100, dp == null ? 2 : dp).toFixed(dp == null ? 2 : dp) + '%' : ''; }

  var ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve',
    'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
  var TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
  function two(n) { return n < 20 ? ONES[n] : TENS[Math.floor(n / 10)] + (n % 10 ? '-' + ONES[n % 10] : ''); }
  function three(n) {
    var h = Math.floor(n / 100), r = n % 100;
    return (h ? ONES[h] + ' Hundred' + (r ? ' ' : '') : '') + (r ? two(r) : '');
  }
  function wordsInt(n) {
    if (n === 0) return 'Zero';
    var out = [];
    var crore = Math.floor(n / 1e7), lakh = Math.floor((n % 1e7) / 1e5), thousand = Math.floor((n % 1e5) / 1e3), rest = n % 1000;
    if (crore) out.push(wordsInt(crore) + ' Crore');
    if (lakh) out.push(two(lakh) + ' Lakh');
    if (thousand) out.push(two(thousand) + ' Thousand');
    if (rest) out.push(three(rest));
    return out.join(' ');
  }
  // Indian numbering: lakh and crore. Paise are rounded to two places.
  function amountInWords(amount) {
    if (!isFinite(amount) || Math.abs(amount) >= 1e15) return '';
    var a = Math.abs(round(amount, 2));
    var rupees = Math.floor(a + 1e-9);
    var paise = Math.round((a - rupees) * 100);
    if (paise === 100) { rupees += 1; paise = 0; }
    return (amount < 0 ? 'Minus ' : '') + 'Rupees ' + wordsInt(rupees) + (paise ? ' and Paise ' + two(paise) : '') + ' Only';
  }

  // ── DATES (all arithmetic in UTC, so no time-zone or daylight shifts) ──
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function utc(y, m, d) { return new Date(Date.UTC(y, m - 1, d)); }
  function validYmd(y, m, d) {
    var dt = utc(y, m, d);
    return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d ? dt : null;
  }
  // Accepts yyyy-mm-dd, dd/mm/yyyy (also - or .) and dd-Mon-yyyy.
  function parseDate(v) {
    if (v instanceof Date) return isNaN(v) ? null : v;
    var s = String(v == null ? '' : v).trim();
    var m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
    if (m) return validYmd(+m[1], +m[2], +m[3]);
    m = /^(\d{1,2})[\/\-. ](\d{1,2})[\/\-. ](\d{2,4})$/.exec(s);
    if (m) return validYmd(+m[3] < 100 ? 2000 + +m[3] : +m[3], +m[2], +m[1]);
    m = /^(\d{1,2})[\/\-. ]([A-Za-z]{3})[A-Za-z]*[\/\-. ,]+(\d{2,4})$/.exec(s);
    if (m) {
      var mi = MONTHS.map(function (x) { return x.toLowerCase(); }).indexOf(m[2].toLowerCase());
      if (mi < 0) return null;
      return validYmd(+m[3] < 100 ? 2000 + +m[3] : +m[3], mi + 1, +m[1]);
    }
    return null;
  }
  function iso(d) { return d.toISOString().slice(0, 10); }
  function fmtDate(d) { return d ? d.getUTCDate() + ' ' + MONTHS[d.getUTCMonth()] + ' ' + d.getUTCFullYear() : ''; }
  function addDays(d, n) { return new Date(d.getTime() + n * 864e5); }
  function diffDays(a, b) { return Math.round((b.getTime() - a.getTime()) / 864e5); }
  function addMonths(d, n) {
    var y = d.getUTCFullYear(), m = d.getUTCMonth() + n, day = d.getUTCDate();
    var last = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    var wasLast = day === new Date(Date.UTC(y, d.getUTCMonth() + 1, 0)).getUTCDate();
    return new Date(Date.UTC(y, m, wasLast ? last : Math.min(day, last)));
  }
  function fyStartYear(d) { return d.getUTCMonth() >= 3 ? d.getUTCFullYear() : d.getUTCFullYear() - 1; }
  function fyLabel(startYear) { return 'FY ' + startYear + '-' + String((startYear + 1) % 100).padStart(2, '0'); }
  // Calendar months touched from a to b, both included ("month or part of a month").
  function monthsOrPart(a, b) {
    if (b < a) return 0;
    return (b.getUTCFullYear() - a.getUTCFullYear()) * 12 + (b.getUTCMonth() - a.getUTCMonth()) + 1;
  }

  // ── PASTED DATA ──
  function parseCsvLine(line, sep) {
    var out = [], cur = '', q = false;
    for (var i = 0; i < line.length; i++) {
      var c = line[i];
      if (q) {
        if (c === '"') { if (line[i + 1] === '"') { cur += '"'; i++; } else q = false; }
        else cur += c;
      } else if (c === '"') q = true;
      else if (c === sep) { out.push(cur); cur = ''; }
      else cur += c;
    }
    out.push(cur);
    return out;
  }
  // Rows copied from Excel arrive tab-separated; CSV, semicolon and pipe also work.
  function parseTable(text) {
    var lines = String(text || '').split(/\r?\n/).filter(function (l) { return l.trim() !== ''; });
    if (!lines.length) return [];
    var sample = lines.slice(0, 10).join('\n');
    var sep = sample.indexOf('\t') >= 0 ? '\t' : sample.indexOf(';') >= 0 && sample.indexOf(',') < 0 ? ';' : sample.indexOf('|') >= 0 && sample.indexOf(',') < 0 ? '|' : ',';
    return lines.map(function (l) { return parseCsvLine(l, sep).map(function (c) { return c.trim(); }); });
  }
  function parseNumbers(text) {
    var out = [];
    String(text || '').split(/[\n\t;]+/).forEach(function (cell) {
      var n = num(cell);
      if (!isNaN(n)) out.push(n);
    });
    return out;
  }
  function toCsv(rows) {
    return rows.map(function (r) {
      return r.map(function (c) {
        var s = c == null ? '' : String(c);
        return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
      }).join(',');
    }).join('\n');
  }

  // ── GST ──
  function gstCalc(o) {
    var rate = o.rate || 0, cess = o.cess || 0, r = (rate + cess) / 100;
    var taxable, gst, cessAmt;
    if (o.inclusive) {
      taxable = round(o.amount / (1 + r), 2);
      gst = round(taxable * rate / 100, 2);
      cessAmt = round(o.amount - taxable - gst, 2);
      if (!cess) { taxable = round(o.amount - gst, 2); cessAmt = 0; }
    } else {
      taxable = round(o.amount, 2);
      gst = round(taxable * rate / 100, 2);
      cessAmt = round(taxable * cess / 100, 2);
    }
    var cgst = o.interState ? 0 : round(gst / 2, 2);
    var sgst = o.interState ? 0 : round(gst - cgst, 2);
    return { taxable: taxable, gst: gst, igst: o.interState ? gst : 0, cgst: cgst, sgst: sgst, cess: cessAmt, total: round(taxable + gst + cessAmt, 2) };
  }

  var B36 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  function gstinCheckChar(first14) {
    var sum = 0;
    for (var i = 0; i < 14; i++) {
      var p = B36.indexOf(first14[i]) * (i % 2 === 0 ? 1 : 2);
      sum += Math.floor(p / 36) + (p % 36);
    }
    return B36[(36 - (sum % 36)) % 36];
  }
  var PAN_HOLDER = { P: 'Individual', C: 'Company', H: 'Hindu undivided family', F: 'Firm or LLP', A: 'Association of persons',
    T: 'Trust', B: 'Body of individuals', L: 'Local authority', J: 'Artificial juridical person', G: 'Government' };
  function checkPAN(s) {
    s = String(s || '').toUpperCase().replace(/\s/g, '');
    var issues = [];
    if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(s)) issues.push('A PAN is 10 characters: five letters, four digits, one letter.');
    else if (!PAN_HOLDER[s[3]]) issues.push('The fourth character "' + s[3] + '" is not a recognised holder type.');
    return { type: 'PAN', input: s, valid: !issues.length, issues: issues,
      fields: issues.length ? [] : [['Holder type', PAN_HOLDER[s[3]]], ['Fifth character', s[4] + ' (first letter of the surname, or of the name for non-individuals)']] };
  }
  function checkGSTIN(s) {
    s = String(s || '').toUpperCase().replace(/\s/g, '');
    var issues = [], fields = [];
    if (s.length !== 15) issues.push('A GSTIN is 15 characters; this has ' + s.length + '.');
    else if (!/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z][A-Z][0-9A-Z]$/.test(s)) issues.push('The pattern is two digits, a 10-character PAN, an entity code, a letter (normally Z) and a check character.');
    else {
      var state = DATA.gst.stateCodes[s.slice(0, 2)];
      if (!state) issues.push('State code ' + s.slice(0, 2) + ' is not in the list of GST state codes.');
      var pan = checkPAN(s.slice(2, 12));
      if (!pan.valid) issues.push('The embedded PAN ' + s.slice(2, 12) + ' is not well formed.');
      var expect = gstinCheckChar(s.slice(0, 14));
      if (expect !== s[14]) issues.push('Check character should be ' + expect + ', not ' + s[14] + '. One or more characters are wrong.');
      fields = [['State', (state || 'Unknown') + ' (' + s.slice(0, 2) + ')'], ['PAN', s.slice(2, 12)],
        ['Holder type', PAN_HOLDER[s[5]] || 'Unknown'], ['Registration number under this PAN', s[12]], ['Check character', s[14]]];
    }
    return { type: 'GSTIN', input: s, valid: !issues.length, issues: issues, fields: fields };
  }
  var CIN_CLASS = { PLC: 'Public limited company', PTC: 'Private limited company', OPC: 'One person company', NPL: 'Section 8 (not-for-profit) company',
    FLC: 'Public company, subsidiary of a foreign company', FTC: 'Private company, subsidiary of a foreign company', GOI: 'Company owned by the Government of India',
    SGC: 'Company owned by a State Government', GAP: 'General association, public', GAT: 'General association, private', ULL: 'Public company with unlimited liability', ULT: 'Private company with unlimited liability' };
  var CIN_STATE = { AN: 'Andaman and Nicobar Islands', AP: 'Andhra Pradesh', AR: 'Arunachal Pradesh', AS: 'Assam', BR: 'Bihar', CH: 'Chandigarh', CT: 'Chhattisgarh',
    DD: 'Daman and Diu', DL: 'Delhi', DN: 'Dadra and Nagar Haveli', GA: 'Goa', GJ: 'Gujarat', HP: 'Himachal Pradesh', HR: 'Haryana', JH: 'Jharkhand', JK: 'Jammu and Kashmir',
    KA: 'Karnataka', KL: 'Kerala', LD: 'Lakshadweep', MH: 'Maharashtra', ML: 'Meghalaya', MN: 'Manipur', MP: 'Madhya Pradesh', MZ: 'Mizoram', NL: 'Nagaland', OR: 'Odisha',
    PB: 'Punjab', PY: 'Puducherry', RJ: 'Rajasthan', SK: 'Sikkim', TG: 'Telangana', TN: 'Tamil Nadu', TR: 'Tripura', UP: 'Uttar Pradesh', UR: 'Uttarakhand', WB: 'West Bengal' };
  function checkCIN(s) {
    s = String(s || '').toUpperCase().replace(/\s/g, '');
    var m = /^([LU])([0-9]{5})([A-Z]{2})([0-9]{4})([A-Z]{3})([0-9]{6})$/.exec(s), issues = [], fields = [];
    if (!m) issues.push('A CIN is 21 characters: L or U, a 5-digit industry code, a 2-letter State code, the year, a 3-letter class and a 6-digit number.');
    else {
      if (!CIN_CLASS[m[5]]) issues.push('Class code ' + m[5] + ' is not a recognised company class.');
      fields = [['Listing status', m[1] === 'L' ? 'Listed' : 'Unlisted'], ['Industry code (NIC)', m[2]], ['State of registration', (CIN_STATE[m[3]] || 'Code') + ' (' + m[3] + ')'],
        ['Year of incorporation', m[4]], ['Class', CIN_CLASS[m[5]] || m[5]], ['Registration number', m[6]]];
    }
    return { type: 'CIN', input: s, valid: !issues.length, issues: issues, fields: fields };
  }
  function checkPattern(type, s, re, rule, fieldsFn) {
    s = String(s || '').toUpperCase().replace(/\s/g, '');
    var ok = re.test(s);
    return { type: type, input: s, valid: ok, issues: ok ? [] : [rule], fields: ok && fieldsFn ? fieldsFn(s) : [] };
  }
  // Works out which identifier was entered from its shape, then checks it.
  function identify(raw) {
    var s = String(raw || '').toUpperCase().replace(/\s/g, '');
    if (!s) return null;
    if (s.length === 15) return checkGSTIN(s);
    if (s.length === 21) return checkCIN(s);
    if (/^[A-Z]{3}-?[0-9]{4}$/.test(s)) return checkPattern('LLPIN', s, /^[A-Z]{3}-?[0-9]{4}$/, '', null);
    if (/^[0-9]{8}$/.test(s)) return checkPattern('DIN', s, /^[0-9]{8}$/, '', null);
    if (/^[A-Z]{4}[0-9]/.test(s)) return checkPattern('TAN', s, /^[A-Z]{4}[0-9]{5}[A-Z]$/, 'A TAN is 10 characters: four letters, five digits, one letter.',
      function (v) { return [['Jurisdiction code', v.slice(0, 3)], ['Fourth character', v[3] + ' (first letter of the deductor\'s name)']]; });
    if (s.length === 10) return checkPAN(s);
    return { type: 'Unrecognised', input: s, valid: false, fields: [],
      issues: ['Length ' + s.length + ' does not match a GSTIN (15), CIN (21), PAN or TAN (10), DIN (8) or LLPIN (7 or 8).'] };
  }

  function gstInterest(o) {
    var days = Math.max(0, diffDays(o.due, o.paid));
    var rate = o.rate == null ? DATA.gst.interestRate : o.rate;
    return { days: days, rate: rate, interest: round(o.tax * rate * days / 365, 2) };
  }
  function gstLateFee(o) {
    var L = DATA.gst.lateFee, days = Math.max(0, diffDays(o.due, o.filed)), perDay, cap, i;
    if (o.type === 'annual') {
      for (i = 0; i < L.annual.length; i++) if (o.turnover <= L.annual[i][0]) break;
      perDay = L.annual[i][1]; cap = round(L.annual[i][2] * o.turnover, 2);
    } else if (o.nil) { perDay = L.perDayNil; cap = L.capNil; }
    else {
      for (i = 0; i < L.caps.length; i++) if (o.turnover <= L.caps[i][0]) break;
      perDay = L.perDay; cap = L.caps[i][1];
    }
    var uncapped = days * perDay;
    return { days: days, perDay: perDay, cap: cap, uncapped: uncapped, fee: Math.min(uncapped, cap), capped: uncapped > cap };
  }

  // ── TDS ──
  function tdsCompute(row, o) {
    var T = DATA.tds, amount = o.amount || 0, prior = o.prior || 0;
    var rate = o.hasPan === false ? Math.max(row.rate, row.noPanRate != null ? row.noPanRate : T.noPanRate) : row.rate;
    var applies = false, base = 0, why = '';
    if (row.kind === 'aggregate') {
      var total = prior + amount;
      if (total > row.threshold) {
        applies = true;
        // Once the year's aggregate crosses the limit, tax is due on earlier payments too
        // if none was deducted on them.
        base = o.priorTaxed === false && prior > 0 ? total : amount;
        why = 'Payments in the year (' + inr(total, 0) + ') are above ' + inr(row.threshold, 0) + '.' +
          (base > amount ? ' Tax is worked on the earlier untaxed payments as well.' : '');
      } else if (row.single != null && amount > row.single) {
        applies = true; base = amount;
        why = 'This payment is above the single-payment limit of ' + inr(row.single, 0) + '.';
      } else why = 'Payments in the year (' + inr(total, 0) + ') do not exceed ' + inr(row.threshold, 0) + (row.single != null ? ', and this payment does not exceed ' + inr(row.single, 0) : '') + '.';
    } else if (row.kind === 'single') {
      applies = amount >= row.threshold;
      why = applies ? 'The amount is ' + inr(row.threshold, 0) + ' or more.' : 'The amount is below ' + inr(row.threshold, 0) + '.';
      base = applies ? amount : 0;
    } else if (row.kind === 'monthly') {
      applies = amount > row.threshold;
      why = applies ? 'The amount for the month is above ' + inr(row.threshold, 0) + '.' : 'The amount for the month does not exceed ' + inr(row.threshold, 0) + '.';
      base = applies ? amount : 0;
    } else if (row.kind === 'excess') {
      base = Math.max(0, prior + amount - row.threshold) - Math.max(0, prior - row.threshold);
      applies = base > 0;
      why = applies ? 'Tax applies only to the part above ' + inr(row.threshold, 0) + ' for the year.' : 'Purchases in the year do not exceed ' + inr(row.threshold, 0) + '.';
    }
    var tds = applies ? Math.round(base * rate) : 0;
    return { applies: applies, rate: rate, base: base, tds: tds, net: amount - Math.min(tds, amount), why: why, noPan: o.hasPan === false };
  }
  function tdsDepositDue(deducted) {
    var y = deducted.getUTCFullYear(), m = deducted.getUTCMonth() + 1;
    return m === 3 ? utc(y, 4, 30) : (m === 12 ? utc(y + 1, 1, 7) : utc(y, m + 1, 7));
  }
  function tdsInterest(o) {
    var T = DATA.tds;
    var lateDedMonths = o.deducted > o.deductible ? monthsOrPart(o.deductible, o.deducted) : 0;
    var due = tdsDepositDue(o.deducted);
    var lateDepMonths = o.deposited > due ? monthsOrPart(o.deducted, o.deposited) : 0;
    var a = round(o.tds * T.interestLateDeduction * lateDedMonths, 0);
    var b = round(o.tds * T.interestLateDeposit * lateDepMonths, 0);
    return { depositDue: due, lateDeductionMonths: lateDedMonths, lateDepositMonths: lateDepMonths, lateDeductionInterest: a, lateDepositInterest: b, total: a + b };
  }
  function tdsLateFee(o) {
    var days = Math.max(0, diffDays(o.due, o.filed));
    var uncapped = days * DATA.tds.lateFeePerDay;
    return { days: days, uncapped: uncapped, fee: Math.min(uncapped, Math.max(0, o.tds)), capped: uncapped > o.tds };
  }

  // ── INCOME-TAX ──
  function slabTax(income, slabs) {
    var tax = 0, prev = 0;
    for (var i = 0; i < slabs.length; i++) {
      if (income > prev) tax += (Math.min(income, slabs[i][0]) - prev) * slabs[i][1];
      prev = slabs[i][0];
    }
    return tax;
  }
  function taxOnIncome(R, slabs, income) {
    var I = DATA.incomeTax;
    var tax = slabTax(income, slabs), rebate = 0, rebateRelief = 0;
    if (income <= R.rebateLimit) rebate = Math.min(tax, R.rebateMax);
    else if (R.rebateMarginalRelief && tax > income - R.rebateLimit) rebateRelief = tax - (income - R.rebateLimit);
    var net = tax - rebate - rebateRelief;
    var i = 0;
    while (income > R.surcharge[i][0]) i++;
    var sRate = R.surcharge[i][1], surcharge = net * sRate, surRelief = 0;
    if (i > 0) {
      // Marginal relief: tax plus surcharge cannot exceed the tax payable at the
      // threshold plus the income above it.
      var T = R.surcharge[i - 1][0];
      var cap = slabTax(T, slabs) * (1 + R.surcharge[i - 1][1]) + (income - T);
      if (net + surcharge > cap) surRelief = net + surcharge - cap;
    }
    var beforeCess = net + surcharge - surRelief;
    var cess = beforeCess * I.cess;
    return { slabTax: round(tax, 2), rebate: round(rebate, 2), rebateRelief: round(rebateRelief, 2), surchargeRate: sRate, surcharge: round(surcharge, 2),
      surchargeRelief: round(surRelief, 2), cess: round(cess, 2), total: roundTo(beforeCess + cess, I.roundTo) };
  }
  function incomeTax(o) {
    var I = DATA.incomeTax, N = I.regimes.newRegime, O = I.regimes.oldRegime;
    var salary = Math.max(0, o.salary || 0), other = o.other || 0, ded = Math.max(0, o.deductions || 0);
    var gross = salary + other;
    function side(R, slabs, extraDed) {
      var std = Math.min(salary, R.standardDeduction);
      var taxable = roundTo(Math.max(0, gross - std - extraDed), I.roundTo);
      var t = taxOnIncome(R, slabs, taxable);
      t.label = R.label; t.gross = gross; t.standardDeduction = std; t.deductions = extraDed; t.taxable = taxable;
      return t;
    }
    var n = side(N, N.slabs, 0);
    var old = side(O, O.slabsByAge[o.age] || O.slabsByAge.below60, ded);
    return { newRegime: n, oldRegime: old, lower: n.total <= old.total ? 'newRegime' : 'oldRegime', difference: Math.abs(n.total - old.total) };
  }
  function advanceTax(o) {
    var A = DATA.advanceTax, net = Math.max(0, (o.liability || 0) - (o.credits || 0));
    if (net < A.threshold) return { payable: false, net: net, rows: [] };
    var prev = 0;
    var rows = (o.presumptive ? A.presumptive : A.instalments).map(function (x) {
      var cum = Math.round(net * x[2]);
      var row = { date: utc(x[0] >= 4 ? o.fyStart : o.fyStart + 1, x[0], x[1]), share: x[2], cumulative: cum, instalment: cum - prev };
      prev = cum;
      return row;
    });
    return { payable: true, net: net, rows: rows };
  }

  // ── DEPRECIATION (Companies Act, Schedule II) ──
  // Charged pro rata by days from the date put to use; the year in which the useful
  // life ends takes the asset down to its residual value.
  function depreciation(o) {
    var cost = o.cost, residual = cost * (o.residualPct || 0) / 100, wdv = o.method === 'WDV';
    if (!(cost > 0) || !(o.life > 0) || !o.putToUse) return { error: 'Enter the cost, the useful life and the date put to use.' };
    if (wdv && residual <= 0) return { error: 'The written-down-value rate needs a residual value above zero.' };
    var rate = wdv ? 1 - Math.pow(residual / cost, 1 / o.life) : (cost - residual) / cost / o.life;
    var p = o.putToUse;
    var lifeEnd = addDays(utc(p.getUTCFullYear() + Math.round(o.life), p.getUTCMonth() + 1, p.getUTCDate()), -1);
    var rows = [], opening = cost, y = fyStartYear(p), lastY = fyStartYear(lifeEnd);
    for (; y <= lastY && rows.length < 200; y++) {
      var start = utc(y, 4, 1), end = utc(y + 1, 3, 31);
      var from = p > start ? p : start, to = lifeEnd < end ? lifeEnd : end;
      var days = diffDays(from, to) + 1, daysInYear = diffDays(start, end) + 1;
      var dep = y === lastY ? opening - residual : (wdv ? opening * rate : cost * rate) * days / daysInYear;
      dep = round(Math.max(0, Math.min(dep, opening - residual)), 2);
      rows.push({ fy: fyLabel(y), days: days, opening: round(opening, 2), depreciation: dep, closing: round(opening - dep, 2) });
      opening = round(opening - dep, 2);
    }
    return { rate: rate, residual: round(residual, 2), lifeEnd: lifeEnd, rows: rows };
  }

  // ── LOAN ──
  function loanSchedule(o) {
    var P = o.principal, n = o.months, r = (o.annualRate || 0) / 1200;
    var emi = r === 0 ? P / n : P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1);
    var rows = [], bal = P, totalInterest = 0;
    for (var k = 1; k <= n; k++) {
      var interest = round(bal * r, 2);
      var principal = k === n ? bal : round(emi - interest, 2);
      bal = round(bal - principal, 2);
      totalInterest += interest;
      rows.push({ no: k, date: addMonths(o.firstEmi, k - 1), emi: round(principal + interest, 2), interest: interest, principal: principal, balance: bal });
    }
    var byFy = {}, order = [];
    rows.forEach(function (x) {
      var f = fyStartYear(x.date);
      if (!byFy[f]) { byFy[f] = { fy: fyLabel(f), start: f, interest: 0, principal: 0, closing: 0 }; order.push(f); }
      byFy[f].interest += x.interest; byFy[f].principal += x.principal; byFy[f].closing = x.balance;
    });
    var years = order.map(function (f, i) {
      var Y = byFy[f], next = byFy[order[i + 1]];
      Y.interest = round(Y.interest, 2); Y.principal = round(Y.principal, 2);
      Y.current = next ? round(next.principal, 2) : 0;          // due within 12 months of the year end
      Y.nonCurrent = round(Y.closing - Y.current, 2);
      return Y;
    });
    return { emi: round(emi, 2), totalInterest: round(totalInterest, 2), totalPaid: round(P + totalInterest, 2), rows: rows, years: years };
  }

  // ── AUDIT: MATERIALITY AND SAMPLING ──
  function materiality(o) {
    var overall = o.benchmark * o.pct / 100;
    return { overall: overall, performance: overall * o.performancePct / 100, trivial: overall * o.trivialPct / 100 };
  }
  function binomCdf(k, n, p) {
    var term = Math.pow(1 - p, n), sum = term;
    for (var i = 0; i < k; i++) { term *= (n - i) / (i + 1) * p / (1 - p); sum += term; }
    return sum;
  }
  // Attribute sampling for tests of controls: the smallest sample for which, if the
  // true deviation rate equalled the tolerable rate, finding no more than the
  // allowed deviations would be less likely than the accepted risk.
  function attributeSampleSize(o) {
    var alpha = 1 - o.confidence, p = o.tolerable, e = o.expected || 0;
    if (!(p > 0 && p < 1) || e >= p) return { error: 'The expected deviation rate must be lower than the tolerable rate.' };
    var n = 1;
    for (var k = 0; k <= 60; k++) {
      n = Math.max(n, k + 1);
      while (binomCdf(k, n, p) > alpha) { n++; if (n > 20000) return { error: 'The sample exceeds 20,000 items; revisit the inputs.' }; }
      if (e * n <= k + 1e-9) {
        var adj = o.population && o.population > 0 ? Math.ceil(n / (1 + n / o.population)) : n;
        return { size: n, allowedDeviations: k, adjusted: adj };
      }
    }
    return { error: 'No sample size found; the expected rate is too close to the tolerable rate.' };
  }
  function musSampleSize(o) {
    var f = DATA.sampling.mus[String(Math.round(o.confidence * 100))];
    if (!f) return { error: 'No factors are tabulated for that confidence level.' };
    var denom = o.tolerable - (o.expected || 0) * f[1];
    if (denom <= 0) return { error: 'Expected misstatement, after the expansion factor, uses up the whole tolerable misstatement.' };
    var size = Math.ceil(o.population * f[0] / denom - 1e-9);
    return { size: size, interval: o.population / size, confidenceFactor: f[0], expansionFactor: f[1] };
  }
  // Seeded generator (mulberry32): the same seed always gives the same selection,
  // so the working paper can be reperformed.
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function selectRandom(N, n, seed) {
    n = Math.min(n, N);
    var rand = rng(seed), swapped = {}, out = [];
    for (var i = 0; i < n; i++) {
      var j = i + Math.floor(rand() * (N - i));
      var vi = swapped[i] == null ? i : swapped[i], vj = swapped[j] == null ? j : swapped[j];
      swapped[i] = vj; swapped[j] = vi;
      out.push(vj + 1);
    }
    return out.sort(function (x, y) { return x - y; });
  }
  function selectSystematic(N, n, seed) {
    n = Math.min(n, N);
    var interval = N / n, start = rng(seed)() * interval, out = [];
    for (var i = 0; i < n; i++) out.push(Math.min(N, Math.floor(start + i * interval) + 1));
    return { interval: interval, start: start, items: out };
  }
  // Monetary unit selection: every nth rupee is picked, so an item is as likely
  // to be chosen as it is large. Items at least as large as the interval are certain.
  function selectMUS(amounts, n, seed) {
    var total = 0;
    amounts.forEach(function (a) { total += Math.abs(a); });
    if (!(total > 0) || !(n > 0)) return { error: 'The population needs amounts that add up to more than zero.' };
    var interval = total / n, next = rng(seed)() * interval, cum = 0, picks = [];
    amounts.forEach(function (a, idx) {
      var v = Math.abs(a), hits = 0;
      cum += v;
      while (next < cum) { hits++; next += interval; }
      if (hits) picks.push({ item: idx + 1, amount: a, hits: hits, certain: v >= interval });
    });
    return { total: total, interval: interval, picks: picks };
  }

  // ── AUDIT: ANALYTICS ──
  function benford(numbers, min) {
    var counts = [0, 0, 0, 0, 0, 0, 0, 0, 0], n = 0;
    numbers.forEach(function (v) {
      v = Math.abs(v);
      if (!(v > 0) || !isFinite(v) || v < (min || 0)) return;
      var d = +v.toExponential(15)[0];
      counts[d - 1]++; n++;
    });
    var chi = 0, mad = 0, rows = [];
    for (var d = 1; d <= 9; d++) {
      var exp = Math.log10(1 + 1 / d), obs = n ? counts[d - 1] / n : 0, gap = Math.abs(obs - exp);
      chi += n ? Math.pow(counts[d - 1] - exp * n, 2) / (exp * n) : 0;
      mad += gap;
      // Z-statistic with the continuity correction, applied only where it is smaller than the gap (Nigrini).
      var cc = n && 1 / (2 * n) < gap ? 1 / (2 * n) : 0;
      var z = n ? (gap - cc) / Math.sqrt(exp * (1 - exp) / n) : 0;
      rows.push({ digit: d, count: counts[d - 1], observed: obs, expected: exp, difference: obs - exp, z: z, significant: z > 1.96 });
    }
    mad /= 9;
    var S = DATA.sampling, verdict = '';
    for (var i = 0; i < S.benfordMad.length; i++) if (mad <= S.benfordMad[i][0]) { verdict = S.benfordMad[i][1]; break; }
    return { n: n, rows: rows, chiSquare: chi, mad: mad, verdict: verdict, exceeds5pc: chi > S.chiSquareCritical5pc, exceeds1pc: chi > S.chiSquareCritical1pc };
  }
  function ranges(sorted) {
    var out = [], s = null, p = null;
    sorted.forEach(function (v) {
      if (s == null) { s = p = v; return; }
      if (v === p + 1) { p = v; return; }
      out.push([s, p]); s = p = v;
    });
    if (s != null) out.push([s, p]);
    return out;
  }
  // Duplicates, and numbers missing from each numbered series (grouped by the text
  // before the trailing number, so INV/001 and CN/001 are separate series).
  function dupesAndGaps(items) {
    var seen = {}, order = [], series = {};
    items.forEach(function (raw) {
      var v = String(raw).trim();
      if (!v) return;
      var key = v.toUpperCase();
      if (!seen[key]) { seen[key] = { value: v, count: 0 }; order.push(key); }
      seen[key].count++;
      var m = /^(.*?)(\d+)$/.exec(key);
      if (m) {
        var sk = m[1] + '#' + m[2].length;
        (series[sk] = series[sk] || { prefix: m[1], width: m[2].length, nums: {} }).nums[+m[2]] = true;
      }
    });
    var dupes = order.filter(function (k) { return seen[k].count > 1; }).map(function (k) { return seen[k]; });
    var gaps = [];
    Object.keys(series).forEach(function (sk) {
      var S = series[sk], nums = Object.keys(S.nums).map(Number).sort(function (a, b) { return a - b; });
      if (nums.length < 2) return;
      var missing = [], have = S.nums;
      for (var v = nums[0]; v <= nums[nums.length - 1] && missing.length < 5000; v++) if (!have[v]) missing.push(v);
      function show(x) { return S.prefix + String(x).padStart(S.width, '0'); }
      gaps.push({ prefix: S.prefix || '(numbers only)', from: show(nums[0]), to: show(nums[nums.length - 1]), present: nums.length, missingCount: missing.length,
        missing: ranges(missing).map(function (r) { return r[0] === r[1] ? show(r[0]) : show(r[0]) + ' to ' + show(r[1]); }) });
    });
    return { total: items.filter(function (x) { return String(x).trim(); }).length, unique: order.length, duplicates: dupes, series: gaps };
  }
  function ageing(rows, asAt, buckets) {
    var totals = buckets.map(function () { return 0; }), notDue = 0, grand = 0, byParty = {}, parties = [];
    rows.forEach(function (r) {
      var idx = -1;
      if (r.date <= asAt) { idx = 0; while (idx < buckets.length - 1 && asAt >= addMonths(r.date, buckets[idx][1])) idx++; }
      if (idx < 0) notDue += r.amount; else totals[idx] += r.amount;
      grand += r.amount;
      if (r.party) {
        if (!byParty[r.party]) { byParty[r.party] = { party: r.party, notDue: 0, buckets: buckets.map(function () { return 0; }), total: 0 }; parties.push(r.party); }
        var P = byParty[r.party];
        if (idx < 0) P.notDue += r.amount; else P.buckets[idx] += r.amount;
        P.total += r.amount;
      }
    });
    return { notDue: notDue, totals: totals, grand: grand, parties: parties.map(function (p) { return byParty[p]; }).sort(function (a, b) { return b.total - a.total; }) };
  }
  // Loose matching ignores case, punctuation and spaces, and leading zeros in each
  // number, so INV/2026/045 matches inv-2026-45.
  function normKey(k, loose) {
    var s = String(k == null ? '' : k).trim().toUpperCase();
    if (loose) s = s.split(/[^A-Z0-9]+/).map(function (t) { return t.replace(/(^|[A-Z])0+(?=\d)/g, '$1'); }).join('');
    return s;
  }
  // Matches two lists on a key. Repeated keys within a list are added together first.
  function reconcile(a, b, o) {
    o = o || {};
    var tol = o.tolerance || 0;
    function index(list) {
      var map = {}, keys = [];
      list.forEach(function (r) {
        var k = normKey(r.key, o.loose);
        if (!k) return;
        if (!map[k]) { map[k] = { key: String(r.key).trim(), amount: 0, count: 0 }; keys.push(k); }
        map[k].amount += r.amount || 0; map[k].count++;
      });
      return { map: map, keys: keys };
    }
    var A = index(a), B = index(b), matched = [], mismatched = [], onlyA = [], onlyB = [];
    A.keys.forEach(function (k) {
      var x = A.map[k], y = B.map[k];
      if (!y) { onlyA.push(x); return; }
      var diff = round(x.amount - y.amount, 2);
      (Math.abs(diff) <= tol + 1e-9 ? matched : mismatched).push({ key: x.key, a: round(x.amount, 2), b: round(y.amount, 2), difference: diff });
    });
    B.keys.forEach(function (k) { if (!A.map[k]) onlyB.push(B.map[k]); });
    function sum(list, f) { return round(list.reduce(function (s, r) { return s + r[f]; }, 0), 2); }
    return { matched: matched, mismatched: mismatched, onlyA: onlyA, onlyB: onlyB,
      totals: { a: sum(matched, 'a') + sum(mismatched, 'a') + sum(onlyA, 'amount'), b: sum(matched, 'b') + sum(mismatched, 'b') + sum(onlyB, 'amount'),
        mismatch: sum(mismatched, 'difference'), onlyA: sum(onlyA, 'amount'), onlyB: sum(onlyB, 'amount') } };
  }

  // ── SCHEDULE III RATIOS ──
  var RATIOS = [
    { id: 'current', name: 'Current ratio', formula: 'Current assets ÷ Current liabilities', unit: 'times', f: function (v) { return v.currentAssets / v.currentLiabilities; } },
    { id: 'debtEquity', name: 'Debt-equity ratio', formula: 'Total debt ÷ Shareholders\' equity', unit: 'times', f: function (v) { return v.debt / v.equity; } },
    { id: 'dscr', name: 'Debt service coverage ratio', formula: '(Profit after tax + Depreciation and other non-cash charges + Interest) ÷ (Interest and lease payments + Principal repayments)', unit: 'times',
      f: function (v) { return (v.pat + v.nonCash + v.interest) / (v.interest + v.leasePayments + v.principalRepaid); } },
    { id: 'roe', name: 'Return on equity', formula: '(Profit after tax − Preference dividend) ÷ Average shareholders\' equity', unit: '%', f: function (v) { return (v.pat - v.prefDividend) / ((v.equity + v.equityOpening) / 2); } },
    { id: 'inventory', name: 'Inventory turnover ratio', formula: 'Cost of goods sold ÷ Average inventory', unit: 'times', f: function (v) { return v.cogs / ((v.inventory + v.inventoryOpening) / 2); } },
    { id: 'receivables', name: 'Trade receivables turnover ratio', formula: 'Net credit sales ÷ Average trade receivables', unit: 'times', f: function (v) { return v.creditSales / ((v.receivables + v.receivablesOpening) / 2); } },
    { id: 'payables', name: 'Trade payables turnover ratio', formula: 'Net credit purchases ÷ Average trade payables', unit: 'times', f: function (v) { return v.creditPurchases / ((v.payables + v.payablesOpening) / 2); } },
    { id: 'capitalTurnover', name: 'Net capital turnover ratio', formula: 'Net sales ÷ Working capital (current assets − current liabilities)', unit: 'times', f: function (v) { return v.sales / (v.currentAssets - v.currentLiabilities); } },
    { id: 'netProfit', name: 'Net profit ratio', formula: 'Profit after tax ÷ Net sales', unit: '%', f: function (v) { return v.pat / v.sales; } },
    { id: 'roce', name: 'Return on capital employed', formula: 'Earnings before interest and tax ÷ Capital employed (tangible net worth + total debt + deferred tax liability)', unit: '%', f: function (v) { return v.ebit / v.capitalEmployed; } },
    { id: 'roi', name: 'Return on investment', formula: 'Income from investments ÷ Average investments', unit: '%', f: function (v) { return v.investmentIncome / v.avgInvestments; } }
  ];
  function ratios(cy, py) {
    var flagAt = DATA.scheduleIII.ratioVarianceFlag;
    return RATIOS.map(function (R) {
      var c = R.f(cy), p = R.f(py);
      var ok = isFinite(c) && isFinite(p) && p !== 0;
      var change = ok ? (c - p) / Math.abs(p) : NaN;
      return { id: R.id, name: R.name, formula: R.formula, unit: R.unit, cy: isFinite(c) ? c : NaN, py: isFinite(p) ? p : NaN, change: change, explain: ok && Math.abs(change) > flagAt };
    });
  }

  // ── MSME PAYMENTS ──
  function msme(o) {
    var M = DATA.msme;
    var credit = o.agreedDays == null || isNaN(o.agreedDays) ? M.noAgreementDays : Math.min(o.agreedDays, M.maxCreditDays);
    var due = addDays(o.acceptance, credit), days = Math.max(0, diffDays(due, o.asAt));
    var rate = (o.bankRate || 0) / 100 * M.interestMultiple;
    // Whole months are compounded; the days left over carry simple interest at the same rate.
    var months = 0, cursor = due;
    while (addMonths(due, months + 1) <= o.asAt) months++;
    cursor = addMonths(due, months);
    var extraDays = Math.max(0, diffDays(cursor, o.asAt));
    var grown = o.amount * Math.pow(1 + rate / 12, months) * (1 + rate * extraDays / 365);
    return { creditDays: credit, capped: o.agreedDays > M.maxCreditDays, due: due, daysOverdue: days, annualRate: rate, months: months, extraDays: extraDays,
      interest: days > 0 ? round(grown - o.amount, 2) : 0 };
  }

  // ── COMPANY LAW DATES ──
  function rocDates(o) {
    var C = DATA.companies, out = [];
    if (o.entity === 'llp') {
      out.push({ what: 'Form 11 (annual return)', date: addDays(o.fyEnd, C.llpForm11DaysFromYearEnd), basis: C.llpForm11DaysFromYearEnd + ' days from the close of the financial year' });
      out.push({ what: 'Form 8 (statement of account and solvency)', date: addDays(addMonths(o.fyEnd, 6), C.llpForm8DaysAfterSixMonths), basis: C.llpForm8DaysAfterSixMonths + ' days from the end of six months after the year end' });
      return out;
    }
    var months = o.firstAgm ? C.firstAgmMonthsFromYearEnd : C.agmMonthsFromYearEnd;
    out.push({ what: 'Last date for the annual general meeting', date: addMonths(o.fyEnd, months), basis: months + ' months from the close of the financial year' });
    if (o.agm) {
      // The AGM date is counted as day one, which gives the earlier, safer date.
      out.push({ what: 'ADT-1 (appointment of auditor)', date: addDays(o.agm, C.adt1DaysFromAgm - 1), basis: C.adt1DaysFromAgm + ' days of the AGM' });
      out.push({ what: 'AOC-4 (financial statements)', date: addDays(o.agm, C.aoc4DaysFromAgm - 1), basis: C.aoc4DaysFromAgm + ' days of the AGM' });
      out.push({ what: 'MGT-7 or MGT-7A (annual return)', date: addDays(o.agm, C.mgt7DaysFromAgm - 1), basis: C.mgt7DaysFromAgm + ' days of the AGM' });
    }
    return out;
  }

  // ── COMPLIANCE CALENDAR ──
  function calendar(fyStart) {
    var C = DATA.calendar, out = [];
    for (var i = 0; i < 12; i++) {
      var m = ((3 + i) % 12) + 1, y = m >= 4 ? fyStart : fyStart + 1;
      C.monthly.forEach(function (r) {
        var what = r.what;
        if (r.except && Object.prototype.hasOwnProperty.call(r.except, m)) { if (r.except[m] == null) return; what = r.except[m]; }
        out.push({ date: utc(y, m, r.d), law: r.law, what: what, prev: false });
      });
    }
    C.fixed.forEach(function (r) { out.push({ date: utc(r.m >= 4 ? fyStart : fyStart + 1, r.m, r.d), law: r.law, what: r.what, prev: !!r.prev }); });
    var prevEnd = utc(fyStart, 3, 31), agm = addMonths(prevEnd, DATA.companies.agmMonthsFromYearEnd);
    rocDates({ fyEnd: prevEnd, agm: agm }).forEach(function (r) {
      out.push({ date: r.date, law: 'Company law', what: r.what + (r.what.indexOf('Last date') === 0 ? '' : ', for an AGM held on ' + fmtDate(agm)), prev: true });
    });
    return out.sort(function (a, b) { return a.date - b.date || (a.law < b.law ? -1 : 1); });
  }

  return {
    data: DATA, num: num, round: round, roundTo: roundTo, inr: inr, pct: pct, amountInWords: amountInWords,
    utc: utc, parseDate: parseDate, iso: iso, fmtDate: fmtDate, addDays: addDays, diffDays: diffDays, addMonths: addMonths,
    fyStartYear: fyStartYear, fyLabel: fyLabel, monthsOrPart: monthsOrPart,
    parseTable: parseTable, parseNumbers: parseNumbers, toCsv: toCsv,
    gstCalc: gstCalc, gstinCheckChar: gstinCheckChar, checkGSTIN: checkGSTIN, checkPAN: checkPAN, checkCIN: checkCIN, identify: identify,
    gstInterest: gstInterest, gstLateFee: gstLateFee,
    tdsCompute: tdsCompute, tdsDepositDue: tdsDepositDue, tdsInterest: tdsInterest, tdsLateFee: tdsLateFee,
    slabTax: slabTax, incomeTax: incomeTax, advanceTax: advanceTax,
    depreciation: depreciation, loanSchedule: loanSchedule,
    materiality: materiality, binomCdf: binomCdf, attributeSampleSize: attributeSampleSize, musSampleSize: musSampleSize,
    rng: rng, selectRandom: selectRandom, selectSystematic: selectSystematic, selectMUS: selectMUS,
    benford: benford, dupesAndGaps: dupesAndGaps, ageing: ageing, reconcile: reconcile,
    RATIOS: RATIOS, ratios: ratios, msme: msme, rocDates: rocDates, calendar: calendar
  };
});
