// ── EXCEL EXPORT — PROPER XLSX (Open XML / ZIP) FORMAT ──
// No external library required. Generates a valid .xlsx file that opens
// in all Excel versions without format warnings or Table errors.

// ── XML HELPER ──
function xe(s) {
  if (s == null) return '';
  return String(s)
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── COLUMN LETTER HELPER ──
function colLetter(n) { // 1-based
  let s = '';
  while (n > 0) { n--; s = String.fromCharCode(65 + n % 26) + s; n = Math.floor(n / 26); }
  return s;
}

// ── CELL BUILDERS ──
// s = style index (0=default), t = 'inlineStr' or omit for number
function xlStr(col, row, val, s) {
  const v = xe(String(val == null ? '' : val));
  return `<c r="${colLetter(col)}${row}" s="${s || 0}" t="inlineStr"><is><t xml:space="preserve">${v}</t></is></c>`;
}
function xlNum(col, row, val, s) {
  return `<c r="${colLetter(col)}${row}" s="${s || 0}"><v>${val}</v></c>`;
}
function xlBlank(col, row, s) {
  return `<c r="${colLetter(col)}${row}" s="${s || 0}"/>`;
}
function xlRow(rn, ht, cells) {
  const h = ht ? ` ht="${ht}" customHeight="1"` : '';
  return `<row r="${rn}"${h}>${cells.join('')}</row>`;
}

// ── STYLE INDEX MAP ──
// These numbers correspond to positions in the cellXfs array in buildStylesXml()
const S = {
  def:0, title:1, subtitle:2, secHdr:3, colHdr:4,
  label:5, val:6, statNum:7, statLbl:8,
  crit_badge:9, crit_row:10, crit_law:11,
  high_badge:12, high_row:13, high_law:14,
  med_badge:15, med_row:16, med_law:17,
  low_badge:18, low_row:19, low_law:20,
  dead_cell:21, pen_cell:22, freq_cell:23, auth_cell:24,
  norm:25, norm_bold:26,
  cal_monthly:27, cal_quarterly:28, cal_annual:29,
  cal_onetime:30, cal_asreq:31, cal_halfy:32,
  blank:33
};

function getPriorityStyles(p) {
  const m = {critical:['crit_badge','crit_row','crit_law'], high:['high_badge','high_row','high_law'], medium:['med_badge','med_row','med_law'], low:['low_badge','low_row','low_law']};
  return (m[p] || ['def','def','def']).map(k => S[k]);
}
function getPriorityLabel(p) {
  return {critical:'CRITICAL', high:'HIGH', medium:'MEDIUM', low:'LOW'}[p] || p.toUpperCase();
}

// ── STYLES XML ──
function buildStylesXml() {
  // Helper for solid fill
  const fill = (hex) => `<fill><patternFill patternType="solid"><fgColor rgb="FF${hex.replace('#','')}"/><bgColor indexed="64"/></patternFill></fill>`;
  // Helper for font
  const font = (sz, bold, hex, name) => {
    name = name || 'Calibri';
    return `<font><sz val="${sz}"/>${bold?'<b/>':''}<color rgb="FF${hex.replace('#','')}"/><name val="${name}"/><family val="2"/></font>`;
  };
  // Helper for border side
  const side = (style, hex) => hex ? `style="${style}"><color rgb="FF${hex.replace('#','')}"/>` : 'style="none">';
  const border = (r,b) => {
    const rs = r ? `<right style="thin"><color rgb="FF${r.replace('#','')}"/></right>` : '<right/>';
    const bs = b ? `<bottom style="thin"><color rgb="FF${b.replace('#','')}"/></bottom>` : '<bottom/>';
    return `<border><left/>${rs}<top/>${bs}<diagonal/></border>`;
  };

  const fonts = [
    font(10, false, 'FFFFFF'),        // F0  default (unused)
    font(16, true,  'FFFFFF'),        // F1  title
    font(9,  false, '7FB3D3'),        // F2  subtitle
    font(11, true,  'FFFFFF'),        // F3  secHdr
    font(9,  true,  'FFFFFF'),        // F4  colHdr / badges / cal headers
    font(9,  true,  '7FB3D3'),        // F5  label
    font(10, false, 'E8F0FE'),        // F6  val
    font(22, true,  'F0C060'),        // F7  statNum
    font(8,  true,  '7FB3D3'),        // F8  statLbl
    font(9,  false, '1A0000'),        // F9  crit_row
    font(9,  true,  '991B1B'),        // F10 crit_law
    font(9,  false, '1A0E00'),        // F11 high_row
    font(9,  true,  '92400E'),        // F12 high_law
    font(9,  false, '001A2E'),        // F13 med_row
    font(9,  true,  '075985'),        // F14 med_law
    font(9,  false, '001A0E'),        // F15 low_row
    font(9,  true,  '065F46'),        // F16 low_law
    font(9,  true,  '065F46'),        // F17 dead_cell
    font(9,  false, '991B1B'),        // F18 pen_cell
    font(9,  true,  '1E40AF'),        // F19 freq_cell
    font(9,  false, '713F12'),        // F20 auth_cell
    font(9,  false, '111827'),        // F21 norm
    font(9,  true,  '111827'),        // F22 norm_bold
    font(10, false, '374151'),        // F23 default visible
  ].join('');

  const fills = [
    '<fill><patternFill patternType="none"/></fill>',  // FL0 required
    '<fill><patternFill patternType="gray125"/></fill>',// FL1 required
    fill('#0A1628'),  // FL2 dark blue header bg
    fill('#1D3A6B'),  // FL3 navy section header
    fill('#162844'),  // FL4 col header
    fill('#0D1B2E'),  // FL5 label
    fill('#0F1F38'),  // FL6 val / stat
    fill('#DC2626'),  // FL7 crit badge / cal_monthly
    fill('#FEE2E2'),  // FL8 crit row
    fill('#D97706'),  // FL9 high badge / cal_quarterly
    fill('#FEF3C7'),  // FL10 high row
    fill('#0284C7'),  // FL11 med badge
    fill('#E0F2FE'),  // FL12 med row
    fill('#059669'),  // FL13 low badge / cal_annual
    fill('#D1FAE5'),  // FL14 low row
    fill('#EFF6FF'),  // FL15 freq
    fill('#FFFBEB'),  // FL16 auth
    fill('#7C3AED'),  // FL17 cal_onetime
    fill('#0891B2'),  // FL18 cal_asreq
    fill('#BE185D'),  // FL19 cal_halfy
  ].join('');

  const borders = [
    border(null, null),          // B0 none
    border(null, 'C8A951'),      // B1 gold bottom (secHdr)
    border('1E3A5F', '1E3A5F'), // B2 navy all (val/label)
    border('D1D5DB', 'D1D5DB'), // B3 grey (norm / deadline / penalty)
    border('FCA5A5', 'FCA5A5'), // B4 light red (crit)
    border('FDE68A', 'FDE68A'), // B5 light gold (high / auth)
    border('BAE6FD', 'BAE6FD'), // B6 light blue (med)
    border('A7F3D0', 'A7F3D0'), // B7 light green (low)
    border('BFDBFE', 'BFDBFE'), // B8 freq blue
    border('1E3A5F', null),     // B9 right navy only (badge)
    border(null, 'C8A951'),     // B10 gold bottom only (colHdr)
  ].join('');

  // Helper: xf element
  const xf = (fid, flid, bid, xfId, alStr, applyFl, applyFn, applyBd, applyAl) => {
    const af = applyFl ? ' applyFill="1"' : '';
    const an = applyFn ? ' applyFont="1"' : '';
    const ab = applyBd ? ' applyBorder="1"' : '';
    const aa = alStr ? ' applyAlignment="1"' : '';
    const al = alStr ? `<alignment ${alStr}/>` : '';
    return `<xf numFmtId="0" fontId="${fid}" fillId="${flid}" borderId="${bid}" xfId="${xfId||0}"${af}${an}${ab}${aa}>${al}</xf>`;
  };

  // cellXfs - order MUST match S constants above
  const cellXfs = [
    xf(23, 0, 0, 0, '', 0,0,0,0),                                           // 0 def
    xf(1, 2, 0, 0, 'horizontal="left" vertical="center" wrapText="1"', 1,1,0,1), // 1 title
    xf(2, 2, 0, 0, 'horizontal="left" vertical="center"', 1,1,0,1),         // 2 subtitle
    xf(3, 3, 1, 0, 'horizontal="left" vertical="center"', 1,1,1,1),         // 3 secHdr
    xf(4, 4, 10,0, 'horizontal="center" vertical="center" wrapText="1"', 1,1,1,1), // 4 colHdr
    xf(5, 5, 2, 0, 'horizontal="right" vertical="top"', 1,1,1,1),           // 5 label
    xf(6, 6, 2, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 6 val
    xf(7, 6, 0, 0, 'horizontal="center" vertical="center"', 1,1,0,1),       // 7 statNum
    xf(8, 6, 0, 0, 'horizontal="center" vertical="center"', 1,1,0,1),       // 8 statLbl
    xf(4, 7, 9, 0, 'horizontal="center" vertical="center"', 1,1,1,1),       // 9 crit_badge
    xf(9, 8, 4, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 10 crit_row
    xf(10,8, 4, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 11 crit_law
    xf(4, 9, 9, 0, 'horizontal="center" vertical="center"', 1,1,1,1),       // 12 high_badge
    xf(11,10,5, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 13 high_row
    xf(12,10,5, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 14 high_law
    xf(4, 11,9, 0, 'horizontal="center" vertical="center"', 1,1,1,1),       // 15 med_badge
    xf(13,12,6, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 16 med_row
    xf(14,12,6, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 17 med_law
    xf(4, 13,9, 0, 'horizontal="center" vertical="center"', 1,1,1,1),       // 18 low_badge
    xf(15,14,7, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 19 low_row
    xf(16,14,7, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 20 low_law
    xf(17,0, 3, 0, 'horizontal="left" vertical="top" wrapText="1"', 0,1,1,1), // 21 dead_cell
    xf(18,0, 3, 0, 'horizontal="left" vertical="top" wrapText="1"', 0,1,1,1), // 22 pen_cell
    xf(19,15,8, 0, 'horizontal="center" vertical="top" wrapText="1"', 1,1,1,1), // 23 freq_cell
    xf(20,16,5, 0, 'horizontal="left" vertical="top" wrapText="1"', 1,1,1,1), // 24 auth_cell
    xf(21,0, 3, 0, 'horizontal="left" vertical="top" wrapText="1"', 0,1,1,1), // 25 norm
    xf(22,0, 3, 0, 'horizontal="left" vertical="top" wrapText="1"', 0,1,1,1), // 26 norm_bold
    xf(4, 7, 0, 0, 'horizontal="left" vertical="center"', 1,1,0,1),         // 27 cal_monthly
    xf(4, 9, 0, 0, 'horizontal="left" vertical="center"', 1,1,0,1),         // 28 cal_quarterly
    xf(4, 13,0, 0, 'horizontal="left" vertical="center"', 1,1,0,1),         // 29 cal_annual
    xf(4, 17,0, 0, 'horizontal="left" vertical="center"', 1,1,0,1),         // 30 cal_onetime
    xf(4, 18,0, 0, 'horizontal="left" vertical="center"', 1,1,0,1),         // 31 cal_asreq
    xf(4, 19,0, 0, 'horizontal="left" vertical="center"', 1,1,0,1),         // 32 cal_halfy
    xf(23,2, 0, 0, '', 1,0,0,0),                                            // 33 blank
  ].join('');

  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="24">${fonts}</fonts>
  <fills count="20">${fills}</fills>
  <borders count="11">${borders}</borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="34">${cellXfs}</cellXfs>
</styleSheet>`;
}

// ── XLSX BOILERPLATE XML ──
const CONTENT_TYPES_XML = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet4.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet5.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>`;

const RELS_XML = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>`;

const WORKBOOK_XML = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Dashboard" sheetId="1" r:id="rId1"/>
    <sheet name="Laws Overview" sheetId="2" r:id="rId2"/>
    <sheet name="Compliance Checklist" sheetId="3" r:id="rId3"/>
    <sheet name="Compliance Calendar" sheetId="4" r:id="rId4"/>
    <sheet name="Urgent Actions" sheetId="5" r:id="rId5"/>
  </sheets>
</workbook>`;

const WORKBOOK_RELS_XML = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet5.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>`;

function wrapSheet(cols, rows, freeze) {
  const fr = freeze ? `<sheetView workbookViewId="0"><pane ySplit="${freeze}" topLeftCell="A${freeze+1}" state="frozen" activePane="bottomLeft"/></sheetView>` : '<sheetView workbookViewId="0"/>';
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews>${fr}</sheetViews>
  <sheetFormatPr defaultRowHeight="15" customHeight="1"/>
  <cols>${cols}</cols>
  <sheetData>${rows}</sheetData>
</worksheet>`;
}

function col(min, max, w) {
  return `<col min="${min}" max="${max}" width="${w}" customWidth="1"/>`;
}

// ── SHEET 1: DASHBOARD ──
function buildDashboardSheet() {
  const d = formData;
  const today = new Date().toLocaleDateString('en-IN', {day:'2-digit', month:'long', year:'numeric'});
  const counts = {critical:0, high:0, medium:0, low:0};
  allResults.forEach(l => counts[l.priority]++);
  const catCounts = {};
  allResults.forEach(l => { catCounts[l.category] = (catCounts[l.category]||0)+1; });
  const totalActions = allResults.reduce((s,l) => s + l.actions.length, 0);

  const sectorMap = {manufacturing:'Manufacturing',trading:'Trading',services:'Services',it:'IT / Software',construction:'Construction',mining:'Mining',financial:'Financial Services',insurance:'Insurance',nbfc:'NBFC',healthcare:'Healthcare',food:'Food & Beverage',pharma:'Pharmaceutical',realestate:'Real Estate',media:'Media / Entertainment',agriculture:'Agriculture',education:'Education',hospitality:'Hospitality',transport:'Transportation',energy:'Energy / Power',telecom:'Telecom',retail:'Retail',ecommerce:'E-Commerce'};
  const entityMap = {private_ltd:'Private Limited Company',public_ltd:'Public Limited Company',opc:'One Person Company (OPC)',llp:'Limited Liability Partnership',partnership:'Partnership Firm',proprietorship:'Sole Proprietorship',section8:'Section 8 Company',govt:'Government / PSU'};
  const turnoverMap = {'0':'Below Rs.20 Lakhs','20':'Rs.20-40 Lakhs','40':'Rs.40 Lakhs - Rs.1 Crore','100':'Rs.1-10 Crore','1000':'Rs.10-100 Crore','10000':'Rs.100-500 Crore','50000':'Rs.500-1000 Crore','100000':'Above Rs.1000 Crore'};

  const rows = [];
  let r = 1;

  rows.push(xlRow(r++, 48, [xlStr(1,r-1,'Indian Law Compliance | Sagar Khatri & Associates, Chartered Accountants', S.title)]));
  rows.push(xlRow(r++, 18, [xlStr(1,r-1,'Generated on ' + today + '  |  Expert Compliance  Audit  Advisory  Tax  Business Consulting', S.subtitle)]));
  rows.push(xlRow(r++, 6, [xlBlank(1,r-1, S.blank)]));

  rows.push(xlRow(r++, 22, [xlStr(1,r-1,'CLIENT CONTACT DETAILS', S.secHdr)]));
  [[' Contact Person', d.contactName||'—'],[' Mobile Number', d.mobileNumber||'—'],[' Email Address', d.emailAddress||'—'],[' Report Date', today]].forEach(([lbl,v]) => {
    rows.push(xlRow(r++, 18, [xlStr(1,r-1,lbl,S.label), xlStr(2,r-1,v,S.val)]));
  });
  rows.push(xlRow(r++, 6, [xlBlank(1,r-1, S.blank)]));

  rows.push(xlRow(r++, 22, [xlStr(1,r-1,'COMPANY PROFILE', S.secHdr)]));
  [
    [' Company Name', d.companyName||'—'],
    [' Entity Type', entityMap[d.entityType]||d.entityType||'—'],
    [' State of Registration', d.stateOfReg||'—'],
    [' States of Operation', (d.statesOfOperation||[]).join(', ')||'—'],
    [' Primary Sector', sectorMap[d.primarySector]||d.primarySector||'—'],
    [' Annual Turnover', turnoverMap[String(d.annualTurnover)]||'—'],
    [' Total Employees', d.totalEmployees||0],
    [' Contract Workers', d.contractWorkers||0],
    [' Women Employees', d.womenEmployees||0],
    [' Listed on Exchange', d.isListed?'Yes':'No'],
    [' Has Factory', d.hasFactory?('Yes (Power: '+(d.factoryHasPower?'Yes':'No')+', Workers: '+d.factoryWorkers+')'):'No'],
    [' Foreign Investment (FDI)', d.hasFDI?'Yes':'No'],
    [' Import / Export', d.doesImportExport?'Yes':'No'],
    [' Collects Personal Data', d.collectsData?'Yes':'No'],
  ].forEach(([lbl,v]) => {
    const cell = typeof v === 'number' ? xlNum(2,r,v,S.val) : xlStr(2,r,v,S.val);
    rows.push(xlRow(r++, 18, [xlStr(1,r-1,lbl,S.label), cell]));
  });
  rows.push(xlRow(r++, 8, [xlBlank(1,r-1, S.blank)]));

  rows.push(xlRow(r++, 22, [xlStr(1,r-1,'COMPLIANCE SUMMARY', S.secHdr)]));
  rows.push(xlRow(r++, 40, [xlNum(1,r-1,allResults.length,S.statNum),xlNum(2,r-1,counts.critical,S.statNum),xlNum(3,r-1,counts.high,S.statNum),xlNum(4,r-1,counts.medium,S.statNum),xlNum(5,r-1,counts.low,S.statNum),xlNum(6,r-1,totalActions,S.statNum)]));
  rows.push(xlRow(r++, 18, [xlStr(1,r-1,'Total Laws',S.statLbl),xlStr(2,r-1,'Critical',S.statLbl),xlStr(3,r-1,'High',S.statLbl),xlStr(4,r-1,'Medium',S.statLbl),xlStr(5,r-1,'Low',S.statLbl),xlStr(6,r-1,'Total Actions',S.statLbl)]));
  rows.push(xlRow(r++, 8, [xlBlank(1,r-1, S.blank)]));

  rows.push(xlRow(r++, 22, [xlStr(1,r-1,'BREAKDOWN BY CATEGORY', S.secHdr)]));
  rows.push(xlRow(r++, 0, [xlStr(1,r-1,'Category',S.colHdr), xlStr(2,r-1,'Laws Applicable',S.colHdr)]));
  Object.entries(catCounts).sort((a,b)=>b[1]-a[1]).forEach(([cat,cnt]) => {
    rows.push(xlRow(r++, 0, [xlStr(1,r-1,cat,S.norm_bold), xlNum(2,r-1,cnt,S.norm)]));
  });
  rows.push(xlRow(r++, 8, [xlBlank(1,r-1, S.blank)]));

  rows.push(xlRow(r++, 22, [xlStr(1,r-1,'PRIORITY GUIDE', S.secHdr)]));
  [[S.crit_badge,'CRITICAL','Immediate action required. Heavy penalties including imprisonment. Non-compliance can halt operations.'],
   [S.high_badge,'HIGH','Important ongoing obligations. Significant fines and legal exposure.'],
   [S.med_badge,'MEDIUM','Required compliance with moderate penalties. Should be addressed within 3 months.'],
   [S.low_badge,'LOW','Recommended or applicable to specific situations. Lower penalty risk.']
  ].forEach(([bs,lbl,desc]) => {
    rows.push(xlRow(r++, 0, [xlStr(1,r-1,lbl,bs), xlStr(2,r-1,desc,S.norm)]));
  });
  rows.push(xlRow(r++, 8, [xlBlank(1,r-1, S.blank)]));
  rows.push(xlRow(r++, 18, [xlStr(1,r-1,'DISCLAIMER: This report is for informational purposes only and does not constitute legal advice. Consult a qualified lawyer or compliance professional for specific guidance.',S.subtitle)]));

  const cols = col(1,1,28) + col(2,2,50) + col(3,6,20);
  return wrapSheet(cols, rows.join(''), 1);
}

// ── SHEET 2: LAWS OVERVIEW ──
function buildLawsSheet() {
  const sorted = [...allResults].sort((a,b) => {const po={critical:0,high:1,medium:2,low:3}; return po[a.priority]-po[b.priority]||a.category.localeCompare(b.category);});
  const rows = [];
  let r = 1;
  rows.push(xlRow(r++, 14, [xlStr(1,r-1,'Applicable Laws - Priority Overview', S.secHdr)]));
  rows.push(xlRow(r++, 0, [
    xlStr(1,r-1,'#',S.colHdr), xlStr(2,r-1,'Priority',S.colHdr), xlStr(3,r-1,'Law Name',S.colHdr),
    xlStr(4,r-1,'Category',S.colHdr), xlStr(5,r-1,'Why Applicable',S.colHdr),
    xlStr(6,r-1,'Actions',S.colHdr), xlStr(7,r-1,'Enforcing Authority',S.colHdr)
  ]));
  sorted.forEach((law, i) => {
    const [bs,rs,ls] = getPriorityStyles(law.priority);
    rows.push(xlRow(r++, 28, [
      xlNum(1,r-1,i+1,rs), xlStr(2,r-1,getPriorityLabel(law.priority),bs),
      xlStr(3,r-1,law.name,ls), xlStr(4,r-1,law.category,rs),
      xlStr(5,r-1,law.applicableReason,rs), xlNum(6,r-1,law.actions.length,rs),
      xlStr(7,r-1,(law.actions[0]||{}).authority||'—',rs)
    ]));
  });
  const cols = col(1,1,5)+col(2,2,14)+col(3,3,36)+col(4,4,20)+col(5,5,35)+col(6,6,9)+col(7,7,28);
  return wrapSheet(cols, rows.join(''), 2);
}

// ── SHEET 3: COMPLIANCE CHECKLIST ──
function buildChecklistSheet() {
  const sorted = [...allResults].sort((a,b)=>{const po={critical:0,high:1,medium:2,low:3};return po[a.priority]-po[b.priority];});
  const rows = [];
  let r = 1, sr = 1;

  rows.push(xlRow(r++, 14, [xlStr(1,r-1,'Master Compliance Checklist - All Required Actions', S.secHdr)]));
  rows.push(xlRow(r++, 0, [
    xlStr(1,r-1,'Sr.',S.colHdr), xlStr(2,r-1,'Priority',S.colHdr), xlStr(3,r-1,'Law / Act',S.colHdr),
    xlStr(4,r-1,'Category',S.colHdr), xlStr(5,r-1,'Compliance Action Required',S.colHdr),
    xlStr(6,r-1,'Frequency',S.colHdr), xlStr(7,r-1,'Deadline',S.colHdr),
    xlStr(8,r-1,'Enforcing Authority',S.colHdr), xlStr(9,r-1,'Penalty',S.colHdr),
    xlStr(10,r-1,'Details',S.colHdr), xlStr(11,r-1,'Status',S.colHdr)
  ]));

  sorted.forEach(law => {
    const [bs,rs,ls] = getPriorityStyles(law.priority);
    law.actions.forEach(a => {
      rows.push(xlRow(r++, 36, [
        xlNum(1,r-1,sr++,rs), xlStr(2,r-1,getPriorityLabel(law.priority),bs),
        xlStr(3,r-1,law.shortName,ls), xlStr(4,r-1,law.category,rs),
        xlStr(5,r-1,a.title,ls), xlStr(6,r-1,a.freq,S.freq_cell),
        xlStr(7,r-1,a.deadline,S.dead_cell), xlStr(8,r-1,a.authority,S.auth_cell),
        xlStr(9,r-1,a.penalty,S.pen_cell), xlStr(10,r-1,a.desc||'',S.norm),
        xlStr(11,r-1,'[ ] Pending',S.norm)
      ]));
    });
  });

  const cols = col(1,1,6)+col(2,2,13)+col(3,3,27)+col(4,4,17)+col(5,5,35)+col(6,6,13)+col(7,7,22)+col(8,8,25)+col(9,9,30)+col(10,10,40)+col(11,11,13);
  return wrapSheet(cols, rows.join(''), 2);
}

// ── SHEET 4: COMPLIANCE CALENDAR ──
function buildCalendarSheet() {
  const buckets = {'One-time':[],'Monthly':[],'Quarterly':[],'Half-yearly':[],'Annual':[],'As required':[]};
  function classify(freq) {
    const f = freq.toLowerCase();
    if(f.includes('one-time')||f.includes('one time')||f.includes('per employee')||f.includes('per contract')||f.includes('per worker')||f.includes('per consignment')||f.includes('per mark')||f.includes('per work')||f.includes('per product')||f.includes('per project')||f.includes('per transaction')) return 'One-time';
    if(f.includes('month')) return 'Monthly';
    if(f.includes('quarter')) return 'Quarterly';
    if(f.includes('half')) return 'Half-yearly';
    if(f.includes('annual')||f.includes('year')||f.includes('every 3')||f.includes('10 year')) return 'Annual';
    return 'As required';
  }
  const sorted = [...allResults].sort((a,b)=>{const po={critical:0,high:1,medium:2,low:3};return po[a.priority]-po[b.priority];});
  sorted.forEach(law => law.actions.forEach(a => buckets[classify(a.freq)].push({law, action:a})));

  const bucketStyleMap = {'One-time':S.cal_onetime,'Monthly':S.cal_monthly,'Quarterly':S.cal_quarterly,'Half-yearly':S.cal_halfy,'Annual':S.cal_annual,'As required':S.cal_asreq};
  const bucketLabel = {'One-time':'ONE-TIME SETUP','Monthly':'MONTHLY (Recurring)','Quarterly':'QUARTERLY','Half-yearly':'HALF-YEARLY','Annual':'ANNUAL','As required':'AS REQUIRED / ONGOING'};

  const rows = [];
  let r = 1;
  rows.push(xlRow(r++, 14, [xlStr(1,r-1,'Compliance Calendar - Actions Grouped by Frequency', S.secHdr)]));

  Object.entries(buckets).forEach(([bucket, items]) => {
    if(!items.length) return;
    rows.push(xlRow(r++, 6, [xlBlank(1,r-1, S.blank)]));
    rows.push(xlRow(r++, 22, [xlStr(1,r-1,bucketLabel[bucket] + '  (' + items.length + ' actions)', bucketStyleMap[bucket])]));
    rows.push(xlRow(r++, 0, [
      xlStr(1,r-1,'Priority',S.colHdr), xlStr(2,r-1,'Law Name',S.colHdr), xlStr(3,r-1,'Action Required',S.colHdr),
      xlStr(4,r-1,'Deadline',S.colHdr), xlStr(5,r-1,'Enforcing Authority',S.colHdr), xlStr(6,r-1,'Penalty',S.colHdr)
    ]));
    items.forEach(({law, action:a}) => {
      const [bs,rs,ls] = getPriorityStyles(law.priority);
      rows.push(xlRow(r++, 32, [
        xlStr(1,r-1,getPriorityLabel(law.priority),bs), xlStr(2,r-1,law.shortName,ls),
        xlStr(3,r-1,a.title,rs), xlStr(4,r-1,a.deadline,S.dead_cell),
        xlStr(5,r-1,a.authority,S.auth_cell), xlStr(6,r-1,a.penalty,S.pen_cell)
      ]));
    });
  });

  const cols = col(1,1,14)+col(2,2,30)+col(3,3,38)+col(4,4,27)+col(5,5,28)+col(6,6,35);
  return wrapSheet(cols, rows.join(''), 2);
}

// ── SHEET 5: URGENT ACTIONS ──
function buildUrgentSheet() {
  const urgent = allResults
    .filter(l => l.priority === 'critical' || l.priority === 'high')
    .sort((a,b) => {const po={critical:0,high:1}; return po[a.priority]-po[b.priority];});
  const rows = [];
  let r = 1;
  rows.push(xlRow(r++, 14, [xlStr(1,r-1,'Urgent Action Required - Critical & High Priority Only', S.secHdr)]));
  rows.push(xlRow(r++, 14, [xlStr(1,r-1,'These compliance actions carry the highest risk of penalties, business closure, or imprisonment. Address these IMMEDIATELY.', S.subtitle)]));
  rows.push(xlRow(r++, 6, [xlBlank(1,r-1, S.blank)]));
  rows.push(xlRow(r++, 0, [
    xlStr(1,r-1,'Priority',S.colHdr), xlStr(2,r-1,'Law / Act',S.colHdr),
    xlStr(3,r-1,'Action Required',S.colHdr), xlStr(4,r-1,'Deadline',S.colHdr),
    xlStr(5,r-1,'Penalty',S.colHdr), xlStr(6,r-1,'Enforcing Authority',S.colHdr),
    xlStr(7,r-1,'Done?',S.colHdr)
  ]));
  urgent.forEach(law => {
    const [bs,rs,ls] = getPriorityStyles(law.priority);
    law.actions.forEach(a => {
      rows.push(xlRow(r++, 32, [
        xlStr(1,r-1,getPriorityLabel(law.priority),bs), xlStr(2,r-1,law.shortName,ls),
        xlStr(3,r-1,a.title,ls), xlStr(4,r-1,a.deadline,S.dead_cell),
        xlStr(5,r-1,a.penalty,S.pen_cell), xlStr(6,r-1,a.authority,S.auth_cell),
        xlStr(7,r-1,'[ ]',rs)
      ]));
    });
  });
  const cols = col(1,1,14)+col(2,2,28)+col(3,3,38)+col(4,4,24)+col(5,5,34)+col(6,6,28)+col(7,7,8);
  return wrapSheet(cols, rows.join(''), 4);
}

// ── MINIMAL ZIP BUILDER ──
const _crcTable = (() => {
  const t = new Uint32Array(256);
  for(let i=0;i<256;i++){let c=i;for(let j=0;j<8;j++)c=(c&1)?(0xEDB88320^(c>>>1)):(c>>>1);t[i]=c;}
  return t;
})();

function _crc32(buf) {
  let c = 0xFFFFFFFF;
  for(let i=0;i<buf.length;i++) c=(c>>>8)^_crcTable[(c^buf[i])&0xFF];
  return (c^0xFFFFFFFF)>>>0;
}

function _u32(n) { const b=new Uint8Array(4); b[0]=n&0xFF; b[1]=(n>>8)&0xFF; b[2]=(n>>16)&0xFF; b[3]=(n>>24)&0xFF; return b; }
function _u16(n) { return new Uint8Array([n&0xFF,(n>>8)&0xFF]); }
function _str2u8(s) { return new TextEncoder().encode(s); }

function _buildZip(files) {
  const enc = new TextEncoder();
  const parts = [];
  const cdParts = [];
  let offset = 0;

  files.forEach(({name, data}) => {
    const nameBuf = enc.encode(name);
    const dataBuf = typeof data === 'string' ? enc.encode(data) : data;
    const crc = _crc32(dataBuf);
    const size = dataBuf.length;

    // Local file header (signature + 26 bytes fixed + filename)
    const lh = new Uint8Array(30 + nameBuf.length);
    lh.set([0x50,0x4B,0x03,0x04]);  // signature
    lh.set(_u16(20),  4);  // version needed
    lh.set(_u16(0),   6);  // general flags
    lh.set(_u16(0),   8);  // compression: stored
    lh.set(_u16(0),  10);  // mod time
    lh.set(_u16(0),  12);  // mod date
    lh.set(_u32(crc),14);  // crc32
    lh.set(_u32(size),18); // compressed size
    lh.set(_u32(size),22); // uncompressed size
    lh.set(_u16(nameBuf.length),26); // filename length
    lh.set(_u16(0),  28); // extra field length
    lh.set(nameBuf,  30);

    parts.push(lh, dataBuf);

    // Central directory entry
    const cd = new Uint8Array(46 + nameBuf.length);
    cd.set([0x50,0x4B,0x01,0x02]);  // signature
    cd.set(_u16(20),  4);  // version made by
    cd.set(_u16(20),  6);  // version needed
    cd.set(_u16(0),   8);  // flags
    cd.set(_u16(0),  10);  // compression
    cd.set(_u16(0),  12);  // mod time
    cd.set(_u16(0),  14);  // mod date
    cd.set(_u32(crc),16);  // crc32
    cd.set(_u32(size),20); // compressed size
    cd.set(_u32(size),24); // uncompressed size
    cd.set(_u16(nameBuf.length),28); // filename length
    cd.set(_u16(0),  30);  // extra field length
    cd.set(_u16(0),  32);  // comment length
    cd.set(_u16(0),  34);  // disk start
    cd.set(_u16(0),  36);  // internal attributes
    cd.set(_u32(0),  38);  // external attributes
    cd.set(_u32(offset),42); // local header offset
    cd.set(nameBuf,  46);
    cdParts.push(cd);

    offset += lh.length + size;
  });

  const cdOffset = offset;
  const cdSize = cdParts.reduce((s,p)=>s+p.length,0);

  const eocd = new Uint8Array(22);
  eocd.set([0x50,0x4B,0x05,0x06]);  // signature
  eocd.set(_u16(0), 4);  // disk number
  eocd.set(_u16(0), 6);  // disk with CD
  eocd.set(_u16(files.length), 8);  // entries on disk
  eocd.set(_u16(files.length),10);  // total entries
  eocd.set(_u32(cdSize),12);        // CD size
  eocd.set(_u32(cdOffset),16);      // CD offset
  eocd.set(_u16(0),20);             // comment length

  const allParts = [...parts, ...cdParts, eocd];
  const total = allParts.reduce((s,p)=>s+p.length,0);
  const out = new Uint8Array(total);
  let pos = 0;
  allParts.forEach(p => { out.set(p,pos); pos+=p.length; });
  return out;
}

// ── MASTER EXPORT ──
function exportToExcel() {
  if(!allResults || !allResults.length) {
    alert('Please complete the compliance analysis first.');
    return;
  }
  const btn = document.getElementById('xlsBtn');
  btn.textContent = 'Generating...';
  btn.disabled = true;

  setTimeout(() => {
    try {
      const files = [
        {name:'[Content_Types].xml',      data:CONTENT_TYPES_XML},
        {name:'_rels/.rels',              data:RELS_XML},
        {name:'xl/workbook.xml',          data:WORKBOOK_XML},
        {name:'xl/_rels/workbook.xml.rels',data:WORKBOOK_RELS_XML},
        {name:'xl/styles.xml',            data:buildStylesXml()},
        {name:'xl/worksheets/sheet1.xml', data:buildDashboardSheet()},
        {name:'xl/worksheets/sheet2.xml', data:buildLawsSheet()},
        {name:'xl/worksheets/sheet3.xml', data:buildChecklistSheet()},
        {name:'xl/worksheets/sheet4.xml', data:buildCalendarSheet()},
        {name:'xl/worksheets/sheet5.xml', data:buildUrgentSheet()},
      ];
      const zip = _buildZip(files);
      const blob = new Blob([zip], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const safe = (formData.companyName||'Company').replace(/[^a-z0-9]/gi,'_');
      const date = new Date().toISOString().slice(0,10);
      a.href = url;
      a.download = `LexComply_${safe}_${date}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch(err) {
      alert('Export failed: ' + err.message);
      console.error(err);
    } finally {
      btn.textContent = 'Download Excel Report';
      btn.disabled = false;
    }
  }, 100);
}
