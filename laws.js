// Indian Law Compliance Database — 60+ Laws
const INDIAN_LAWS = [

// ══════════════════════════════════════════
// A. SOCIAL SECURITY LAWS
// ══════════════════════════════════════════
{
  id:'epf', name:"Employees' Provident Fund & Miscellaneous Provisions Act, 1952",
  shortName:'EPF & MP Act, 1952', category:'Social Security', priority:'critical',
  description:"Mandatory provident fund (retirement savings), employees' pension, and deposit-linked insurance for organised sector workers.",
  reason: c => c.totalEmployees >= 20 ? `Mandatory: company has ${c.totalEmployees} employees (threshold: 20)` : null,
  actions:[
    {title:'Register establishment with EPFO', freq:'One-time', deadline:'Within 30 days of reaching 20 employees', authority:'EPFO Regional Office', penalty:'Damages @ 5–25% of arrears + imprisonment up to 3 years', desc:'Obtain a 7-digit PF Code by registering on the EPFO Unified Shram Suvidha Portal.'},
    {title:'Deduct 12% of Basic+DA from employee salary (EPF)', freq:'Monthly', deadline:'15th of following month', authority:'EPFO', penalty:'Interest @ 12% p.a. + damages', desc:"Employee contributes 12% of basic+DA. Employer contributes 12% split as: 8.33% → EPS (Employees' Pension Scheme) and 3.67% → EPF."},
    {title:'File Electronic Challan cum Return (ECR)', freq:'Monthly', deadline:'15th of following month', authority:'EPFO portal', penalty:'₹5,000 per day of delay', desc:'Upload monthly ECR on the EPFO Unified Portal showing member-wise contribution details.'},
    {title:'Maintain statutory registers: Form 12A, 5, 10, 3A, 6A', freq:'Annual', deadline:'30th April each year', authority:'EPFO', penalty:'Fine', desc:'Maintain up-to-date wage and contribution registers as prescribed.'},
    {title:'Issue UAN (Universal Account Number) to every employee', freq:'One-time per employee', deadline:'At time of joining', authority:'EPFO', penalty:'Non-compliance', desc:'Seed Aadhaar, PAN, and bank account with UAN for every employee.'},
    {title:"File Annual PF Return (Form 3A and 6A)", freq:'Annual', deadline:'30th April', authority:'EPFO', penalty:'Fine', desc:"Annual member-wise and consolidated contribution statement."}
  ]
},
{
  id:'esi', name:"Employees' State Insurance Act, 1948",
  shortName:'ESI Act, 1948', category:'Social Security', priority:'critical',
  description:'Provides medical, sickness, maternity, disablement, and death benefits to insured employees and their families.',
  reason: c => (c.hasFactory && c.factoryWorkers >= 10) || (!c.hasFactory && c.totalEmployees >= 20)
    ? `Applicable: ${c.hasFactory ? 'factory with ' + c.factoryWorkers + ' workers' : c.totalEmployees + ' employees'}` : null,
  actions:[
    {title:'Register establishment with ESIC', freq:'One-time', deadline:'Within 15 days of applicability', authority:'ESIC Regional Office / Shram Suvidha Portal', penalty:'Imprisonment up to 2 years + fine up to ₹5,000', desc:'Register on ESIC portal and obtain Employer Code Number. Also register all covered employees (wages ≤ ₹21,000/month).'},
    {title:"Deduct employee's ESI contribution: 0.75% of wages", freq:'Monthly', deadline:'15th of following month', authority:'ESIC', penalty:'Damages + 12% p.a. interest', desc:"Applicable to employees earning up to ₹21,000/month gross (₹25,000 for persons with disability)."},
    {title:"Contribute employer's ESI: 3.25% of wages", freq:'Monthly', deadline:'15th of following month', authority:'ESIC', penalty:'Damages + interest', desc:'Employer pays 3.25% of gross wages of covered employees.'},
    {title:'File half-yearly returns (Form 5)', freq:'Half-yearly', deadline:'November 11 and May 11', authority:'ESIC', penalty:'Fine', desc:'Submit details of employees and wages for each half-year.'},
    {title:'Maintain accident book and submit accident reports', freq:'As required', deadline:'Within 24 hours of accident', authority:'ESIC', penalty:'Fine', desc:'Report any accidents causing injury or death to ESIC and local office.'},
    {title:'Display ESIC notice on premises', freq:'Permanent', deadline:'Immediately on registration', authority:'ESIC', penalty:'Fine', desc:'Mandatory notice stating registration details must be displayed at the workplace.'}
  ]
},
{
  id:'gratuity', name:'Payment of Gratuity Act, 1972',
  shortName:'Gratuity Act, 1972', category:'Social Security', priority:'critical',
  description:'Provides for payment of gratuity to employees upon retirement, resignation, or death after 5 years of continuous service.',
  reason: c => c.totalEmployees >= 10 ? `Applicable: company has ${c.totalEmployees} employees (threshold: 10). Once applicable, always applicable.` : null,
  actions:[
    {title:'Pay gratuity to eligible employees', freq:'As applicable', deadline:'Within 30 days of becoming due', authority:'Labour Commissioner', penalty:'10% p.a. simple interest + fine up to ₹1 lakh', desc:'Formula: (Last drawn basic+DA × 15 × No. of completed years) ÷ 26. Payable on resignation/retirement/death after 5 continuous years.'},
    {title:'Obtain gratuity insurance or create gratuity trust', freq:'Annual', deadline:'Within 1 year of applicability', authority:'Labour Commissioner / LIC', penalty:'Fine', desc:'Either obtain group gratuity insurance from LIC/insurance company or set up an approved gratuity fund.'},
    {title:'File Form F (nomination) from every employee', freq:'One-time per employee', deadline:'Within 30 days of joining', authority:'Employer records', penalty:'Fine', desc:'Each employee must nominate a beneficiary using Form F.'},
    {title:'Submit gratuity notice (Form A or B) to controlling authority', freq:'One-time', deadline:'On applicability', authority:'Labour Department', penalty:'Fine', desc:'Notify the Controlling Authority (Labour Commissioner) when the Act becomes applicable.'}
  ]
},
{
  id:'bonus', name:'Payment of Bonus Act, 1965',
  shortName:'Bonus Act, 1965', category:'Labour', priority:'high',
  description:'Mandates annual bonus payment to employees in establishments with 20 or more employees.',
  reason: c => c.totalEmployees >= 20 ? `Applicable: ${c.totalEmployees} employees (threshold: 20)` : null,
  actions:[
    {title:'Pay minimum bonus: 8.33% of annual wages (or ₹100, whichever is higher)', freq:'Annual', deadline:'Within 8 months of close of accounting year', authority:'Labour Department', penalty:'Imprisonment up to 6 months + fine up to ₹1,000', desc:'Minimum 8.33%, maximum 20% of salary/wages. Eligible employees: earning up to ₹21,000/month gross; calculated on ₹7,000 or minimum wage (whichever higher).'},
    {title:'Maintain bonus registers: Form A, B, C', freq:'Annual', deadline:'On computation / payment', authority:'Labour Department', penalty:'Fine', desc:'Form A: Computation of allocable surplus; Form B: Set-on/Set-off; Form C: Bonus paid.'},
    {title:'File annual bonus return (Form D)', freq:'Annual', deadline:'Within 30 days of payment', authority:'Labour Commissioner', penalty:'Fine', desc:'File Form D showing details of bonus paid to all employees.'}
  ]
},
{
  id:'maternity', name:'Maternity Benefit Act, 1961',
  shortName:'Maternity Benefit Act', category:'Labour', priority:'high',
  description:"Protects employment of women during maternity and entitles them to maternity benefit, nursing breaks, and other facilities.",
  reason: c => c.womenEmployees > 0 ? `Applicable: company employs ${c.womenEmployees} women` : null,
  actions:[
    {title:'Grant 26 weeks paid maternity leave (first 2 children)', freq:'As required', deadline:'On employee request', authority:'Labour Department', penalty:'Imprisonment up to 1 year + fine up to ₹5,000', desc:'26 weeks for first/second child; 12 weeks for third child onwards; 12 weeks for adoption/surrogacy. Pre-natal: 8 weeks.'},
    {title:'Set up crèche facility (if 50+ employees)', freq:'Permanent', deadline:'Ongoing', authority:'Labour Department', penalty:'Fine', desc:'Companies with 50+ employees must provide crèche within 500m. Women employees allowed 4 visits per day.'},
    {title:'Display notice about maternity benefit at conspicuous place', freq:'Permanent', deadline:'Immediately', authority:'Labour Department', penalty:'Fine', desc:'Mandatory notice must be displayed at workplace listing employee rights.'},
    {title:'Permit nursing breaks (2 per day until child is 15 months)', freq:'Daily', deadline:'Ongoing', authority:'Labour Department', penalty:'Fine', desc:'Two breaks per day for nursing mothers, in addition to regular intervals.'},
    {title:'Provide work-from-home option (where feasible)', freq:'As required', deadline:'On request', authority:'—', penalty:'Fine', desc:'For employers with 50+ employees, provide WFH option after 26 weeks if nature of work permits.'}
  ]
},
{
  id:'compworkers', name:"Employees' Compensation Act, 1923",
  shortName:"Employees' Compensation Act", category:'Social Security', priority:'high',
  description:'Requires employers to pay compensation for work-related injury, occupational disease, or death of employees.',
  reason: c => c.totalEmployees > 0 ? 'Applicable to all employers with workers in specified occupations' : null,
  actions:[
    {title:'Pay compensation for work injury / death', freq:'As required', deadline:'Within 30 days of death; on settlement for injuries', authority:'Commissioner for Employees\' Compensation', penalty:'Additional 50% of compensation as penalty + interest', desc:'Death: 50% of monthly wages × Relevant Factor OR ₹1.2 lakh minimum. Permanent total disablement: 60% × factor OR ₹1.4 lakh minimum.'},
    {title:'Obtain employer\'s liability insurance policy', freq:'Annual renewal', deadline:'Before policy expiry', authority:'Insurance Company', penalty:'Fine', desc:'Strongly recommended to obtain insurance for employees\' compensation liability.'},
    {title:'Maintain register of workers in Schedule-II occupations', freq:'Ongoing', deadline:'At all times', authority:'Factory Inspector / Labour Inspector', penalty:'Fine', desc:'Keep records of workers employed in hazardous/scheduled occupations.'},
    {title:'Report fatal accidents to Commissioner', freq:'As required', deadline:'Within 7 days of accident', authority:'Commissioner for Employees\' Compensation', penalty:'Fine', desc:'Notify the Commissioner for Employees\' Compensation immediately after a workplace fatality.'}
  ]
},

// ══════════════════════════════════════════
// B. LABOUR & EMPLOYMENT LAWS
// ══════════════════════════════════════════
{
  id:'factories', name:'Factories Act, 1948',
  shortName:'Factories Act, 1948', category:'Labour', priority:'critical',
  description:'Regulates health, safety, welfare, and working conditions in factories.',
  reason: c => c.hasFactory
    ? ((c.factoryHasPower && c.factoryWorkers >= 10) ? `Applicable: power-driven factory with ${c.factoryWorkers} workers (threshold 10)`
       : (!c.factoryHasPower && c.factoryWorkers >= 20) ? `Applicable: non-power factory with ${c.factoryWorkers} workers (threshold 20)` : null)
    : null,
  actions:[
    {title:'Obtain Factory Registration and License', freq:'One-time + Annual renewal', deadline:'Before commencing operations', authority:'Chief Inspector of Factories (State)', penalty:'Imprisonment up to 2 years + fine up to ₹2 lakh', desc:'Apply to the State Factory Inspector with prescribed Form 1 + plan/layout. Renew license annually before December 31.'},
    {title:'Appoint Occupier and notify to Inspector', freq:'One-time', deadline:'Before registration', authority:'Chief Inspector of Factories', penalty:'Fine', desc:'The "Occupier" (person responsible for factory management) must be registered and is personally liable for compliance.'},
    {title:'Maintain health, safety, and welfare provisions', freq:'Ongoing', deadline:'Continuous', authority:'Factory Inspector', penalty:'Fine up to ₹2 lakh per violation', desc:'Ensure cleanliness, drainage, ventilation, lighting, drinking water, latrines/urinals, first aid, canteen (if 250+ workers), shelter (if 150+ workers).'},
    {title:'Comply with working hours: max 9 hrs/day, 48 hrs/week', freq:'Daily', deadline:'Always', authority:'Factory Inspector', penalty:'Fine', desc:'No worker to work more than 9 hours/day or 48 hours/week. Overtime at 2× regular wages. Max 60 hours/week with permission.'},
    {title:'Grant earned leave: 1 day for every 20 days worked', freq:'Annual', deadline:'On request', authority:'Factory Inspector', penalty:'Fine', desc:'Workers who have worked 240+ days entitled to earned leave. Maximum accumulation: 30 days.'},
    {title:'Maintain factory registers and forms (Form 15, 16, 21, 22, 23)', freq:'Annual', deadline:'As prescribed', authority:'Factory Inspector', penalty:'Fine', desc:'Register of adult workers, overtime, accidents, dangerous occurrences, notices, annual returns.'},
    {title:'Submit annual return (Form 21)', freq:'Annual', deadline:'31st January of following year', authority:'Chief Inspector of Factories', penalty:'Fine', desc:'File annual return showing details of workers, working hours, accidents, etc.'}
  ]
},
{
  id:'shops', name:'Shops and Establishments Act (State-specific)',
  shortName:'Shops & Establishments Act', category:'Labour', priority:'critical',
  description:'State legislation governing working conditions in shops, commercial establishments, and offices (every state has its own Act).',
  reason: c => c.hasShop || c.totalEmployees > 0 ? 'Applicable to all shops and commercial establishments in states of operation' : null,
  actions:[
    {title:'Register establishment with local authority (within 30 days)', freq:'One-time + Annual renewal', deadline:'Within 30 days of opening', authority:'Labour Department / Municipal Corporation (State)', penalty:'Fine up to ₹5,000 depending on state', desc:'Register each office/shop/establishment in every state of operation. e.g., Maharashtra: MLWF portal; Karnataka: Dept of Labour; Delhi: Labour Dept.'},
    {title:'Display registration certificate at premises', freq:'Permanent', deadline:'Immediately on registration', authority:'Labour Department', penalty:'Fine', desc:'Original certificate must be displayed prominently at the establishment.'},
    {title:'Comply with working hours (max 9 hrs/day, 48 hrs/week)', freq:'Daily', deadline:'Always', authority:'Labour Inspector', penalty:'Fine', desc:'State-specific rules on opening/closing times, weekly holiday, and overtime.'},
    {title:'Maintain attendance, wage, and leave registers', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Statutory registers must be maintained; now digital maintenance allowed in most states.'},
    {title:'Submit annual return as per state rules', freq:'Annual', deadline:'January 31 (most states)', authority:'Labour Department', penalty:'Fine', desc:'Annual return covering employee details, wages, and leaves for the previous year.'}
  ]
},
{
  id:'minwages', name:'Minimum Wages Act, 1948',
  shortName:'Minimum Wages Act, 1948', category:'Labour', priority:'critical',
  description:'Requires employers to pay workers not less than the minimum wage fixed by the State/Central Government for scheduled employments.',
  reason: c => c.totalEmployees > 0 ? 'Applicable to all employers with employees in scheduled employments' : null,
  actions:[
    {title:'Pay minimum wages as notified by State / Central Government', freq:'Monthly', deadline:'Before 7th of following month', authority:'Labour Commissioner', penalty:'Imprisonment up to 6 months + fine up to ₹500 per violation', desc:'Check the current minimum wage rates for the relevant state and category of work (unskilled/semi-skilled/skilled/highly-skilled). Rates revised periodically.'},
    {title:'Display minimum wage rates at the workplace', freq:'Permanent', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'A notice showing the current applicable minimum wage rates must be displayed at a conspicuous place.'},
    {title:'Maintain wage register showing wages paid', freq:'Monthly', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Maintain muster roll-cum-wages register (Form XVII). Wage slips must be issued to workers.'},
    {title:'File annual return (Form III)', freq:'Annual', deadline:'1st February each year', authority:'Labour Commissioner', penalty:'Fine', desc:'Annual return showing number of workers, wages paid, and compliance with minimum wage requirements.'}
  ]
},
{
  id:'paywages', name:'Payment of Wages Act, 1936',
  shortName:'Payment of Wages Act, 1936', category:'Labour', priority:'high',
  description:'Ensures timely payment of wages and restricts unauthorised deductions for employees earning up to ₹24,000/month.',
  reason: c => c.totalEmployees > 0 ? 'Applicable to all establishments with employees' : null,
  actions:[
    {title:'Pay wages on time: by 7th (if <1000 employees) or 10th (if 1000+ employees)', freq:'Monthly', deadline:'7th or 10th of following month', authority:'Labour Commissioner', penalty:'Fine up to ₹7,500 per affected employee', desc:'Wages must be paid in legal tender (or bank transfer). No unauthorised deductions allowed.'},
    {title:'Issue wage slips to all employees', freq:'Monthly', deadline:'On payment day', authority:'Labour Inspector', penalty:'Fine', desc:'Wage slip must show gross wages, all deductions (with reasons), and net wages paid.'},
    {title:'Maintain wage register', freq:'Monthly', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Register showing wages paid to each employee, deductions, and signature/acknowledgement of receipt.'}
  ]
},
{
  id:'posh', name:'Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013',
  shortName:'POSH Act, 2013', category:'Labour', priority:'critical',
  description:'Protects women from sexual harassment at the workplace and requires setting up redressal committees.',
  reason: c => c.womenEmployees > 0 || c.totalEmployees >= 10 ? 'Applicable to all workplaces (mandatory ICC for 10+ employees)' : null,
  actions:[
    {title:'Constitute Internal Complaints Committee (ICC)', freq:'One-time + Re-constitute every 3 years', deadline:'Immediately', authority:'Labour Department', penalty:'Fine up to ₹50,000 for first offence; ₹1 lakh for repeat + business closure', desc:'ICC must have: a woman presiding officer, at least 2 employees (preferably women), and 1 external member from NGO. Minimum 50% members must be women.'},
    {title:'Display POSH policy and ICC details at workplace', freq:'Permanent', deadline:'Immediately', authority:'Labour Department', penalty:'Fine', desc:'POSH policy, ICC constitution, and contact details must be displayed prominently.'},
    {title:'Conduct POSH awareness training for all employees', freq:'Annual', deadline:'Ongoing', authority:'Employer', penalty:'Fine', desc:'Sensitisation workshops, training programmes, and orientation for new joiners.'},
    {title:'Submit annual POSH report to District Officer', freq:'Annual', deadline:'31st January each year', authority:'District Officer / Labour Department', penalty:'Fine', desc:'Annual report must include number of complaints received, disposed, and pending during the year.'},
    {title:'Prepare and distribute an anti-sexual harassment policy', freq:'One-time', deadline:'Immediately', authority:'Employer', penalty:'Fine', desc:'A written policy covering definition, complaint procedure, inquiry process, and protection against retaliation.'}
  ]
},
{
  id:'contractlabour', name:'Contract Labour (Regulation and Abolition) Act, 1970',
  shortName:'Contract Labour Act, 1970', category:'Labour', priority:'high',
  description:'Regulates employment of contract workers and defines obligations of principal employers and contractors.',
  reason: c => c.contractWorkers >= 20 ? `Applicable: company uses ${c.contractWorkers} contract workers (threshold: 20)` : null,
  actions:[
    {title:'Register as Principal Employer with Labour Commissioner', freq:'One-time', deadline:'Before engaging contract labour', authority:'Labour Commissioner', penalty:'Fine', desc:'Apply in Form I under the CLRA Rules to the Registering Officer for registration as Principal Employer.'},
    {title:'Ensure every contractor obtains a License', freq:'Per contract', deadline:'Before contract work begins', authority:'Labour Commissioner', penalty:'Imprisonment + fine', desc:'Each contractor must obtain a licence from the Licensing Officer. Principal employer must verify contractor licences.'},
    {title:'Ensure amenities for contract workers (rest rooms, drinking water, toilets)', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:"If contractor fails to provide amenities, principal employer is liable to provide them and recover costs from contractor's security deposit."},
    {title:'Maintain register of contractors (Form XII)', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Maintain details of all contractors engaged, their licences, number of workers deployed.'},
    {title:'File half-yearly return (Form VI-B)', freq:'Half-yearly', deadline:'15th February and 15th August', authority:'Labour Commissioner', penalty:'Fine', desc:'Return showing details of contractors and workers engaged.'}
  ]
},
{
  id:'industrialdisputes', name:'Industrial Disputes Act, 1947',
  shortName:'Industrial Disputes Act, 1947', category:'Labour', priority:'high',
  description:'Governs investigation and settlement of industrial disputes; regulates layoff, retrenchment, and closure.',
  reason: c => c.totalEmployees >= 1 && !['proprietorship','llp'].includes(c.entityType)
    ? 'Applicable to all industrial establishments' : c.totalEmployees >= 1 ? 'Applicable to all establishments with workers' : null,
  actions:[
    {title:'Comply with retrenchment notice requirements (100+ workers: govt permission needed)', freq:'As required', deadline:'3 months prior notice (100+ workers)', authority:'State Government / Labour Commissioner', penalty:'Retrenchment is void; workers reinstated with full back wages', desc:'Retrenchment of workers requires: 1 month notice or wages in lieu; priority to rehire if business resumes. 100+ workers: prior permission from State Government.'},
    {title:'Follow due process for layoffs (100+ workers: government permission)', freq:'As required', deadline:'Written notice before layoff', authority:'State Government', penalty:'Compensation payment obligation', desc:'Layoff compensation = 50% of basic + DA for each day of layoff. 100+ workers: Govt permission required.'},
    {title:'Display notice of standing orders or work rules', freq:'Permanent', deadline:'At all times', authority:'Labour Department', penalty:'Fine', desc:'Notices must be displayed in English and a language understood by the majority of workers.'},
    {title:'Constitute Works Committee (if 100+ workers)', freq:'One-time', deadline:'Within 30 days of reaching threshold', authority:'Labour Department', penalty:'Fine', desc:'Promote industrial peace; equal numbers of employer and worker representatives.'}
  ]
},
{
  id:'standingorders', name:'Industrial Employment (Standing Orders) Act, 1946',
  shortName:'Standing Orders Act, 1946', category:'Labour', priority:'medium',
  description:'Requires industrial establishments with 100+ workers to define and certify standing orders (rules of employment).',
  reason: c => c.totalEmployees >= 100 ? `Applicable: ${c.totalEmployees} employees (threshold: 100)` : null,
  actions:[
    {title:'Draft and get standing orders certified', freq:'One-time', deadline:'Within 6 months of reaching 100 workers', authority:'Certifying Officer (Labour Commissioner)', penalty:'Fine up to ₹500 per day', desc:'Draft standing orders covering classification of workers, terms of employment, leave rules, disciplinary procedures, grievance redressal.'},
    {title:'Display certified standing orders at workplace', freq:'Permanent', deadline:'Immediately after certification', authority:'Labour Department', penalty:'Fine', desc:'English + vernacular language copies must be displayed at main entrance and at other conspicuous places.'},
    {title:'File draft standing orders for certification (Form B)', freq:'One-time', deadline:'Within 6 months', authority:'Certifying Officer', penalty:'Fine', desc:'Submit draft along with prescribed form and fee to the Certifying Officer.'}
  ]
},
{
  id:'equalrem', name:'Equal Remuneration Act, 1976',
  shortName:'Equal Remuneration Act, 1976', category:'Labour', priority:'medium',
  description:'Prohibits discrimination in wages between men and women for same or similar work.',
  reason: c => c.womenEmployees > 0 && c.totalEmployees > c.womenEmployees ? 'Applicable: company employs both men and women' : null,
  actions:[
    {title:'Ensure equal pay for equal work regardless of gender', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine up to ₹10,000 + imprisonment up to 1 month', desc:'No discrimination in wages for men and women performing same or similar work.'},
    {title:'Maintain register of workers (Form D)', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Register showing names, nature of work, and wages paid to male and female workers.'},
    {title:'File annual return (Form D)', freq:'Annual', deadline:'January 31', authority:'Labour Commissioner', penalty:'Fine', desc:'Annual return showing male/female workforce and wages paid.'}
  ]
},
{
  id:'interstateMigrant', name:'Inter-State Migrant Workmen (Regulation of Employment and Conditions of Service) Act, 1979',
  shortName:'Inter-State Migrant Workmen Act', category:'Labour', priority:'medium',
  description:'Protects workers recruited from one state and employed in another, requiring registration and prescribed facilities.',
  reason: c => c.migrantWorkers >= 5 ? `Applicable: ${c.migrantWorkers} inter-state migrant workers (threshold: 5)` : null,
  actions:[
    {title:'Register as Principal Employer with Labour Commissioner', freq:'One-time', deadline:'Before engaging migrant workers', authority:'Labour Commissioner', penalty:'Imprisonment + fine', desc:'Apply in Form II to the Registering Officer. Contractor must also obtain a licence in the source and destination states.'},
    {title:'Provide journey allowance and displacement allowance', freq:'Per engagement', deadline:'Before journey', authority:'Labour Inspector', penalty:'Fine', desc:'Displacement allowance = 50% of monthly wages or ₹75 minimum; journey allowance (to and fro).'},
    {title:'Provide suitable accommodation, medical facilities, and protective clothing', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Principal employer must ensure these facilities are provided at the worksite.'},
    {title:'Maintain register of migrant workers (Form IX)', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Record with details of migrant workers including source state, date of engagement, wages.'}
  ]
},
{
  id:'childlabour', name:'Child Labour (Prohibition and Regulation) Act, 1986',
  shortName:'Child Labour Act, 1986', category:'Labour', priority:'critical',
  description:'Prohibits employment of children below 14 years in any occupation and adolescents (14–18) in hazardous occupations.',
  reason: c => true,
  actions:[
    {title:'ABSOLUTE BAN: Do not employ any person below 14 years', freq:'Permanent', deadline:'Always', authority:'Labour Department / Police', penalty:'Imprisonment 6 months–2 years + fine ₹20,000–₹50,000 (first offence). Repeat: 1–3 years', desc:'Employing a child is a cognisable and non-bailable offence. Includes unpaid/family work in commercial establishments.'},
    {title:'Do not employ adolescents (14–18 years) in hazardous processes', freq:'Permanent', deadline:'Always', authority:'Labour Department', penalty:'Fine + imprisonment', desc:'List of hazardous occupations includes mines, explosives, construction, chemical factories, and others listed in Schedule.'},
    {title:'Maintain register of adolescent workers (if employed in non-hazardous work)', freq:'Ongoing', deadline:'At all times', authority:'Labour Inspector', penalty:'Fine', desc:'Adolescents (14–18) may work in non-hazardous environments. Working hours max 6 hours/day, no night shift, no overtime.'}
  ]
},
{
  id:'apprentices', name:'Apprentices Act, 1961',
  shortName:'Apprentices Act, 1961', category:'Labour', priority:'medium',
  description:'Mandates engagement of apprentices in designated trades for establishments in specified industries.',
  reason: c => c.hasApprentices || c.isManufacturing || c.primarySector === 'manufacturing'
    ? 'Applicable to establishments in specified industries (manufacturing, IT, etc.)' : null,
  actions:[
    {title:'Engage apprentices as per prescribed quota (2.5–10% of total strength)', freq:'Annual', deadline:'As per DGT notification', authority:'Directorate General of Training (DGT)', penalty:'Fine up to ₹1,000 per quarter', desc:'Register on the BOAT (Board of Apprenticeship Training) portal and engage apprentices in each trade. Quota differs by industry.'},
    {title:'Pay apprentice stipend as per prescribed rates', freq:'Monthly', deadline:'On due date', authority:'DGT', penalty:'Fine', desc:'Stipend fixed by the Central Government based on trade and year of apprenticeship.'},
    {title:'Provide training as per Apprenticeship Training Scheme', freq:'Ongoing', deadline:'For duration of apprenticeship', authority:'DGT / Regional Directorate of Apprenticeship Training', penalty:'Fine', desc:'Theoretical and practical training must be provided as per the curriculum for each designated trade.'},
    {title:'Register apprenticeship contracts with BOAT', freq:'Per apprentice', deadline:'Within 3 months of engagement', authority:'BOAT', penalty:'Fine', desc:'Each apprenticeship agreement must be registered on the National Apprenticeship Training Scheme (NATS) / BOAT portal.'}
  ]
},
{
  id:'boca', name:'Building and Other Construction Workers (Regulation of Employment & Conditions of Service) Act, 1996',
  shortName:'BOCW Act, 1996', category:'Labour', priority:'high',
  description:'Regulates employment and working conditions of building and construction workers.',
  reason: c => c.hasConstruction && c.totalEmployees >= 10 ? `Applicable: construction activities with ${c.totalEmployees} workers` : null,
  actions:[
    {title:'Register as Establishment under BOCW Act', freq:'One-time', deadline:'60 days from commencement', authority:'State BOCW Welfare Board', penalty:'Fine', desc:'Every establishment employing 10+ construction workers must register.'},
    {title:'Pay 1% cess on cost of construction', freq:'Per project', deadline:'On commencement of project', authority:'State BOCW Welfare Board / Municipal Authority', penalty:'Penalty + interest', desc:'BOCW Cess is 1% of the total cost of construction. Collected by the assessing officer or municipal body.'},
    {title:'Register all construction workers with State Welfare Board', freq:'Per worker', deadline:'Within 90 days of engagement', authority:'State BOCW Welfare Board', penalty:'Fine', desc:'Workers register themselves; employer must facilitate registration and welfare fund contributions.'},
    {title:'Provide safety measures: helmets, harnesses, nets, first aid', freq:'Ongoing', deadline:'Always', authority:'BOCW Inspector', penalty:'Fine', desc:'Mandatory safety equipment for workers at height, in excavations, near machinery, etc.'}
  ]
},
{
  id:'rpwd', name:'Rights of Persons with Disabilities Act, 2016',
  shortName:'RPwD Act, 2016', category:'Labour', priority:'medium',
  description:'Protects rights of persons with disabilities; requires equal opportunity policy in establishments with 20+ employees.',
  reason: c => c.pwdEmployees > 0 || c.totalEmployees >= 20 ? 'Applicable: requires Equal Opportunity Policy for companies with 20+ employees' : null,
  actions:[
    {title:'Formulate and publish Equal Opportunity Policy', freq:'One-time', deadline:'Within 1 year', authority:'Chief Commissioner for Persons with Disabilities', penalty:'Fine up to ₹10,000', desc:"Policy must cover: list of posts reserved for PwD, facilities provided, manner of selection for PwD, list of liaison officer's name."},
    {title:'Register Equal Opportunity Policy with authorities', freq:'One-time', deadline:'Within 1 year', authority:'Chief Commissioner for Persons with Disabilities / DOPT', penalty:'Fine', desc:'File the policy with the appropriate authority.'},
    {title:'Maintain register of PwD employees', freq:'Ongoing', deadline:'At all times', authority:'Chief Commissioner', penalty:'Fine', desc:'Record of PwD employees, their disability certificates, and positions held.'},
    {title:'Ensure accessible infrastructure (ramps, accessible washrooms, etc.)', freq:'Ongoing', deadline:'Within reasonable time', authority:'District Magistrate', penalty:'Fine', desc:'Workplaces must progressively move towards accessibility standards.'}
  ]
},

// ══════════════════════════════════════════
// C. TAX LAWS
// ══════════════════════════════════════════
{
  id:'incometax', name:'Income Tax Act, 1961',
  shortName:'Income Tax Act, 1961', category:'Tax', priority:'critical',
  description:'Governs taxation of income of companies, LLPs, and individuals. Includes TDS, advance tax, and filing obligations.',
  reason: c => true,
  actions:[
    {title:'Obtain and quote PAN for all financial transactions', freq:'One-time', deadline:'Before commencing business', authority:'Income Tax Department', penalty:'₹10,000 fine; 20% TDS without PAN', desc:'Every company/LLP/firm must obtain a Permanent Account Number (PAN).'},
    {title:'Deduct TDS on salary, contractor payments, rent, interest, etc.', freq:'Monthly', deadline:'7th of following month (March: 30th April)', authority:'Income Tax Department (TRACES)', penalty:'1.5% per month interest + penalty equal to TDS amount', desc:'Deduct TDS at prescribed rates under Sections 192 (salary), 194C (contractor), 194I (rent), 194J (professional), etc. Deposit to Government by due date.'},
    {title:'File TDS Returns quarterly (Forms 24Q, 26Q, 27Q)', freq:'Quarterly', deadline:'31st July, 31st Oct, 31st Jan, 31st May', authority:'Income Tax Department / TRACES', penalty:'₹200/day late fee + penalty up to TDS amount', desc:'24Q: TDS on salary; 26Q: TDS on non-salary payments to residents; 27Q: TDS on non-resident payments.'},
    {title:'Pay Advance Tax (if liability > ₹10,000)', freq:'Quarterly', deadline:'15th June (15%), 15th Sept (45%), 15th Dec (75%), 15th Mar (100%)', authority:'Income Tax Department', penalty:'Interest u/s 234B and 234C (1% per month)', desc:'Applicable if tax liability after TDS exceeds ₹10,000. Companies must pay 100% advance tax by 15th March.'},
    {title:'File Annual Income Tax Return (ITR-6 for companies)', freq:'Annual', deadline:'31st October (if tax audit applicable), 31st July otherwise', authority:'Income Tax Department', penalty:'₹5,000 late fee + interest on tax due', desc:'Companies file ITR-6. LLPs file ITR-5. Proprietorships use ITR-3/4.'},
    {title:'Tax Audit (u/s 44AB): Turnover > ₹1 Cr (business) or ₹50L (profession)', freq:'Annual', deadline:'30th September', authority:'Chartered Accountant + Income Tax Department', penalty:'0.5% of turnover or ₹1.5 lakh (whichever lower) + interest', desc:'Tax audit by CA is mandatory if annual turnover exceeds ₹1 crore for business (₹10 crore for digital transactions) or ₹50 lakhs for professionals.'},
    {title:'Issue TDS Certificates (Form 16 / 16A)', freq:'Annual / Quarterly', deadline:'Form 16: 15th June; Form 16A: 15 days from due date of return', authority:'Income Tax Department', penalty:'₹100 per day per certificate', desc:'Issue Form 16 (salary) and Form 16A (non-salary TDS) to payees.'}
  ]
},
{
  id:'gst', name:'Goods and Services Tax (CGST / SGST / IGST) Acts, 2017',
  shortName:'GST Acts, 2017', category:'Tax', priority:'critical',
  description:'Unified indirect tax on supply of goods and services across India. Subsumes earlier taxes like VAT, Service Tax, and Excise Duty.',
  reason: c => {
    const t = parseInt(c.annualTurnover)||0;
    const isSpecialState = ['manipur','mizoram','nagaland','tripura','sikkim','meghalaya','arunachal','uttarakhand','himachal','jammu'].some(s => (c.statesOfOperation||[]).includes(s));
    const goodsThresh = isSpecialState ? 20 : 40;
    const servThresh = isSpecialState ? 10 : 20;
    if(t >= goodsThresh || t >= servThresh) return `Applicable: turnover ₹${t} Lakhs exceeds GST threshold`;
    if(c.doesImportExport) return 'Applicable: import/export business (mandatory GST registration)';
    if(c.isECommerce) return 'Applicable: e-commerce operators must register regardless of turnover';
    return null;
  },
  actions:[
    {title:'Obtain GST Registration', freq:'One-time', deadline:'Within 30 days of exceeding threshold', authority:'GST Portal (gstin.gov.in)', penalty:'10% of tax due (min ₹10,000) or 100% of tax if fraudulent', desc:'Register on gst.gov.in. GSTIN is mandatory. Separate registration required in each state of business.'},
    {title:'File GSTR-1 (Outward supplies)', freq:'Monthly or Quarterly', deadline:'11th of following month (monthly) / 13th of following month (quarterly - QRMP)', authority:'GST Portal', penalty:'₹50/day (₹25 CGST + ₹25 SGST), max ₹5,000', desc:'Upload all sales invoices, credit/debit notes, and amendments.'},
    {title:'File GSTR-3B (Monthly summary + tax payment)', freq:'Monthly', deadline:'20th of following month (large taxpayers)', authority:'GST Portal', penalty:'₹50/day + interest @ 18% p.a. on unpaid tax', desc:'Self-assessed summary of outward and inward supplies and payment of net GST liability.'},
    {title:'File GSTR-9 (Annual Return)', freq:'Annual', deadline:'31st December of following year', authority:'GST Portal', penalty:'₹200/day (max 0.25% of turnover)', desc:'Consolidated annual statement of all supplies made/received and tax paid during the year.'},
    {title:'Reconcile ITC (Input Tax Credit) with GSTR-2B', freq:'Monthly', deadline:'Before filing GSTR-3B', authority:'GST Portal', penalty:'Interest + reversal of excess ITC', desc:'Verify that ITC claimed matches auto-populated GSTR-2B from suppliers\' GSTR-1.'},
    {title:'Issue GST-compliant invoices for all supplies', freq:'Per transaction', deadline:'Before or at time of supply', authority:'GST Portal', penalty:'₹10,000 or 100% of tax per invoice', desc:'Invoices must contain: GSTIN, HSN/SAC code, tax rate, CGST/SGST/IGST amounts, place of supply.'},
    {title:'File e-way bill for goods movement (value > ₹50,000)', freq:'Per consignment', deadline:'Before goods movement', authority:'E-way Bill Portal (ewaybillgst.gov.in)', penalty:'₹10,000 or tax evaded (whichever higher) + detention of goods', desc:'Generate e-way bill for inter-state and intra-state movement of goods where value exceeds ₹50,000.'}
  ]
},
{
  id:'profTax', name:'Professional Tax (State-specific)',
  shortName:'Professional Tax', category:'Tax', priority:'medium',
  description:'State-level tax levied on salaried employees and professionals in certain states. Maximum ceiling ₹2,500/year.',
  reason: c => {
    const ptStates = ['maharashtra','karnataka','gujarat','westbengal','andhrapradesh','telangana','tamilnadu','madhyapradesh','assam','kerala','odisha','jharkhand','bihar','tripura','meghalaya','sikkim','manipur','mizoram','nagaland'];
    const ops = (c.statesOfOperation||[]).map(s=>s.toLowerCase());
    const applicable = ptStates.filter(s => ops.some(o => o.includes(s)));
    return applicable.length > 0 ? `Applicable in states: ${applicable.join(', ')}` : null;
  },
  actions:[
    {title:'Register for Professional Tax with State authority', freq:'One-time per state', deadline:'Within 30 days of applicability', authority:'State Commercial Tax / Labour Department', penalty:'Penalty varying by state (typically ₹5/day)', desc:'Register in each applicable state: e.g., Maharashtra PT Portal, Karnataka CTO, West Bengal PT authority.'},
    {title:'Deduct Professional Tax from employee salary', freq:'Monthly', deadline:'Last day of month', authority:'State authority', penalty:'Penalty + interest', desc:'PT deducted from employee salary as per state slab (usually ₹200/month for income above threshold; ₹300 for February in Maharashtra).'},
    {title:'File Professional Tax Returns and pay employer PT', freq:'Monthly / Annual (varies by state)', deadline:'Varies by state (e.g., Maharashtra: 31st March)', authority:'State authority', penalty:'Penalty + interest', desc:'Employer also pays PT on its own profession. File returns showing employees and PT deducted.'}
  ]
},

// ══════════════════════════════════════════
// D. COMPANY / CORPORATE LAW
// ══════════════════════════════════════════
{
  id:'companiesact', name:'Companies Act, 2013',
  shortName:'Companies Act, 2013', category:'Corporate', priority:'critical',
  description:'Comprehensive legislation governing incorporation, management, and winding up of companies in India.',
  reason: c => ['private_ltd','public_ltd','opc','section8','govt'].includes(c.entityType)
    ? `Applicable to all ${c.entityType.replace('_',' ')} companies` : null,
  actions:[
    {title:'Hold Annual General Meeting (AGM)', freq:'Annual', deadline:'Within 6 months of financial year end (by 30 Sep for Apr–Mar FY)', authority:'MCA / ROC', penalty:'Fine up to ₹1 lakh + ₹5,000/day for continuing default', desc:'Every company except OPC must hold AGM. Lay financial statements, appoint auditors, declare dividends, appoint directors.'},
    {title:'Hold minimum 4 Board Meetings per year', freq:'Quarterly', deadline:'Max gap 120 days between any two meetings', authority:'MCA / ROC', penalty:'Fine on company (₹25,000) and officers in default (₹5,000 each)', desc:'At least 4 board meetings per financial year with a maximum gap of 120 days between two meetings.'},
    {title:'File Annual Return (MGT-7 / MGT-7A for small companies)', freq:'Annual', deadline:'Within 60 days of AGM', authority:'MCA (ROC)', penalty:'₹100/day per day of delay', desc:'Contains details of shareholders, directors, meetings, and other corporate information.'},
    {title:'File Financial Statements (AOC-4)', freq:'Annual', deadline:'Within 30 days of AGM', authority:'MCA (ROC)', penalty:'₹100/day per day of delay', desc:'Balance Sheet, Profit & Loss, Cash Flow, Directors\' Report, Auditor\'s Report.'},
    {title:'Appoint Statutory Auditor and file ADT-1', freq:'Annual or as required', deadline:'Within 15 days of AGM', authority:'MCA (ROC)', penalty:'Fine', desc:'Appoint CA firm as statutory auditor. An individual auditor can be appointed for max 5 consecutive years, firm for 10 years.'},
    {title:'Complete Director KYC (DIR-3 KYC)', freq:'Annual', deadline:'30th September each year', authority:'MCA', penalty:'₹5,000 per director (DIN deactivated)', desc:'Every director with an active DIN must file DIR-3 KYC or DIR-3 KYC Web annually.'},
    {title:'CSR Compliance (if net worth ≥ ₹500 Cr OR turnover ≥ ₹1000 Cr OR net profit ≥ ₹5 Cr)', freq:'Annual', deadline:'Within 31st March of following year', authority:'MCA', penalty:'Fine ₹50,000–₹25 lakh + imprisonment up to 3 years for officers', desc:'Spend 2% of average net profit of last 3 years on CSR activities. Form CSR-1 for registration of CSR implementing agencies. File Form CSR-2.'},
    {title:'Maintain statutory registers (MGT-1, MGT-3, MBP-1, CHG-1, etc.)', freq:'Ongoing', deadline:'At all times', authority:'ROC', penalty:'Fine', desc:'Register of members, directors, charges, contracts, related parties, key managerial personnel.'},
    {title:'File XBRL Financial Statements (if applicable)', freq:'Annual', deadline:'With AOC-4', authority:'MCA', penalty:'Fine', desc:'Mandatory for listed companies and public companies with paid-up capital ≥ ₹5 crore or turnover ≥ ₹100 crore.'},
    {title:'Secretarial Audit (if listed or public company with large cap)', freq:'Annual', deadline:'With Board Report', authority:'Company Secretary in Practice', penalty:'Fine ₹1 lakh–₹5 lakh', desc:'Mandatory for: listed companies; unlisted public companies with paid-up capital ≥ ₹50Cr or turnover ≥ ₹250Cr; private companies with turnover ≥ ₹250Cr.'},
    {title:'Internal Audit (if applicable thresholds met)', freq:'Quarterly', deadline:'As per Board decision', authority:'Internal Auditor (CA / CMA)', penalty:'—', desc:'Mandatory for: listed companies; unlisted public companies with paid-up capital ≥ ₹50Cr, turnover ≥ ₹200Cr, loans ≥ ₹100Cr, deposits ≥ ₹25Cr.'}
  ]
},
{
  id:'llp', name:'Limited Liability Partnership Act, 2008',
  shortName:'LLP Act, 2008', category:'Corporate', priority:'critical',
  description:'Governs formation, management, and compliance obligations of Limited Liability Partnerships in India.',
  reason: c => c.entityType === 'llp' ? 'Applicable: entity is an LLP' : null,
  actions:[
    {title:'File Annual Return (Form 11)', freq:'Annual', deadline:'30th May each year', authority:'MCA (ROC)', penalty:'₹100/day per day of delay', desc:'Details of partners, changes during the year, and statements about business activities.'},
    {title:'File Statement of Accounts and Solvency (Form 8)', freq:'Annual', deadline:'30th October each year', authority:'MCA (ROC)', penalty:'₹100/day per day of delay', desc:'Balance Sheet and Statement of Income & Expenditure. Must be certified by a Designated Partner.'},
    {title:'Statutory Audit (if turnover > ₹40 lakh or contribution > ₹25 lakh)', freq:'Annual', deadline:'Before filing Form 8', authority:'Chartered Accountant', penalty:'Penal provisions under LLP Act', desc:'LLPs exceeding ₹40 lakh turnover or ₹25 lakh contribution must get accounts audited by a CA.'},
    {title:'Maintain proper books of accounts', freq:'Ongoing', deadline:'At all times', authority:'Partners', penalty:'Fine', desc:'Books must be kept at registered office; double-entry system recommended.'},
    {title:'Update KYC of Designated Partners (DPIN/DIN)', freq:'Annual', deadline:'30th September', authority:'MCA', penalty:'DPIN deactivated + ₹5,000 penalty', desc:'Each Designated Partner must complete annual KYC.'}
  ]
},
{
  id:'sebi_lodr', name:'SEBI (Listing Obligations and Disclosure Requirements) Regulations, 2015',
  shortName:'SEBI LODR Regulations', category:'Corporate', priority:'critical',
  description:'Governs compliance obligations of companies listed on Indian stock exchanges (NSE/BSE).',
  reason: c => c.isListed ? 'Applicable: company is listed on a stock exchange' : null,
  actions:[
    {title:'Publish quarterly financial results within 45 days of quarter end', freq:'Quarterly', deadline:'45 days from quarter end; 60 days for last quarter', authority:'SEBI / Stock Exchange', penalty:'Fine + suspension of trading', desc:'Quarterly unaudited (or audited for Q4) standalone and consolidated financial results must be published.'},
    {title:'File corporate governance compliance report (Reg 27)', freq:'Quarterly', deadline:'21 days from quarter end', authority:'Stock Exchange', penalty:'Fine ₹20,000–₹5 lakh per non-compliance', desc:'Details of board composition, committees, meetings, and other governance requirements.'},
    {title:'Ensure minimum public shareholding of 25%', freq:'Ongoing', deadline:'Always', authority:'SEBI', penalty:'Suspension of trading + other penalties', desc:'Listed companies must maintain at least 25% public float at all times.'},
    {title:'Disclose material events to stock exchange immediately', freq:'As required', deadline:'Within 24 hours of occurrence', authority:'Stock Exchange / SEBI', penalty:'Fine + suspension', desc:'Includes: board decisions, acquisition/disposal of significant assets, fraud, defaults, court orders, etc.'},
    {title:'Hold board meetings to approve quarterly results', freq:'Quarterly', deadline:'Within 45/60 days of quarter', authority:'Board of Directors', penalty:'SEBI action', desc:'Board must formally approve quarterly and annual financial results.'},
    {title:'Conduct Annual General Meeting within 6 months of FY end', freq:'Annual', deadline:'September 30 each year', authority:'ROC / SEBI', penalty:'Fine', desc:'Comply with both Companies Act 2013 AGM requirements and SEBI LODR.'},
    {title:'Maintain minimum board composition with independent directors', freq:'Ongoing', deadline:'Always', authority:'SEBI', penalty:'Fine up to ₹25 lakh per non-compliance', desc:'At least 1/3rd of board must be independent directors; 50% if executive chairman; at least one woman director.'}
  ]
},

// ══════════════════════════════════════════
// E. ENVIRONMENTAL LAWS
// ══════════════════════════════════════════
{
  id:'envprotection', name:'Environment Protection Act, 1986',
  shortName:'Environment Protection Act, 1986', category:'Environment', priority:'high',
  description:'Umbrella legislation for environmental protection; basis for Environmental Clearance, EIA, and environmental standards.',
  reason: c => c.hasFactory || c.hasMines || c.hasConstruction || c.generatesHazardousWaste || c.dealsPetroleum || c.primarySector === 'energy'
    ? 'Applicable: industrial/construction/mining activities' : null,
  actions:[
    {title:'Obtain Environmental Clearance (EC) for specified projects', freq:'One-time per project', deadline:'Before commencement', authority:'MoEFCC / State EIA Authority', penalty:'Imprisonment up to 5 years + fine up to ₹1 lakh + ₹5,000/day', desc:'Mandatory for: industries/mines above threshold size; highways; airports; ports; dams; SEZs. Prior EC is mandatory.'},
    {title:'Comply with Environmental Quality Standards', freq:'Ongoing', deadline:'Always', authority:'MoEFCC / SPCB', penalty:'Imprisonment + fine + closure', desc:'Comply with effluent, emission, noise, and other environmental standards prescribed under EPA.'},
    {title:'Submit annual environmental compliance reports', freq:'Annual', deadline:'As per EC conditions', authority:'MoEFCC / SPCB', penalty:'Penalty under EPA', desc:'Report compliance status with EC conditions and environmental standards.'},
    {title:'Maintain environment-related records for inspection', freq:'Ongoing', deadline:'At all times', authority:'SPCB Inspector', penalty:'Fine', desc:'Records of waste generation, treatment, disposal, and environmental parameters.'}
  ]
},
{
  id:'wateract', name:'Water (Prevention and Control of Pollution) Act, 1974',
  shortName:'Water Act, 1974', category:'Environment', priority:'high',
  description:'Prevents and controls water pollution; requires industries discharging effluents to obtain consent from State Pollution Control Boards.',
  reason: c => c.hasFactory || c.dischargesWastewater || c.generatesHazardousWaste
    ? 'Applicable: industrial effluent discharge or hazardous waste' : null,
  actions:[
    {title:'Obtain Consent to Establish (CTE) from State Pollution Control Board', freq:'One-time', deadline:'Before establishing plant/unit', authority:'State Pollution Control Board (SPCB)', penalty:'Imprisonment up to 6 years + fine', desc:"Apply to SPCB before setting up any industry that discharges effluents into water bodies."},
    {title:'Obtain Consent to Operate (CTO) / Annual Renewal', freq:'Annual', deadline:'Before expiry of existing CTO', authority:'SPCB', penalty:'Closure order + fine', desc:'CTO must be renewed annually (or as per SPCB timeline). Non-renewal = illegal operation.'},
    {title:'Install and operate Effluent Treatment Plant (ETP)', freq:'Ongoing', deadline:'Before receiving CTO', authority:'SPCB', penalty:'Closure order + fine', desc:'ETP must meet prescribed effluent standards before discharge into any water body or municipal drain.'},
    {title:'Maintain records of water consumption and effluent discharge', freq:'Monthly', deadline:'As per SPCB norms', authority:'SPCB', penalty:'Fine', desc:'Log book of daily effluent quality, quantity, and treatment records.'},
    {title:'Submit monthly/quarterly environmental reports to SPCB', freq:'Quarterly', deadline:'As per SPCB schedule', authority:'SPCB', penalty:'Fine', desc:'Reports on effluent quality and quantity treated/discharged.'}
  ]
},
{
  id:'airact', name:'Air (Prevention and Control of Pollution) Act, 1981',
  shortName:'Air Act, 1981', category:'Environment', priority:'high',
  description:'Controls air pollution from industrial and other sources; requires consent from State Pollution Control Boards.',
  reason: c => c.hasFactory || c.emitsAirPollutants || c.hasMines || c.hasConstruction
    ? 'Applicable: industrial air emission / dust generation' : null,
  actions:[
    {title:'Obtain Consent to Establish and Operate from SPCB', freq:'Annual renewal', deadline:'Before establishing / before renewal date', authority:'SPCB', penalty:'Imprisonment up to 6 years + fine', desc:'Required for all industrial plants that emit air pollutants. Applies across all industrial categories.'},
    {title:'Install Air Pollution Control Equipment (APCE)', freq:'Ongoing', deadline:'Before CTO', authority:'SPCB', penalty:'Closure + fine', desc:'Adequate dust collectors, scrubbers, electrostatic precipitators, or other approved equipment as required.'},
    {title:'Conduct stack emission monitoring', freq:'Quarterly', deadline:'Submit reports quarterly', authority:'SPCB', penalty:'Fine', desc:'Monitor and report stack emissions from chimneys and stacks as per prescribed frequency and standards.'},
    {title:'Comply with ambient air quality standards', freq:'Ongoing', deadline:'Always', authority:'SPCB / CPCB', penalty:'Fine + closure', desc:'Ensure that emissions from the plant do not cause ambient air quality to exceed prescribed standards.'}
  ]
},
{
  id:'hazwaste', name:'Hazardous and Other Wastes (Management and Transboundary Movement) Rules, 2016',
  shortName:'Hazardous Waste Rules, 2016', category:'Environment', priority:'high',
  description:'Regulates management, storage, transport, and disposal of hazardous waste by industrial units.',
  reason: c => c.generatesHazardousWaste || c.dealsChemicals ? 'Applicable: generates or deals in hazardous waste/chemicals' : null,
  actions:[
    {title:'Obtain Authorization from SPCB for hazardous waste handling', freq:'Annual renewal', deadline:'Before generating/storing/disposing hazardous waste', authority:'SPCB', penalty:'Imprisonment up to 5 years + fine', desc:'Apply in Form 1 to SPCB for authorisation. Renew annually.'},
    {title:'Maintain manifest for every hazardous waste consignment', freq:'Per consignment', deadline:'Before dispatch', authority:'SPCB', penalty:'Fine', desc:'Use the online HWMS system for manifests. Copy must accompany every consignment of hazardous waste.'},
    {title:'Dispose hazardous waste only through SPCB-authorised agencies', freq:'As required', deadline:'No accumulation beyond limits', authority:'SPCB / CPCB', penalty:'Fine + imprisonment', desc:'Cannot dump in general waste or drain. Must use authorised common Treatment, Storage and Disposal Facilities (TSDF).'},
    {title:'Maintain records of waste generation, storage, and disposal', freq:'Annual', deadline:'Submit annual return to SPCB by 30 June', authority:'SPCB', penalty:'Fine', desc:'Annual return in Form 4 showing quantities generated, stored, treated, and disposed.'}
  ]
},
{
  id:'ewaste', name:'E-Waste (Management) Rules, 2022',
  shortName:'E-Waste Rules, 2022', category:'Environment', priority:'medium',
  description:'Regulates management of electronic waste and mandates Extended Producer Responsibility (EPR) for producers of electronic equipment.',
  reason: c => c.generatesEWaste || c.primarySector === 'it' || c.isITService
    ? 'Applicable: IT company / electronic equipment producer / user' : null,
  actions:[
    {title:'Register on CPCB E-Waste portal as Producer/Manufacturer', freq:'One-time', deadline:'Before selling/distributing electrical/electronic equipment', authority:'CPCB', penalty:'Fine + imprisonment', desc:'Producers of electrical/electronic equipment (phones, computers, appliances, etc.) must register and set up EPR plan.'},
    {title:'Meet EPR (Extended Producer Responsibility) targets for collection/recycling', freq:'Annual', deadline:'As per CPCB schedule', authority:'CPCB', penalty:'Environmental Compensation', desc:'Collect and ensure recycling of specified percentage of e-waste generated from products sold.'},
    {title:'Dispose e-waste through authorised e-waste recyclers only', freq:'As required', deadline:'No stockpiling beyond limits', authority:'SPCB / CPCB', penalty:'Fine', desc:'Cannot throw electronics in general waste. Must use authorised recyclers with SPCB authorisation.'},
    {title:'Maintain records and file annual returns', freq:'Annual', deadline:'30th June', authority:'CPCB / SPCB', penalty:'Fine', desc:'Annual return showing e-waste generated, collected, and recycled/disposed.'}
  ]
},
{
  id:'plastic', name:'Plastic Waste Management Rules, 2016 (as amended)',
  shortName:'Plastic Waste Rules, 2016', category:'Environment', priority:'medium',
  description:'Governs management of plastic waste including ban on single-use plastics and EPR obligations for plastic packaging producers.',
  reason: c => c.usesPlastic || c.isManufacturing || c.primarySector === 'food' || c.primarySector === 'trading'
    ? 'Applicable: company uses plastic packaging or manufactures plastic products' : null,
  actions:[
    {title:'Stop using banned single-use plastic items (effective July 2022)', freq:'Immediate', deadline:'Immediate', authority:'CPCB / SPCB / Local Authority', penalty:'Fine up to ₹1 lakh + imprisonment', desc:'Banned items include: cutlery, straws, stirrers, plates, cups below 100 microns, polystyrene decoration items.'},
    {title:'Register under EPR for plastic packaging (if producer/importer/brand owner)', freq:'Annual', deadline:'Before selling packaged products', authority:'CPCB', penalty:'Environmental Compensation', desc:'Producers of plastic packaging must register on CPCB EPR portal and meet collection/recycling targets.'},
    {title:'Ensure plastic packaging thickness compliance (≥ 120 microns)', freq:'Ongoing', deadline:'Always', authority:'CPCB / Local Body', penalty:'Fine', desc:'Plastic bags must be at least 120 microns thick.'}
  ]
},

// ══════════════════════════════════════════
// F. FOOD & HEALTH LAWS
// ══════════════════════════════════════════
{
  id:'fssai', name:'Food Safety and Standards Act, 2006',
  shortName:'FSSAI Act, 2006', category:'Food & Health', priority:'critical',
  description:"Regulates manufacturing, storage, distribution, sale and import of food to ensure safe and wholesome food for human consumption.",
  reason: c => c.dealsFoodBeverages || c.primarySector === 'food' || c.primarySector === 'hospitality'
    ? 'Applicable: company is in food/beverage/hospitality business' : null,
  actions:[
    {title:'Obtain FSSAI Registration or License', freq:'One-time + Annual renewal', deadline:'Before commencing food business', authority:'Food Safety and Standards Authority of India (FSSAI)', penalty:'Imprisonment up to 6 months + fine up to ₹5 lakh', desc:'Registration (turnover < ₹12 lakh): with local food safety officer. State License (₹12L–₹20Cr turnover or specific activities). Central License (turnover > ₹20Cr or import/export/food park).'},
    {title:'Display FSSAI License number on all products and premises', freq:'Permanent', deadline:'Immediately', authority:'FSSAI', penalty:'Fine', desc:'14-digit FSSAI licence number must be displayed on premises and printed on all food labels.'},
    {title:'Maintain hygiene and food safety standards (Schedule 4)', freq:'Ongoing', deadline:'Always', authority:'FSSAI / State Food Safety Officer', penalty:'Fine + cancellation of licence', desc:'Comply with Good Manufacturing Practices (GMP), Good Hygienic Practices (GHP), HACCP principles as applicable.'},
    {title:'Ensure proper food labelling as per FSSAI Labelling Regulations', freq:'Per product', deadline:'Before sale', authority:'FSSAI', penalty:'Fine up to ₹3 lakh', desc:'Labels must show: name, ingredients, nutritional info, FSSAI number, MFD/best before, net quantity, manufacturer address.'},
    {title:'File Annual Return (Form D-1) — for manufacturers only', freq:'Annual', deadline:'31st May each year', authority:'FSSAI / State Licensing Authority', penalty:'Fine', desc:'Annual return covering details of production, import, and sale.'},
    {title:'Conduct food safety trainings for food handlers', freq:'Annual', deadline:'Periodically', authority:'FSSAI / State', penalty:'—', desc:'Food handlers must be trained in hygiene, personal cleanliness, and safe food handling practices.'}
  ]
},
{
  id:'drugs', name:'Drugs and Cosmetics Act, 1940',
  shortName:'Drugs & Cosmetics Act, 1940', category:'Food & Health', priority:'critical',
  description:"Regulates import, manufacture, distribution, and sale of drugs and cosmetics in India.",
  reason: c => c.dealsPharma || c.primarySector === 'pharma' || c.primarySector === 'healthcare'
    ? 'Applicable: company deals in drugs, cosmetics, or healthcare products' : null,
  actions:[
    {title:'Obtain Drug Manufacturing Licence from State Licensing Authority', freq:'One-time + Renewal', deadline:'Before manufacturing', authority:'State Drugs Controller / CDSCO (Central)', penalty:'Imprisonment up to 3 years + fine', desc:'Form 25 / 28 for different drug categories. GMP certificate required. Separate licence for each category (allopathic, ayurvedic, cosmetics).'},
    {title:'Obtain Drug Sales / Wholesale Licence (if not manufacturer)', freq:'One-time + Annual', deadline:'Before selling drugs', authority:'State Licensing Authority / Drugs Inspector', penalty:'Imprisonment up to 2 years + fine', desc:'Form 20/21 for retail pharmacy; Form 20B/21B for wholesale drugs. Premises and personnel (qualified pharmacist) requirements apply.'},
    {title:'Maintain records of purchase and sale of drugs', freq:'Monthly', deadline:'At all times', authority:'Drugs Inspector', penalty:'Fine', desc:'Schedule H and Schedule H1 drugs require additional prescription register and special records.'},
    {title:'Ensure proper labelling, storage, and transport of drugs', freq:'Ongoing', deadline:'Always', authority:'Drugs Inspector', penalty:'Fine + imprisonment', desc:'Temperature-sensitive drugs must be stored as prescribed. Labels must include: drug name, dosage, manufacturer, batch number, expiry date.'},
    {title:'Submit periodic reports to CDSCO/State Licensing Authority', freq:'As required', deadline:'As per licence conditions', authority:'CDSCO / State', penalty:'Fine', desc:'Adverse Drug Reaction (ADR) reporting; post-market surveillance for specified drugs.'}
  ]
},

// ══════════════════════════════════════════
// G. IT & DATA LAWS
// ══════════════════════════════════════════
{
  id:'itact', name:'Information Technology Act, 2000 & IT (Amendment) Act, 2008',
  shortName:'IT Act, 2000', category:'Technology & Data', priority:'high',
  description:'Governs legal recognition of electronic transactions, cybercrime, and obligations for intermediaries and body corporates handling sensitive personal data.',
  reason: c => c.hasWeb || c.collectsData || c.isITService || c.isECommerce || c.hasPayment
    ? 'Applicable: company has digital/online presence or deals in electronic data' : null,
  actions:[
    {title:'Publish Privacy Policy on website/app (Section 43A + IT Rules 2011)', freq:'One-time + as updated', deadline:'Immediately', authority:'MeitY (Ministry of Electronics & IT)', penalty:'Compensation payable to affected persons (no fixed cap)', desc:'Privacy policy must disclose: what data is collected, purpose, how it is used/shared, how to withdraw consent.'},
    {title:'Implement reasonable security practices for SPDI (Sensitive Personal Data)', freq:'Ongoing', deadline:'Always', authority:'MeitY', penalty:'Compensation up to full loss caused', desc:'SPDI includes: passwords, financial data, health data, biometric data, sexual orientation, medical records. Must have ISO 27001 or similar standard.'},
    {title:'Comply with Intermediary Guidelines and Digital Media Ethics Code (IT Rules, 2021)', freq:'Ongoing', deadline:'As applicable', authority:'MeitY', penalty:'Loss of intermediary safe harbour + fine', desc:'Social media intermediaries with >50L users must: appoint Grievance Officer, Nodal Contact Person, Chief Compliance Officer; publish transparency reports.'},
    {title:'Report cybersecurity incidents to CERT-In within 6 hours', freq:'As required', deadline:'Within 6 hours of detection', authority:'CERT-In (Indian Computer Emergency Response Team)', penalty:'Imprisonment + fine', desc:'Mandatory reporting for: data breaches, cyberattacks, ransomware, fraud, identity theft. Retain logs for 180 days.'},
    {title:'Appoint Grievance Officer with contact details published', freq:'One-time', deadline:'Immediately', authority:'MeitY', penalty:'Loss of safe harbour', desc:'Intermediaries must appoint a Grievance Officer to handle user complaints. Acknowledge within 24 hours, resolve within 15 days.'}
  ]
},
{
  id:'dpdp', name:'Digital Personal Data Protection Act, 2023',
  shortName:'DPDP Act, 2023', category:'Technology & Data', priority:'critical',
  description:"India's comprehensive data protection law. Governs processing of digital personal data with consent-based framework.",
  reason: c => c.collectsData || c.hasWeb || c.isITService
    ? 'Applicable: company collects or processes personal data of individuals' : null,
  actions:[
    {title:'Obtain free, specific, informed, and unambiguous consent before processing personal data', freq:'Per data principal', deadline:'Before processing', authority:'Data Protection Board of India', penalty:'Up to ₹250 crore per violation', desc:'Consent must be sought through a clear and plain notice. Separate consent for each purpose. No consent by default/bundled.'},
    {title:'Publish clear and accessible Privacy Notice', freq:'One-time + as updated', deadline:'Before or at the time of data collection', authority:'Data Protection Board', penalty:'Up to ₹200 crore', desc:'Notice must specify: what data is collected, purpose of processing, how data principals can exercise rights.'},
    {title:'Fulfil Data Principal Rights: access, correction, erasure, grievance redressal', freq:'On request', deadline:'Within prescribed timelines (rules awaited)', authority:'Data Protection Board', penalty:'Up to ₹150 crore', desc:'Individuals have the right to: access their data, correct inaccuracies, erase data, know about processing, and nominate a person.'},
    {title:'Appoint Data Protection Officer (for Significant Data Fiduciaries)', freq:'One-time', deadline:'On notification by Central Government', authority:'Data Protection Board', penalty:'Up to ₹150 crore', desc:'Significant Data Fiduciaries (to be notified by Govt) must appoint a DPO based in India.'},
    {title:'Implement Data Security Safeguards', freq:'Ongoing', deadline:'Always', authority:'Data Protection Board', penalty:'Up to ₹250 crore', desc:'Implement appropriate technical and organizational measures to prevent data breaches.'},
    {title:'Notify Data Protection Board of data breaches', freq:'As required', deadline:'Without undue delay (timeline in Rules)', authority:'Data Protection Board', penalty:'Up to ₹200 crore', desc:'Any breach affecting personal data must be reported to the Board and affected individuals.'}
  ]
},

// ══════════════════════════════════════════
// H. FOREIGN EXCHANGE & FINANCIAL
// ══════════════════════════════════════════
{
  id:'fema', name:'Foreign Exchange Management Act, 1999',
  shortName:'FEMA, 1999', category:'Financial', priority:'high',
  description:'Regulates all foreign exchange transactions in India, including FDI, ODI, imports, exports, and foreign currency accounts.',
  reason: c => c.hasFDI || c.doesImportExport || c.hasForex
    ? 'Applicable: company has FDI, imports/exports, or foreign exchange transactions' : null,
  actions:[
    {title:'Report inward FDI to RBI (Form FC-GPR)', freq:'Per transaction', deadline:'Within 30 days of allotment of shares', authority:'RBI (via authorised dealer bank)', penalty:'Up to 3× the amount of contravention or ₹2 lakh + ₹5,000/day', desc:'Every time shares are issued to foreign investors, file Form FC-GPR (Foreign Currency – Gross Provisional Return) through AD bank.'},
    {title:'File Annual Return on Foreign Liabilities and Assets (FLA)', freq:'Annual', deadline:'15th July each year', authority:'RBI (FEMA Division)', penalty:'Fine + compounding', desc:'Companies with FDI or ODI must file the FLA return with RBI every year on the RBI XBRL site.'},
    {title:'Obtain IEC (Importer Exporter Code) for import/export', freq:'One-time', deadline:'Before first import/export transaction', authority:'DGFT (Directorate General of Foreign Trade)', penalty:'Cannot import/export without IEC', desc:'Apply online on DGFT portal for an 10-digit IEC. Free of cost. Update annually.'},
    {title:'Comply with FEMA (Current Account Transactions) Rules for import payments', freq:'Per transaction', deadline:'As per payment terms', authority:'RBI / AD Bank', penalty:'Compounding + fine', desc:'Pay for imports within prescribed time (6 months for goods; 1 year for services via LUT). Submit import documents to AD bank.'},
    {title:'Realise export proceeds within prescribed time (9 months for goods)', freq:'Per export', deadline:'Within 9 months of shipment', authority:'RBI / AD Bank', penalty:'Fine proportional to unrealised amount', desc:'All export proceeds must be repatriated to India. File softex/EFMS for software exports.'},
    {title:'File ODI returns if company has overseas investment', freq:'Per transaction + Annual', deadline:'Within 30 days of transaction', authority:'RBI', penalty:'Fine + compounding', desc:'Outward direct investment in foreign entities requires RBI reporting via Form ODI.'}
  ]
},
{
  id:'pmla', name:'Prevention of Money Laundering Act, 2002',
  shortName:'PMLA, 2002', category:'Financial', priority:'critical',
  description:'Requires reporting entities (banks, NBFCs, insurance, payment systems, etc.) to comply with KYC/AML norms and report suspicious transactions.',
  reason: c => c.isPMLA || c.isNBFC || c.isBanking || c.isInsurance || c.isRealEstate || c.primarySector === 'financial'
    ? 'Applicable: company is a reporting entity under PMLA' : null,
  actions:[
    {title:'Implement KYC (Know Your Customer) Policy', freq:'Ongoing', deadline:'Before onboarding any customer', authority:'FIU-IND / RBI / SEBI / IRDAI', penalty:'Imprisonment up to 7 years + fine equal to property involved', desc:'KYC must include: Customer identification, UBO (Ultimate Beneficial Owner) identification, risk categorisation, ongoing monitoring.'},
    {title:'File Suspicious Transaction Reports (STR) with FIU-IND', freq:'As required', deadline:'Within 7 days of suspicion', authority:'FIU-IND (Financial Intelligence Unit)', penalty:'Fine + imprisonment', desc:'Report any transaction suspected to be related to money laundering or terrorist financing to FIU-IND via FINnet 2.0 portal.'},
    {title:'File Cash Transaction Reports (CTR) for cash transactions > ₹10 lakh', freq:'Monthly', deadline:'15th of following month', authority:'FIU-IND', penalty:'Fine + imprisonment', desc:'All cash transactions (individually or in aggregate) exceeding ₹10 lakh in a month must be reported.'},
    {title:'Maintain records for 5 years after transaction', freq:'Ongoing', deadline:'At all times', authority:'FIU-IND', penalty:'Fine', desc:'KYC records, transaction records, and STR/CTR copies must be preserved for minimum 5 years.'},
    {title:'Appoint a Principal Officer and file with FIU-IND', freq:'One-time', deadline:'Before commencing regulated activities', authority:'FIU-IND', penalty:'Fine', desc:'Designated Principal Officer must be registered with FIU-IND and is responsible for AML compliance and reporting.'}
  ]
},

// ══════════════════════════════════════════
// I. CONSUMER & TRADE
// ══════════════════════════════════════════
{
  id:'consumerprotection', name:'Consumer Protection Act, 2019',
  shortName:'Consumer Protection Act, 2019', category:'Consumer', priority:'high',
  description:"Protects consumers from unfair trade practices, misleading advertisements, and product defects. Applies to all businesses.",
  reason: c => true,
  actions:[
    {title:'Avoid misleading advertisements and unfair trade practices', freq:'Ongoing', deadline:'Always', authority:'Central Consumer Protection Authority (CCPA) / NCDRC', penalty:'Fine up to ₹10 lakh (first offence), ₹50 lakh (repeat) + imprisonment', desc:'Do not make false claims about products/services. No bait advertising, pyramid schemes, or psychological pricing tactics.'},
    {title:'Establish consumer grievance redressal mechanism', freq:'Ongoing', deadline:'Immediately', authority:'CCPA', penalty:'Fine', desc:'Display contact details for consumer complaints prominently. E-commerce platforms must resolve complaints within 15 days.'},
    {title:'E-commerce: Comply with Consumer Protection (E-Commerce) Rules, 2020', freq:'Ongoing', deadline:'Always', authority:'CCPA / Consumer Courts', penalty:'Fine + imprisonment', desc:'Display: seller details, country of origin, expiry date, return/refund policy, customer care number. No manipulation of price or search results.'},
    {title:'Register on National Consumer Helpline portal (e-commerce businesses)', freq:'One-time', deadline:'Within 90 days of notification', authority:'CCPA / Ministry of Consumer Affairs', penalty:'Fine', desc:'E-commerce entities must register on NCH portal and respond to complaints filed there.'},
    {title:'Comply with product liability provisions', freq:'Ongoing', deadline:'Always', authority:'Consumer Courts / CCPA', penalty:'Compensation to consumers + fine', desc:'Manufacturers/sellers/service providers are liable for defective products and deficient services. Maintain product safety documentation.'}
  ]
},
{
  id:'legalmetrology', name:'Legal Metrology Act, 2009',
  shortName:'Legal Metrology Act, 2009', category:'Consumer', priority:'medium',
  description:'Regulates weights, measures, and labelling of pre-packaged commodities including declaration of MRP, net quantity, and manufacturer details.',
  reason: c => c.isManufacturing || c.isTrading || c.primarySector === 'trading' || c.primarySector === 'food' || c.primarySector === 'retail'
    ? 'Applicable: company manufactures or sells pre-packaged goods' : null,
  actions:[
    {title:'Declare MRP, net quantity, and manufacturer details on all pre-packaged goods', freq:'Per product', deadline:'Before sale', authority:'Legal Metrology Inspector / State Weights & Measures Department', penalty:'Fine up to ₹25,000 + imprisonment', desc:'Mandatory declarations on label: name/address of manufacturer, net quantity, manufacturing date, MRP (inclusive of all taxes), country of origin.'},
    {title:'Ensure accuracy of weights and measures used in trade', freq:'Annual verification', deadline:'Annual stamping/verification', authority:'Legal Metrology Inspector', penalty:'Fine + confiscation of instrument', desc:'All weighing/measuring instruments used in trade must be verified and stamped by Legal Metrology Inspector annually.'},
    {title:'Obtain Dealer Licence for weighing instruments (if applicable)', freq:'Annual', deadline:'Before selling instruments', authority:'Controller of Legal Metrology (State)', penalty:'Fine', desc:'Dealers and repairers of weighing/measuring instruments must obtain a licence.'},
    {title:'Comply with e-commerce labelling requirements', freq:'Ongoing', deadline:'Always', authority:'Legal Metrology Inspector', penalty:'Fine', desc:'E-commerce product listings must display all mandatory declarations as required on physical labels.'}
  ]
},
{
  id:'competition', name:'Competition Act, 2002',
  shortName:'Competition Act, 2002', category:'Consumer', priority:'medium',
  description:'Prohibits anti-competitive agreements, abuse of dominant position, and regulates mergers/acquisitions above prescribed thresholds.',
  reason: c => {
    const t = parseInt(c.annualTurnover)||0;
    return t >= 25000 || c.isListed ? 'Applicable: company meets CCI threshold OR anti-competitive conduct obligations apply to all businesses' : 'Applicable: prohibitions on anti-competitive conduct apply to all enterprises';
  },
  actions:[
    {title:'Avoid anti-competitive agreements (price fixing, market sharing, bid rigging)', freq:'Ongoing', deadline:'Always', authority:'Competition Commission of India (CCI)', penalty:'Fine up to 10% of average 3-year turnover + imprisonment', desc:'Prohibited: agreements between competitors to fix prices, divide markets, rig bids. Also: exclusive dealing, tie-in arrangements, resale price maintenance.'},
    {title:'Do not abuse dominant position in relevant market', freq:'Ongoing', deadline:'Always', authority:'CCI', penalty:'Fine up to 10% of turnover + structural remedies', desc:'If the company is dominant in any market: do not engage in predatory pricing, denial of market access, or exclusive dealing.'},
    {title:'File notification with CCI for mergers/acquisitions above prescribed thresholds', freq:'As required', deadline:'Within 30 days of approval of combination', authority:'CCI', penalty:'Fine up to ₹1 crore + up to 1% of total assets/turnover of combination per day', desc:'Notification required if: combined assets in India > ₹2,000 crore OR combined turnover > ₹6,000 crore; or global thresholds. Wait for CCI clearance before closing.'}
  ]
},

// ══════════════════════════════════════════
// J. SECTOR-SPECIFIC LAWS
// ══════════════════════════════════════════
{
  id:'mines', name:'Mines Act, 1952',
  shortName:'Mines Act, 1952', category:'Sector-Specific', priority:'critical',
  description:'Governs health, safety, and welfare of workers in mines.',
  reason: c => c.hasMines ? 'Applicable: company operates mines or quarries' : null,
  actions:[
    {title:'Appoint Manager with a valid Mine Manager Certificate of Competency', freq:'One-time', deadline:'Before commencing operations', authority:'Director General of Mines Safety (DGMS)', penalty:'Imprisonment + fine', desc:'Every mine must have a qualified Mine Manager with a certificate from DGMS. Manager is responsible for all safety.'},
    {title:'Obtain Mine Opening Permission and comply with DGMS regulations', freq:'One-time + periodic', deadline:'Before opening mine', authority:'DGMS (Regional Inspector of Mines)', penalty:'Closure order + fine', desc:'Submit Mine Opening Notice. Obtain various permits. File quarterly and annual statistical returns.'},
    {title:'Maintain safety systems: supports, ventilation, drainage, fire prevention', freq:'Ongoing', deadline:'Always', authority:'DGMS Inspector', penalty:'Closure + imprisonment', desc:'Compulsory safety measures for underground/opencast mines including roof support, VHF communication, rescue equipment.'},
    {title:'Work hours: max 8 hours/day, rest of 8 hours below ground', freq:'Daily', deadline:'Always', authority:'DGMS', penalty:'Fine', desc:'Overtime only with DGMS permission. Weekly rest mandatory.'},
    {title:'Submit accident reports to DGMS', freq:'As required', deadline:'Immediately for serious accidents', authority:'DGMS', penalty:'Fine', desc:'Fatal/serious accidents must be reported by telephone immediately and in writing within 2 hours.'}
  ]
},
{
  id:'petroleum', name:'Petroleum Act, 1934 & Petroleum Rules, 2002',
  shortName:'Petroleum Act, 1934', category:'Sector-Specific', priority:'critical',
  description:'Regulates storage, import, and use of petroleum products; requires licenses for storage above specified quantities.',
  reason: c => c.dealsPetroleum ? 'Applicable: company stores or deals in petroleum products' : null,
  actions:[
    {title:'Obtain Petroleum Storage Licence from PESO', freq:'Annual renewal', deadline:'Before storing petroleum above threshold quantities', authority:'PESO (Petroleum and Explosives Safety Organisation)', penalty:'Imprisonment up to 3 years + fine', desc:'Class A petroleum (flash point < 23°C): licence for any storage; Class B (23°C–65°C): > 2500 L; Class C (>65°C): > 45,000 L.'},
    {title:'Comply with petroleum storage safety requirements', freq:'Ongoing', deadline:'Always', authority:'PESO Inspector', penalty:'Fine + closure', desc:'Fire prevention systems, grounding/bonding of tanks, safety distances from buildings, no smoking zones, emergency procedures.'},
    {title:'Ensure trained personnel for petroleum handling', freq:'Ongoing', deadline:'Always', authority:'PESO', penalty:'Fine', desc:'Personnel must be trained in safe handling of petroleum products and emergency response.'}
  ]
},
{
  id:'boilers', name:'Indian Boilers Act, 1923',
  shortName:'Indian Boilers Act, 1923', category:'Sector-Specific', priority:'high',
  description:'Regulates safety of steam boilers used in industrial and commercial establishments.',
  reason: c => c.hasBoilers ? 'Applicable: company uses industrial steam boilers' : null,
  actions:[
    {title:'Register every boiler with the State Boiler Inspectorate', freq:'One-time + Annual', deadline:'Before using boiler', authority:'State Boiler Inspector (Chief Inspector of Boilers)', penalty:'Imprisonment + fine; cannot operate unregistered boiler', desc:'New boilers must be inspected and registered before use. Certificate of registration is issued for 1–2 years.'},
    {title:'Obtain annual fitness certificate for every boiler', freq:'Annual', deadline:'Before expiry of existing certificate', authority:'Boiler Inspector', penalty:'Cannot operate; fine + imprisonment', desc:'Annual inspection by Boiler Inspector. Certificate of fitness renewed annually or as per Inspector\'s decision.'},
    {title:'Employ only certified boiler attendants', freq:'Ongoing', deadline:'Always', authority:'State Boiler Inspector', penalty:'Fine', desc:'Persons operating boilers must hold a Boiler Attendant Certificate of Competency.'}
  ]
},
{
  id:'explosives', name:'Explosives Act, 1884 and Explosives Rules, 2008',
  shortName:'Explosives Act, 1884', category:'Sector-Specific', priority:'critical',
  description:'Governs manufacture, possession, use, sale, transport, and import of explosives.',
  reason: c => c.dealsExplosives ? 'Applicable: company uses, manufactures, or stores explosives' : null,
  actions:[
    {title:'Obtain Explosives Licence from PESO', freq:'Annual', deadline:'Before storing/using explosives', authority:'PESO / Chief Controller of Explosives', penalty:'Imprisonment up to 10 years + fine', desc:'Different licences for manufacture, storage, sale, transport, import. Apply in prescribed form to PESO.'},
    {title:'Comply with storage and handling safety requirements', freq:'Ongoing', deadline:'Always', authority:'PESO Inspector', penalty:'Fine + imprisonment + cancellation of licence', desc:'Explosives must be stored in licensed magazines; safety distances maintained; no unauthorised access.'},
    {title:'Maintain records of explosives received, issued, and remaining', freq:'Daily', deadline:'At all times', authority:'PESO Inspector', penalty:'Fine', desc:'Detailed registers for all explosives movements. Periodic returns to licensing authority.'}
  ]
},
{
  id:'rera', name:'Real Estate (Regulation and Development) Act, 2016',
  shortName:'RERA, 2016', category:'Sector-Specific', priority:'critical',
  description:'Regulates real estate sector; requires registration of projects and agents; protects home buyers.',
  reason: c => c.isRealEstate || c.primarySector === 'realestate' ? 'Applicable: company is a real estate developer or agent' : null,
  actions:[
    {title:'Register every real estate project with State RERA Authority', freq:'Per project', deadline:'Before advertising or booking', authority:'State Real Estate Regulatory Authority', penalty:'Fine up to 10% of project cost; imprisonment up to 3 years', desc:'Mandatory for all projects: plot area > 500 sq m OR > 8 apartments. Register on State RERA portal with all project details.'},
    {title:'Open dedicated Escrow Account: deposit 70% of collections', freq:'Per project', deadline:'Before receiving bookings', authority:'State RERA Authority', penalty:'Fine up to 10% of project cost', desc:'70% of all amounts collected from buyers must be kept in a separate bank account (per project) to be used only for construction costs.'},
    {title:'File Quarterly Progress Reports with RERA', freq:'Quarterly', deadline:'Within 15 days of quarter end', authority:'State RERA', penalty:'Fine', desc:'Reports on construction progress, funds collected and utilized, units sold, and completion status.'},
    {title:'Deliver project as per registered timelines', freq:'Per project', deadline:'As per registered completion date', authority:'State RERA / Consumer Courts', penalty:'Refund + interest @ SBI MCLR+2% to buyers', desc:'Any delay requires buyer consent or payment of interest. Cannot alter project plans without buyer consent.'},
    {title:'Register as Real Estate Agent (if acting as agent)', freq:'One-time + renewal', deadline:'Before facilitating any transaction', authority:'State RERA', penalty:'Fine up to ₹10,000/day', desc:'Real estate agents must register with State RERA before facilitating sale/purchase of RERA-registered projects.'}
  ]
},
{
  id:'customs', name:'Customs Act, 1962 and Foreign Trade Policy',
  shortName:'Customs Act & Foreign Trade Policy', category:'Sector-Specific', priority:'high',
  description:'Governs import and export of goods; requires IEC, customs duty payment, and adherence to import/export procedures.',
  reason: c => c.doesImportExport ? 'Applicable: company imports or exports goods/services' : null,
  actions:[
    {title:'Obtain IEC (Importer Exporter Code) from DGFT', freq:'One-time + Annual update', deadline:'Before first import/export', authority:'DGFT (Directorate General of Foreign Trade)', penalty:'Cannot import/export without IEC', desc:'Free of cost, 10-digit code. Apply online at DGFT portal. Update annually to keep it active.'},
    {title:'File Bill of Entry for every import consignment', freq:'Per consignment', deadline:'Before clearance', authority:'Customs Department (ICEGATE)', penalty:'Demurrage + penalty + detention', desc:'File Bill of Entry on ICEGATE portal. Pay customs duty and IGST. Obtain Customs clearance before taking delivery.'},
    {title:'File Shipping Bill for every export consignment', freq:'Per consignment', deadline:'Before shipment', authority:'Customs Department (ICEGATE)', penalty:'Penalty', desc:'File Shipping Bill on ICEGATE and obtain Let Export Order (LEO) from Customs.'},
    {title:'Comply with import licensing requirements for restricted goods', freq:'Per consignment', deadline:'Before import', authority:'DGFT', penalty:'Confiscation + fine', desc:'Certain items require prior import licence (e.g., hazardous chemicals, second-hand goods, specific food items).'},
    {title:'Claim export benefits (RoDTEP, MEIS, SEIS as applicable)', freq:'Per shipment', deadline:'Within 1 year of export', authority:'DGFT', penalty:'Forfeiture of benefit if not claimed in time', desc:'File application for export incentive schemes as applicable to the product/service exported.'}
  ]
},

// ══════════════════════════════════════════
// K. INTELLECTUAL PROPERTY
// ══════════════════════════════════════════
{
  id:'trademark', name:'Trade Marks Act, 1999',
  shortName:'Trade Marks Act, 1999', category:'Intellectual Property', priority:'medium',
  description:'Provides for registration and protection of trade marks (brand names, logos) and service marks.',
  reason: c => c.hasIP || c.totalEmployees > 0 ? 'Applicable: company should register its brand name, logo, and tagline' : null,
  actions:[
    {title:'Conduct trademark search before adopting brand name', freq:'One-time', deadline:'Before use', authority:'IP India (CGPDTM)', penalty:'N/A – preventive step', desc:'Search on IP India trademark database to ensure no prior conflicting mark exists.'},
    {title:'File trademark application with Trade Marks Registry', freq:'Per mark', deadline:'As early as possible (first use or intent to use)', authority:'Trade Marks Registry, CGPDTM', penalty:'No penalty for not registering; but risk of infringement by others', desc:'File TM-A form on IP India portal. Application is examined within 12–18 months. ™ can be used after filing; ® only after registration.'},
    {title:'Renew registered trademark every 10 years', freq:'Every 10 years', deadline:'Before expiry (renewal possible 6 months after expiry)', authority:'Trade Marks Registry', penalty:'Removal from register after 1 year from expiry', desc:'Pay renewal fees and file TM-R form to renew the trademark.'},
    {title:'Monitor and take action against infringers', freq:'Ongoing', deadline:'Promptly on discovery', authority:'District Court / IP India / Police (for counterfeiting)', penalty:'N/A – civil/criminal action against infringer', desc:'Registered trademark owner can sue for infringement + damages + injunction.'}
  ]
},
{
  id:'copyright', name:'Copyright Act, 1957',
  shortName:'Copyright Act, 1957', category:'Intellectual Property', priority:'low',
  description:'Protects original literary, artistic, musical, dramatic works, films, and software from unauthorised copying.',
  reason: c => c.isITService || c.primarySector === 'media' || c.primarySector === 'education' || c.primarySector === 'it' || c.hasIP
    ? 'Applicable: company creates software, content, designs, or other copyrightable works' : null,
  actions:[
    {title:'Register copyright for original works (optional but recommended)', freq:'Per work', deadline:'Any time after creation', authority:'Copyright Office, DPIIT', penalty:'N/A – registration is voluntary (copyright exists from creation)', desc:'File application with Copyright Office. Certificate strengthens legal position. Especially important for software, websites, databases, marketing material.'},
    {title:'Ensure employees assign copyright to the company via employment contracts', freq:'At hiring', deadline:'Before commencement of work', authority:'N/A', penalty:'Employer may not own employee-created works without assignment', desc:'Employment agreements should explicitly assign IP created during employment to the company.'},
    {title:'Obtain licences for copyrighted material used by company (software, images, fonts)', freq:'Before use', deadline:'Before deploying in product/marketing', authority:'N/A', penalty:'Civil and criminal action by copyright owner', desc:'Ensure all third-party software, stock photos, fonts, and music used in business have valid licences.'}
  ]
},

// ══════════════════════════════════════════
// L. MISCELLANEOUS
// ══════════════════════════════════════════
{
  id:'electricityact', name:'Electricity Act, 2003',
  shortName:'Electricity Act, 2003', category:'Infrastructure', priority:'medium',
  description:'Governs generation, transmission, distribution, and use of electricity; mandates energy audits for large consumers.',
  reason: c => c.hasLargeElectrical || c.hasFactory || c.hasMines
    ? 'Applicable: company is a large electricity consumer or industrial unit' : null,
  actions:[
    {title:'Obtain electrical contractor licence for in-house electrical work', freq:'Per contractor', deadline:'Before commencing electrical work', authority:'State Electrical Inspectorate', penalty:'Fine + imprisonment', desc:'All electrical work must be carried out by licensed electrical contractors.'},
    {title:'Conduct mandatory Energy Audit if Designated Consumer', freq:'Every 3 years', deadline:'As per Bureau of Energy Efficiency (BEE) schedule', authority:'BEE (Bureau of Energy Efficiency)', penalty:'Fine up to ₹10 lakh', desc:'Designated Consumers (industries consuming > 500 TOE/year or > 30,000 units/month) must conduct energy audits by accredited energy auditors.'},
    {title:'Appoint Energy Manager (for Designated Consumers)', freq:'One-time', deadline:'Within 6 months of designation', authority:'BEE / State Designated Agency', penalty:'Fine', desc:'Designated Consumers must appoint a certified Energy Manager and register with BEE.'},
    {title:'File Annual Energy Consumption Return', freq:'Annual', deadline:'30th September', authority:'BEE', penalty:'Fine', desc:'Designated Consumers must file annual return showing energy consumption, efficiency measures taken, and targets.'}
  ]
},
{
  id:'bureau_standards', name:'Bureau of Indian Standards Act, 2016',
  shortName:'BIS Act, 2016', category:'Consumer', priority:'medium',
  description:'Mandates BIS certification for a specified list of goods; ensures products conform to Indian Standards.',
  reason: c => c.isManufacturing || c.primarySector === 'manufacturing' ? 'Applicable: manufacturing company may need BIS certification for specified products' : null,
  actions:[
    {title:'Obtain BIS Certification Mark (ISI mark) for compulsorily certified products', freq:'One-time + Annual surveillance', deadline:'Before selling compulsorily certified products', authority:'Bureau of Indian Standards (BIS)', penalty:'Imprisonment up to 2 years + fine up to ₹5 lakh', desc:'100+ product categories are compulsorily required to have BIS ISI mark (e.g., electrical appliances, cement, steel, packaged drinking water, children\'s toys).'},
    {title:'Maintain quality management system and records for BIS surveillance', freq:'Ongoing', deadline:'At all times', authority:'BIS Inspector', penalty:'Suspension/cancellation of licence', desc:'BIS conducts factory visits and testing. Maintain calibration records, raw material test reports, and finished product test records.'},
    {title:'Foreign manufacturers: obtain Compulsory Registration Scheme (CRS) for electronics', freq:'Per model', deadline:'Before import/sale in India', authority:'BIS', penalty:'Cannot sell in India without registration', desc:'Electronics items (phones, laptops, power banks, etc.) must be registered under BIS CRS before import or sale.'}
  ]
},
{
  id:'labourwelfarefund', name:'Labour Welfare Fund Act (State-specific)',
  shortName:'Labour Welfare Fund Act', category:'Labour', priority:'medium',
  description:'State legislation requiring contribution to Labour Welfare Fund for welfare activities of workers.',
  reason: c => {
    const lwfStates = ['andhra','telangana','chandigarh','delhi','goa','gujarat','haryana','karnataka','kerala','madhyapradesh','maharashtra','orissa','punjab','tamilnadu','uttarakhand','westbengal'];
    const ops = (c.statesOfOperation||[]).map(s=>s.toLowerCase());
    const applicable = lwfStates.filter(s => ops.some(o => o.includes(s)));
    return applicable.length > 0 && c.totalEmployees > 0 ? `Applicable in states: ${applicable.join(', ')}` : null;
  },
  actions:[
    {title:'Deduct and deposit Labour Welfare Fund contributions', freq:'Half-yearly or Annual (varies by state)', deadline:'31st Jan and 31st July (most states)', authority:'State Labour Welfare Board', penalty:'Fine (varies by state)', desc:'Contribution amounts vary by state (e.g., Maharashtra: Employee ₹6, Employer ₹18 per employee per 6 months; Kerala: ₹20/₹60). Deposit to State Labour Welfare Board.'},
    {title:'Maintain register of contributions', freq:'Ongoing', deadline:'At all times', authority:'Labour Welfare Inspector', penalty:'Fine', desc:'Register showing employee-wise contributions deducted and deposited.'},
    {title:'File Labour Welfare Fund returns', freq:'Annual or Half-yearly', deadline:'As per state rules', authority:'State Labour Welfare Board', penalty:'Fine', desc:'Return showing number of employees, contributions, and welfare fund payments.'}
  ]
}

]; // end INDIAN_LAWS
