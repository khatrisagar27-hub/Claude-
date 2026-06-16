// ── EXCEL EXPORT (SpreadsheetML / Office XML — no library needed) ──

function xe(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function C(val, sid, type) {
  const t = type || (typeof val === 'number' ? 'Number' : 'String');
  const v = typeof val === 'number' ? val : xe(String(val));
  return `<Cell ss:StyleID="${sid}"><Data ss:Type="${t}">${v}</Data></Cell>`;
}

function CC(val, sid) { // merged cell helper
  return `<Cell ss:StyleID="${sid}" ss:MergeAcross="7"><Data ss:Type="String">${xe(String(val))}</Data></Cell>`;
}

function R(...cells) { return `<Row>${cells.join('')}</Row>`; }
function RH(h) { return `<Row ss:Height="${h}">`; }

const STYLES = `
<Styles>
  <Style ss:ID="Default"><Alignment ss:Vertical="Top"/><Font ss:FontName="Calibri" ss:Size="10"/></Style>

  <Style ss:ID="title">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="18" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#0A1628" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="2" ss:Color="#C8A951"/></Borders>
  </Style>

  <Style ss:ID="subtitle">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Color="#7FB3D3"/>
    <Interior ss:Color="#0A1628" ss:Pattern="Solid"/>
  </Style>

  <Style ss:ID="secHdr">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#1D3A6B" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#C8A951"/>
      <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#1D3A6B"/>
    </Borders>
  </Style>

  <Style ss:ID="colHdr">
    <Alignment ss:Horizontal="Center" ss:Vertical="Center" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#162844" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="2" ss:Color="#C8A951"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#1E3A5F"/>
    </Borders>
  </Style>

  <Style ss:ID="label">
    <Alignment ss:Horizontal="Right" ss:Vertical="Top"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#7FB3D3"/>
    <Interior ss:Color="#0D1B2E" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#1E3A5F"/></Borders>
  </Style>

  <Style ss:ID="val">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Color="#E8F0FE"/>
    <Interior ss:Color="#0F1F38" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#1E3A5F"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#1E3A5F"/>
    </Borders>
  </Style>

  <Style ss:ID="statNum">
    <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="22" ss:Bold="1" ss:Color="#F0C060"/>
    <Interior ss:Color="#0D1B2E" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#1E3A5F"/></Borders>
  </Style>

  <Style ss:ID="statLbl">
    <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="8" ss:Bold="1" ss:Color="#7FB3D3"/>
    <Interior ss:Color="#0F1F38" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="2" ss:Color="#1E3A5F"/></Borders>
  </Style>

  <!-- CRITICAL -->
  <Style ss:ID="crit_badge">
    <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#DC2626" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B91C1C"/></Borders>
  </Style>
  <Style ss:ID="crit_row">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#1A0000"/>
    <Interior ss:Color="#FEE2E2" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FCA5A5"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FCA5A5"/>
    </Borders>
  </Style>
  <Style ss:ID="crit_law">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#991B1B"/>
    <Interior ss:Color="#FEE2E2" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FCA5A5"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FCA5A5"/>
    </Borders>
  </Style>

  <!-- HIGH -->
  <Style ss:ID="high_badge">
    <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#D97706" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#B45309"/></Borders>
  </Style>
  <Style ss:ID="high_row">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#1A0E00"/>
    <Interior ss:Color="#FEF3C7" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FDE68A"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FDE68A"/>
    </Borders>
  </Style>
  <Style ss:ID="high_law">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#92400E"/>
    <Interior ss:Color="#FEF3C7" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FDE68A"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FDE68A"/>
    </Borders>
  </Style>

  <!-- MEDIUM -->
  <Style ss:ID="med_badge">
    <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#0284C7" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0369A1"/></Borders>
  </Style>
  <Style ss:ID="med_row">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#001A2E"/>
    <Interior ss:Color="#E0F2FE" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#BAE6FD"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#BAE6FD"/>
    </Borders>
  </Style>
  <Style ss:ID="med_law">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#075985"/>
    <Interior ss:Color="#E0F2FE" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#BAE6FD"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#BAE6FD"/>
    </Borders>
  </Style>

  <!-- LOW -->
  <Style ss:ID="low_badge">
    <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#059669" ss:Pattern="Solid"/>
    <Borders><Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#047857"/></Borders>
  </Style>
  <Style ss:ID="low_row">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#001A0E"/>
    <Interior ss:Color="#D1FAE5" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A7F3D0"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A7F3D0"/>
    </Borders>
  </Style>
  <Style ss:ID="low_law">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#065F46"/>
    <Interior ss:Color="#D1FAE5" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A7F3D0"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#A7F3D0"/>
    </Borders>
  </Style>

  <!-- DEADLINE / PENALTY special cells -->
  <Style ss:ID="dead_cell">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#065F46"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
    </Borders>
  </Style>
  <Style ss:ID="pen_cell">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#991B1B"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
    </Borders>
  </Style>
  <Style ss:ID="freq_cell">
    <Alignment ss:Horizontal="Center" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#1E40AF"/>
    <Interior ss:Color="#EFF6FF" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#BFDBFE"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#BFDBFE"/>
    </Borders>
  </Style>
  <Style ss:ID="auth_cell">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#713F12"/>
    <Interior ss:Color="#FFFBEB" ss:Pattern="Solid"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FDE68A"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#FDE68A"/>
    </Borders>
  </Style>
  <Style ss:ID="norm">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#111827"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
    </Borders>
  </Style>
  <Style ss:ID="norm_bold">
    <Alignment ss:Horizontal="Left" ss:Vertical="Top" ss:WrapText="1"/>
    <Font ss:FontName="Calibri" ss:Size="9" ss:Bold="1" ss:Color="#111827"/>
    <Borders>
      <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
      <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#D1D5DB"/>
    </Borders>
  </Style>

  <!-- Calendar freq headers -->
  <Style ss:ID="cal_monthly">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#DC2626" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="cal_quarterly">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#D97706" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="cal_annual">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#059669" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="cal_onetime">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#7C3AED" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="cal_asreq">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#0891B2" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="cal_halfy">
    <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
    <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#FFFFFF"/>
    <Interior ss:Color="#BE185D" ss:Pattern="Solid"/>
  </Style>

  <Style ss:ID="blank">
    <Interior ss:Color="#0A1628" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="divider">
    <Interior ss:Color="#1E3A5F" ss:Pattern="Solid"/>
  </Style>
</Styles>`;

const _PMAP = {critical:'crit', medium:'med'};
function badgeStyle(p) { return (_PMAP[p]||p)+'_badge'; }
function rowStyle(p)  { return (_PMAP[p]||p)+'_row'; }
function lawStyle(p)  { return (_PMAP[p]||p)+'_law'; }

function getPriorityLabel(p) {
  return { critical:'CRITICAL', high:'HIGH', medium:'MEDIUM', low:'LOW' }[p] || p.toUpperCase();
}

// ── SHEET 1: DASHBOARD ──
function buildDashboardSheet() {
  const d = formData;
  const today = new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'long',year:'numeric'});
  const counts = {critical:0,high:0,medium:0,low:0};
  allResults.forEach(l => counts[l.priority]++);

  const catCounts = {};
  allResults.forEach(l => { catCounts[l.category] = (catCounts[l.category]||0)+1; });

  const totalActions = allResults.reduce((sum,l) => sum + l.actions.length, 0);

  const sectorMap = {
    manufacturing:'Manufacturing',trading:'Trading',services:'Services',
    it:'IT / Software',construction:'Construction',mining:'Mining',
    financial:'Financial Services',insurance:'Insurance',nbfc:'NBFC',
    healthcare:'Healthcare',food:'Food & Beverage',pharma:'Pharmaceutical',
    realestate:'Real Estate',media:'Media / Entertainment',agriculture:'Agriculture',
    education:'Education',hospitality:'Hospitality',transport:'Transportation',
    energy:'Energy / Power',telecom:'Telecom',retail:'Retail',ecommerce:'E-Commerce'
  };

  const entityMap = {
    private_ltd:'Private Limited Company',public_ltd:'Public Limited Company',
    opc:'One Person Company (OPC)',llp:'Limited Liability Partnership',
    partnership:'Partnership Firm',proprietorship:'Sole Proprietorship',
    section8:'Section 8 Company',govt:'Government / PSU'
  };

  const turnoverMap = {
    '0':'Below ₹20 Lakhs','20':'₹20–₹40 Lakhs','40':'₹40 Lakhs–₹1 Crore',
    '100':'₹1–₹10 Crore','1000':'₹10–₹100 Crore','10000':'₹100–₹500 Crore',
    '50000':'₹500–₹1000 Crore','100000':'Above ₹1000 Crore'
  };

  let rows = '';

  // Title block
  rows += `<Row ss:Height="50">${C('Indian Law Compliance | Sagar Khatri & Associates, Chartered Accountants','title')}</Row>`;
  rows += `<Row ss:Height="18">${C('Generated on ' + today + '  |  Expert Compliance · Audit · Advisory · Tax · Business Consulting','subtitle')}</Row>`;
  rows += `<Row ss:Height="8">${C('','blank')}</Row>`;

  // Client contact section
  rows += `<Row ss:Height="24">${C('CLIENT CONTACT DETAILS','secHdr')}</Row>`;
  const contactRows = [
    ['Contact Person', d.contactName || '—'],
    ['Mobile Number', d.mobileNumber || '—'],
    ['Email Address', d.emailAddress || '—'],
    ['Report Date', today],
  ];
  contactRows.forEach(([lbl, val]) => {
    rows += `<Row ss:Height="18">${C(lbl,'label')}${C(val,'val')}</Row>`;
  });
  rows += `<Row ss:Height="8">${C('','blank')}</Row>`;

  // Company profile section
  rows += `<Row ss:Height="24">${C('COMPANY PROFILE','secHdr')}</Row>`;

  const profileRows = [
    ['Company Name', d.companyName || '—'],
    ['Entity Type', entityMap[d.entityType] || d.entityType],
    ['State of Registration', d.stateOfReg || '—'],
    ['States of Operation', (d.statesOfOperation||[]).join(', ') || '—'],
    ['Primary Sector', sectorMap[d.primarySector] || d.primarySector],
    ['Annual Turnover', turnoverMap[String(d.annualTurnover)] || '—'],
    ['Total Employees', d.totalEmployees || 0],
    ['Contract Workers', d.contractWorkers || 0],
    ['Women Employees', d.womenEmployees || 0],
    ['Listed on Exchange', d.isListed ? 'Yes' : 'No'],
    ['Has Factory', d.hasFactory ? 'Yes (Power: '+(d.factoryHasPower?'Yes':'No')+', Workers: '+d.factoryWorkers+')' : 'No'],
    ['Foreign Investment (FDI)', d.hasFDI ? 'Yes' : 'No'],
    ['Import / Export', d.doesImportExport ? 'Yes' : 'No'],
    ['Collects Personal Data', d.collectsData ? 'Yes' : 'No'],
  ];

  profileRows.forEach(([lbl, val]) => {
    rows += R(
      C(lbl,'label'),
      C(typeof val === 'number' ? val : String(val), 'val', typeof val === 'number' ? 'Number' : 'String')
    );
  });

  rows += `<Row ss:Height="12">${C('','blank')}</Row>`;

  // Summary stats
  rows += `<Row ss:Height="24">${C('COMPLIANCE SUMMARY','secHdr')}</Row>`;
  rows += R(
    C(allResults.length,'statNum'),
    C(counts.critical,'statNum'),
    C(counts.high,'statNum'),
    C(counts.medium,'statNum'),
    C(counts.low,'statNum'),
    C(totalActions,'statNum')
  );
  rows += R(
    C('Total Laws Applicable','statLbl'),
    C('Critical Priority','statLbl'),
    C('High Priority','statLbl'),
    C('Medium Priority','statLbl'),
    C('Low Priority','statLbl'),
    C('Total Compliance Actions','statLbl')
  );

  rows += `<Row ss:Height="12">${C('','blank')}</Row>`;

  // By category
  rows += `<Row ss:Height="24">${C('BREAKDOWN BY CATEGORY','secHdr')}</Row>`;
  rows += R(C('Category','colHdr'), C('Laws Applicable','colHdr'), C('','colHdr'), C('','colHdr'));
  Object.entries(catCounts).sort((a,b) => b[1]-a[1]).forEach(([cat,cnt]) => {
    rows += R(C(cat,'norm_bold'), C(cnt,'norm','Number'), C('','norm'), C('','norm'));
  });

  rows += `<Row ss:Height="12">${C('','blank')}</Row>`;

  // Priority guide
  rows += `<Row ss:Height="24">${C('PRIORITY GUIDE','secHdr')}</Row>`;
  rows += R(C('CRITICAL','crit_badge'),  C('Immediate action required. Heavy penalties including imprisonment. Non-compliance can halt operations.','crit_row'));
  rows += R(C('HIGH','high_badge'),      C('Important ongoing obligations. Significant fines and legal exposure.','high_row'));
  rows += R(C('MEDIUM','med_badge'),     C('Required compliance with moderate penalties. Should be addressed within 3 months.','med_row'));
  rows += R(C('LOW','low_badge'),        C('Recommended or applicable to specific situations. Lower penalty risk.','low_row'));

  rows += `<Row ss:Height="12">${C('','blank')}</Row>`;
  rows += `<Row ss:Height="18">${C('DISCLAIMER: This report is for informational purposes only and does not constitute legal advice. Consult a qualified lawyer or compliance professional for specific guidance.','subtitle')}</Row>`;

  return `<Worksheet ss:Name="Dashboard">
    <Table ss:DefaultColumnWidth="200" ss:DefaultRowHeight="16">
      <Column ss:Width="180"/>
      <Column ss:Width="320"/>
      <Column ss:Width="120"/>
      <Column ss:Width="120"/>
      <Column ss:Width="120"/>
      <Column ss:Width="140"/>
      ${rows}
    </Table>
    <WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">
      <FitToPage/>
      <Print><ValidPrinterInfo/><HorizontalResolution>600</HorizontalResolution><VerticalResolution>600</VerticalResolution></Print>
      <FreezePanes/><FrozenNoSplit/><SplitHorizontal>3</SplitHorizontal><TopRowBottomPane>3</TopRowBottomPane>
    </WorksheetOptions>
  </Worksheet>`;
}

// ── SHEET 2: LAWS OVERVIEW ──
function buildLawsSheet() {
  const sorted = [...allResults].sort((a,b) => {
    const po = {critical:0,high:1,medium:2,low:3};
    return po[a.priority]-po[b.priority] || a.category.localeCompare(b.category);
  });

  let rows = '';
  rows += `<Row ss:Height="14">${C('Applicable Laws - Priority Overview','secHdr')}</Row>`;
  rows += R(
    C('#','colHdr'),
    C('Priority','colHdr'),
    C('Law Name','colHdr'),
    C('Category','colHdr'),
    C('Why Applicable','colHdr'),
    C('Actions','colHdr'),
    C('Enforcing Authority (sample)','colHdr')
  );

  sorted.forEach((law, i) => {
    const p = law.priority;
    const firstAuth = law.actions[0]?.authority || '—';
    rows += R(
      C(i+1, rowStyle(p), 'Number'),
      C(getPriorityLabel(p), badgeStyle(p)),
      C(law.name, lawStyle(p)),
      C(law.category, rowStyle(p)),
      C(law.applicableReason, rowStyle(p)),
      C(law.actions.length, rowStyle(p), 'Number'),
      C(firstAuth, rowStyle(p))
    );
  });

  return `<Worksheet ss:Name="Laws Overview">
    <Table ss:DefaultRowHeight="28">
      <Column ss:Width="30"/>
      <Column ss:Width="90"/>
      <Column ss:Width="230"/>
      <Column ss:Width="130"/>
      <Column ss:Width="220"/>
      <Column ss:Width="55"/>
      <Column ss:Width="180"/>
      ${rows}
    </Table>
    <WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">
      <FreezePanes/><FrozenNoSplit/><SplitHorizontal>2</SplitHorizontal><TopRowBottomPane>2</TopRowBottomPane>
      <ActivePane>2</ActivePane>
    </WorksheetOptions>
  </Worksheet>`;
}

// ── SHEET 3: MASTER COMPLIANCE CHECKLIST ──
function buildChecklistSheet() {
  const sorted = [...allResults].sort((a,b) => {
    const po = {critical:0,high:1,medium:2,low:3};
    return po[a.priority]-po[b.priority];
  });

  let rows = '';
  rows += `<Row ss:Height="14">${C('Master Compliance Checklist - All Required Actions','secHdr')}</Row>`;
  rows += R(
    C('Sr.','colHdr'),
    C('Priority','colHdr'),
    C('Law / Act','colHdr'),
    C('Category','colHdr'),
    C('Compliance Action Required','colHdr'),
    C('Frequency','colHdr'),
    C('Deadline','colHdr'),
    C('Enforcing Authority','colHdr'),
    C('Penalty for Non-Compliance','colHdr'),
    C('Details','colHdr'),
    C('Status','colHdr')
  );

  let sr = 1;
  sorted.forEach(law => {
    const p = law.priority;
    law.actions.forEach(a => {
      rows += R(
        C(sr++, rowStyle(p), 'Number'),
        C(getPriorityLabel(p), badgeStyle(p)),
        C(law.shortName, lawStyle(p)),
        C(law.category, rowStyle(p)),
        C(a.title, norm_bold_row(p)),
        C(a.freq, 'freq_cell'),
        C(a.deadline, 'dead_cell'),
        C(a.authority, 'auth_cell'),
        C(a.penalty, 'pen_cell'),
        C(a.desc || '', 'norm'),
        C('[ ] Pending', 'norm')
      );
    });
  });

  return `<Worksheet ss:Name="Compliance Checklist">
    <Table ss:DefaultRowHeight="36">
      <Column ss:Width="35"/>
      <Column ss:Width="85"/>
      <Column ss:Width="170"/>
      <Column ss:Width="110"/>
      <Column ss:Width="220"/>
      <Column ss:Width="85"/>
      <Column ss:Width="140"/>
      <Column ss:Width="160"/>
      <Column ss:Width="200"/>
      <Column ss:Width="260"/>
      <Column ss:Width="80"/>
      ${rows}
    </Table>
    <WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">
      <FreezePanes/><FrozenNoSplit/><SplitHorizontal>2</SplitHorizontal><TopRowBottomPane>2</TopRowBottomPane>
      <ActivePane>2</ActivePane>
    </WorksheetOptions>
  </Worksheet>`;
}

function norm_bold_row(p) {
  const styles = {critical:'crit_law',high:'high_law',medium:'med_law',low:'low_law'};
  return styles[p] || 'norm_bold';
}

// ── SHEET 4: COMPLIANCE CALENDAR ──
function buildCalendarSheet() {
  // Group actions by frequency bucket
  const buckets = {
    'One-time':[],
    'Monthly':[],
    'Quarterly':[],
    'Half-yearly':[],
    'Annual':[],
    'As required':[]
  };

  function classify(freq) {
    const f = freq.toLowerCase();
    if(f.includes('one-time') || f.includes('one time') || f.includes('per employee') || f.includes('per contract') || f.includes('per worker') || f.includes('per consignment') || f.includes('per mark') || f.includes('per work') || f.includes('per product') || f.includes('per project') || f.includes('per transaction')) return 'One-time';
    if(f.includes('month')) return 'Monthly';
    if(f.includes('quarter')) return 'Quarterly';
    if(f.includes('half')) return 'Half-yearly';
    if(f.includes('annual') || f.includes('year') || f.includes('every 3') || f.includes('10 year')) return 'Annual';
    if(f.includes('permanent') || f.includes('ongoing') || f.includes('continuous') || f.includes('daily') || f.includes('always')) return 'As required';
    return 'As required';
  }

  const sorted = [...allResults].sort((a,b)=>{
    const po={critical:0,high:1,medium:2,low:3};return po[a.priority]-po[b.priority];
  });

  sorted.forEach(law => {
    law.actions.forEach(a => {
      const bucket = classify(a.freq);
      buckets[bucket].push({law, action:a});
    });
  });

  const bucketStyles = {
    'One-time':'cal_onetime',
    'Monthly':'cal_monthly',
    'Quarterly':'cal_quarterly',
    'Half-yearly':'cal_halfy',
    'Annual':'cal_annual',
    'As required':'cal_asreq'
  };

  const bucketEmojis = {
    'One-time':'ONE-TIME SETUP',
    'Monthly':'MONTHLY (Recurring)',
    'Quarterly':'QUARTERLY',
    'Half-yearly':'HALF-YEARLY',
    'Annual':'ANNUAL',
    'As required':'AS REQUIRED / ONGOING'
  };

  let rows = '';
  rows += `<Row ss:Height="14">${C('Compliance Calendar - Actions Grouped by Frequency','secHdr')}</Row>`;

  Object.entries(buckets).forEach(([bucket, items]) => {
    if(!items.length) return;
    rows += `<Row ss:Height="6">${C('','blank')}</Row>`;
    rows += `<Row ss:Height="22">${C(bucketEmojis[bucket] + '  (' + items.length + ' actions)', bucketStyles[bucket])}</Row>`;
    rows += R(
      C('Priority','colHdr'),
      C('Law Name','colHdr'),
      C('Action Required','colHdr'),
      C('Deadline','colHdr'),
      C('Enforcing Authority','colHdr'),
      C('Penalty','colHdr')
    );
    items.forEach(({law, action: a}) => {
      const p = law.priority;
      rows += R(
        C(getPriorityLabel(p), badgeStyle(p)),
        C(law.shortName, lawStyle(p)),
        C(a.title, rowStyle(p)),
        C(a.deadline, 'dead_cell'),
        C(a.authority, 'auth_cell'),
        C(a.penalty, 'pen_cell')
      );
    });
  });

  return `<Worksheet ss:Name="Compliance Calendar">
    <Table ss:DefaultRowHeight="32">
      <Column ss:Width="90"/>
      <Column ss:Width="190"/>
      <Column ss:Width="240"/>
      <Column ss:Width="170"/>
      <Column ss:Width="180"/>
      <Column ss:Width="220"/>
      ${rows}
    </Table>
    <WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">
      <FreezePanes/><FrozenNoSplit/><SplitHorizontal>2</SplitHorizontal><TopRowBottomPane>2</TopRowBottomPane>
      <ActivePane>2</ActivePane>
    </WorksheetOptions>
  </Worksheet>`;
}

// ── SHEET 5: CRITICAL & HIGH PRIORITY ONLY ──
function buildUrgentSheet() {
  const urgent = allResults
    .filter(l => l.priority === 'critical' || l.priority === 'high')
    .sort((a,b)=>{ const po={critical:0,high:1}; return po[a.priority]-po[b.priority]; });

  let rows = '';
  rows += `<Row ss:Height="14">${C('Urgent Action Required - Critical & High Priority Only','secHdr')}</Row>`;
  rows += `<Row ss:Height="14">${C('These compliance actions carry the highest risk of penalties, business closure, or imprisonment. Address these IMMEDIATELY.','subtitle')}</Row>`;
  rows += `<Row ss:Height="8">${C('','blank')}</Row>`;
  rows += R(
    C('Priority','colHdr'),
    C('Law / Act','colHdr'),
    C('Action Required','colHdr'),
    C('Deadline','colHdr'),
    C('Penalty for Non-Compliance','colHdr'),
    C('Enforcing Authority','colHdr'),
    C('Done?','colHdr')
  );

  urgent.forEach(law => {
    const p = law.priority;
    law.actions.forEach(a => {
      rows += R(
        C(getPriorityLabel(p), badgeStyle(p)),
        C(law.shortName, lawStyle(p)),
        C(a.title, norm_bold_row(p)),
        C(a.deadline, 'dead_cell'),
        C(a.penalty, 'pen_cell'),
        C(a.authority, 'auth_cell'),
        C('[ ]', rowStyle(p))
      );
    });
  });

  return `<Worksheet ss:Name="Urgent Actions">
    <Table ss:DefaultRowHeight="32">
      <Column ss:Width="90"/>
      <Column ss:Width="180"/>
      <Column ss:Width="240"/>
      <Column ss:Width="150"/>
      <Column ss:Width="220"/>
      <Column ss:Width="180"/>
      <Column ss:Width="60"/>
      ${rows}
    </Table>
    <WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">
      <FreezePanes/><FrozenNoSplit/><SplitHorizontal>4</SplitHorizontal><TopRowBottomPane>4</TopRowBottomPane>
      <ActivePane>2</ActivePane>
    </WorksheetOptions>
  </Worksheet>`;
}

// ── MASTER EXPORT FUNCTION ──
function exportToExcel() {
  if(!allResults || !allResults.length) {
    alert('Please complete the compliance analysis first.');
    return;
  }

  const btn = document.getElementById('xlsBtn');
  btn.textContent = '⏳ Generating…';
  btn.disabled = true;

  setTimeout(() => {
    try {
      const xml = '﻿' + `<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook
  xmlns="urn:schemas-microsoft-com:office:spreadsheet"
  xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
  xmlns:x="urn:schemas-microsoft-com:office:excel"
  xmlns:o="urn:schemas-microsoft-com:office:office">
  <DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">
    <Title>LexComply India — Compliance Report</Title>
    <Author>LexComply India</Author>
    <Company>${xe(formData.companyName || 'Company')}</Company>
    <Created>${new Date().toISOString()}</Created>
  </DocumentProperties>
  ${STYLES}
  ${buildDashboardSheet()}
  ${buildLawsSheet()}
  ${buildChecklistSheet()}
  ${buildCalendarSheet()}
  ${buildUrgentSheet()}
</Workbook>`;

      const blob = new Blob([xml], {type:'application/vnd.ms-excel;charset=utf-8'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const safe = (formData.companyName||'Company').replace(/[^a-z0-9]/gi,'_');
      const date = new Date().toISOString().slice(0,10);
      a.href = url;
      a.download = `LexComply_${safe}_${date}.xls`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch(err) {
      alert('Export failed: ' + err.message);
    } finally {
      btn.textContent = '📊 Download Excel Report';
      btn.disabled = false;
    }
  }, 100);
}
