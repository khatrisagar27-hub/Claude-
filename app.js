// ── FIRM CONFIGURATION ──
const FIRM_CONFIG = {
  name: 'Sagar Khatri & Associates, Chartered Accountants',
  shortName: 'SK & Associates, CA',
  email: 'khatrisagar27@gmail.com',
  whatsapp: '919000000000', // update with actual WhatsApp number (country code + number, no +)
  tagline: 'Expert Compliance | Audit | Advisory | Tax | Business Consulting'
};

// ── INDIAN STATES DATA ──
const INDIAN_STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka',
  'Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram',
  'Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana',
  'Tripura','Uttar Pradesh','Uttarakhand','West Bengal',
  'Delhi (NCT)','Jammu & Kashmir','Ladakh','Puducherry','Chandigarh',
  'Dadra & Nagar Haveli','Lakshadweep','Andaman & Nicobar'
];

const STEPS = [
  {num:1,label:'Company'},
  {num:2,label:'Business'},
  {num:3,label:'Finance'},
  {num:4,label:'Workforce'},
  {num:5,label:'Premises'},
  {num:6,label:'Tech & Data'}
];

let currentStep = 1;
let formData = {};
let allResults = [];
let activeFilter = 'all';
let searchTimer = null;

// ── INIT ──
function initApp() {
  buildProgress();
  populateStatesGrid();
  populateStateSelect();
  updateProgress();
  initBackToTop();
}

function buildProgress() {
  const stepsEl = document.getElementById('progressSteps');
  const labelsEl = document.getElementById('progressLabels');
  const frag = document.createDocumentFragment();
  const fragL = document.createDocumentFragment();
  STEPS.forEach(s => {
    const dot = document.createElement('div');
    dot.className = 'step-dot' + (s.num === 1 ? ' active' : '');
    dot.id = `dot-${s.num}`;
    dot.textContent = s.num;
    frag.appendChild(dot);

    const lbl = document.createElement('div');
    lbl.className = 'progress-label' + (s.num === 1 ? ' active' : '');
    lbl.id = `lbl-${s.num}`;
    lbl.textContent = s.label;
    fragL.appendChild(lbl);
  });
  stepsEl.appendChild(frag);
  labelsEl.appendChild(fragL);
}

function populateStatesGrid() {
  const grid = document.getElementById('statesGrid');
  const frag = document.createDocumentFragment();
  INDIAN_STATES.forEach(state => {
    const chip = document.createElement('label');
    chip.className = 'state-chip';
    chip.dataset.state = state;
    chip.innerHTML = `<input type="checkbox" value="${state}" onchange="toggleStateChip(this)"> ${state}`;
    frag.appendChild(chip);
  });
  grid.appendChild(frag);
}

function toggleStateChip(cb) {
  cb.closest('.state-chip').classList.toggle('checked', cb.checked);
}

function populateStateSelect() {
  const sel = document.getElementById('stateOfReg');
  const frag = document.createDocumentFragment();
  INDIAN_STATES.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s; opt.textContent = s;
    frag.appendChild(opt);
  });
  sel.appendChild(frag);
}

function initBackToTop() {
  const btn = document.getElementById('backTop');
  if (!btn) return;
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
}

function updateProgress() {
  const fill = document.getElementById('progressFill');
  const pct = ((currentStep - 1) / (STEPS.length - 1)) * 100;
  fill.style.width = pct + '%';
  STEPS.forEach(s => {
    const dot = document.getElementById(`dot-${s.num}`);
    const lbl = document.getElementById(`lbl-${s.num}`);
    dot.className = 'step-dot' + (s.num < currentStep ? ' done' : s.num === currentStep ? ' active' : '');
    lbl.className = 'progress-label' + (s.num === currentStep ? ' active' : '');
  });
}

// ── NAVIGATION ──
function startTool() {
  document.getElementById('landing').style.display = 'none';
  document.getElementById('form-section').style.display = 'block';
  window.scrollTo(0,0);
}

function resetTool() {
  currentStep = 1;
  formData = {};
  allResults = [];
  activeFilter = 'all';
  document.getElementById('results').style.display = 'none';
  document.getElementById('landing').style.display = 'flex';
  document.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = false);
  document.querySelectorAll('input[type=radio]').forEach(r => r.checked = false);
  document.querySelectorAll('.radio-pill').forEach(p => p.classList.remove('selected'));
  document.querySelectorAll('.state-chip').forEach(c => c.classList.remove('checked'));
  document.querySelectorAll('.conditional').forEach(c => c.classList.remove('show'));
  document.querySelectorAll('input[type=text],input[type=number],input[type=tel],input[type=email],select').forEach(i => i.value='');
  const sb = document.getElementById('searchBox');
  if (sb) sb.value = '';
  // Reset form-section state without showing it
  document.getElementById('form-section').style.display = 'none';
  currentStep = 1;
  document.querySelectorAll('.form-step').forEach((s,i) => {
    s.classList.toggle('active', i === 0);
  });
  updateProgress();
  window.scrollTo(0,0);
}

function showStep(n) {
  document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
  document.getElementById(`step-${n}`).classList.add('active');
  currentStep = n;
  updateProgress();
  window.scrollTo(0,0);
}

function nextStep(from) {
  if (!validateStep(from)) return;
  showStep(from + 1);
}

function prevStep(from) {
  showStep(from - 1);
}

function toggleCond(id, show) {
  document.getElementById(id).classList.toggle('show', show);
}

function selectPill(el, name, value) {
  const group = el.closest('.radio-group') || el.parentElement;
  group.querySelectorAll('.radio-pill').forEach(p => p.classList.remove('selected'));
  el.classList.add('selected');
  el.querySelector('input').checked = true;
}

// ── VALIDATION ──
function validateStep(step) {
  if (step === 1) {
    if (!document.getElementById('contactName').value.trim()) {
      alert('Please enter your name (contact person).'); return false;
    }
    const mobile = document.getElementById('mobileNumber').value.trim();
    if (!mobile || !/^[6-9]\d{9}$/.test(mobile)) {
      alert('Please enter a valid 10-digit Indian mobile number (starting with 6–9).'); return false;
    }
    const email = document.getElementById('emailAddress').value.trim();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      alert('Please enter a valid email address.'); return false;
    }
    if (!document.getElementById('companyName').value.trim()) {
      alert('Please enter the company name.'); return false;
    }
    if (!document.getElementById('entityType').value) {
      alert('Please select the entity type.'); return false;
    }
    if (!document.getElementById('stateOfReg').value) {
      alert('Please select state of registration.'); return false;
    }
    if (getCheckedStates().length === 0) {
      alert('Please select at least one state of operation.'); return false;
    }
  }
  if (step === 2) {
    if (!document.getElementById('primarySector').value) {
      alert('Please select the primary business sector.'); return false;
    }
  }
  if (step === 3) {
    if (!document.getElementById('annualTurnover').value) {
      alert('Please select the annual turnover range.'); return false;
    }
  }
  if (step === 4) {
    const emp = document.getElementById('totalEmployees').value;
    if (emp === '' || isNaN(emp)) {
      alert('Please enter the total number of employees.'); return false;
    }
  }
  return true;
}

function getCheckedStates() {
  return Array.from(document.querySelectorAll('#statesGrid input:checked')).map(cb => cb.value);
}

function getRadioVal(name) {
  const r = document.querySelector(`input[name="${name}"]:checked`);
  return r ? r.value : 'no';
}

function safeCheckbox(id) {
  const el = document.getElementById(id);
  return el ? el.checked : false;
}

// ── COLLECT FORM DATA ──
function collectFormData() {
  const totalEmployees     = parseInt(document.getElementById('totalEmployees').value) || 0;
  const contractWorkers    = parseInt(document.getElementById('contractWorkers').value) || 0;
  const womenEmployees     = parseInt(document.getElementById('womenEmployees').value) || 0;
  const migrantWorkers     = parseInt(document.getElementById('migrantWorkers').value) || 0;
  const permanentEmployees = parseInt(document.getElementById('permanentEmployees').value) || 0;
  const pwdEmployees       = parseInt(document.getElementById('pwdEmployees').value) || 0;
  const factoryWorkers     = parseInt(document.getElementById('factoryWorkers').value) || 0;
  const annualTurnover     = parseInt(document.getElementById('annualTurnover').value) || 0;
  const netWorth           = parseInt(document.getElementById('netWorth').value) || 0;
  const netProfit          = parseInt(document.getElementById('netProfit').value) || 0;
  const paidUpCapital      = parseInt(document.getElementById('paidUpCapital').value) || 0;
  const sector             = document.getElementById('primarySector').value;

  formData = {
    contactName:     document.getElementById('contactName').value.trim(),
    mobileNumber:    document.getElementById('mobileNumber').value.trim(),
    emailAddress:    document.getElementById('emailAddress').value.trim(),
    companyName:     document.getElementById('companyName').value.trim(),
    entityType:      document.getElementById('entityType').value,
    stateOfReg:      document.getElementById('stateOfReg').value,
    statesOfOperation: getCheckedStates(),
    isListed:        getRadioVal('isListed') === 'yes',

    primarySector:   sector,
    isManufacturing: safeCheckbox('isManufacturing'),
    isTrading:       safeCheckbox('isTrading'),
    isECommerce:     safeCheckbox('isECommerce') || sector === 'ecommerce',
    dealsFoodBeverages: safeCheckbox('dealsFoodBeverages'),
    dealsPharma:     safeCheckbox('dealsPharma'),
    dealsPetroleum:  safeCheckbox('dealsPetroleum'),
    dealsExplosives: safeCheckbox('dealsExplosives'),
    dealsChemicals:  safeCheckbox('dealsChemicals'),
    hasBoilers:      safeCheckbox('hasBoilers'),
    hasMines:        safeCheckbox('hasMines'),
    hasConstruction: safeCheckbox('hasConstruction'),
    isRealEstate:    safeCheckbox('isRealEstate'),
    isNBFC:          safeCheckbox('isNBFC'),
    isInsurance:     safeCheckbox('isInsurance'),
    isBanking:       safeCheckbox('isBanking'),
    // New fields
    isHealthcare:    safeCheckbox('isHealthcare'),
    hasVehicleFleet: safeCheckbox('hasVehicleFleet'),
    isDigitalPlatform: safeCheckbox('isDigitalPlatform'),

    annualTurnover, netWorth, netProfit, paidUpCapital,
    hasFDI:          getRadioVal('hasFDI') === 'yes',
    doesImportExport: getRadioVal('doesImportExport') === 'yes',
    isMSME:          getRadioVal('isMSME') === 'yes',
    hasForex:        getRadioVal('hasForex') === 'yes',

    totalEmployees, permanentEmployees, contractWorkers,
    womenEmployees, migrantWorkers, pwdEmployees,
    hasApprentices:  getRadioVal('hasApprentices') === 'yes',
    employsMinors:   getRadioVal('employsMinors') === 'yes',

    hasFactory:      getRadioVal('hasFactory') === 'yes',
    factoryHasPower: getRadioVal('factoryHasPower') === 'yes',
    factoryWorkers,
    hasShop:         getRadioVal('hasShop') === 'yes',
    generatesHazardousWaste: safeCheckbox('generatesHazardousWaste'),
    generatesEWaste:         safeCheckbox('generatesEWaste'),
    usesPlastic:             safeCheckbox('usesPlastic'),
    dischargesWastewater:    safeCheckbox('dischargesWastewater'),
    emitsAirPollutants:      safeCheckbox('emitsAirPollutants'),
    hasLargeElectrical:      safeCheckbox('hasLargeElectrical'),

    hasWeb:           getRadioVal('hasWeb') === 'yes',
    collectsData:     getRadioVal('collectsData') === 'yes',
    hasPayment:       getRadioVal('hasPayment') === 'yes',
    isITService:      getRadioVal('isITService') === 'yes',
    isPMLA:           getRadioVal('isPMLA') === 'yes',
    hasIP:            getRadioVal('hasIP') === 'yes',
    receivesForeignContrib: getRadioVal('receivesForeignContrib') === 'yes',
  };

  // Derived flags
  formData.isITSector = sector === 'it' || formData.isITService;
  formData.isFinancialSector = ['financial','nbfc','insurance'].includes(sector) ||
    formData.isNBFC || formData.isBanking || formData.isInsurance;
}

// ── ANALYZE ──
function analyzeCompliance() {
  collectFormData();
  document.getElementById('form-section').style.display = 'none';
  document.getElementById('loading').style.display = 'flex';

  setTimeout(() => {
    allResults = INDIAN_LAWS
      .map(law => ({ ...law, applicableReason: law.reason(formData) }))
      .filter(law => law.applicableReason != null);

    document.getElementById('loading').style.display = 'none';
    renderResults();
    document.getElementById('results').style.display = 'block';
    window.scrollTo(0,0);
  }, 1200);
}

// ── RENDER RESULTS ──
const PRIORITY_ORDER = { critical:0, high:1, medium:2, low:3 };
const PRIORITY_LABEL = { critical:'CRITICAL', high:'HIGH', medium:'MEDIUM', low:'LOW' };

function renderResults() {
  const co = formData.companyName || 'Your Company';
  document.getElementById('resultsCompanyTag').textContent = `📋 ${co}`;

  const counts = { critical:0, high:0, medium:0, low:0 };
  allResults.forEach(l => { counts[l.priority] = (counts[l.priority]||0) + 1; });

  const totalActions = allResults.reduce((s, l) => s + l.actions.length, 0);

  document.getElementById('resultsSubtitle').textContent =
    `${allResults.length} laws apply to ${co} across ${Object.keys(counts).filter(k=>counts[k]).length} priority levels. ${totalActions} compliance actions identified.`;

  // Summary cards
  document.getElementById('summaryGrid').innerHTML = `
    <div class="summary-card total"><div class="s-num">${allResults.length}</div><div class="s-label">Total Laws</div></div>
    <div class="summary-card critical"><div class="s-num">${counts.critical||0}</div><div class="s-label">Critical</div></div>
    <div class="summary-card high"><div class="s-num">${counts.high||0}</div><div class="s-label">High Priority</div></div>
    <div class="summary-card medium"><div class="s-num">${counts.medium||0}</div><div class="s-label">Medium</div></div>
    <div class="summary-card low"><div class="s-num">${counts.low||0}</div><div class="s-label">Low Priority</div></div>
  `;

  // Client info bar
  const cib = document.getElementById('clientInfoBar');
  if (cib) {
    cib.innerHTML = `
      <div class="cib-item"><span class="cib-label">Contact</span><strong>${xe(formData.contactName || '—')}</strong></div>
      <div class="cib-item"><span class="cib-label">Mobile</span><strong>${xe(formData.mobileNumber || '—')}</strong></div>
      <div class="cib-item"><span class="cib-label">Email</span><strong>${xe(formData.emailAddress || '—')}</strong></div>
      <div class="cib-item"><span class="cib-label">Company</span><strong>${xe(formData.companyName || '—')}</strong></div>
      <div class="cib-item"><span class="cib-label">Date</span><strong>${new Date().toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</strong></div>`;
  }

  // Meta bar
  const mb = document.getElementById('resultsMetaBar');
  if (mb) {
    mb.innerHTML = `<span>Generated: <strong>${new Date().toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</strong></span>
    <span>Total compliance actions: <strong>${totalActions}</strong></span>
    <span style="color:var(--danger)">Critical actions needing immediate attention: <strong>${allResults.filter(l=>l.priority==='critical').reduce((s,l)=>s+l.actions.length,0)}</strong></span>`;
  }

  // Update filter button counts
  updateFilterCounts(counts);

  renderFilteredLaws(allResults);
}

function updateFilterCounts(counts) {
  const map = { fbAll: allResults.length, fbCrit: counts.critical||0, fbHigh: counts.high||0, fbMed: counts.medium||0, fbLow: counts.low||0 };
  Object.entries(map).forEach(([id, n]) => {
    const el = document.getElementById(id);
    if (el) { const badge = el.querySelector('.f-count'); if(badge) badge.textContent = n; }
  });
}

function renderFilteredLaws(laws) {
  const out = document.getElementById('lawsOutput');
  if (!laws.length) {
    out.innerHTML = '<div class="no-results">No laws match the current filter.</div>';
    return;
  }

  // Sort by priority, then group by category
  const byCategory = {};
  [...laws].sort((a,b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
    .forEach(l => {
      (byCategory[l.category] = byCategory[l.category] || []).push(l);
    });

  const frag = document.createDocumentFragment();
  Object.entries(byCategory).forEach(([cat, catLaws]) => {
    const section = document.createElement('div');
    section.className = 'cat-section';
    section.innerHTML = `
      <div class="cat-label-row" data-cat="${cat}">
        <div class="cat-label">${cat}</div>
        <div class="cat-line"></div>
        <div class="cat-count">${catLaws.length} law${catLaws.length>1?'s':''}</div>
      </div>
      <div class="laws-grid">${catLaws.map(buildLawCard).join('')}</div>`;
    frag.appendChild(section);
  });

  out.innerHTML = '';
  out.appendChild(frag);
}

function buildLawCard(law) {
  const actionsHtml = law.actions.map(a => `
    <div class="action-item">
      <div class="action-title">${a.title}</div>
      <div class="action-meta">
        <span class="action-tag freq">⏱ ${a.freq}</span>
        <span class="action-tag dead">📅 ${a.deadline}</span>
        <span class="action-tag auth">🏛 ${a.authority}</span>
        <span class="action-tag pen">⚠ ${a.penalty}</span>
      </div>
      ${a.desc ? `<div class="action-desc">${a.desc}</div>` : ''}
    </div>`).join('');

  return `
    <div class="law-card" id="law-${law.id}" data-priority="${law.priority}">
      <div class="law-header" onclick="toggleLaw('${law.id}')">
        <div class="law-priority ${law.priority}"></div>
        <div class="law-meta">
          <div class="law-name">${law.name}<span class="law-cat">${law.category}</span></div>
          <div class="law-reason">✓ ${law.applicableReason}</div>
        </div>
        <span class="law-actions-count">${law.actions.length} action${law.actions.length>1?'s':''}</span>
        <div class="law-badge ${law.priority}">${PRIORITY_LABEL[law.priority]}</div>
        <div class="expand-icon">▼</div>
      </div>
      <div class="law-body">
        <div class="law-desc">${law.description}</div>
        <div class="compliance-title">COMPLIANCE ACTIONS REQUIRED (${law.actions.length})</div>
        <div class="actions-list">${actionsHtml}</div>
      </div>
    </div>`;
}

function toggleLaw(id) {
  document.getElementById(`law-${id}`).classList.toggle('expanded');
}

// ── EXPAND / COLLAPSE ALL ──
function expandAllLaws() {
  document.querySelectorAll('.law-card:not(.expanded)').forEach(c => c.classList.add('expanded'));
  showToast('All laws expanded');
}

function collapseAllLaws() {
  document.querySelectorAll('.law-card.expanded').forEach(c => c.classList.remove('expanded'));
  showToast('All laws collapsed');
}

// ── TOAST ──
function showToast(msg, ms = 2000) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), ms);
}

// ── FILTER ──
function filterLaws(priority, btn) {
  activeFilter = priority;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  applyFilters();
}

// ── DEBOUNCED SEARCH ──
function searchLaws(query) {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => applyFilters(query), 250);
}

function applyFilters(query) {
  const sb = document.getElementById('searchBox');
  const q = (query !== undefined ? query : (sb ? sb.value : '')).toLowerCase().trim();
  let filtered = allResults;
  if (activeFilter !== 'all') filtered = filtered.filter(l => l.priority === activeFilter);
  if (q) filtered = filtered.filter(l =>
    l.name.toLowerCase().includes(q) ||
    l.category.toLowerCase().includes(q) ||
    l.description.toLowerCase().includes(q) ||
    l.applicableReason.toLowerCase().includes(q)
  );
  renderFilteredLaws(filtered);
}

// ── HTML ESCAPE ──
function xe(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── LEAD CAPTURE — WHATSAPP ──
function sendToWhatsApp() {
  const fd = formData;
  const lawsCount = allResults.length;
  const critCount = allResults.filter(l=>l.priority==='critical').length;
  const highCount = allResults.filter(l=>l.priority==='high').length;
  const totalActions = allResults.reduce((s,l)=>s+l.actions.length,0);

  const msg = [
    `Hello ${FIRM_CONFIG.name},`,
    ``,
    `I have used your Indian Law Compliance Tool and would like professional assistance.`,
    ``,
    `*My Details:*`,
    `Name: ${fd.contactName}`,
    `Mobile: ${fd.mobileNumber}`,
    `Email: ${fd.emailAddress}`,
    ``,
    `*Company Profile:*`,
    `Company: ${fd.companyName}`,
    `Entity: ${fd.entityType || '—'}`,
    `Sector: ${fd.primarySector || '—'}`,
    `State of Reg: ${fd.stateOfReg || '—'}`,
    `Employees: ${fd.totalEmployees}`,
    `Annual Turnover: ${fd.annualTurnover ? '₹'+fd.annualTurnover+' L' : '—'}`,
    ``,
    `*Compliance Summary:*`,
    `Total Applicable Laws: ${lawsCount}`,
    `Critical Priority: ${critCount}`,
    `High Priority: ${highCount}`,
    `Total Actions Required: ${totalActions}`,
    ``,
    `Please contact me to discuss compliance requirements.`
  ].join('\n');

  const url = `https://wa.me/${FIRM_CONFIG.whatsapp}?text=${encodeURIComponent(msg)}`;
  window.open(url, '_blank');
}

// ── LEAD CAPTURE — EMAIL ──
function sendToEmail() {
  const fd = formData;
  const lawsCount = allResults.length;
  const critCount = allResults.filter(l=>l.priority==='critical').length;
  const highCount = allResults.filter(l=>l.priority==='high').length;
  const totalActions = allResults.reduce((s,l)=>s+l.actions.length,0);

  const subject = `Compliance Inquiry — ${fd.companyName} | Indian Law Compliance Tool`;

  const topLaws = allResults
    .filter(l=>l.priority==='critical')
    .slice(0,5)
    .map(l=>`  • ${l.shortName || l.name}`)
    .join('\n');

  const body = [
    `Dear ${FIRM_CONFIG.name},`,
    ``,
    `I have used your Indian Law Compliance Tool and would like professional assistance with implementing the identified compliance requirements.`,
    ``,
    `CONTACT DETAILS`,
    `Name: ${fd.contactName}`,
    `Mobile: ${fd.mobileNumber}`,
    `Email: ${fd.emailAddress}`,
    ``,
    `COMPANY PROFILE`,
    `Company Name: ${fd.companyName}`,
    `Entity Type: ${fd.entityType || '—'}`,
    `Primary Sector: ${fd.primarySector || '—'}`,
    `State of Registration: ${fd.stateOfReg || '—'}`,
    `States of Operation: ${(fd.statesOfOperation||[]).join(', ') || '—'}`,
    `Total Employees: ${fd.totalEmployees}`,
    `Annual Turnover: ${fd.annualTurnover ? '₹'+fd.annualTurnover+' Lakhs' : '—'}`,
    `Listed Company: ${fd.isListed ? 'Yes' : 'No'}`,
    `MSME Registered: ${fd.isMSME ? 'Yes' : 'No'}`,
    ``,
    `COMPLIANCE SUMMARY`,
    `Total Applicable Laws: ${lawsCount}`,
    `Critical Priority: ${critCount}`,
    `High Priority: ${highCount}`,
    `Total Compliance Actions: ${totalActions}`,
    ``,
    topLaws ? `TOP CRITICAL LAWS:\n${topLaws}\n` : '',
    `Please contact me at your earliest convenience.`,
    ``,
    `Regards,`,
    `${fd.contactName}`,
    `${fd.mobileNumber}`
  ].join('\n');

  window.location.href = `mailto:${FIRM_CONFIG.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

// ── BOOTSTRAP ──
initApp();
