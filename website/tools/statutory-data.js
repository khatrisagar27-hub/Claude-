// ── STATUTORY FIGURES ──
// Every rate, threshold, cap and due date the tools use lives in this one file.
// Nothing statutory is hardcoded in the calculators or the page.
//
// HOW TO VERIFY
// 1. Check each block below against the Act, rules or notification named in its
//    `source` line.
// 2. Correct any figure here. The tools pick it up; no other file changes.
// 3. Set `verifiedOn` (ISO date) and `verifiedBy`. Until `verifiedOn` is filled,
//    every tool that reads a figure from this file shows a
//    "figures pending verification by the firm" notice.
// 4. Clear `verifiedOn` again whenever a Finance Act, notification or rule
//    changes one of these figures and it has not been rechecked.
//
// These figures were compiled from secondary sources in November 2026. They have
// NOT been checked against the bare Act or the official portals.
(function (root) {
  'use strict';
  var INF = Infinity;

  var DATA = {
    verifiedOn: '',
    verifiedBy: '',

    // ── INCOME-TAX: resident individual, income taxed at normal rates ──
    incomeTax: {
      source: 'FY 2025-26: Income-tax Act, 1961, s.115BAC(1A) and Finance Act, 2025, First Schedule. ' +
              'Tax year 2026-27: Income-tax Act, 2025 as amended by Finance Act, 2026 (slabs reported unchanged).',
      cess: 0.04,                       // health and education cess on tax plus surcharge
      roundTo: 10,                      // total income and tax are rounded to the nearest Rs 10
      years: ['FY 2026-27', 'FY 2025-26'],
      regimes: {
        // Same figures for both years listed above.
        newRegime: {
          label: 'New regime',
          slabs: [[400000, 0], [800000, 0.05], [1200000, 0.10], [1600000, 0.15], [2000000, 0.20], [2400000, 0.25], [INF, 0.30]],
          standardDeduction: 75000,     // from salary or pension income
          rebateLimit: 1200000,         // total income up to which the rebate applies
          rebateMax: 60000,
          rebateMarginalRelief: true,   // above the limit, tax cannot exceed the income over the limit
          surcharge: [[5000000, 0], [10000000, 0.10], [20000000, 0.15], [INF, 0.25]]
        },
        oldRegime: {
          label: 'Old regime',
          slabsByAge: {
            below60: [[250000, 0], [500000, 0.05], [1000000, 0.20], [INF, 0.30]],
            senior: [[300000, 0], [500000, 0.05], [1000000, 0.20], [INF, 0.30]],      // 60 to 79 years
            superSenior: [[500000, 0], [1000000, 0.20], [INF, 0.30]]                  // 80 years and above
          },
          standardDeduction: 50000,
          rebateLimit: 500000,
          rebateMax: 12500,
          rebateMarginalRelief: false,
          surcharge: [[5000000, 0], [10000000, 0.10], [20000000, 0.15], [50000000, 0.25], [INF, 0.37]]
        }
      }
    },

    // ── ADVANCE TAX ──
    advanceTax: {
      source: 'Income-tax Act, 1961, ss.208, 211 (Income-tax Act, 2025: advance tax provisions).',
      threshold: 10000,                 // payable only if the liability for the year is Rs 10,000 or more
      // [month (1-12), day, cumulative share of the liability]
      instalments: [[6, 15, 0.15], [9, 15, 0.45], [12, 15, 0.75], [3, 15, 1.00]],
      presumptive: [[3, 15, 1.00]]      // presumptive-income taxpayers: whole amount by 15 March
    },

    // ── TDS: payments to residents ──
    tds: {
      source: 'Income-tax Act, 2025, s.393 (tables), s.397 (no PAN), s.398(3) (interest), s.427 (late fee). ' +
              '1961 Act references are shown against each row.',
      noPanRate: 0.20,                  // or the row's own rate if higher; a row may set its own noPanRate
      interestLateDeduction: 0.01,      // per month or part, from the date deductible to the date deducted
      interestLateDeposit: 0.015,       // per month or part, from the date deducted to the date deposited
      lateFeePerDay: 200,               // per day of delay in the statement, capped at the tax deductible
      // kind: 'aggregate' = applies once payments in the year cross the threshold
      //       'single'    = applies when this one payment reaches the threshold
      //       'monthly'   = threshold is per month
      //       'excess'    = tax only on the amount above the threshold
      // `single` (optional) adds a per-payment limit alongside an aggregate one.
      rows: [
        { id: 'contractor-ind', label: 'Contractor: payee is an individual or HUF', old: '194C', rate: 0.01, kind: 'aggregate', threshold: 100000, single: 30000 },
        { id: 'contractor-oth', label: 'Contractor: any other payee', old: '194C', rate: 0.02, kind: 'aggregate', threshold: 100000, single: 30000 },
        { id: 'professional', label: 'Professional fees', old: '194J', rate: 0.10, kind: 'aggregate', threshold: 50000 },
        { id: 'technical', label: 'Technical services, call centre, royalty on films', old: '194J', rate: 0.02, kind: 'aggregate', threshold: 50000 },
        { id: 'commission', label: 'Commission or brokerage', old: '194H', rate: 0.02, kind: 'aggregate', threshold: 20000 },
        { id: 'rent-plant', label: 'Rent: plant, machinery or equipment', old: '194-I', rate: 0.02, kind: 'monthly', threshold: 50000 },
        { id: 'rent-land', label: 'Rent: land, building or furniture', old: '194-I', rate: 0.10, kind: 'monthly', threshold: 50000 },
        { id: 'rent-individual', label: 'Rent paid by an individual or HUF not liable to tax audit', old: '194-IB', rate: 0.02, kind: 'monthly', threshold: 50000 },
        { id: 'interest-bank', label: 'Interest paid by a bank, co-operative bank or post office', old: '194A', rate: 0.10, kind: 'aggregate', threshold: 50000 },
        { id: 'interest-senior', label: 'Interest paid by a bank to a senior citizen', old: '194A', rate: 0.10, kind: 'aggregate', threshold: 100000 },
        { id: 'interest-other', label: 'Interest paid by any other payer', old: '194A', rate: 0.10, kind: 'aggregate', threshold: 10000 },
        { id: 'dividend', label: 'Dividend', old: '194', rate: 0.10, kind: 'aggregate', threshold: 10000 },
        { id: 'goods', label: 'Purchase of goods (buyer turnover above Rs 10 crore)', old: '194Q', rate: 0.001, kind: 'excess', threshold: 5000000, noPanRate: 0.05 },
        { id: 'property', label: 'Purchase of immovable property', old: '194-IA', rate: 0.01, kind: 'single', threshold: 5000000 },
        { id: 'partner', label: 'Salary, interest or commission to a partner', old: '194T', rate: 0.10, kind: 'aggregate', threshold: 20000 },
        { id: 'perquisite', label: 'Benefit or perquisite of business or profession', old: '194R', rate: 0.10, kind: 'aggregate', threshold: 20000 },
        { id: 'individual-payer', label: 'Contract or professional payment by an individual or HUF', old: '194M', rate: 0.02, kind: 'aggregate', threshold: 5000000 }
      ]
    },

    // ── GST ──
    gst: {
      source: 'CGST Act, 2017, s.47 (late fee) and s.50 (interest); Notifications 19/2021-CT, 20/2021-CT and 07/2023-CT. ' +
              'Late-fee figures are CGST and SGST together.',
      interestRate: 0.18,               // per annum, on tax paid late in cash
      commonRates: [0, 0.25, 3, 5, 12, 18, 28, 40],
      lateFee: {
        perDay: 50,
        perDayNil: 20,
        capNil: 500,
        // [aggregate turnover up to, cap per return] for GSTR-1 and GSTR-3B with tax
        caps: [[15000000, 2000], [50000000, 5000], [INF, 10000]],
        // GSTR-9: [turnover up to, fee per day, cap as a share of turnover]
        annual: [[50000000, 50, 0.0004], [200000000, 100, 0.0004], [INF, 200, 0.005]]
      },
      stateCodes: {
        '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab', '04': 'Chandigarh', '05': 'Uttarakhand',
        '06': 'Haryana', '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh', '10': 'Bihar', '11': 'Sikkim',
        '12': 'Arunachal Pradesh', '13': 'Nagaland', '14': 'Manipur', '15': 'Mizoram', '16': 'Tripura', '17': 'Meghalaya',
        '18': 'Assam', '19': 'West Bengal', '20': 'Jharkhand', '21': 'Odisha', '22': 'Chhattisgarh', '23': 'Madhya Pradesh',
        '24': 'Gujarat', '25': 'Daman and Diu (before merger)', '26': 'Dadra and Nagar Haveli and Daman and Diu',
        '27': 'Maharashtra', '28': 'Andhra Pradesh (before division)', '29': 'Karnataka', '30': 'Goa', '31': 'Lakshadweep',
        '32': 'Kerala', '33': 'Tamil Nadu', '34': 'Puducherry', '35': 'Andaman and Nicobar Islands', '36': 'Telangana',
        '37': 'Andhra Pradesh', '38': 'Ladakh', '97': 'Other Territory', '99': 'Centre Jurisdiction'
      }
    },

    // ── MSME PAYMENTS ──
    msme: {
      source: 'Micro, Small and Medium Enterprises Development Act, 2006, ss.15 and 16.',
      maxCreditDays: 45,                // agreed credit period cannot exceed 45 days
      noAgreementDays: 15,              // where there is no written agreement
      interestMultiple: 3               // compound interest, monthly rests, at three times the RBI bank rate
    },

    // ── COMPANIES ACT ──
    companies: {
      source: 'Companies Act, 2013, ss.92, 96, 137, 139 and Schedule II; LLP Rules, 2009, rr.24, 25; ' +
              'Companies (Registration Offices and Fees) Rules, 2014.',
      agmMonthsFromYearEnd: 6,
      firstAgmMonthsFromYearEnd: 9,
      aoc4DaysFromAgm: 30,
      mgt7DaysFromAgm: 60,
      adt1DaysFromAgm: 15,
      llpForm11DaysFromYearEnd: 60,
      llpForm8DaysAfterSixMonths: 30,
      additionalFeePerDay: 100,         // AOC-4 and MGT-7 filed late
      scheduleIIResidualMax: 0.05,
      // Useful lives from Schedule II, Part C: [class, years]
      usefulLives: [
        ['Buildings, RCC frame (other than factory)', 60],
        ['Buildings, other than RCC frame', 30],
        ['Factory buildings', 30],
        ['Plant and machinery, general', 15],
        ['Continuous process plant', 25],
        ['Furniture and fittings, general', 10],
        ['Office equipment', 5],
        ['Computers: end-user devices', 3],
        ['Computers: servers and networks', 6],
        ['Electrical installations and equipment', 10],
        ['Motor cars (not used for hire)', 8],
        ['Motor cycles and scooters', 10],
        ['Buses and lorries used for hire', 6],
        ['Laboratory equipment, general', 10]
      ]
    },

    // ── SCHEDULE III PRESENTATION ──
    scheduleIII: {
      source: 'Companies Act, 2013, Schedule III, Division I (as amended with effect from 1 April 2021).',
      // Upper limit of each bucket in months from the due date of payment; the last is open-ended.
      receivableBuckets: [['Less than 6 months', 6], ['6 months to 1 year', 12], ['1 to 2 years', 24], ['2 to 3 years', 36], ['More than 3 years', INF]],
      payableBuckets: [['Less than 1 year', 12], ['1 to 2 years', 24], ['2 to 3 years', 36], ['More than 3 years', INF]],
      ratioVarianceFlag: 0.25           // a change above 25% over the previous year needs an explanation
    },

    // ── AUDIT SAMPLING FACTORS (methodology, not statute) ──
    sampling: {
      source: 'Monetary unit sampling confidence and expansion factors as tabulated in the AICPA Audit Guide, Audit Sampling. ' +
              'SA 530 does not prescribe a formula; set these to the firm\'s methodology.',
      // confidence level -> [confidence factor, expansion factor for expected misstatement]
      mus: { '99': [4.61, 1.9], '95': [3.00, 1.6], '90': [2.31, 1.5], '85': [1.90, 1.4], '80': [1.61, 1.3] },
      // Benford first-digit conformity by mean absolute deviation (Nigrini)
      benfordMad: [[0.006, 'Close conformity'], [0.012, 'Acceptable conformity'], [0.015, 'Marginally acceptable conformity'], [INF, 'Nonconformity']],
      chiSquareCritical5pc: 15.507,     // 8 degrees of freedom
      chiSquareCritical1pc: 20.090
    },

    // ── COMPLIANCE CALENDAR ──
    // m = month (1-12), d = day. `prev: true` marks a date that relates to the previous financial year.
    // AGM-linked company filings (ADT-1, AOC-4, MGT-7) are worked out from `companies` above,
    // for an AGM held on the last permitted day.
    // Check in particular: the 31 August return date and the 31 December revised-return date
    // after the Finance Act, 2026.
    calendar: {
      source: 'Income-tax Act and Rules (TDS deposit and statements, advance tax, returns as amended by Finance Act, 2026); ' +
              'CGST Rules, 2017, rr.59, 61, 61A, 62, 80; EPF Scheme, 1952, para 38; ESI (General) Regulations, 1950, reg.31; ' +
              'Companies Act, 2013 and LLP Rules, 2009.',
      monthly: [
        { d: 7, law: 'TDS', what: 'Deposit TDS and TCS for the previous month', except: { 4: null } },
        { d: 11, law: 'GST', what: 'GSTR-1 for the previous month (monthly filers)' },
        { d: 15, law: 'PF and ESI', what: 'PF and ESI contributions for the previous month' },
        { d: 20, law: 'GST', what: 'GSTR-3B for the previous month (monthly filers)' }
      ],
      fixed: [
        { m: 4, d: 30, law: 'TDS', what: 'Deposit TDS deducted in March', prev: true },
        { m: 4, d: 30, law: 'Company law', what: 'MSME Form I for October to March', prev: true },
        { m: 5, d: 15, law: 'TDS', what: 'TCS statement for January to March', prev: true },
        { m: 5, d: 30, law: 'Company law', what: 'LLP Form 11 (annual return)', prev: true },
        { m: 5, d: 31, law: 'TDS', what: 'TDS statements for January to March', prev: true },
        { m: 6, d: 15, law: 'Income-tax', what: 'Advance tax: first instalment (15%)' },
        { m: 6, d: 15, law: 'TDS', what: 'Form 16 to employees', prev: true },
        { m: 6, d: 30, law: 'Company law', what: 'DPT-3 (return of deposits)', prev: true },
        { m: 6, d: 30, law: 'Company law', what: 'DIR-3 KYC, for directors whose three-year cycle falls due this year' },
        { m: 4, d: 18, law: 'GST', what: 'CMP-08 for January to March (composition)', prev: true },
        { m: 4, d: 22, law: 'GST', what: 'GSTR-3B for January to March (quarterly filers; 22nd or 24th by State)', prev: true },
        { m: 4, d: 30, law: 'GST', what: 'GSTR-4 annual return (composition)', prev: true },
        { m: 7, d: 18, law: 'GST', what: 'CMP-08 for April to June (composition)' },
        { m: 7, d: 22, law: 'GST', what: 'GSTR-3B for April to June (quarterly filers; 22nd or 24th by State)' },
        { m: 10, d: 18, law: 'GST', what: 'CMP-08 for July to September (composition)' },
        { m: 10, d: 22, law: 'GST', what: 'GSTR-3B for July to September (quarterly filers; 22nd or 24th by State)' },
        { m: 1, d: 18, law: 'GST', what: 'CMP-08 for October to December (composition)' },
        { m: 1, d: 22, law: 'GST', what: 'GSTR-3B for October to December (quarterly filers; 22nd or 24th by State)' },
        { m: 4, d: 13, law: 'GST', what: 'GSTR-1 for January to March (quarterly filers)', prev: true },
        { m: 7, d: 13, law: 'GST', what: 'GSTR-1 for April to June (quarterly filers)' },
        { m: 7, d: 15, law: 'TDS', what: 'TCS statement for April to June' },
        { m: 7, d: 31, law: 'TDS', what: 'TDS statements for April to June' },
        { m: 7, d: 31, law: 'Income-tax', what: 'Return of income: individuals and others not liable to audit, without business income', prev: true },
        { m: 8, d: 31, law: 'Income-tax', what: 'Return of income: business or profession not liable to audit', prev: true },
        { m: 9, d: 15, law: 'Income-tax', what: 'Advance tax: second instalment (45%)' },
        { m: 9, d: 30, law: 'Income-tax', what: 'Tax audit report', prev: true },
        { m: 10, d: 13, law: 'GST', what: 'GSTR-1 for July to September (quarterly filers)' },
        { m: 10, d: 15, law: 'TDS', what: 'TCS statement for July to September' },
        { m: 10, d: 30, law: 'Company law', what: 'LLP Form 8 (statement of account and solvency)', prev: true },
        { m: 10, d: 31, law: 'TDS', what: 'TDS statements for July to September' },
        { m: 10, d: 31, law: 'Income-tax', what: 'Return of income: audit cases', prev: true },
        { m: 10, d: 31, law: 'Company law', what: 'MSME Form I for April to September' },
        { m: 11, d: 30, law: 'Income-tax', what: 'Return of income: transfer pricing cases', prev: true },
        { m: 12, d: 15, law: 'Income-tax', what: 'Advance tax: third instalment (75%)' },
        { m: 12, d: 31, law: 'Income-tax', what: 'Belated or revised return of income', prev: true },
        { m: 12, d: 31, law: 'GST', what: 'GSTR-9 and GSTR-9C (annual return and reconciliation)', prev: true },
        { m: 1, d: 13, law: 'GST', what: 'GSTR-1 for October to December (quarterly filers)' },
        { m: 1, d: 15, law: 'TDS', what: 'TCS statement for October to December' },
        { m: 1, d: 31, law: 'TDS', what: 'TDS statements for October to December' },
        { m: 3, d: 15, law: 'Income-tax', what: 'Advance tax: final instalment (100%)' }
      ]
    }
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = DATA;
  else root.SKA_DATA = DATA;
})(typeof self !== 'undefined' ? self : this);
