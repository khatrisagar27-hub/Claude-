// Sagar Khatri & Associates — tools page: the directory and every tool's form and
// result. All arithmetic is in core.js and every statutory figure in
// statutory-data.js; this file only reads inputs and lays out what core returns.
(function () {
  'use strict';
  var S = window.SKA, app = document.getElementById('app');
  if (!S || !app) return;
  var D = S.data;

  // ── DOM ──
  function add(el, c) {
    if (c == null || c === false) return el;
    if (Array.isArray(c)) { c.forEach(function (x) { add(el, x); }); return el; }
    el.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
    return el;
  }
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v == null || v === false) return;
      if (k === 'class') el.className = v;
      else if (k.slice(0, 2) === 'on' && typeof v === 'function') el.addEventListener(k.slice(2), v);
      else if (v === true) el.setAttribute(k, '');
      else el.setAttribute(k, v);
    });
    for (var i = 2; i < arguments.length; i++) add(el, arguments[i]);
    return el;
  }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }
  function $(id) { return document.getElementById(id); }

  // ── FORMATS ──
  var R = function (v) { return S.inr(v); };
  var R0 = function (v) { return S.inr(v, 0); };
  function count(v) { return S.inr(v, 0).replace('₹', ''); }
  function grouped(v) { return S.inr(v, Math.abs(v % 1) > 1e-9 ? 2 : 0).replace('₹', ''); }
  function pc(v, dp) { return S.pct(v, dp == null ? 2 : dp); }
  var F = S.fmtDate;
  function plural(n, one, many) { return n + ' ' + (n === 1 ? one : (many || one + 's')); }

  var now = new Date();
  var TODAY = S.utc(now.getFullYear(), now.getMonth() + 1, now.getDate());
  var THIS_FY = S.fyStartYear(TODAY);
  function fyOptions() { return [THIS_FY - 1, THIS_FY, THIS_FY + 1].map(function (y) { return [String(y), S.fyLabel(y)]; }); }

  // ── INPUTS ──
  function fld(label, control, hint) {
    return h('div', { class: 'fld' }, h('label', { for: control.id }, label), control, hint ? h('p', { class: 'hint' }, hint) : null);
  }
  function money(id, v) {
    var i = h('input', { id: id, type: 'text', inputmode: 'decimal', autocomplete: 'off', spellcheck: 'false', class: 'in-num', value: v == null || v === '' ? '' : grouped(v) });
    i.addEventListener('blur', function () { var x = S.num(i.value); if (!isNaN(x)) i.value = grouped(x); });
    return i;
  }
  function dec(id, v) { return h('input', { id: id, type: 'text', inputmode: 'decimal', autocomplete: 'off', spellcheck: 'false', class: 'in-num', value: v == null ? '' : String(v) }); }
  function date(id, d) { return h('input', { id: id, type: 'date', value: d ? S.iso(d) : '' }); }
  function sel(id, opts, v) {
    return h('select', { id: id }, opts.map(function (o) { return h('option', { value: String(o[0]), selected: String(o[0]) === String(v) }, o[1]); }));
  }
  function check(id, label, on) {
    return h('label', { class: 'check', for: id }, h('input', { type: 'checkbox', id: id, checked: !!on }), h('span', null, label));
  }
  function seg(name, opts, v, legend) {
    return h('fieldset', { class: 'seg' }, h('legend', null, legend),
      h('div', { class: 'seg__row' }, opts.map(function (o) {
        return h('label', { class: 'seg__opt' }, h('input', { type: 'radio', name: name, id: name + '-' + o[0], value: o[0], checked: o[0] === v }), h('span', null, o[1]));
      })));
  }
  function pasteField(id, label, text, rows, hint) {
    var ta = h('textarea', { id: id, rows: rows || 9, spellcheck: 'false', autocomplete: 'off', wrap: 'off' }, text);
    var clearBtn = h('button', { type: 'button', class: 'btn-sm' }, 'Clear');
    clearBtn.addEventListener('click', function () { ta.value = ''; ta.focus(); ta.dispatchEvent(new Event('input', { bubbles: true })); });
    return h('div', { class: 'fld' }, h('div', { class: 'fld__bar' }, h('label', { for: id }, label), clearBtn), ta, hint ? h('p', { class: 'hint' }, hint) : null);
  }
  function val(id) { var e = $(id); return e ? e.value : ''; }
  function n(id) { return S.num(val(id)); }
  function dt(id) { return S.parseDate(val(id)); }
  function isOn(id) { var e = $(id); return !!(e && e.checked); }
  function radio(name) { var e = document.querySelector('input[name="' + name + '"]:checked'); return e ? e.value : ''; }
  function selText(id) { var e = $(id); return e && e.selectedIndex >= 0 ? e.options[e.selectedIndex].text : ''; }
  function show(id, yes) { var e = $(id); if (e) e.hidden = !yes; }

  function UserError(message) { this.message = message; }
  function need(cond, message) { if (!cond) throw new UserError(message); }

  // ── OUTPUT ──
  function tiles(list) {
    return h('div', { class: 'tiles' }, list.filter(Boolean).map(function (t) {
      return h('div', { class: 'tile' + (t.lead ? ' tile--lead' : '') },
        h('p', { class: 'tile__label' }, t.label), h('p', { class: 'tile__value num' }, t.value), t.sub ? h('p', { class: 'tile__sub' }, t.sub) : null);
    }));
  }
  function note(text, kind) { return h('p', { class: 'msg' + (kind ? ' msg--' + kind : '') }, text); }
  function subh(text) { return h('h3', { class: 'subh' }, text); }
  function pill(text, kind) {
    var icon = { good: '✓', bad: '✕', warn: '!', muted: '–' }[kind] || '';
    return h('span', { class: 'pill pill--' + (kind || 'muted') }, icon ? h('span', { 'aria-hidden': 'true' }, icon) : null, text);
  }
  // cols: [{ label, num }]; rows: arrays of cells; opts: { caption, foot, rowClass(i) }
  function table(cols, rows, opts) {
    opts = opts || {};
    function cell(tag, v, i) { return h(tag, { class: cols[i] && cols[i].num ? 'n num' : null, scope: tag === 'th' ? 'row' : null }, v); }
    var t = h('table', { class: 't' },
      opts.caption ? h('caption', null, opts.caption) : null,
      h('thead', null, h('tr', null, cols.map(function (c) { return h('th', { scope: 'col', class: c.num ? 'n' : null }, c.label); }))),
      h('tbody', null, rows.map(function (r, ri) {
        return h('tr', { class: opts.rowClass ? opts.rowClass(ri) : null }, r.map(function (v, i) { return cell(i === 0 && opts.rowHeads ? 'th' : 'td', v, i); }));
      })),
      opts.foot ? h('tfoot', null, h('tr', null, opts.foot.map(function (v, i) { return cell(i === 0 ? 'th' : 'td', v, i); }))) : null);
    return h('div', { class: 'tbl-wrap', tabindex: '0', role: 'region', 'aria-label': opts.caption || 'Result table' }, t);
  }
  function download(filename, text, type) {
    var url = URL.createObjectURL(new Blob([text], { type: type }));
    var a = h('a', { href: url, download: filename });
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }
  function copyText(text, status, okMsg) {
    function fallback() {
      var ta = h('textarea', { class: 'offscreen', readonly: true }, text);
      document.body.appendChild(ta); ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      status.textContent = ok ? okMsg : 'The browser blocked copying. Select the text and copy it instead.';
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(function () { status.textContent = okMsg; }, fallback);
    else fallback();
    setTimeout(function () { status.textContent = ''; }, 3000);
  }
  // getRows returns an array of arrays, header row first; amounts stay unformatted for Excel.
  function exportBar(name, getRows, extra) {
    var status = h('span', { class: 'export__status', role: 'status' });
    return h('div', { class: 'export' },
      h('button', { type: 'button', class: 'btn-sm', onclick: function () {
        var tsv = getRows().map(function (r) { return r.map(function (c) { return String(c == null ? '' : c).replace(/[\t\n]/g, ' '); }).join('\t'); }).join('\n');
        copyText(tsv, status, 'Copied. Paste it into Excel.');
      } }, 'Copy table'),
      h('button', { type: 'button', class: 'btn-sm', onclick: function () { download(name + '.csv', '﻿' + S.toCsv(getRows()), 'text/csv;charset=utf-8'); } }, 'Download CSV'),
      extra || null, status);
  }
  function wp(text) {
    var status = h('span', { class: 'export__status', role: 'status' });
    return h('div', { class: 'wp' }, h('p', { class: 'subh' }, 'For the working paper'), h('p', null, text),
      h('div', { class: 'export' }, h('button', { type: 'button', class: 'btn-sm', onclick: function () { copyText(text, status, 'Copied.'); } }, 'Copy text'), status));
  }
  function figuresNote() {
    if (D.verifiedOn) {
      return h('p', { class: 'figs figs--ok' }, h('span', { class: 'figs__icon', 'aria-hidden': 'true' }, '✓'),
        'Rates and dates checked by the firm on ' + F(S.parseDate(D.verifiedOn)) + '. ', h('a', { href: '#figures' }, 'See the figures and their sources'), '.');
    }
    return h('p', { class: 'figs figs--pending' }, h('span', { class: 'figs__icon', 'aria-hidden': 'true' }, '!'),
      'The rates and dates in this tool have not yet been checked by the firm against the Act and the notifications. Verify them before relying on the result. ',
      h('a', { href: '#figures' }, 'See the figures and their sources'), '.');
  }

  // Rows pasted from Excel: the first row is a header when its amount column is not a number.
  function pastedRows(text, amountCol) {
    var rows = S.parseTable(text);
    if (rows.length && isNaN(S.num(rows[0][amountCol == null ? rows[0].length - 1 : amountCol]))) rows = rows.slice(1);
    return rows;
  }

  // Deterministic example data, so the first view of a tool shows a result.
  function exampleAmounts(howMany, seed, lo, hi) {
    var r = S.rng(seed), out = [];
    for (var i = 0; i < howMany; i++) out.push(Math.pow(10, lo + (hi - lo) * r()).toFixed(2));
    return out;
  }

  // ── REGISTRY ──
  var GROUPS = [['audit', 'Audit'], ['accounting', 'Accounting'], ['gst', 'GST'], ['tds', 'TDS'], ['income-tax', 'Income-tax'],
    ['company', 'Company law and MSME'], ['compliance', 'Compliance'], ['workbooks', 'Workbooks and generators']];
  var TOOLS = [];
  function tool(def) { TOOLS.push(def); }

  // ══ AUDIT ══
  tool({
    id: 'materiality', group: 'audit', title: 'Materiality',
    summary: 'Overall materiality, performance materiality and the clearly trivial threshold, for SA 320 and SA 450.',
    keywords: 'SA 320 SA 450 benchmark planning',
    notes: [
      'SA 320 gives 5% of profit before tax (for a profit-oriented manufacturer) and 1% of total revenue or total expenses (for a not-for-profit entity) as examples. The percentage is a matter of judgment.',
      'Performance materiality is usually set lower where misstatements were found before or the risk of misstatement is higher.',
      'Misstatements below the clearly trivial threshold need not be accumulated under SA 450.'
    ],
    build: function (f, o) {
      var B = [['pbt', 'Profit before tax', 5], ['revenue', 'Total revenue', 1], ['expenses', 'Total expenses', 1], ['assets', 'Total assets', 1], ['equity', 'Equity', 2]];
      add(f, [
        fld('Benchmark', sel('mat-bench', B.map(function (b) { return [b[0], b[1]]; }), 'pbt')),
        fld('Benchmark amount (₹)', money('mat-amt', 42500000)),
        h('div', { class: 'row3' },
          fld('Overall, % of benchmark', dec('mat-pct', 5)),
          fld('Performance, % of overall', dec('mat-pm', 75)),
          fld('Clearly trivial, % of overall', dec('mat-ct', 5)))
      ]);
      $('mat-bench').addEventListener('change', function () {
        var b = B.filter(function (x) { return x[0] === val('mat-bench'); })[0];
        if (b) $('mat-pct').value = String(b[2]);
      });
      return function () {
        var amt = n('mat-amt'), p = n('mat-pct'), pm = n('mat-pm'), ct = n('mat-ct');
        need(amt > 0, 'Enter the benchmark amount.');
        need(p > 0 && p <= 100, 'Enter the overall materiality percentage, above 0 and up to 100.');
        need(pm > 0 && pm <= 100, 'Enter performance materiality as a percentage of overall materiality, up to 100.');
        need(ct >= 0 && ct <= 100, 'Enter the clearly trivial percentage, from 0 to 100.');
        var r = S.materiality({ benchmark: amt, pct: p, performancePct: pm, trivialPct: ct });
        var bl = selText('mat-bench').toLowerCase();
        add(o, [
          tiles([
            { label: 'Overall materiality', value: R0(r.overall), lead: true, sub: p + '% of ' + bl },
            { label: 'Performance materiality', value: R0(r.performance), sub: pm + '% of overall' },
            { label: 'Clearly trivial', value: R0(r.trivial), sub: ct + '% of overall' }]),
          wp('Overall materiality for the financial statements as a whole is set at ' + R0(r.overall) + ', being ' + p + '% of ' + bl + ' of ' + R0(amt) +
            '. Performance materiality is set at ' + R0(r.performance) + ' (' + pm + '% of overall materiality). Misstatements below ' + R0(r.trivial) +
            ' (' + ct + '% of overall materiality) are treated as clearly trivial and are not accumulated.')
        ]);
      };
    }
  });

  var MUS_CONF = Object.keys(D.sampling.mus).sort(function (a, b) { return a - b; }).map(function (k) { return [k, k + '%']; });
  tool({
    id: 'sample-size', group: 'audit', title: 'Sample size',
    summary: 'Sample sizes for tests of controls (attribute sampling) and tests of details (monetary unit sampling), for SA 530.',
    keywords: 'SA 530 attribute monetary unit MUS PPS statistical',
    notes: [
      'Attribute sizes come from the binomial distribution: the smallest sample for which finding no more than the allowed deviations would be unlikely, at the confidence chosen, if the true deviation rate were the tolerable rate. They agree with the AICPA statistical sampling tables.',
      'Monetary unit sizes use the confidence and expansion factors listed under sampling in the figures file. Change them there to match the firm’s methodology.',
      'SA 530 leaves the method to the auditor’s judgment. Record the inputs and the reasons for them in the working paper.'
    ],
    build: function (f, o) {
      add(f, [
        seg('ss-method', [['attr', 'Tests of controls'], ['mus', 'Tests of details']], 'attr', 'Type of test'),
        h('div', { id: 'ss-attr', class: 'fgroup' },
          fld('Confidence level', sel('ss-a-conf', [['0.90', '90%'], ['0.95', '95%'], ['0.99', '99%']], '0.95')),
          h('div', { class: 'row2' }, fld('Tolerable deviation rate (%)', dec('ss-a-tol', 5)), fld('Expected deviation rate (%)', dec('ss-a-exp', 1))),
          fld('Items in the population (optional)', money('ss-a-pop', 2400), 'Reduces the sample for a small population. Leave blank for a large one.')),
        h('div', { id: 'ss-mus', class: 'fgroup', hidden: true },
          fld('Book value of the population (₹)', money('ss-m-pop', 52500000)),
          h('div', { class: 'row2' }, fld('Tolerable misstatement (₹)', money('ss-m-tol', 2000000)), fld('Expected misstatement (₹)', money('ss-m-exp', 250000))),
          fld('Confidence level', sel('ss-m-conf', MUS_CONF, '95')))
      ]);
      return function () {
        var m = radio('ss-method');
        show('ss-attr', m === 'attr'); show('ss-mus', m === 'mus');
        if (m === 'attr') {
          var tol = n('ss-a-tol'), exp = isNaN(n('ss-a-exp')) ? 0 : n('ss-a-exp'), pop = n('ss-a-pop'), conf = +val('ss-a-conf');
          need(tol > 0 && tol < 100, 'Enter a tolerable deviation rate above 0% and below 100%.');
          need(exp >= 0, 'The expected deviation rate cannot be negative.');
          var r = S.attributeSampleSize({ confidence: conf, tolerable: tol / 100, expected: exp / 100, population: pop > 0 ? pop : null });
          need(!r.error, r.error);
          var size = pop > 0 ? r.adjusted : r.size;
          add(o, [
            tiles([
              { label: 'Sample size', value: count(size), lead: true, sub: pop > 0 && r.adjusted !== r.size ? 'Adjusted for ' + count(pop) + ' items (' + r.size + ' before adjustment)' : 'Items to test' },
              { label: 'Deviations allowed', value: String(r.allowedDeviations), sub: 'Finding more means the control cannot be relied on at this confidence' }]),
            wp('Test of controls at ' + pc(conf, 0) + ' confidence, with a tolerable deviation rate of ' + tol + '% and an expected deviation rate of ' + exp +
              '%: sample size ' + size + ' items' + (pop > 0 ? ' from a population of ' + count(pop) : '') + ', with no more than ' + plural(r.allowedDeviations, 'deviation') + ' allowed.')
          ]);
        } else {
          var bv = n('ss-m-pop'), tm = n('ss-m-tol'), em = isNaN(n('ss-m-exp')) ? 0 : n('ss-m-exp');
          need(bv > 0, 'Enter the book value of the population.');
          need(tm > 0 && tm < bv, 'Enter a tolerable misstatement above zero and below the book value.');
          var c = val('ss-m-conf'), q = S.musSampleSize({ population: bv, tolerable: tm, expected: em, confidence: +c / 100 });
          need(!q.error, q.error);
          add(o, [
            tiles([
              { label: 'Sample size', value: count(q.size), lead: true, sub: 'Monetary units to select' },
              { label: 'Sampling interval', value: R0(q.interval), sub: 'Every item at or above this is selected with certainty' }]),
            table([{ label: 'Factor' }, { label: 'Value', num: true }], [['Confidence factor', q.confidenceFactor.toFixed(2)], ['Expansion factor', q.expansionFactor.toFixed(1)]]),
            wp('Monetary unit sampling at ' + c + '% confidence. Population ' + R0(bv) + ', tolerable misstatement ' + R0(tm) + ', expected misstatement ' + R0(em) +
              '. Sample size ' + q.size + ' (confidence factor ' + q.confidenceFactor.toFixed(2) + ', expansion factor ' + q.expansionFactor.toFixed(1) + '); sampling interval ' + R0(q.interval) + '.')
          ]);
        }
      };
    }
  });

  var SEED_TODAY = TODAY.getUTCFullYear() * 10000 + (TODAY.getUTCMonth() + 1) * 100 + TODAY.getUTCDate();
  tool({
    id: 'sample-select', group: 'audit', title: 'Sample selection',
    summary: 'Random, systematic or monetary unit selection from a seed you record, so anyone can reperform it.',
    keywords: 'SA 530 random systematic MUS PPS seed',
    notes: [
      'The same seed, population and sample size always give the same items. Record all three in the working paper.',
      'Random selection draws without replacement. Systematic selection takes every k-th item from a random start.',
      'Monetary unit selection picks every k-th rupee from a random start, so larger items are more likely to be chosen. Items at least as large as the interval are always selected and may be hit more than once.'
    ],
    build: function (f, o) {
      add(f, [
        seg('sel-m', [['random', 'Random'], ['systematic', 'Systematic'], ['mus', 'Monetary unit']], 'random', 'Method'),
        h('div', { id: 'sel-count-box' }, fld('Items in the population', money('sel-n', 1840), 'Items are numbered 1 to this number, in the order of the listing.')),
        h('div', { id: 'sel-amt-box', hidden: true }, pasteField('sel-amts', 'Amounts, one per line, in listing order', exampleAmounts(120, 3, 3, 5.7).join('\n'), 8, 'Paste a column from Excel. Line 1 is item 1.')),
        h('div', { class: 'row2' }, fld('Sample size', money('sel-k', 25)), fld('Seed', dec('sel-seed', SEED_TODAY), 'Any whole number.'))
      ]);
      return function () {
        var m = radio('sel-m'), k = Math.floor(n('sel-k')), seed = Math.floor(n('sel-seed'));
        show('sel-count-box', m !== 'mus'); show('sel-amt-box', m === 'mus');
        need(k > 0, 'Enter the sample size.');
        need(isFinite(seed), 'Enter a whole number as the seed.');
        if (m === 'mus') {
          var amts = S.parseNumbers(val('sel-amts'));
          need(amts.length > 0, 'Paste the population amounts, one per line.');
          var r = S.selectMUS(amts, k, seed);
          need(!r.error, r.error);
          var rows = r.picks.map(function (p, i) { return [i + 1, p.item, p.amount, p.hits, p.certain ? 'Yes' : '']; });
          add(o, [
            tiles([
              { label: 'Items selected', value: count(r.picks.length), lead: true, sub: 'From ' + count(amts.length) + ' items' },
              { label: 'Sampling interval', value: R(r.interval), sub: 'Population ' + R(r.total) },
              { label: 'Selected with certainty', value: count(r.picks.filter(function (p) { return p.certain; }).length), sub: 'At or above the interval' }]),
            table([{ label: 'Sr.' }, { label: 'Item no.', num: true }, { label: 'Amount', num: true }, { label: 'Hits', num: true }, { label: 'Certain' }],
              r.picks.map(function (p, i) { return [String(i + 1), String(p.item), R(p.amount), String(p.hits), p.certain ? pill('Certain', 'muted') : '']; })),
            exportBar('mus-selection', function () { return [['Sr.', 'Item no.', 'Amount', 'Hits', 'Certain']].concat(rows); }),
            wp('Monetary unit selection of ' + k + ' units from ' + count(amts.length) + ' items totalling ' + R(r.total) + ', interval ' + R(r.interval) + ', seed ' + seed + '. Items selected: ' + r.picks.map(function (p) { return p.item; }).join(', ') + '.')
          ]);
          return;
        }
        var N = Math.floor(n('sel-n'));
        need(N > 0, 'Enter the number of items in the population.');
        need(k <= N, 'The sample cannot be larger than the population.');
        var items, interval = null;
        if (m === 'random') items = S.selectRandom(N, k, seed);
        else { var s = S.selectSystematic(N, k, seed); items = s.items; interval = s.interval; }
        add(o, [
          tiles([
            { label: 'Items selected', value: count(items.length), lead: true, sub: 'From items 1 to ' + count(N) },
            interval != null ? { label: 'Interval', value: interval.toFixed(2), sub: 'Every ' + interval.toFixed(2) + ' items from a random start' } : { label: 'Seed', value: String(seed), sub: 'Record it in the working paper' }]),
          h('ol', { class: 'picks' }, items.map(function (x) { return h('li', { class: 'num' }, count(x)); })),
          exportBar(m + '-selection', function () { return [['Sr.', 'Item no.']].concat(items.map(function (x, i) { return [i + 1, x]; })); }),
          wp((m === 'random' ? 'Random' : 'Systematic') + ' selection of ' + k + ' items from a population of ' + count(N) + ', seed ' + seed + '. Items selected: ' + items.join(', ') + '.')
        ]);
      };
    }
  });

  tool({
    id: 'benford', group: 'audit', title: 'Benford first-digit test', layout: 'stack',
    summary: 'Compares the leading digits of a set of amounts with Benford’s law and flags the digits that stand out.',
    keywords: 'benford law first digit analytics fraud journal',
    notes: [
      'Suited to amounts that span several orders of magnitude and arise naturally: purchase invoices, expense claims, journal amounts. Not suited to assigned numbers, prices with a set range, or amounts with a ceiling.',
      'Conformity is judged by the mean absolute deviation (MAD) against Nigrini’s first-digit ranges, with the chi-square test (8 degrees of freedom) shown alongside. With large populations chi-square flags trivial differences, so read MAD first.',
      'A digit marked significant has a z-statistic above 1.96. It points to where to look; it is not evidence of fraud on its own.'
    ],
    build: function (f, o) {
      add(f, [
        h('div', { class: 'row-wide' },
          pasteField('bf-list', 'Amounts, one per line', exampleAmounts(1000, 2027, 2, 6).join('\n'), 10, 'Paste a column from Excel. Commas, ₹ signs and minus signs are handled.'),
          h('div', { class: 'fgroup' }, check('bf-min', 'Leave out amounts below ₹10', true)))
      ]);
      return function () {
        var nums = S.parseNumbers(val('bf-list'));
        need(nums.length >= 50, 'Paste at least 50 amounts. The test is reliable from about 1,000.');
        var r = S.benford(nums, isOn('bf-min') ? 10 : 0);
        need(r.n >= 50, 'Fewer than 50 amounts are left after leaving out the small ones.');
        var crit = D.sampling.chiSquareCritical5pc;
        add(o, [
          tiles([
            { label: 'Amounts tested', value: count(r.n), sub: nums.length > r.n ? count(nums.length - r.n) + ' left out' : 'All pasted amounts' },
            { label: 'Mean absolute deviation', value: r.mad.toFixed(4), lead: true, sub: r.verdict },
            { label: 'Chi-square', value: r.chiSquare.toFixed(2), sub: (r.exceeds5pc ? 'Above' : 'Within') + ' the 5% critical value of ' + crit.toFixed(3) }]),
          r.n < 1000 ? note('With fewer than 1,000 amounts the test has little power. Read the result as indicative.', 'warn') : null,
          benfordChart(r),
          table([{ label: 'Digit' }, { label: 'Count', num: true }, { label: 'Observed', num: true }, { label: 'Expected', num: true }, { label: 'Difference', num: true }, { label: 'Z', num: true }, { label: '' }],
            r.rows.map(function (x) { return [String(x.digit), count(x.count), pc(x.observed, 1), pc(x.expected, 1), (x.difference >= 0 ? '+' : '') + (x.difference * 100).toFixed(1) + ' pts', x.z.toFixed(2), x.significant ? pill('Significant', 'warn') : '']; }),
            { caption: 'First digits', rowHeads: true }),
          exportBar('benford', function () { return [['Digit', 'Count', 'Observed', 'Expected', 'Z', 'Significant']].concat(r.rows.map(function (x) { return [x.digit, x.count, x.observed, x.expected, x.z, x.significant ? 'Yes' : '']; })); })
        ]);
      };
    }
  });

  // Observed share as bars, Benford's expected share as a line. Both series are labelled
  // in the legend; the table below the chart carries the exact values.
  function benfordChart(r) {
    var W = 640, H = 260, L = 44, Rm = 12, T = 14, B = 34, pw = W - L - Rm, ph = H - T - B;
    var top = Math.max(0.35, Math.ceil(Math.max.apply(null, r.rows.map(function (x) { return x.observed; })) * 20) / 20);
    var y = function (v) { return T + ph - v / top * ph; }, step = pw / 9, bw = Math.min(40, step * 0.56);
    var NS = 'http://www.w3.org/2000/svg';
    function s(tag, a) { var e = document.createElementNS(NS, tag); Object.keys(a || {}).forEach(function (k) { e.setAttribute(k, a[k]); }); for (var i = 2; i < arguments.length; i++) if (arguments[i]) e.appendChild(arguments[i]); return e; }
    var svg = s('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Observed first-digit shares against Benford’s expected shares' });
    var grid = s('g', { class: 'grid' }), axis = s('g', { class: 'axis' });
    for (var g = 0; g <= top + 1e-9; g += 0.05) {
      grid.appendChild(s('line', { x1: L, x2: W - Rm, y1: y(g), y2: y(g) }));
      var lab = s('text', { x: L - 8, y: y(g) + 4, 'text-anchor': 'end' }); lab.textContent = Math.round(g * 100) + '%'; axis.appendChild(lab);
    }
    svg.appendChild(grid);
    var bars = s('g'), pts = [];
    r.rows.forEach(function (x, i) {
      var cx = L + step * i + step / 2, by = y(x.observed), bh = T + ph - by, rad = Math.min(4, bh);
      var d = 'M' + (cx - bw / 2) + ',' + (T + ph) + 'V' + (by + rad) + 'Q' + (cx - bw / 2) + ',' + by + ' ' + (cx - bw / 2 + rad) + ',' + by +
        'H' + (cx + bw / 2 - rad) + 'Q' + (cx + bw / 2) + ',' + by + ' ' + (cx + bw / 2) + ',' + (by + rad) + 'V' + (T + ph) + 'Z';
      bars.appendChild(s('path', { class: 'bar', d: d, 'data-i': i }));
      pts.push([cx, y(x.expected)]);
      var t = s('text', { x: cx, y: H - B + 18, 'text-anchor': 'middle' }); t.textContent = String(x.digit); axis.appendChild(t);
    });
    svg.appendChild(bars);
    svg.appendChild(s('line', { class: 'baseline', x1: L, x2: W - Rm, y1: T + ph, y2: T + ph }));
    svg.appendChild(s('polyline', { class: 'exp-line', points: pts.map(function (p) { return p[0] + ',' + p[1]; }).join(' ') }));
    pts.forEach(function (p) { svg.appendChild(s('circle', { class: 'exp-dot', cx: p[0], cy: p[1], r: 4.5 })); });
    svg.appendChild(axis);
    var tip = h('div', { class: 'tip', hidden: true });
    var hits = s('g');
    r.rows.forEach(function (x, i) {
      var rect = s('rect', { class: 'hit', x: L + step * i, y: T, width: step, height: ph + 20 });
      function on() {
        tip.hidden = false; clear(tip);
        add(tip, [h('strong', null, 'Digit ' + x.digit), h('span', null, 'Observed ' + pc(x.observed, 1) + ' (' + count(x.count) + ')'), h('span', null, 'Expected ' + pc(x.expected, 1))]);
        var box = wrap.getBoundingClientRect(), px = (L + step * i + step / 2) / W * box.width;
        tip.style.left = Math.min(Math.max(px, 70), box.width - 70) + 'px';
        tip.style.top = (y(Math.max(x.observed, x.expected)) / H * box.height) + 'px';
        Array.prototype.forEach.call(bars.childNodes, function (b, j) { b.classList.toggle('dim', j !== i); });
      }
      rect.addEventListener('pointerenter', on);
      hits.appendChild(rect);
    });
    hits.addEventListener('pointerleave', function () { tip.hidden = true; Array.prototype.forEach.call(bars.childNodes, function (b) { b.classList.remove('dim'); }); });
    svg.appendChild(hits);
    var wrap = h('div', { class: 'chart__plot' }, svg, tip);
    return h('figure', { class: 'chart' },
      h('div', { class: 'legend' },
        h('span', { class: 'legend__item' }, h('span', { class: 'sw sw--bar' }), 'Observed share'),
        h('span', { class: 'legend__item' }, h('span', { class: 'sw sw--line' }), 'Expected under Benford’s law')),
      wrap);
  }

  function exampleSeries() {
    var out = [];
    for (var i = 1; i <= 48; i++) {
      if ([23, 24, 25, 31].indexOf(i) >= 0) continue;
      out.push('INV/2026/' + String(i).padStart(3, '0'));
      if (i === 17 || i === 9) out.push('INV/2026/' + String(i).padStart(3, '0'));
    }
    [1, 2, 3, 5, 6].forEach(function (i) { out.push('CN/2026/' + String(i).padStart(2, '0')); });
    return out.join('\n');
  }
  tool({
    id: 'duplicates', group: 'audit', title: 'Duplicates and gaps',
    summary: 'Finds repeated document numbers and the numbers missing from each series in a register.',
    keywords: 'invoice voucher sequence completeness missing repeated cheque',
    notes: [
      'Numbers are compared ignoring case. Each series is the text before the trailing number, so INV/2026/001 and CN/2026/01 are checked separately.',
      'A gap needs an explanation: a cancelled document, a number used in another register, or a document left out of the books.'
    ],
    build: function (f, o) {
      add(f, pasteField('dg-list', 'Document numbers, one per line', exampleSeries(), 12, 'Paste the number column of a sales register, voucher list or cheque register.'));
      return function () {
        var items = val('dg-list').split(/\r?\n/);
        var r = S.dupesAndGaps(items);
        need(r.total > 0, 'Paste the document numbers, one per line.');
        var missing = r.series.reduce(function (s, x) { return s + x.missingCount; }, 0);
        add(o, [
          tiles([
            { label: 'Numbers read', value: count(r.total), sub: count(r.unique) + ' different' },
            { label: 'Repeated', value: count(r.duplicates.length), lead: r.duplicates.length > 0, sub: r.duplicates.length ? 'Numbers that appear more than once' : 'No number repeats' },
            { label: 'Missing', value: count(missing), lead: missing > 0, sub: 'Across ' + plural(r.series.length, 'series', 'series') }]),
          r.duplicates.length ? table([{ label: 'Number' }, { label: 'Times', num: true }], r.duplicates.map(function (x) { return [x.value, String(x.count)]; }), { caption: 'Repeated numbers' }) : null,
          r.series.length ? table([{ label: 'Series' }, { label: 'From' }, { label: 'To' }, { label: 'Present', num: true }, { label: 'Missing', num: true }, { label: 'Missing numbers' }],
            r.series.map(function (x) {
              var list = x.missing.slice(0, 40).join(', ') + (x.missing.length > 40 ? ' and ' + (x.missing.length - 40) + ' more ranges' : '');
              return [x.prefix, x.from, x.to, count(x.present), count(x.missingCount), list || '—'];
            }), { caption: 'Series' }) : note('No numbered series found. Each number needs to end in digits.'),
          exportBar('duplicates-and-gaps', function () {
            var out = [['Finding', 'Number or range', 'Times']];
            r.duplicates.forEach(function (x) { out.push(['Repeated', x.value, x.count]); });
            r.series.forEach(function (x) { x.missing.forEach(function (m) { out.push(['Missing', m, '']); }); });
            return out;
          })
        ]);
      };
    }
  });

  var REC_A = ['GSTIN\tInvoice\tTax', '24ABCPS1234K1ZS\tINV-101\t18000', '24ABCPS1234K1ZS\tINV-102\t9000', '27PQRSM5678K1Z2\tA/2026/45\t45000',
    '29LMNOP4321Q1Z8\t771\t12600', '24ABCPS1234K1ZS\tINV-105\t3600', '24ABCPS1234K1ZS\tINV-106\t7200'].join('\n');
  var REC_B = ['GSTIN\tInvoice\tTax', '24ABCPS1234K1ZS\tINV101\t18000', '24ABCPS1234K1ZS\tINV102\t8100', '27PQRSM5678K1Z2\tA/2026/045\t45000',
    '33WXYZA9876B1Z3\tSB-9\t5400', '24ABCPS1234K1ZS\tINV-106\t7200'].join('\n');
  tool({
    id: 'reconcile', group: 'audit', title: 'Two-list reconciliation', layout: 'stack',
    summary: 'Matches two lists on a key and amount: books against GSTR-2B, a ledger against a party statement, or any two registers.',
    keywords: 'GSTR-2B ITC purchase register matching ledger confirmation vendor',
    notes: [
      'All columns except the last form the key; the last column is the amount. A header row is detected and skipped.',
      'Repeated keys within a list are added together before matching.',
      'Loose matching ignores case, spaces, punctuation and leading zeros in each number, so INV-0101 matches inv/101.'
    ],
    build: function (f, o) {
      add(f, [
        h('div', { class: 'row2 row2--top' },
          h('div', { class: 'fgroup' }, fld('Name of the first list', h('input', { id: 'rc-an', type: 'text', value: 'Books' })), pasteField('rc-a', 'First list', REC_A, 9)),
          h('div', { class: 'fgroup' }, fld('Name of the second list', h('input', { id: 'rc-bn', type: 'text', value: 'GSTR-2B' })), pasteField('rc-b', 'Second list', REC_B, 9))),
        h('div', { class: 'row2' }, h('div', { class: 'fgroup' }, check('rc-loose', 'Loose matching of keys', true)), fld('Difference to ignore (₹)', money('rc-tol', 1)))
      ]);
      return function () {
        var an = val('rc-an').trim() || 'First list', bn = val('rc-bn').trim() || 'Second list', skipped = 0;
        function read(text) {
          var out = [];
          pastedRows(text).forEach(function (r) {
            var amt = S.num(r[r.length - 1]);
            if (r.length < 2 || isNaN(amt)) { skipped++; return; }
            out.push({ key: r.slice(0, -1).join(' | '), amount: amt });
          });
          return out;
        }
        var A = read(val('rc-a')), B = read(val('rc-b'));
        need(A.length && B.length, 'Paste both lists, each with a key column and an amount column.');
        var tol = n('rc-tol');
        var r = S.reconcile(A, B, { loose: isOn('rc-loose'), tolerance: isNaN(tol) ? 0 : tol });
        var T = r.totals;
        function sumOf(list, key) { return list.reduce(function (s, x) { return s + x[key]; }, 0); }
        add(o, [
          tiles([
            { label: 'Matched', value: count(r.matched.length), sub: R(sumOf(r.matched, 'a')) },
            { label: 'Amounts differ', value: count(r.mismatched.length), lead: r.mismatched.length > 0, sub: 'Net ' + R(T.mismatch) + ' (' + an + ' less ' + bn + ')' },
            { label: 'Only in ' + an, value: count(r.onlyA.length), lead: r.onlyA.length > 0, sub: R(T.onlyA) },
            { label: 'Only in ' + bn, value: count(r.onlyB.length), lead: r.onlyB.length > 0, sub: R(T.onlyB) }]),
          table([{ label: 'Reconciliation' }, { label: 'Amount', num: true }], [
            ['Total of ' + an, R(T.a)], ['Less: only in ' + an, R(-T.onlyA)], ['Less: differences on matched keys', R(-T.mismatch)], ['Add: only in ' + bn, R(T.onlyB)]],
            { rowHeads: true, foot: ['Total of ' + bn, R(T.b)], caption: 'Summary' }),
          skipped ? note(plural(skipped, 'line') + ' skipped because the last column was not an amount.', 'warn') : null,
          r.mismatched.length ? table([{ label: 'Key' }, { label: an, num: true }, { label: bn, num: true }, { label: 'Difference', num: true }],
            r.mismatched.map(function (x) { return [x.key, R(x.a), R(x.b), R(x.difference)]; }), { caption: 'Amounts differ' }) : null,
          r.onlyA.length ? table([{ label: 'Key' }, { label: 'Amount', num: true }], r.onlyA.map(function (x) { return [x.key, R(x.amount)]; }), { caption: 'Only in ' + an }) : null,
          r.onlyB.length ? table([{ label: 'Key' }, { label: 'Amount', num: true }], r.onlyB.map(function (x) { return [x.key, R(x.amount)]; }), { caption: 'Only in ' + bn }) : null,
          r.matched.length ? h('details', { class: 'more' }, h('summary', null, 'Matched items (' + r.matched.length + ')'),
            table([{ label: 'Key' }, { label: an, num: true }, { label: bn, num: true }], r.matched.map(function (x) { return [x.key, R(x.a), R(x.b)]; }))) : null,
          exportBar('reconciliation', function () {
            var out = [['Status', 'Key', an, bn, 'Difference']];
            r.mismatched.forEach(function (x) { out.push(['Amounts differ', x.key, x.a, x.b, x.difference]); });
            r.onlyA.forEach(function (x) { out.push(['Only in ' + an, x.key, x.amount, '', x.amount]); });
            r.onlyB.forEach(function (x) { out.push(['Only in ' + bn, x.key, '', x.amount, -x.amount]); });
            r.matched.forEach(function (x) { out.push(['Matched', x.key, x.a, x.b, x.difference]); });
            return out;
          })
        ]);
      };
    }
  });

  var AGE_EX = ['Party\tDue date\tAmount\tCategory', 'Alpha Traders\t15/03/2026\t185000\tUndisputed', 'Alpha Traders\t30/11/2025\t92000\tUndisputed',
    'Beta Industries\t10/04/2026\t240000\tUndisputed', 'Beta Industries\t31/05/2025\t64500\tUndisputed', 'Gamma Agro\t20/01/2025\t118000\tDisputed',
    'Delta Exports\t05/08/2024\t56000\tUndisputed', 'Delta Exports\t28/02/2023\t31000\tDisputed', 'Epsilon Retail\t12/12/2025\t77500\tUndisputed',
    'Zeta Builders\t30/09/2022\t45000\tDisputed'].join('\n');
  tool({
    id: 'ageing', group: 'audit', title: 'Ageing schedule', layout: 'stack', figures: true,
    summary: 'Ages receivables or payables into the Schedule III periods from the due date, by category and by party.',
    keywords: 'Schedule III trade receivables payables ageing debtors creditors MSME disputed',
    notes: [
      'Schedule III ages balances from the due date of payment. If you have only invoice dates, enter the credit period and the tool adds it.',
      'The optional fourth column becomes the rows of the Schedule III table, for example Undisputed and Disputed, or MSME and Others for payables.',
      'Amounts not yet due as at the reporting date appear under Not due.'
    ],
    build: function (f, o) {
      add(f, [
        h('div', { class: 'row3' },
          seg('ag-type', [['rec', 'Receivables'], ['pay', 'Payables']], 'rec', 'Balances'),
          fld('As at', date('ag-asat', S.utc(2026, 3, 31))),
          fld('Credit period to add (days)', dec('ag-credit', ''), 'Leave blank if the dates are already due dates.')),
        pasteField('ag-rows', 'Party, date, amount and an optional category', AGE_EX, 10, 'Paste four columns from Excel: party, due date (dd/mm/yyyy), amount, category.')
      ]);
      return function () {
        var asAt = dt('ag-asat'), credit = n('ag-credit'), buckets = radio('ag-type') === 'pay' ? D.scheduleIII.payableBuckets : D.scheduleIII.receivableBuckets;
        need(asAt, 'Enter the reporting date.');
        var rows = [], bad = [];
        pastedRows(val('ag-rows'), 2).forEach(function (c, i) {
          var d0 = S.parseDate(c[1]), a = S.num(c[2]);
          if (!d0 || isNaN(a)) { bad.push(i + 1); return; }
          rows.push({ party: c[0] || '(no name)', date: credit > 0 ? S.addDays(d0, credit) : d0, amount: a, cat: (c[3] || '').trim() });
        });
        need(rows.length, 'Paste rows with a party, a date and an amount.');
        var cats = [];
        rows.forEach(function (r) { if (cats.indexOf(r.cat) < 0) cats.push(r.cat); });
        var heads = [{ label: 'Category' }, { label: 'Not due', num: true }].concat(buckets.map(function (b) { return { label: b[0], num: true }; })).concat([{ label: 'Total', num: true }]);
        var catRows = cats.map(function (c) {
          var a = S.ageing(rows.filter(function (r) { return r.cat === c; }), asAt, buckets);
          return [c || 'All balances', a.notDue].concat(a.totals).concat([a.grand]);
        });
        var all = S.ageing(rows, asAt, buckets);
        var allRow = ['Total', all.notDue].concat(all.totals).concat([all.grand]);
        function fmtRow(r) { return r.map(function (v, i) { return i === 0 ? v : R(v); }); }
        var partyHeads = [{ label: 'Party' }, { label: 'Not due', num: true }].concat(buckets.map(function (b) { return { label: b[0], num: true }; })).concat([{ label: 'Total', num: true }]);
        var partyRows = all.parties.map(function (p) { return [p.party, p.notDue].concat(p.buckets).concat([p.total]); });
        var overdue = all.totals.reduce(function (s, v) { return s + v; }, 0);
        add(o, [
          tiles([
            { label: 'Total balances', value: R(all.grand), sub: plural(rows.length, 'item') + ', ' + plural(all.parties.length, 'party', 'parties') },
            { label: 'Past due', value: R(overdue), lead: true, sub: all.grand ? pc(overdue / all.grand, 1) + ' of the total' : '' },
            { label: 'Older than ' + buckets[buckets.length - 2][0].replace(/^.* to /, ''), value: R(all.totals[all.totals.length - 1]), sub: 'Oldest period' }]),
          bad.length ? note('Skipped ' + plural(bad.length, 'line') + ' without a valid date or amount (data line ' + bad.slice(0, 5).join(', ') + (bad.length > 5 ? ' and more' : '') + ').', 'warn') : null,
          table(heads, catRows.map(fmtRow), { caption: 'Schedule III ageing as at ' + F(asAt), rowHeads: true, foot: cats.length > 1 ? fmtRow(allRow) : null }),
          table(partyHeads, partyRows.slice(0, 30).map(fmtRow), { caption: 'By party, largest first' + (partyRows.length > 30 ? ' (top 30 of ' + partyRows.length + ')' : ''), rowHeads: true }),
          exportBar('ageing-' + S.iso(asAt), function () {
            var hd = heads.map(function (x) { return x.label; });
            return [hd].concat(catRows).concat([allRow]).concat([[]]).concat([partyHeads.map(function (x) { return x.label; })]).concat(partyRows);
          })
        ]);
      };
    }
  });

  var RT_FLOWS = [
    ['sales', 'Revenue from operations', 84000000, 71000000], ['creditSales', 'Net credit sales', 79000000, 66000000],
    ['creditPurchases', 'Net credit purchases', 51000000, 44000000], ['cogs', 'Cost of goods sold', 60500000, 51800000],
    ['pbt', 'Profit before tax', 5650000, 4900000], ['pat', 'Profit after tax', 4200000, 3650000],
    ['nonCash', 'Depreciation and other non-cash charges', 1850000, 1600000], ['interest', 'Finance cost', 1420000, 1280000],
    ['leasePayments', 'Lease payments', 240000, 240000], ['principalRepaid', 'Principal repaid on borrowings', 3000000, 2500000],
    ['prefDividend', 'Preference dividend', 0, 0], ['investmentIncome', 'Income from investments', 310000, 220000]];
  var RT_BAL = [
    ['currentAssets', 'Current assets', 36500000, 28500000], ['currentLiabilities', 'Current liabilities', 21000000, 19500000],
    ['debt', 'Total borrowings', 16000000, 18500000], ['equity', 'Shareholders’ equity', 31000000, 26800000, 23150000],
    ['inventory', 'Inventories', 13200000, 9800000, 9100000], ['receivables', 'Trade receivables', 14400000, 10800000, 10200000],
    ['payables', 'Trade payables', 8600000, 7900000, 7000000], ['capitalEmployed', 'Capital employed', 47000000, 45300000],
    ['investments', 'Investments', 4200000, 3500000, 3000000]];
  tool({
    id: 'ratios', group: 'audit', title: 'Schedule III ratios', layout: 'stack', figures: true,
    summary: 'The eleven ratios Schedule III requires, for the current and previous year, with each change above 25% marked for an explanation.',
    keywords: 'Schedule III ratios current ratio debt equity DSCR ROE ROCE turnover disclosure',
    notes: [
      'Formulas follow the definitions in the ICAI Guidance Note on Division I of Schedule III. Where a company uses a different definition, disclose it.',
      'Averages use the opening and closing balance of each year, so the previous year needs its own opening balances.',
      'Capital employed is tangible net worth plus total debt plus deferred tax liability. EBIT is profit before tax plus finance cost.'
    ],
    build: function (f, o) {
      function rowIn(r, opening) {
        return h('tr', null, h('th', { scope: 'row' }, r[1]),
          h('td', null, money('rt-' + r[0] + '-cy', r[2])), h('td', null, money('rt-' + r[0] + '-py', r[3])),
          h('td', null, opening ? (r[4] != null ? money('rt-' + r[0] + '-po', r[4]) : h('span', { class: 'na' }, 'Not needed')) : null));
      }
      function grid(title, list, opening) {
        var t = h('table', { class: 't t--in' },
          h('caption', null, title),
          h('thead', null, h('tr', null, h('th', { scope: 'col' }, 'Item (₹)'), h('th', { scope: 'col', class: 'n' }, 'Current year'), h('th', { scope: 'col', class: 'n' }, 'Previous year'),
            opening ? h('th', { scope: 'col', class: 'n' }, 'Previous year, opening') : null)),
          h('tbody', null, list.map(function (r) { return rowIn(r, opening); })));
        return h('div', { class: 'tbl-wrap' }, t);
      }
      add(f, [grid('Profit and loss', RT_FLOWS, false), grid('Balance sheet, closing balances', RT_BAL, true)]);
      Array.prototype.forEach.call(f.querySelectorAll('.t--in input'), function (i) {
        var row = i.closest('tr'), col = i.closest('td').cellIndex, head = i.closest('table').querySelectorAll('thead th')[col];
        i.setAttribute('aria-label', row.querySelector('th').textContent + ', ' + head.textContent.toLowerCase());
      });
      return function () {
        function year(which) {
          var v = {};
          RT_FLOWS.forEach(function (r) { v[r[0]] = n('rt-' + r[0] + '-' + which) || 0; });
          RT_BAL.forEach(function (r) {
            var close = n('rt-' + r[0] + '-' + which) || 0;
            var open = r[4] == null ? close : (which === 'cy' ? n('rt-' + r[0] + '-py') : n('rt-' + r[0] + '-po')) || 0;
            v[r[0]] = close; v[r[0] + 'Opening'] = open;
          });
          v.ebit = v.pbt + v.interest;
          v.avgInvestments = (v.investments + v.investmentsOpening) / 2;
          return v;
        }
        var res = S.ratios(year('cy'), year('py'));
        function ratioText(x, v) { return isNaN(v) ? '—' : x.unit === '%' ? pc(v, 2) : v.toFixed(2); }
        var flagged = res.filter(function (x) { return x.explain; }).length;
        add(o, [
          tiles([{ label: 'Ratios worked', value: String(res.length) }, { label: 'Change above ' + pc(D.scheduleIII.ratioVarianceFlag, 0), value: String(flagged), lead: flagged > 0, sub: 'Each needs an explanation in the notes' }]),
          table([{ label: 'Ratio' }, { label: 'Current year', num: true }, { label: 'Previous year', num: true }, { label: 'Change', num: true }, { label: '' }],
            res.map(function (x) {
              return [h('span', { class: 'cellstack' }, h('span', null, x.name), h('span', { class: 'cellnote' }, x.formula)), ratioText(x, x.cy), ratioText(x, x.py),
                isNaN(x.change) ? '—' : (x.change >= 0 ? '+' : '') + pc(x.change, 1), x.explain ? pill('Explain', 'warn') : ''];
            }), { caption: 'Ratios', rowHeads: true }),
          exportBar('schedule-iii-ratios', function () { return [['Ratio', 'Formula', 'Unit', 'Current year', 'Previous year', 'Change', 'Explain']].concat(res.map(function (x) { return [x.name, x.formula, x.unit, x.cy, x.py, x.change, x.explain ? 'Yes' : '']; })); })
        ]);
      };
    }
  });

  // ══ ACCOUNTING ══
  tool({
    id: 'depreciation', group: 'accounting', title: 'Depreciation under Schedule II', figures: true,
    summary: 'Year-by-year depreciation on straight-line or written-down-value basis over the Schedule II useful life, pro rata from the date put to use.',
    keywords: 'Schedule II useful life SLM WDV fixed assets PPE',
    notes: [
      'The written-down-value rate is worked out so that the asset reaches its residual value at the end of its useful life: 1 − (residual ÷ cost)^(1 ÷ life).',
      'The year in which the useful life ends takes the carrying amount down to the residual value.',
      'For a full fixed asset register with disposals, income-tax blocks and deferred tax, use the Fixed Asset Register workbook.'
    ],
    build: function (f, o) {
      var lives = D.companies.usefulLives;
      add(f, [
        fld('Class of asset', sel('dp-class', lives.map(function (l, i) { return [String(i), l[0] + ' (' + l[1] + ' years)']; }).concat([['other', 'Other: enter the life']]), '3')),
        h('div', { class: 'row2' }, fld('Cost (₹)', money('dp-cost', 1250000)), fld('Date put to use', date('dp-date', S.utc(2025, 8, 10)))),
        h('div', { class: 'row3' }, fld('Useful life (years)', dec('dp-life', 15)), fld('Residual value (%)', dec('dp-res', 5), 'Schedule II: normally not more than ' + pc(D.companies.scheduleIIResidualMax, 0) + ' of cost.'),
          seg('dp-m', [['SLM', 'Straight line'], ['WDV', 'Written down']], 'SLM', 'Method'))
      ]);
      $('dp-class').addEventListener('change', function () { var l = lives[+val('dp-class')]; if (l) $('dp-life').value = String(l[1]); });
      return function () {
        var cost = n('dp-cost'), life = n('dp-life'), res = isNaN(n('dp-res')) ? 0 : n('dp-res'), d0 = dt('dp-date');
        need(cost > 0, 'Enter the cost.'); need(d0, 'Enter the date the asset was put to use.');
        need(life > 0 && life <= 100 && Math.round(life) === life, 'Enter the useful life in whole years.');
        need(res >= 0 && res < 100, 'Enter a residual value from 0% to below 100%.');
        var r = S.depreciation({ cost: cost, residualPct: res, life: life, method: radio('dp-m'), putToUse: d0 });
        need(!r.error, r.error);
        add(o, [
          tiles([
            { label: radio('dp-m') === 'WDV' ? 'Written-down-value rate' : 'Straight-line rate', value: pc(r.rate, 2), lead: true, sub: 'On ' + (radio('dp-m') === 'WDV' ? 'the opening carrying amount' : 'cost') },
            { label: 'Residual value', value: R(r.residual) },
            { label: 'Useful life ends', value: F(r.lifeEnd) }]),
          res > D.companies.scheduleIIResidualMax * 100 ? note('A residual value above ' + pc(D.companies.scheduleIIResidualMax, 0) + ' of cost needs justification in the financial statements.', 'warn') : null,
          table([{ label: 'Year' }, { label: 'Days', num: true }, { label: 'Opening', num: true }, { label: 'Depreciation', num: true }, { label: 'Closing', num: true }],
            r.rows.map(function (x) { return [x.fy, String(x.days), R(x.opening), R(x.depreciation), R(x.closing)]; }), { caption: 'Depreciation schedule', rowHeads: true }),
          exportBar('depreciation', function () { return [['Year', 'Days', 'Opening', 'Depreciation', 'Closing']].concat(r.rows.map(function (x) { return [x.fy, x.days, x.opening, x.depreciation, x.closing]; })); })
        ]);
      };
    }
  });

  tool({
    id: 'loan', group: 'accounting', title: 'Loan schedule',
    summary: 'EMI, the full repayment schedule, and the year-wise split of interest and principal with current and non-current maturities.',
    keywords: 'EMI amortisation term loan current maturities interest',
    notes: [
      'Interest is worked monthly on the opening balance at one-twelfth of the annual rate. The last instalment clears any rounding.',
      'Current maturities are the principal falling due in the twelve months after each year end; the rest of the closing balance is non-current.'
    ],
    build: function (f, o) {
      add(f, [
        fld('Loan amount (₹)', money('ln-p', 2500000)),
        h('div', { class: 'row3' }, fld('Interest rate (% a year)', dec('ln-r', 9.5)), fld('Tenure (months)', dec('ln-m', 84)), fld('First EMI on', date('ln-d', S.utc(2026, 5, 5))))
      ]);
      return function () {
        var P = n('ln-p'), r = n('ln-r'), m = n('ln-m'), d0 = dt('ln-d');
        need(P > 0, 'Enter the loan amount.'); need(r >= 0 && r < 100, 'Enter the annual interest rate.');
        need(m > 0 && m <= 600 && Math.round(m) === m, 'Enter the tenure in whole months, up to 600.'); need(d0, 'Enter the date of the first EMI.');
        var s = S.loanSchedule({ principal: P, annualRate: r, months: m, firstEmi: d0 });
        add(o, [
          tiles([{ label: 'EMI', value: R(s.emi), lead: true, sub: plural(m, 'instalment') }, { label: 'Total interest', value: R(s.totalInterest) }, { label: 'Total repaid', value: R(s.totalPaid) }]),
          table([{ label: 'Year' }, { label: 'Interest', num: true }, { label: 'Principal', num: true }, { label: 'Closing balance', num: true }, { label: 'Current', num: true }, { label: 'Non-current', num: true }],
            s.years.map(function (y) { return [y.fy, R(y.interest), R(y.principal), R(y.closing), R(y.current), R(y.nonCurrent)]; }), { caption: 'By financial year', rowHeads: true }),
          h('details', { class: 'more' }, h('summary', null, 'Monthly schedule (' + s.rows.length + ' instalments)'),
            table([{ label: 'No.' }, { label: 'Date' }, { label: 'EMI', num: true }, { label: 'Interest', num: true }, { label: 'Principal', num: true }, { label: 'Balance', num: true }],
              s.rows.map(function (x) { return [String(x.no), F(x.date), R(x.emi), R(x.interest), R(x.principal), R(x.balance)]; }))),
          exportBar('loan-schedule', function () { return [['No.', 'Date', 'EMI', 'Interest', 'Principal', 'Balance']].concat(s.rows.map(function (x) { return [x.no, S.iso(x.date), x.emi, x.interest, x.principal, x.balance]; })); })
        ]);
      };
    }
  });

  tool({
    id: 'words', group: 'accounting', title: 'Amount in words',
    summary: 'Writes an amount in words in the Indian system of lakh and crore, with paise, for cheques, certificates and agreements.',
    keywords: 'rupees words lakh crore cheque certificate',
    build: function (f, o) {
      add(f, fld('Amount (₹)', money('wd-a', 1234567.89)));
      return function () {
        var a = n('wd-a');
        need(!isNaN(a), 'Enter an amount.');
        need(Math.abs(a) < 1e15, 'Enter an amount below ₹1,000 lakh crore.');
        var w = S.amountInWords(a), status = h('span', { class: 'export__status', role: 'status' });
        add(o, [h('p', { class: 'figure-big num' }, R(a)), h('p', { class: 'words' }, w),
          h('div', { class: 'export' }, h('button', { type: 'button', class: 'btn-sm', onclick: function () { copyText(w, status, 'Copied.'); } }, 'Copy words'), status)]);
      };
    }
  });

  // ══ GST ══
  tool({
    id: 'gst', group: 'gst', title: 'GST calculator',
    summary: 'Splits an amount into taxable value and tax, inclusive or exclusive, as IGST or as CGST and SGST.',
    keywords: 'GST CGST SGST IGST inclusive exclusive cess invoice',
    build: function (f, o) {
      add(f, [
        fld('Amount (₹)', money('gc-a', 50000)),
        h('div', { class: 'row2' },
          seg('gc-incl', [['ex', 'Before GST'], ['in', 'Including GST']], 'ex', 'The amount is'),
          seg('gc-st', [['intra', 'Within the State'], ['inter', 'Between States']], 'intra', 'Supply')),
        h('div', { class: 'row2' },
          fld('GST rate', sel('gc-r', D.gst.commonRates.map(function (r) { return [String(r), r + '%']; }), '18')),
          fld('Compensation cess (%)', dec('gc-c', ''), 'Leave blank if none.'))
      ]);
      return function () {
        var a = n('gc-a'), rate = +val('gc-r'), cess = isNaN(n('gc-c')) ? 0 : n('gc-c'), inter = radio('gc-st') === 'inter';
        need(a > 0, 'Enter the amount.'); need(cess >= 0 && cess < 1000, 'Enter the cess percentage.');
        var r = S.gstCalc({ amount: a, rate: rate, cess: cess, inclusive: radio('gc-incl') === 'in', interState: inter });
        var rows = [['Taxable value', R(r.taxable)]];
        if (inter) rows.push(['IGST at ' + rate + '%', R(r.igst)]);
        else { rows.push(['CGST at ' + rate / 2 + '%', R(r.cgst)]); rows.push(['SGST or UTGST at ' + rate / 2 + '%', R(r.sgst)]); }
        if (cess) rows.push(['Compensation cess at ' + cess + '%', R(r.cess)]);
        add(o, [
          tiles([{ label: 'Taxable value', value: R(r.taxable) }, { label: 'Total tax', value: R(r.gst + r.cess) }, { label: 'Invoice value', value: R(r.total), lead: true }]),
          table([{ label: 'Component' }, { label: 'Amount', num: true }], rows, { rowHeads: true, foot: ['Invoice value', R(r.total)] }),
          h('p', { class: 'cellnote' }, S.amountInWords(r.total))
        ]);
      };
    }
  });

  tool({
    id: 'gst-late', group: 'gst', title: 'GST late fee and interest', figures: true,
    summary: 'Late fee for GSTR-3B, GSTR-1 and GSTR-9 with the turnover-based caps, and interest on tax paid late.',
    keywords: 'GST late fee interest section 47 section 50 GSTR-3B GSTR-1 GSTR-9',
    notes: [
      'The late fee is shown as CGST and SGST together, split equally between them.',
      'Interest is worked on the tax paid late in cash, by days, at the rate in the figures file. Interest on input tax credit wrongly availed and utilised is not covered.',
      'For GSTR-9 the cap is a share of turnover in the State or Union territory; enter that turnover.'
    ],
    build: function (f, o) {
      add(f, [
        fld('Return', sel('gl-type', [['3b', 'GSTR-3B'], ['1', 'GSTR-1'], ['9', 'GSTR-9 (annual return)']], '3b')),
        h('div', { id: 'gl-nil-box' }, check('gl-nil', 'Nil return', false)),
        h('div', { class: 'row2' }, fld('Due date', date('gl-due', S.utc(2026, 6, 20))), fld('Date filed', date('gl-filed', S.utc(2026, 8, 14)))),
        fld('Aggregate turnover of the year (₹)', money('gl-to', 32000000), 'For GSTR-3B and GSTR-1, the previous financial year.'),
        h('div', { id: 'gl-tax-box' }, fld('Tax paid late in cash (₹)', money('gl-tax', 185000), 'Leave blank if no tax was paid late.'),
          fld('Date tax paid', date('gl-paid', S.utc(2026, 8, 14))))
      ]);
      return function () {
        var type = val('gl-type'), annual = type === '9';
        show('gl-nil-box', !annual); show('gl-tax-box', type === '3b');
        var due = dt('gl-due'), filed = dt('gl-filed'), to = n('gl-to');
        need(due && filed, 'Enter the due date and the date filed.');
        need(to >= 0, 'Enter the aggregate turnover.');
        var fee = S.gstLateFee({ type: annual ? 'annual' : 'monthly', nil: !annual && isOn('gl-nil'), due: due, filed: filed, turnover: to });
        var list = [{ label: 'Late fee', value: R0(fee.fee), lead: true, sub: fee.days ? (fee.capped ? 'Capped; ' : '') + plural(fee.days, 'day') + ' late at ' + R0(fee.perDay) + ' a day' : 'Filed on time' }];
        var rows = [['Days late', String(fee.days)], ['Fee before the cap', R0(fee.uncapped)], ['Cap for this turnover', R0(fee.cap)], ['Late fee: CGST', R(fee.fee / 2)], ['Late fee: SGST', R(fee.fee / 2)]];
        var tax = n('gl-tax'), paid = dt('gl-paid'), it = null;
        if (type === '3b' && tax > 0) {
          need(paid, 'Enter the date the tax was paid.');
          it = S.gstInterest({ tax: tax, due: due, paid: paid });
          list.push({ label: 'Interest', value: R0(it.interest), sub: plural(it.days, 'day') + ' at ' + pc(it.rate, 0) + ' a year' });
          rows.push(['Interest on ' + R0(tax) + ' for ' + plural(it.days, 'day'), R(it.interest)]);
        }
        add(o, [tiles(list), table([{ label: 'Working' }, { label: 'Amount', num: true }], rows, { rowHeads: true })]);
      };
    }
  });

  var ID_EX = ['24ABCPS1234K1ZS', '24ABCPS1234K1ZT', 'ABCPS1234K', 'ABCXS1234K', 'AHMA12345B', 'U74999GJ2022PTC123456', '01234567', 'AAB-1234'].join('\n');
  tool({
    id: 'identifiers', group: 'gst', title: 'GSTIN, PAN, TAN and CIN checker',
    summary: 'Checks the structure of GSTINs, PANs, TANs, CINs, DINs and LLPINs, including the GSTIN check character, for a whole vendor or customer list at once.',
    keywords: 'GSTIN PAN TAN CIN DIN LLPIN validate checksum vendor master KYC',
    notes: [
      'A GSTIN that passes has the right structure and check character. Whether it is active, and whose it is, can only be confirmed on the GST portal.',
      'The fourth character of a PAN gives the holder type: P individual, C company, H HUF, F firm or LLP, and so on.'
    ],
    build: function (f, o) {
      add(f, pasteField('id-list', 'Numbers to check, one per line', ID_EX, 10));
      return function () {
        var list = val('id-list').split(/\r?\n/).map(function (x) { return x.trim(); }).filter(Boolean);
        need(list.length, 'Paste the numbers to check, one per line.');
        var res = list.map(S.identify);
        var good = res.filter(function (r) { return r.valid; }).length;
        add(o, [
          tiles([{ label: 'Checked', value: count(res.length) }, { label: 'Well formed', value: count(good) }, { label: 'With problems', value: count(res.length - good), lead: res.length - good > 0 }]),
          table([{ label: 'Entered' }, { label: 'Type' }, { label: 'Result' }, { label: 'Details' }], res.map(function (r) {
            var detail = r.valid ? r.fields.map(function (x) { return x[0] + ': ' + x[1]; }).join(' · ') : r.issues.join(' ');
            return [h('code', null, r.input), r.type, r.valid ? pill('Well formed', 'good') : pill('Problem', 'bad'), detail || '—'];
          })),
          exportBar('identifier-check', function () { return [['Entered', 'Type', 'Result', 'Details']].concat(res.map(function (r) { return [r.input, r.type, r.valid ? 'Well formed' : 'Problem', r.valid ? r.fields.map(function (x) { return x[0] + ': ' + x[1]; }).join('; ') : r.issues.join(' ')]; })); })
        ]);
      };
    }
  });

  // ══ TDS ══
  function tdsLabel(r) { return r.label + ' (' + r.old + ')'; }
  function thresholdText(r) {
    var t = R0(r.threshold);
    if (r.kind === 'monthly') return 'Above ' + t + ' a month';
    if (r.kind === 'single') return t + ' or more';
    if (r.kind === 'excess') return 'On the part above ' + t + ' a year';
    return 'Above ' + t + ' a year' + (r.single != null ? ', or ' + R0(r.single) + ' in one payment' : '');
  }
  tool({
    id: 'tds', group: 'tds', title: 'TDS on a payment', figures: true,
    summary: 'Whether tax is to be deducted on a payment, at what rate and on what amount, with the reasons.',
    keywords: 'TDS 194C 194J 194H 194I 194A 194Q 194T rate threshold section 393 deduction',
    notes: [
      'Section numbers in brackets are those of the Income-tax Act, 1961, for reference; payments from 1 April 2026 fall under section 393 of the Income-tax Act, 2025.',
      'Where earlier payments in the year carried no deduction and this payment takes the year’s total over the limit, tax is due on the earlier payments too.',
      'Lower or nil deduction certificates, payees exempt by notification, and higher rates for non-filers are not covered.'
    ],
    build: function (f, o) {
      var rows = D.tds.rows;
      add(f, [
        fld('Nature of payment', sel('td-row', rows.map(function (r) { return [r.id, tdsLabel(r)]; }), 'professional')),
        fld('This payment or credit (₹)', money('td-amt', 85000), 'For rent, the rent for the month.'),
        fld('Earlier payments to the same payee this year (₹)', money('td-prior', 0)),
        check('td-taxed', 'Tax was deducted on the earlier payments', false),
        check('td-pan', 'The payee has given a valid PAN', true)
      ]);
      return function () {
        var row = rows.filter(function (r) { return r.id === val('td-row'); })[0], amt = n('td-amt'), prior = isNaN(n('td-prior')) ? 0 : n('td-prior');
        need(amt > 0, 'Enter the amount of this payment.'); need(prior >= 0, 'Earlier payments cannot be negative.');
        var r = S.tdsCompute(row, { amount: amt, prior: prior, priorTaxed: isOn('td-taxed'), hasPan: isOn('td-pan') });
        add(o, [
          tiles([
            { label: 'Tax to deduct', value: R0(r.tds), lead: true, sub: r.applies ? 'At ' + pc(r.rate, r.rate < 0.01 ? 1 : 0) + ' on ' + R0(r.base) : 'No deduction' },
            { label: 'Net payable to the payee', value: R0(r.net), sub: 'On this payment of ' + R0(amt) }]),
          note(r.why + (r.noPan && r.applies ? ' Without a PAN the higher rate applies.' : ''), r.applies ? null : 'good'),
          table([{ label: 'Item' }, { label: 'Detail' }], [['Section (1961 Act)', row.old], ['Rate', pc(row.rate, row.rate < 0.01 ? 1 : 0) + (r.noPan ? '; ' + pc(r.rate, 0) + ' without PAN' : '')], ['Threshold', thresholdText(row)]], { rowHeads: true }),
          h('details', { class: 'more' }, h('summary', null, 'All payment types in the figures file (' + rows.length + ')'),
            table([{ label: 'Nature of payment' }, { label: '1961 Act' }, { label: 'Rate', num: true }, { label: 'Threshold' }],
              rows.map(function (x) { return [x.label, x.old, pc(x.rate, x.rate < 0.01 ? 1 : 0), thresholdText(x)]; })))
        ]);
      };
    }
  });

  tool({
    id: 'tds-interest', group: 'tds', title: 'TDS interest and late fee', figures: true,
    summary: 'Interest for late deduction and late deposit, the deposit due date, and the late fee on a TDS or TCS statement.',
    keywords: 'TDS interest 201(1A) 398 late fee 234E 427 statement deposit',
    notes: [
      'Interest runs for each month or part of a month, counted by calendar month: from the date tax was deductible to the date deducted, and from the date deducted to the date deposited when the deposit is late.',
      'The deposit is due by the 7th of the next month, and for March by 30 April. Government deductors paying without a challan have different dates.',
      'The late fee runs for each day of delay in filing the statement and cannot exceed the tax deductible.'
    ],
    build: function (f, o) {
      add(f, [
        fld('Tax deductible (₹)', money('ti-tax', 25000)),
        h('div', { class: 'row3' }, fld('Payment or credit on', date('ti-due', S.utc(2026, 4, 15))), fld('Tax deducted on', date('ti-ded', S.utc(2026, 5, 10))), fld('Tax deposited on', date('ti-dep', S.utc(2026, 6, 12)))),
        h('div', { class: 'row2' }, fld('Statement due on', date('ti-sdue', S.utc(2026, 7, 31))), fld('Statement filed on', date('ti-sfil', S.utc(2026, 8, 20))))
      ]);
      return function () {
        var tax = n('ti-tax'), a = dt('ti-due'), b = dt('ti-ded'), c = dt('ti-dep');
        need(tax > 0, 'Enter the tax deductible.'); need(a && b && c, 'Enter the three dates for the deduction and deposit.');
        need(b >= a, 'The date of deduction cannot be before the payment or credit.'); need(c >= b, 'The deposit cannot be before the deduction.');
        var r = S.tdsInterest({ tds: tax, deductible: a, deducted: b, deposited: c });
        var sd = dt('ti-sdue'), sf = dt('ti-sfil'), fee = sd && sf ? S.tdsLateFee({ due: sd, filed: sf, tds: tax }) : null;
        add(o, [
          tiles([
            { label: 'Interest', value: R0(r.total), lead: true, sub: r.total ? 'Late deduction and late deposit' : 'None' },
            { label: 'Deposit was due by', value: F(r.depositDue), sub: c > r.depositDue ? 'Deposited ' + plural(S.diffDays(r.depositDue, c), 'day') + ' late' : 'Deposited on time' },
            fee ? { label: 'Statement late fee', value: R0(fee.fee), sub: fee.days ? plural(fee.days, 'day') + ' late' + (fee.capped ? '; capped at the tax' : '') : 'Filed on time' } : null]),
          table([{ label: 'Working' }, { label: 'Months', num: true }, { label: 'Rate', num: true }, { label: 'Amount', num: true }], [
            ['Late deduction', String(r.lateDeductionMonths), pc(D.tds.interestLateDeduction, 1) + ' a month', R0(r.lateDeductionInterest)],
            ['Late deposit', String(r.lateDepositMonths), pc(D.tds.interestLateDeposit, 1) + ' a month', R0(r.lateDepositInterest)]],
            { rowHeads: true, foot: ['Total interest', '', '', R0(r.total)] })
        ]);
      };
    }
  });

  // ══ INCOME-TAX ══
  tool({
    id: 'income-tax', group: 'income-tax', title: 'Old and new regime', figures: true,
    summary: 'Tax for a resident individual under both regimes side by side, with rebate, surcharge, marginal relief and cess.',
    keywords: 'income tax slab regime 115BAC 87A rebate surcharge salary comparison',
    notes: [
      'For income taxed at the normal slab rates only. Capital gains and other income at special rates are not included.',
      'The standard deduction is applied against salary or pension. Deductions and exemptions entered are allowed only under the old regime.',
      'Total income and tax are rounded to the nearest ₹10. Slabs used: ' + D.incomeTax.years.join(' and ') + ' (the same figures).'
    ],
    build: function (f, o) {
      add(f, [
        fld('Age during the year', sel('it-age', [['below60', 'Below 60'], ['senior', '60 to 79'], ['superSenior', '80 or above']], 'below60')),
        fld('Salary or pension (₹)', money('it-sal', 1850000)),
        fld('Other income at normal rates (₹)', money('it-oth', 120000), 'Interest, rent after deductions, business income and so on.'),
        fld('Deductions and exemptions under the old regime (₹)', money('it-ded', 275000), 'Chapter VI-A, HRA exemption, interest on a home loan and the like.')
      ]);
      return function () {
        var sal = isNaN(n('it-sal')) ? 0 : n('it-sal'), oth = isNaN(n('it-oth')) ? 0 : n('it-oth'), ded = isNaN(n('it-ded')) ? 0 : n('it-ded');
        need(sal >= 0 && ded >= 0, 'Salary and deductions cannot be negative.');
        need(sal + oth > 0, 'Enter the income.');
        var r = S.incomeTax({ salary: sal, other: oth, deductions: ded, age: val('it-age') });
        var A = r.oldRegime, B = r.newRegime;
        function line(label, k, neg) { return [label, (neg && A[k] ? '−' : '') + R0(A[k]), (neg && B[k] ? '−' : '') + R0(B[k])]; }
        add(o, [
          tiles([
            { label: 'Old regime', value: R0(A.total), lead: r.lower === 'oldRegime' },
            { label: 'New regime', value: R0(B.total), lead: r.lower === 'newRegime' },
            { label: 'Difference', value: R0(r.difference), sub: r.difference ? (r.lower === 'newRegime' ? 'New' : 'Old') + ' regime is lower' : 'Same under both' }]),
          table([{ label: '' }, { label: 'Old regime', num: true }, { label: 'New regime', num: true }], [
            line('Gross income', 'gross'), line('Standard deduction', 'standardDeduction', true), line('Deductions and exemptions', 'deductions', true),
            line('Total income', 'taxable'), line('Tax at slab rates', 'slabTax'), line('Rebate', 'rebate', true), line('Marginal relief on rebate', 'rebateRelief', true),
            ['Surcharge', A.surchargeRate ? R0(A.surcharge) + ' (' + pc(A.surchargeRate, 0) + ')' : R0(0), B.surchargeRate ? R0(B.surcharge) + ' (' + pc(B.surchargeRate, 0) + ')' : R0(0)],
            line('Marginal relief on surcharge', 'surchargeRelief', true), line('Health and education cess', 'cess')],
            { rowHeads: true, foot: ['Tax payable', R0(A.total), R0(B.total)] })
        ]);
      };
    }
  });

  tool({
    id: 'advance-tax', group: 'income-tax', title: 'Advance tax instalments', figures: true,
    summary: 'The instalments of advance tax due for the year and their dates, for regular and presumptive-income taxpayers.',
    keywords: 'advance tax instalment 15 June 234C 44AD 44ADA presumptive',
    notes: [
      'Advance tax is due only if the tax for the year, after TDS and TCS, is at or above the threshold in the figures file.',
      'Interest for shortfall or deferment of instalments is not worked out here.'
    ],
    build: function (f, o) {
      add(f, [
        fld('Financial year', sel('at-fy', fyOptions(), String(THIS_FY))),
        h('div', { class: 'row2' }, fld('Estimated tax for the year (₹)', money('at-tax', 480000)), fld('TDS and TCS expected (₹)', money('at-tds', 120000))),
        check('at-pres', 'Income declared on a presumptive basis (one instalment)', false)
      ]);
      return function () {
        var tax = n('at-tax'), tds = isNaN(n('at-tds')) ? 0 : n('at-tds');
        need(tax >= 0, 'Enter the estimated tax for the year.');
        var r = S.advanceTax({ liability: tax, credits: tds, fyStart: +val('at-fy'), presumptive: isOn('at-pres') });
        if (!r.payable) { add(o, note('No advance tax is due: the tax after TDS and TCS is ' + R0(r.net) + ', below ' + R0(D.advanceTax.threshold) + '.', 'good')); return; }
        add(o, [
          tiles([{ label: 'Advance tax for the year', value: R0(r.net), lead: true, sub: 'After TDS and TCS of ' + R0(tds) }, { label: 'Next instalment', value: nextDue(r.rows) }]),
          table([{ label: 'Due by' }, { label: 'Cumulative share', num: true }, { label: 'Cumulative amount', num: true }, { label: 'Instalment', num: true }],
            r.rows.map(function (x) { return [F(x.date), pc(x.share, 0), R0(x.cumulative), R0(x.instalment)]; }), { rowHeads: true, rowClass: function (i) { return r.rows[i].date < TODAY ? 'is-past' : null; } })
        ]);
      };
      function nextDue(rows) { var x = rows.filter(function (r) { return r.date >= TODAY; })[0]; return x ? F(x.date) + ': ' + R0(x.instalment) : 'All past'; }
    }
  });

  // ══ COMPANY LAW AND MSME ══
  tool({
    id: 'roc', group: 'company', title: 'Annual filing dates', figures: true,
    summary: 'The last date for the AGM and the due dates of ADT-1, AOC-4 and MGT-7, or of LLP Forms 8 and 11.',
    keywords: 'ROC AGM AOC-4 MGT-7 MGT-7A ADT-1 LLP Form 8 Form 11 MCA due date',
    notes: [
      'Periods counted from the AGM treat the AGM date as day one, which gives the earlier date of the two readings.',
      'An extension of the AGM granted by the Registrar is not taken into account; enter the actual AGM date instead.',
      'Filing after the due date attracts additional fees for each day of delay.'
    ],
    build: function (f, o) {
      add(f, [
        seg('rc-ent', [['company', 'Company'], ['llp', 'LLP']], 'company', 'Entity'),
        fld('Financial year ended on', date('rc-fy', S.utc(2026, 3, 31))),
        h('div', { id: 'rc-co' }, check('rc-first', 'This is the first AGM', false), fld('AGM held or planned on (optional)', date('rc-agm', S.utc(2026, 9, 26))))
      ]);
      return function () {
        var ent = radio('rc-ent'), fy = dt('rc-fy'), agm = dt('rc-agm');
        show('rc-co', ent === 'company');
        need(fy, 'Enter the date the financial year ended.');
        var rows = S.rocDates({ entity: ent, fyEnd: fy, agm: ent === 'company' ? agm : null, firstAgm: isOn('rc-first') });
        var last = rows[0];
        if (ent === 'company' && agm && agm > last.date) add(o, note('The AGM date is after the last permitted date of ' + F(last.date) + '.', 'error'));
        add(o, [
          table([{ label: 'Filing' }, { label: 'Due by' }, { label: 'Basis' }, { label: '' }],
            rows.map(function (x) { return [x.what, F(x.date), x.basis, x.date < TODAY ? pill('Passed', 'muted') : pill(plural(S.diffDays(TODAY, x.date), 'day') + ' left', 'good')]; }), { rowHeads: true }),
          ent === 'company' && !agm ? note('Enter the AGM date to see ADT-1, AOC-4 and MGT-7.') : null
        ]);
      };
    }
  });

  tool({
    id: 'msme', group: 'company', title: 'Interest on delayed MSME payments', figures: true,
    summary: 'Due date and compound interest under sections 15 and 16 of the MSMED Act on a payment to a micro or small enterprise.',
    keywords: 'MSME MSMED section 15 16 43B(h) delayed payment interest supplier Udyam',
    notes: [
      'The credit period cannot exceed the limit in the figures file even if the agreement allows more; without a written agreement the shorter period applies.',
      'Interest is compounded with monthly rests at the multiple of the RBI bank rate in the figures file. Enter the bank rate in force.',
      'Under the income-tax law, an amount owed to a micro or small enterprise and paid after this due date is deductible only in the year of payment.'
    ],
    build: function (f, o) {
      add(f, [
        fld('Amount due (₹)', money('ms-a', 340000)),
        h('div', { class: 'row2' }, fld('Goods or services accepted on', date('ms-acc', S.utc(2026, 6, 5))), fld('Credit period agreed in writing (days)', dec('ms-days', 60), 'Leave blank if there is no written agreement.'))
        , h('div', { class: 'row2' }, fld('RBI bank rate (% a year)', dec('ms-bank', 5.5), 'The example uses 5.50%. Enter the rate notified by RBI.'), fld('Paid on, or interest up to', date('ms-paid', S.utc(2026, 9, 30))))
      ]);
      return function () {
        var a = n('ms-a'), acc = dt('ms-acc'), days = n('ms-days'), bank = n('ms-bank'), paid = dt('ms-paid');
        need(a > 0, 'Enter the amount due.'); need(acc && paid, 'Enter the date of acceptance and the date of payment.');
        need(bank > 0 && bank < 50, 'Enter the RBI bank rate.'); need(paid >= acc, 'The payment date cannot be before acceptance.');
        var r = S.msme({ amount: a, acceptance: acc, agreedDays: isNaN(days) ? null : days, bankRate: bank, asAt: paid });
        add(o, [
          tiles([
            { label: 'Payment due by', value: F(r.due), sub: r.creditDays + ' days from acceptance' + (r.capped ? ' (capped)' : isNaN(days) ? ' (no written agreement)' : '') },
            { label: 'Interest', value: R(r.interest), lead: r.interest > 0, sub: r.daysOverdue ? plural(r.daysOverdue, 'day') + ' late' : 'Paid in time' },
            { label: 'Rate', value: pc(r.annualRate, 2), sub: D.msme.interestMultiple + ' times the bank rate, monthly rests' }]),
          r.capped ? note('The agreed period of ' + days + ' days is longer than the ' + D.msme.maxCreditDays + ' days the Act allows, so ' + D.msme.maxCreditDays + ' days is used.', 'warn') : null,
          r.daysOverdue ? table([{ label: 'Working' }, { label: 'Value', num: true }], [['Whole months compounded', String(r.months)], ['Days after the last whole month', String(r.extraDays)], ['Amount due', R(a)], ['Interest', R(r.interest)]], { rowHeads: true, foot: ['Amount with interest', R(a + r.interest)] }) : null
        ]);
      };
    }
  });

  // ══ COMPLIANCE ══
  var LAWS = ['TDS', 'GST', 'Income-tax', 'PF and ESI', 'Company law'];
  tool({
    id: 'calendar', group: 'compliance', title: 'Compliance calendar', layout: 'stack', figures: true,
    summary: 'Due dates for TDS, GST, income-tax, PF and ESI and company law across a financial year, filterable and exportable to a calendar app.',
    keywords: 'due dates calendar compliance GSTR TDS return ITR DPT-3 MSME-1 DIR-3 KYC',
    notes: [
      'Dates falling on a holiday are shown as prescribed; check for extensions notified by the CBDT, the CBIC or the MCA.',
      'Company filings that run from the AGM are shown for an AGM on the last permitted day. Use Annual filing dates for the actual AGM.',
      'Items marked previous year relate to the year before the one selected.'
    ],
    build: function (f, o) {
      add(f, [
        h('div', { class: 'row2' }, fld('Financial year', sel('cl-fy', fyOptions(), String(THIS_FY))), h('div', { class: 'fgroup' }, check('cl-hide', 'Hide dates already passed', false))),
        h('fieldset', { class: 'seg seg--multi' }, h('legend', null, 'Show'), h('div', { class: 'seg__row' }, LAWS.map(function (l, i) {
          return h('label', { class: 'seg__opt' }, h('input', { type: 'checkbox', id: 'cl-law-' + i, value: l, checked: true }), h('span', null, l));
        })))
      ]);
      return function () {
        var fy = +val('cl-fy'), hide = isOn('cl-hide');
        var laws = LAWS.filter(function (l, i) { return isOn('cl-law-' + i); });
        var items = S.calendar(fy).filter(function (x) { return laws.indexOf(x.law) >= 0 && (!hide || x.date >= TODAY); });
        var next = items.filter(function (x) { return x.date >= TODAY; })[0];
        if (!items.length) { add(o, note('Nothing to show. Choose at least one area, or show past dates.')); return; }
        var months = [], byMonth = {};
        items.forEach(function (x) {
          var k = x.date.getUTCFullYear() * 100 + x.date.getUTCMonth();
          if (!byMonth[k]) { byMonth[k] = []; months.push(k); }
          byMonth[k].push(x);
        });
        var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        add(o, [
          tiles([{ label: 'Due dates shown', value: count(items.length), sub: S.fyLabel(fy) }, next ? { label: 'Next', value: F(next.date), lead: true, sub: next.law + ': ' + next.what } : { label: 'Next', value: 'None left this year' }]),
          exportBar('compliance-calendar-' + S.fyLabel(fy).replace(/\s/g, ''), function () {
            return [['Date', 'Area', 'Due', 'Relates to']].concat(items.map(function (x) { return [S.iso(x.date), x.law, x.what, x.prev ? 'Previous year' : S.fyLabel(fy)]; }));
          }, h('button', { type: 'button', class: 'btn-sm', onclick: function () { download('compliance-calendar-' + fy + '.ics', ics(items), 'text/calendar;charset=utf-8'); } }, 'Add to calendar (.ics)')),
          h('div', { class: 'cal' }, months.map(function (k) {
            return h('section', { class: 'cal-month' }, h('h3', { class: 'subh' }, MONTHS[k % 100] + ' ' + Math.floor(k / 100)),
              h('ul', { class: 'cal-list' }, byMonth[k].map(function (x) {
                var cls = 'cal-row' + (x.date < TODAY ? ' is-past' : '') + (next && x === next ? ' is-next' : '');
                return h('li', { class: cls }, h('span', { class: 'cal-date num' }, x.date.getUTCDate() + ' ' + MONTHS[x.date.getUTCMonth()].slice(0, 3)),
                  h('span', { class: 'tag' }, x.law), h('span', { class: 'cal-what' }, x.what, x.prev ? h('span', { class: 'cellnote' }, ' Previous year') : null));
              })));
          }))
        ]);
      };
    }
  });
  function ics(items) {
    function esc(s) { return String(s).replace(/([,;\\])/g, '\\$1'); }
    function fold(line) { var out = []; while (line.length > 74) { out.push(line.slice(0, 74)); line = ' ' + line.slice(74); } out.push(line); return out.join('\r\n'); }
    var stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');
    var lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Sagar Khatri & Associates//Compliance calendar//EN', 'CALSCALE:GREGORIAN'];
    items.forEach(function (x, i) {
      var d = S.iso(x.date).replace(/-/g, ''), d2 = S.iso(S.addDays(x.date, 1)).replace(/-/g, '');
      lines.push('BEGIN:VEVENT', 'UID:' + d + '-' + i + '-ska-compliance', 'DTSTAMP:' + stamp, 'DTSTART;VALUE=DATE:' + d, 'DTEND;VALUE=DATE:' + d2,
        fold('SUMMARY:' + esc(x.law + ': ' + x.what)), 'TRANSP:TRANSPARENT', 'END:VEVENT');
    });
    lines.push('END:VCALENDAR');
    return lines.join('\r\n') + '\r\n';
  }

  tool({ id: 'lexcomply', group: 'compliance', title: 'Which laws apply', href: '../../index.html', meta: 'Opens as a separate page',
    summary: 'Answer six steps about a business and get the Indian laws that apply to it, with the recurring compliances under each and an Excel export.' });

  // ══ WORKBOOKS AND GENERATORS ══
  tool({ id: 'far', group: 'workbooks', title: 'Fixed asset register', href: '../downloads/FAR_Schedule_II.xlsx', download: true, meta: 'Excel workbook',
    summary: 'Schedule II depreciation (SLM or WDV) asset by asset, income-tax block depreciation, deferred tax, the Schedule III PPE note and the CARO clause 3(i) fields.' });
  tool({ id: 'rcm', group: 'workbooks', title: 'Risk control matrix: manufacturing', href: '../downloads/Risk_Control_Matrix_Manufacturing.xlsx', download: true, meta: 'Excel workbook',
    summary: '84 risks and controls across twelve processes of a manufacturing business, each with the audit test, the data it needs and the red flag to look for.' });
  tool({ id: 'forex', group: 'workbooks', title: 'Foreign exchange gain or loss', href: '../downloads/Foreign_Gain_Loss_Workbook.xlsx', download: true, meta: 'Excel workbook',
    summary: 'Realised and unrealised exchange differences on sales and purchases, with part settlements, advances and one receipt settling several invoices.' });
  tool({ id: 'declaration', group: 'workbooks', title: 'Declaration of income', href: 'declaration-of-income.html', meta: 'Opens as a separate page',
    summary: 'Turns a computation of income, uploaded as a PDF or pasted, into a declaration of income for the assessee to sign. The PDF is read in the browser.' });

  // ── FIGURES VIEW ──
  function renderFigures() {
    function slabs(list) {
      var prev = 0;
      return table([{ label: 'Total income' }, { label: 'Rate', num: true }], list.map(function (s) {
        var label = !isFinite(s[0]) ? 'Above ' + R0(prev) : prev === 0 ? 'Up to ' + R0(s[0]) : R0(prev + 1) + ' to ' + R0(s[0]);
        prev = s[0];
        return [label, pc(s[1], 0)];
      }));
    }
    function sur(list) {
      var prev = 0;
      return table([{ label: 'Total income' }, { label: 'Surcharge', num: true }], list.map(function (s) {
        var label = !isFinite(s[0]) ? 'Above ' + R0(prev) : prev === 0 ? 'Up to ' + R0(s[0]) : 'Above ' + R0(prev) + ' up to ' + R0(s[0]);
        prev = s[0];
        return [label, pc(s[1], 0)];
      }));
    }
    function section(title, source, body) { return h('section', { class: 'fig-sec' }, h('h2', null, title), h('p', { class: 'cellnote' }, 'Source: ' + source), body); }
    var I = D.incomeTax, N = I.regimes.newRegime, O = I.regimes.oldRegime, G = D.gst.lateFee, C = D.companies;
    var prevTo = 0;
    return h('div', { class: 'sheet' },
      h('nav', { class: 'crumbs', 'aria-label': 'Breadcrumb' }, h('a', { href: '#' }, 'All tools'), h('span', { 'aria-hidden': 'true' }, '/'), h('span', null, 'Figures')),
      h('header', { class: 'sheet__head' }, h('h1', null, 'Rates and dates used by the tools'),
        h('p', { class: 'sheet__lede' }, 'Every statutory figure the tools use comes from one file, statutory-data.js, listed here with its source. Changing a figure there changes it in every tool.'),
        D.verifiedOn ? h('p', { class: 'figs figs--ok' }, h('span', { class: 'figs__icon', 'aria-hidden': 'true' }, '✓'), 'Checked by the firm on ' + F(S.parseDate(D.verifiedOn)) + (D.verifiedBy ? ' (' + D.verifiedBy + ')' : '') + '.')
          : h('p', { class: 'figs figs--pending' }, h('span', { class: 'figs__icon', 'aria-hidden': 'true' }, '!'), 'Not yet checked by the firm. These figures were compiled from secondary sources and have not been verified against the Act, the rules or the notifications.')),
      h('div', { class: 'figs-grid' },
        section('Income-tax: new regime', I.source, [slabs(N.slabs), table([{ label: 'Item' }, { label: 'Amount', num: true }], [['Standard deduction', R0(N.standardDeduction)], ['Rebate: income up to', R0(N.rebateLimit)], ['Rebate: maximum', R0(N.rebateMax)], ['Cess', pc(I.cess, 0)]], { rowHeads: true }), sur(N.surcharge)]),
        section('Income-tax: old regime', I.source, [h('p', { class: 'subh' }, 'Below 60'), slabs(O.slabsByAge.below60), h('p', { class: 'subh' }, '60 to 79'), slabs(O.slabsByAge.senior), h('p', { class: 'subh' }, '80 or above'), slabs(O.slabsByAge.superSenior),
          table([{ label: 'Item' }, { label: 'Amount', num: true }], [['Standard deduction', R0(O.standardDeduction)], ['Rebate: income up to', R0(O.rebateLimit)], ['Rebate: maximum', R0(O.rebateMax)]], { rowHeads: true }), sur(O.surcharge)]),
        section('Advance tax', D.advanceTax.source, table([{ label: 'Due by' }, { label: 'Cumulative share', num: true }], D.advanceTax.instalments.map(function (x) { return [x[1] + ' ' + ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][x[0]], pc(x[2], 0)]; }), { caption: 'Payable if the tax for the year is ' + R0(D.advanceTax.threshold) + ' or more' })),
        section('TDS', D.tds.source, [table([{ label: 'Nature of payment' }, { label: '1961 Act' }, { label: 'Rate', num: true }, { label: 'Threshold' }], D.tds.rows.map(function (x) { return [x.label, x.old, pc(x.rate, x.rate < 0.01 ? 1 : 0), thresholdText(x)]; })),
          table([{ label: 'Item' }, { label: 'Rate or amount', num: true }], [['Rate without PAN (at least)', pc(D.tds.noPanRate, 0)], ['Interest, late deduction', pc(D.tds.interestLateDeduction, 1) + ' a month'], ['Interest, late deposit', pc(D.tds.interestLateDeposit, 1) + ' a month'], ['Statement late fee', R0(D.tds.lateFeePerDay) + ' a day']], { rowHeads: true })]),
        section('GST', D.gst.source, [table([{ label: 'Item' }, { label: 'Amount', num: true }], [['Interest on tax paid late', pc(D.gst.interestRate, 0) + ' a year'], ['Late fee a day', R0(G.perDay)], ['Late fee a day, nil return', R0(G.perDayNil)], ['Cap, nil return', R0(G.capNil)]], { rowHeads: true }),
          table([{ label: 'Aggregate turnover' }, { label: 'Cap per return', num: true }], G.caps.map(function (c) { var l = !isFinite(c[0]) ? 'Above ' + R0(prevTo) : 'Up to ' + R0(c[0]); prevTo = c[0]; return [l, R0(c[1])]; }), { caption: 'GSTR-1 and GSTR-3B' }),
          table([{ label: 'Turnover' }, { label: 'A day', num: true }, { label: 'Cap', num: true }], G.annual.map(function (c, i) { var lo = i ? G.annual[i - 1][0] : 0; return [!isFinite(c[0]) ? 'Above ' + R0(lo) : 'Up to ' + R0(c[0]), R0(c[1]), pc(c[2], 2) + ' of turnover']; }), { caption: 'GSTR-9' })]),
        section('MSME payments', D.msme.source, table([{ label: 'Item' }, { label: 'Value', num: true }], [['Longest credit period', D.msme.maxCreditDays + ' days'], ['Without a written agreement', D.msme.noAgreementDays + ' days'], ['Interest', D.msme.interestMultiple + ' × RBI bank rate']], { rowHeads: true })),
        section('Company law', C.source, [table([{ label: 'Item' }, { label: 'Period', num: true }], [['AGM from the year end', C.agmMonthsFromYearEnd + ' months'], ['First AGM from the year end', C.firstAgmMonthsFromYearEnd + ' months'], ['ADT-1 from the AGM', C.adt1DaysFromAgm + ' days'], ['AOC-4 from the AGM', C.aoc4DaysFromAgm + ' days'], ['MGT-7 from the AGM', C.mgt7DaysFromAgm + ' days'], ['LLP Form 11 from the year end', C.llpForm11DaysFromYearEnd + ' days'], ['LLP Form 8 after six months from the year end', C.llpForm8DaysAfterSixMonths + ' days']], { rowHeads: true }),
          table([{ label: 'Class of asset (Schedule II)' }, { label: 'Useful life', num: true }], C.usefulLives.map(function (l) { return [l[0], l[1] + ' years']; }))]),
        section('Schedule III', D.scheduleIII.source, table([{ label: 'Item' }, { label: 'Value' }], [['Receivables ageing', D.scheduleIII.receivableBuckets.map(function (b) { return b[0]; }).join('; ')], ['Payables ageing', D.scheduleIII.payableBuckets.map(function (b) { return b[0]; }).join('; ')], ['Ratio change needing explanation', 'Above ' + pc(D.scheduleIII.ratioVarianceFlag, 0)]], { rowHeads: true })),
        section('Audit sampling factors', D.sampling.source, table([{ label: 'Confidence' }, { label: 'Confidence factor', num: true }, { label: 'Expansion factor', num: true }], Object.keys(D.sampling.mus).sort(function (a, b) { return b - a; }).map(function (k) { return [k + '%', D.sampling.mus[k][0].toFixed(2), D.sampling.mus[k][1].toFixed(1)]; }))),
        section('Compliance calendar', D.calendar.source, h('p', { class: 'cellnote' }, D.calendar.monthly.length + ' monthly and ' + D.calendar.fixed.length + ' yearly dates. See the Compliance calendar tool for the full list.'))));
  }

  // ── DIRECTORY ──
  function card(t) {
    var meta = t.meta || (t.figures ? 'Uses statutory rates and dates' : 'Arithmetic only');
    return h('li', null, h('a', { class: 'tcard spot', href: t.href || '#' + t.id, download: t.download ? '' : null },
      h('span', { class: 'tcard__title' }, t.title), h('span', { class: 'tcard__sum' }, t.summary), h('span', { class: 'tcard__meta' }, meta)));
  }
  function renderDirectory() {
    var q = h('input', { type: 'search', id: 'tool-filter', placeholder: 'Filter by name or subject, for example GSTR-2B', autocomplete: 'off', 'aria-label': 'Filter tools' });
    var body = h('div', { class: 'dir' });
    function draw() {
      clear(body);
      var term = q.value.trim().toLowerCase(), shown = 0;
      GROUPS.forEach(function (g) {
        var list = TOOLS.filter(function (t) { return t.group === g[0] && (!term || (t.title + ' ' + t.summary + ' ' + (t.keywords || '')).toLowerCase().indexOf(term) >= 0); });
        if (!list.length) return;
        shown += list.length;
        body.appendChild(h('section', { class: 'dir-group', 'aria-labelledby': 'g-' + g[0] },
          h('h2', { class: 'dir-group__h', id: 'g-' + g[0] }, g[1], h('span', { class: 'dir-count num' }, String(list.length))),
          h('ul', { class: 'dir-grid' }, list.map(card))));
      });
      if (!shown) body.appendChild(note('No tool matches “' + q.value.trim() + '”.'));
    }
    q.addEventListener('input', draw);
    draw();
    var inBrowser = TOOLS.filter(function (t) { return t.build; }).length;
    return h('div', { class: 'directory' },
      h('header', { class: 'dir-head' },
        h('p', { class: 'label' }, 'Tools'),
        h('h1', null, 'Calculators and checkers for audit, tax and compliance work'),
        h('p', { class: 'sheet__lede' }, inBrowser + ' tools that run in the browser, plus the compliance applicability tool and three Excel workbooks. Nothing you enter leaves your device: there is no upload, no account and no tracking.'),
        D.verifiedOn ? h('p', { class: 'figs figs--ok' }, h('span', { class: 'figs__icon', 'aria-hidden': 'true' }, '✓'), 'Statutory figures checked by the firm on ' + F(S.parseDate(D.verifiedOn)) + '. ', h('a', { href: '#figures' }, 'See them with their sources'), '.')
          : h('p', { class: 'figs figs--pending' }, h('span', { class: 'figs__icon', 'aria-hidden': 'true' }, '!'), 'Tools marked “Uses statutory rates and dates” read them from one file the firm has not yet checked against the Act and notifications. ', h('a', { href: '#figures' }, 'See the figures and their sources'), '.'),
        h('div', { class: 'filter' }, q)),
      body);
  }

  // ── TOOL VIEW ──
  // The view is mounted before the tool builds its form, so builders can look up their own fields.
  function renderTool(t, container) {
    var form = h('form', { class: 'sheet-form', novalidate: true, autocomplete: 'off' });
    form.addEventListener('submit', function (e) { e.preventDefault(); });
    var out = h('div', { class: 'sheet-out', 'aria-live': 'polite' });
    var compute;
    var group = GROUPS.filter(function (g) { return g[0] === t.group; })[0];
    var timer = 0;
    function run() {
      clear(out);
      try { compute(); }
      catch (e) {
        if (e instanceof UserError) out.appendChild(note(e.message, 'error'));
        else { out.appendChild(note('These inputs could not be worked out. Check them and try again.', 'error')); if (window.console) console.error(e); }
      }
    }
    var view = h('article', { class: 'sheet' + (t.layout === 'stack' ? ' sheet--stack' : '') },
      h('nav', { class: 'crumbs', 'aria-label': 'Breadcrumb' }, h('a', { href: '#' }, 'All tools'), h('span', { 'aria-hidden': 'true' }, '/'), h('span', null, group ? group[1] : '')),
      h('header', { class: 'sheet__head' }, h('h1', null, t.title), h('p', { class: 'sheet__lede' }, t.summary), t.figures ? figuresNote() : null),
      h('div', { class: 'sheet-grid' },
        h('section', { class: 'pane', 'aria-labelledby': t.id + '-in' }, h('div', { class: 'pane__top' }, h('h2', { class: 'pane__h', id: t.id + '-in' }, 'Inputs'), h('span', { class: 'example' }, 'Example figures: replace them with your own')), form),
        h('section', { class: 'pane pane--out', 'aria-labelledby': t.id + '-out' }, h('h2', { class: 'pane__h', id: t.id + '-out' }, 'Result'), out)),
      t.notes ? h('section', { class: 'sheet__notes', 'aria-labelledby': t.id + '-notes' }, h('h2', { class: 'pane__h', id: t.id + '-notes' }, 'Basis and limits'), h('ul', null, t.notes.map(function (x) { return h('li', null, x); }))) : null);
    container.appendChild(view);
    compute = t.build(form, out);
    form.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 160); });
    form.addEventListener('change', function () { clearTimeout(timer); run(); });
    run();
  }

  // ── ROUTER ──
  var first = true;
  function route() {
    var id = decodeURIComponent((location.hash || '').replace(/^#/, ''));
    var t = TOOLS.filter(function (x) { return x.id === id && x.build; })[0];
    clear(app);
    var title = null;
    if (t) { renderTool(t, app); title = t.title; }
    else if (id === 'figures') { app.appendChild(renderFigures()); title = 'Rates and dates used'; }
    else app.appendChild(renderDirectory());
    document.title = (title ? title + ' · ' : '') + 'Tools · Sagar Khatri & Associates';
    if (!first) {
      window.scrollTo(0, 0);
      var h1 = app.querySelector('h1');
      if (h1) { h1.setAttribute('tabindex', '-1'); h1.focus({ preventScroll: true }); }
    }
    first = false;
  }
  window.addEventListener('hashchange', route);
  route();
})();
