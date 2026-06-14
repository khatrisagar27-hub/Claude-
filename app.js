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

// ── INIT ──
function initApp() {
  buildProgress();
  populateStatesGrid();
  populateStateSelect();
  updateProgress();
}

function buildProgress() {
  const stepsEl = document.getElementById('progressSteps');
  const labelsEl = document.getElementById('progressLabels');
  // Add fill bar first (already has the fill div)
  STEPS.forEach(s => {
    const dot = document.createElement('div');
    dot.className = 'step-dot' + (s.num === 1 ? ' active' : '');
    dot.id = `dot-${s.num}`;
    dot.textContent = s.num;
    stepsEl.appendChild(dot);

    const lbl = document.createElement('div');
    lbl.className = 'progress-label' + (s.num === 1 ? ' active' : '');
    lbl.id = `lbl-${s.num}`;
    lbl.textContent = s.label;
    labelsEl.appendChild(lbl);
  });
}

function populateStatesGrid() {
  const grid = document.getElementById('statesGrid');
  INDIAN_STATES.forEach(state => {
    const chip = document.createElement('label');
    chip.className = 'state-chip';
    chip.dataset.state = state;
    chip.innerHTML = `<input type="checkbox" value="${state}" onchange="toggleStateChip(this)"> ${state}`;
    grid.appendChild(chip);
  });
}

function toggleStateChip(cb) {
  cb.closest('.state-chip').classList.toggle('checked', cb.checked);
}

function populateStateSelect() {
  const sel = document.getElementById('stateOfReg');
  INDIAN_STATES.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s; opt.textContent = s;
    sel.appendChild(opt);
  });
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
  // reset form
  document.querySelectorAll('input[type=checkbox]').forEach(cb => cb.checked = false);
  document.querySelectorAll('input[type=radio]').forEach(r => r.checked = false);
  document.querySelectorAll('.radio-pill').forEach(p => p.classList.remove('selected'));
  document.querySelectorAll('.state-chip').forEach(c => c.classList.remove('checked'));
  document.querySelectorAll('.conditional').forEach(c => c.classList.remove('show'));
  document.querySelectorAll('input[type=text],input[type=number],select').forEach(i => i.value='');
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
    if (!document.getElementById('companyName').value.trim()) {
      alert('Please enter the company name.'); return false;
    }
    if (!document.getElementById('entityType').value) {
      alert('Please select the entity type.'); return false;
    }
    if (!document.getElementById('stateOfReg').value) {
      alert('Please select state of registration.'); return false;
    }
    const states = getCheckedStates();
    if (states.length === 0) {
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

// ── COLLECT FORM DATA ──
function collectFormData() {
  const totalEmployees = parseInt(document.getElementById('totalEmployees').value) || 0;
  const contractWorkers = parseInt(document.getElementById('contractWorkers').value) || 0;
  const womenEmployees = parseInt(document.getElementById('womenEmployees').value) || 0;
  const migrantWorkers = parseInt(document.getElementById('migrantWorkers').value) || 0;
  const permanentEmployees = parseInt(document.getElementById('permanentEmployees').value) || 0;
  const pwdEmployees = parseInt(document.getElementById('pwdEmployees').value) || 0;
  const factoryWorkers = parseInt(document.getElementById('factoryWorkers').value) || 0;
  const annualTurnover = parseInt(document.getElementById('annualTurnover').value) || 0;
  const netWorth = parseInt(document.getElementById('netWorth').value) || 0;
  const netProfit = parseInt(document.getElementById('netProfit').value) || 0;
  const paidUpCapital = parseInt(document.getElementById('paidUpCapital').value) || 0;

  formData = {
    companyName: document.getElementById('companyName').value.trim(),
    entityType: document.getElementById('entityType').value,
    stateOfReg: document.getElementById('stateOfReg').value,
    statesOfOperation: getCheckedStates(),
    isListed: getRadioVal('isListed') === 'yes',

    primarySector: document.getElementById('primarySector').value,
    isManufacturing: document.getElementById('isManufacturing').checked,
    isTrading: document.getElementById('isTrading').checked,
    isECommerce: document.getElementById('isECommerce').checked || document.getElementById('primarySector').value === 'ecommerce',
    dealsFoodBeverages: document.getElementById('dealsFoodBeverages').checked,
    dealsPharma: document.getElementById('dealsPharma').checked,
    dealsPetroleum: document.getElementById('dealsPetroleum').checked,
    dealsExplosives: document.getElementById('dealsExplosives').checked,
    dealsChemicals: document.getElementById('dealsChemicals').checked,
    hasBoilers: document.getElementById('hasBoilers').checked,
    hasMines: document.getElementById('hasMines').checked,
    hasConstruction: document.getElementById('hasConstruction').checked,
    isRealEstate: document.getElementById('isRealEstate').checked,
    isNBFC: document.getElementById('isNBFC').checked,
    isInsurance: document.getElementById('isInsurance').checked,
    isBanking: document.getElementById('isBanking').checked,

    annualTurnover,
    netWorth,
    netProfit,
    paidUpCapital,
    hasFDI: getRadioVal('hasFDI') === 'yes',
    doesImportExport: getRadioVal('doesImportExport') === 'yes',
    isMSME: getRadioVal('isMSME') === 'yes',
    hasForex: getRadioVal('hasForex') === 'yes',

    totalEmployees,
    permanentEmployees,
    contractWorkers,
    womenEmployees,
    migrantWorkers,
    pwdEmployees,
    hasApprentices: getRadioVal('hasApprentices') === 'yes',
    employsMinors: getRadioVal('employsMinors') === 'yes',

    hasFactory: getRadioVal('hasFactory') === 'yes',
    factoryHasPower: getRadioVal('factoryHasPower') === 'yes',
    factoryWorkers,
    hasShop: getRadioVal('hasShop') === 'yes',
    generatesHazardousWaste: document.getElementById('generatesHazardousWaste').checked,
    generatesEWaste: document.getElementById('generatesEWaste').checked,
    usesPlastic: document.getElementById('usesPlastic').checked,
    dischargesWastewater: document.getElementById('dischargesWastewater').checked,
    emitsAirPollutants: document.getElementById('emitsAirPollutants').checked,
    hasLargeElectrical: document.getElementById('hasLargeElectrical').checked,

    hasWeb: getRadioVal('hasWeb') === 'yes',
    collectsData: getRadioVal('collectsData') === 'yes',
    hasPayment: getRadioVal('hasPayment') === 'yes',
    isITService: getRadioVal('isITService') === 'yes',
    isPMLA: getRadioVal('isPMLA') === 'yes',
    hasIP: getRadioVal('hasIP') === 'yes',
  };

  // Derived flags
  formData.isITSector = formData.primarySector === 'it' || formData.isITService;
  formData.isFinancialSector = ['financial','nbfc','insurance'].includes(formData.primarySector) || formData.isNBFC || formData.isBanking || formData.isInsurance;
}

// ── ANALYZE ──
function analyzeCompliance() {
  collectFormData();
  document.getElementById('form-section').style.display = 'none';
  document.getElementById('loading').style.display = 'flex';

  setTimeout(() => {
    allResults = INDIAN_LAWS
      .map(law => ({ ...law, applicableReason: law.reason(formData) }))
      .filter(law => law.applicableReason !== null && law.applicableReason !== undefined);

    document.getElementById('loading').style.display = 'none';
    renderResults();
    document.getElementById('results').style.display = 'block';
    window.scrollTo(0,0);
  }, 1400);
}

// ── RENDER RESULTS ──
const PRIORITY_ORDER = { critical:0, high:1, medium:2, low:3 };
const PRIORITY_LABEL = { critical:'CRITICAL', high:'HIGH', medium:'MEDIUM', low:'LOW' };

function renderResults() {
  const co = formData.companyName || 'Your Company';
  document.getElementById('resultsCompanyTag').textContent = `📋 ${co}`;

  const counts = { critical:0, high:0, medium:0, low:0 };
  allResults.forEach(l => counts[l.priority] = (counts[l.priority]||0) + 1);

  document.getElementById('resultsSubtitle').textContent =
    `${allResults.length} laws are applicable to your company based on the provided profile. Review each law and its compliance requirements below.`;

  // Summary cards
  const sg = document.getElementById('summaryGrid');
  sg.innerHTML = `
    <div class="summary-card total"><div class="s-num">${allResults.length}</div><div class="s-label">Total Laws</div></div>
    <div class="summary-card critical"><div class="s-num">${counts.critical||0}</div><div class="s-label">Critical Priority</div></div>
    <div class="summary-card high"><div class="s-num">${counts.high||0}</div><div class="s-label">High Priority</div></div>
    <div class="summary-card medium"><div class="s-num">${counts.medium||0}</div><div class="s-label">Medium Priority</div></div>
    <div class="summary-card low"><div class="s-num">${counts.low||0}</div><div class="s-label">Low Priority</div></div>
  `;

  renderFilteredLaws(allResults);
}

function renderFilteredLaws(laws) {
  const out = document.getElementById('lawsOutput');
  if (!laws.length) {
    out.innerHTML = '<div class="no-results">No laws match the current filter.</div>';
    return;
  }

  // Group by category
  const byCategory = {};
  laws.sort((a,b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
      .forEach(l => {
        if(!byCategory[l.category]) byCategory[l.category] = [];
        byCategory[l.category].push(l);
      });

  let html = '';
  Object.entries(byCategory).forEach(([cat, catLaws]) => {
    html += `<div class="cat-section">
      <div class="cat-label-row">
        <div class="cat-label">${cat}</div>
        <div class="cat-line"></div>
        <div class="cat-count">${catLaws.length} law${catLaws.length>1?'s':''}</div>
      </div>
      <div class="laws-grid">`;
    catLaws.forEach(law => { html += buildLawCard(law); });
    html += `</div></div>`;
  });

  out.innerHTML = html;
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
    </div>
  `).join('');

  return `
    <div class="law-card" id="law-${law.id}" data-priority="${law.priority}" data-name="${law.name.toLowerCase()}">
      <div class="law-header" onclick="toggleLaw('${law.id}')">
        <div class="law-priority ${law.priority}"></div>
        <div class="law-meta">
          <div class="law-name">
            ${law.name}
            <span class="law-cat">${law.category}</span>
          </div>
          <div class="law-reason">✓ ${law.applicableReason}</div>
        </div>
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
  const card = document.getElementById(`law-${id}`);
  card.classList.toggle('expanded');
}

// ── FILTER ──
function filterLaws(priority, btn) {
  activeFilter = priority;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  applyFilters();
}

function searchLaws(query) {
  applyFilters(query);
}

function applyFilters(query) {
  const q = (query !== undefined ? query : document.querySelector('.search-box').value).toLowerCase();
  let filtered = allResults;
  if (activeFilter !== 'all') filtered = filtered.filter(l => l.priority === activeFilter);
  if (q) filtered = filtered.filter(l =>
    l.name.toLowerCase().includes(q) ||
    l.category.toLowerCase().includes(q) ||
    l.description.toLowerCase().includes(q)
  );
  renderFilteredLaws(filtered);
}

// ── BOOTSTRAP ──
initApp();
