// Sagar Khatri & Associates — firm website behaviour. No dependencies.
(function () {
  'use strict';

  var root = document.documentElement;
  var F = window.FIRM || {};
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $all(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  // ── FIRM PARTICULARS ──
  function formatDate(iso) {
    var d = new Date(iso + 'T00:00:00');
    if (isNaN(d)) return '';
    var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
  }
  function tbd() {
    var s = document.createElement('span');
    s.className = 'tbd';
    s.textContent = 'To be added';
    return s;
  }
  function valueOf(key) {
    var v = F[key];
    if (key === 'lastUpdated') return v ? formatDate(v) : '';
    return v;
  }
  function fillParticulars() {
    $all('[data-firm]').forEach(function (el) {
      var v = valueOf(el.getAttribute('data-firm'));
      var empty = v == null || v === '' || (Array.isArray(v) && !v.length);
      var row = el.closest('[data-optional]');
      if (empty) {
        if (row) row.hidden = true;
        else if (!el.textContent.trim()) { el.textContent = ''; el.appendChild(tbd()); }
        return;
      }
      if (row) row.hidden = false;
      if (Array.isArray(v)) {
        el.textContent = '';
        v.forEach(function (line, i) {
          if (i) el.appendChild(document.createElement('br'));
          el.appendChild(document.createTextNode(line));
        });
      } else {
        el.textContent = v;
      }
    });
    $all('[data-firm-href="mailto"]').forEach(function (el) {
      if (F.email) el.setAttribute('href', 'mailto:' + F.email); else el.removeAttribute('href');
    });

    var phones = $('#phoneList');
    if (phones && Array.isArray(F.phones) && F.phones.length) {
      var wa = String(F.whatsapp || '').replace(/\D/g, '');
      phones.textContent = '';
      F.phones.forEach(function (num) {
        var digits = String(num).replace(/\D/g, '');
        var a = document.createElement('a');
        a.className = 'plain num';
        a.href = 'tel:+' + digits;
        a.textContent = num;
        phones.appendChild(a);
        if (wa && digits === wa) {
          var w = document.createElement('a');
          w.className = 'chip';
          w.href = 'https://wa.me/' + wa;
          w.target = '_blank'; w.rel = 'noopener';
          w.textContent = 'WhatsApp';
          phones.appendChild(w);
        }
      });
    }

    var map = $('#mapLink');
    if (map) {
      if (F.mapQuery) map.href = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(F.mapQuery);
      else map.hidden = true;
    }
    var y = $('#year');
    if (y) y.textContent = String(new Date().getFullYear());
  }

  function ledgerRow(dl, label, value) {
    if (!value) return;
    var row = document.createElement('div');
    var dt = document.createElement('dt');
    var dd = document.createElement('dd');
    dt.textContent = label;
    dd.textContent = value;
    row.appendChild(dt); row.appendChild(dd); dl.appendChild(row);
  }
  function renderPeople() {
    var grid = $('#peopleGrid');
    if (!grid || !Array.isArray(F.people) || !F.people.length) return;
    grid.textContent = '';
    F.people.forEach(function (p) {
      var card = document.createElement('article');
      card.className = 'person spot';

      var photo = document.createElement('div');
      photo.className = 'person__photo';
      if (p.photo) {
        var img = document.createElement('img');
        img.src = p.photo; img.alt = p.name || ''; img.loading = 'lazy';
        photo.classList.add('has-img');
        photo.appendChild(img);
      } else {
        var ph = document.createElement('span');
        ph.textContent = 'Passport-size photograph';
        photo.appendChild(ph);
      }

      var body = document.createElement('div');
      body.className = 'person__body';
      var h = document.createElement('h3');
      h.textContent = p.name || '';
      body.appendChild(h);
      if (p.role) {
        var role = document.createElement('p');
        role.className = 'person__role';
        role.textContent = p.role;
        body.appendChild(role);
      }

      var dl = document.createElement('dl');
      dl.className = 'ledger ledger--plain';
      ledgerRow(dl, 'ICAI membership no.', p.membershipNo);
      ledgerRow(dl, 'Qualifications', p.qualifications);
      ledgerRow(dl, 'Member since', p.memberSince);
      ledgerRow(dl, 'Areas of work', p.areas);
      body.appendChild(dl);

      card.appendChild(photo); card.appendChild(body);
      grid.appendChild(card);
    });
  }

  // ── COPY BUTTONS ──
  function initCopy() {
    $all('[data-copy]').forEach(function (btn) {
      var text = F[btn.getAttribute('data-copy')];
      if (!text) { btn.hidden = true; return; }
      btn.addEventListener('click', function () {
        function done() {
          btn.textContent = 'Copied';
          setTimeout(function () { btn.textContent = 'Copy'; }, 1600);
        }
        function selectInstead() {
          var target = btn.previousElementSibling;
          if (!target) return;
          var range = document.createRange();
          range.selectNodeContents(target);
          var sel = window.getSelection();
          sel.removeAllRanges(); sel.addRange(range);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, selectInstead);
        } else {
          selectInstead();
        }
      });
    });
  }

  // ── THEME ──
  function currentTheme() {
    var set = root.getAttribute('data-theme');
    if (set === 'light' || set === 'dark') return set;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  function initTheme(onChange) {
    var btn = $('#themeToggle');
    function label() {
      if (btn) btn.setAttribute('aria-label', 'Switch to ' + (currentTheme() === 'dark' ? 'light' : 'dark') + ' theme');
    }
    label();
    if (btn) btn.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('ska-theme', next); } catch (e) { /* storage unavailable */ }
    });
    // Covers the toggle, a host-set data-theme, and an OS theme change.
    new MutationObserver(function () { label(); onChange(); }).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    var mq = window.matchMedia('(prefers-color-scheme: light)');
    var osChange = function () { label(); onChange(); };
    if (mq.addEventListener) mq.addEventListener('change', osChange); else if (mq.addListener) mq.addListener(osChange);
  }

  // ── HEADER: mobile menu, stuck state, current section ──
  function initHeader() {
    var head = $('#siteHead'), nav = $('#nav'), menu = $('#menuToggle');
    function closeMenu() {
      if (!nav) return;
      nav.classList.remove('is-open');
      if (menu) menu.setAttribute('aria-expanded', 'false');
    }
    if (menu && nav) {
      menu.addEventListener('click', function () {
        var open = nav.classList.toggle('is-open');
        menu.setAttribute('aria-expanded', String(open));
      });
      nav.addEventListener('click', function (e) { if (e.target.closest('a')) closeMenu(); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
    }
    function stuck() { if (head) head.classList.toggle('is-stuck', window.scrollY > 8); }
    stuck();
    window.addEventListener('scroll', stuck, { passive: true });

    if (!('IntersectionObserver' in window) || !nav) return;
    var links = {};
    $all('a[href^="#"]', nav).forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = links[en.target.id];
        if (!a || !en.isIntersecting) return;
        Object.keys(links).forEach(function (k) { links[k].removeAttribute('aria-current'); });
        a.setAttribute('aria-current', 'true');
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    Object.keys(links).forEach(function (id) {
      var sec = document.getElementById(id);
      if (sec) io.observe(sec);
    });
  }

  // ── PRACTICE AREAS: tabs. Detail is shown for the area the visitor selects. ──
  function initTabs() {
    var wrap = $('#practiceTabs');
    if (!wrap) return;
    var tabs = $all('[role="tab"]', wrap);
    var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute('aria-controls')); });
    function select(i, focus) {
      tabs.forEach(function (t, n) {
        var on = n === i;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        if (panels[n]) panels[n].hidden = !on;
      });
      if (focus) tabs[i].focus();
      if (tabs[i].scrollIntoView && window.innerWidth < 900) {
        tabs[i].scrollIntoView({ block: 'nearest', inline: 'center', behavior: reduceMotion.matches ? 'auto' : 'smooth' });
      }
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(i, false); });
      t.addEventListener('keydown', function (e) {
        var n = -1;
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') n = (i + 1) % tabs.length;
        else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') n = (i - 1 + tabs.length) % tabs.length;
        else if (e.key === 'Home') n = 0;
        else if (e.key === 'End') n = tabs.length - 1;
        if (n < 0) return;
        e.preventDefault();
        select(n, true);
      });
    });
    panels.forEach(function (p, n) { if (p) p.hidden = n !== 0; });
  }

  // ── FIRST-VISIT NOTICE ──
  function initNotice() {
    var dlg = $('#notice'), ok = $('#noticeAccept');
    var KEY = 'ska-notice-v1';
    if (!dlg || !ok || typeof dlg.showModal !== 'function') return;
    var seen = false;
    try { seen = localStorage.getItem(KEY) === '1'; } catch (e) { /* storage unavailable */ }
    if (seen) return;
    dlg.addEventListener('cancel', function (e) { e.preventDefault(); });
    ok.addEventListener('click', function () {
      try { localStorage.setItem(KEY, '1'); } catch (e) { /* storage unavailable */ }
      dlg.close();
    });
    dlg.showModal();
  }

  // ── THE PLATE ──
  // A guilloche field — the interlaced wave bands engraved on share certificates
  // and stamp paper. It is drawn faint; the pointer acts as a lamp that brings the
  // engraving up and a lens that bends it. Without a pointer the lamp wanders.
  function initPlate() {
    var canvas = $('#engraving'), lamp = $('#lamp');
    if (!canvas || !canvas.getContext) return { refresh: function () {} };
    var ctx = canvas.getContext('2d');
    var W = 0, H = 0;
    var inks = ['#d9b65c', '#5a86d6'], base = 0.2;
    var p = { x: 0, y: 0, tx: 0, ty: 0 };
    var lastMove = -1e9, raf = 0, placed = false;
    var t0 = performance.now();

    function readInks() {
      var cs = getComputedStyle(root);
      var a = cs.getPropertyValue('--ink-a').trim(), b = cs.getPropertyValue('--ink-b').trim();
      if (a && b) inks = [a, b];
      var al = parseFloat(cs.getPropertyValue('--plate-alpha'));
      if (!isNaN(al)) base = al;
    }
    function size() {
      var dpr = Math.min(window.devicePixelRatio || 1, 1.75);
      W = window.innerWidth; H = window.innerHeight;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (!placed) { p.x = p.tx = W * 0.72; p.y = p.ty = H * 0.32; placed = true; }
    }
    function draw(now) {
      var t = (now - t0) / 1000;
      var still = reduceMotion.matches;
      if (still) t = 0;
      else if (now - lastMove > 2600) {
        p.tx = W * (0.5 + 0.34 * Math.sin(t * 0.21 + 0.7));
        p.ty = H * (0.42 + 0.26 * Math.sin(t * 0.29 + 5.4));
      }
      p.x += (p.tx - p.x) * (still ? 1 : 0.085);
      p.y += (p.ty - p.y) * (still ? 1 : 0.085);

      var narrow = W < 720;
      var band = narrow ? 58 : 78;
      var strands = narrow ? 5 : 7;
      var step = W * H > 3.2e6 ? 9 : (narrow ? 7 : 6);
      var shift = (window.scrollY || 0) * 0.18;     // the plate moves slower than the page
      var first = Math.floor(shift / band);
      var off = -(shift - first * band);
      var rows = Math.ceil(H / band) + 2;
      var R = Math.max(150, Math.min(W, H) * 0.24), R2 = 2 * R * R, reach = R * 2.7;
      var amp = band * 0.56, TAU = Math.PI * 2;

      ctx.globalCompositeOperation = 'source-over';
      ctx.clearRect(0, 0, W, H);
      ctx.lineWidth = 0.75;
      for (var r = -1; r < rows; r++) {
        var id = r + first;
        var odd = ((id % 2) + 2) % 2;
        var yc = r * band + off + band / 2;
        var k = (odd ? 0.0105 : 0.0082) * (narrow ? 1.5 : 1);
        var dir = odd ? -1 : 1;
        ctx.strokeStyle = inks[odd];
        ctx.globalAlpha = odd ? 0.5 : 0.62;
        for (var s = 0; s < strands; s++) {
          var ph = s * (TAU / strands) + dir * t * 0.22 + id * 0.9;
          ctx.beginPath();
          for (var x = -step; x <= W + step; x += step) {
            var env = 0.78 + 0.22 * Math.sin(x * 0.0031 + id * 1.7 + t * 0.11);
            var y = yc + amp * env * Math.sin(x * k + ph);
            var dx = x - p.x;
            if (dx < reach && dx > -reach) {
              var dy = y - p.y;
              if (dy < reach && dy > -reach) y += dy * Math.exp(-(dx * dx + dy * dy) / R2) * 0.62;
            }
            if (x === -step) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          }
          ctx.stroke();
        }
      }

      // The lamp: keep only a fraction of the plate away from the pointer.
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'destination-in';
      var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, Math.max(W, H) * 0.5);
      g.addColorStop(0, 'rgba(0,0,0,.9)');
      g.addColorStop(0.32, 'rgba(0,0,0,.5)');
      g.addColorStop(1, 'rgba(0,0,0,' + base + ')');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'source-over';

      if (lamp) lamp.style.transform = 'translate3d(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px,0)';
    }
    function loop(now) {
      draw(now);
      raf = requestAnimationFrame(loop);
    }
    function start() {
      cancelAnimationFrame(raf);
      raf = 0;
      if (reduceMotion.matches || document.hidden) { draw(performance.now()); return; }
      raf = requestAnimationFrame(loop);
    }
    function point(x, y) { p.tx = x; p.ty = y; lastMove = performance.now(); }

    window.addEventListener('pointermove', function (e) { point(e.clientX, e.clientY); }, { passive: true });
    window.addEventListener('touchmove', function (e) {
      if (e.touches && e.touches[0]) point(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });
    window.addEventListener('resize', function () { size(); if (!raf) draw(performance.now()); });
    window.addEventListener('scroll', function () { if (!raf) draw(performance.now()); }, { passive: true });
    document.addEventListener('visibilitychange', start);
    if (reduceMotion.addEventListener) reduceMotion.addEventListener('change', start);

    readInks(); size(); start();
    return { refresh: function () { readInks(); if (!raf) draw(performance.now()); } };
  }

  // ── LIT SURFACES AND TILT ──
  function initLight() {
    if (!finePointer.matches) return;
    var card = $('#particulars'), hero = $('.hero');
    document.addEventListener('pointermove', function (e) {
      var spot = e.target.closest ? e.target.closest('.spot') : null;
      if (spot) {
        var r = spot.getBoundingClientRect();
        spot.style.setProperty('--sx', (e.clientX - r.left) + 'px');
        spot.style.setProperty('--sy', (e.clientY - r.top) + 'px');
      }
      if (card && hero && !reduceMotion.matches) {
        var h = hero.getBoundingClientRect();
        if (e.clientY < h.bottom) {
          var c = card.getBoundingClientRect();
          var nx = (e.clientX - (c.left + c.width / 2)) / window.innerWidth;
          var ny = (e.clientY - (c.top + c.height / 2)) / window.innerHeight;
          card.style.setProperty('--ry', (nx * 10).toFixed(2) + 'deg');
          card.style.setProperty('--rx', (-ny * 8).toFixed(2) + 'deg');
        } else {
          card.style.setProperty('--ry', '0deg');
          card.style.setProperty('--rx', '0deg');
        }
      }
    }, { passive: true });
  }

  fillParticulars();
  renderPeople();
  initCopy();
  initHeader();
  initTabs();
  var plate = initPlate();
  initTheme(plate.refresh);
  initLight();
  initNotice();
})();
