// ── FIRM PARTICULARS ──
// The one place to edit what the website says about the firm.
//
// ICAI Website Guidelines: every particular shown must agree with the firm's
// record at the Institute (name, FRN, address, members). Do not add client
// names, fees, testimonials, rankings or a firm logo/monogram here.
//
// A field left empty ('' or []) is shown on the page as "To be added".
window.FIRM = {
  name: 'Sagar Khatri & Associates',
  frn: '157238W',

  constitution: '',   // 'Proprietorship' or 'Partnership'
  established: '',    // year, e.g. '2019'

  // Office address exactly as registered with ICAI, one line per entry.
  address: [],
  city: '',           // shown in the particulars card, e.g. 'Ahmedabad, Gujarat'

  phone: '',          // e.g. '+91 79 0000 0000'
  whatsapp: '918866262545',          // digits only, with country code
  whatsappDisplay: '+91 88662 62545',
  email: 'khatrisagar27@gmail.com',
  hours: '',          // e.g. 'Monday to Saturday, 10:00 am to 7:00 pm'

  // ISO date. Change it every time the site content changes.
  lastUpdated: '2026-11-16',

  // Partners / proprietor. Photo, if used, must be passport-style.
  people: [
    {
      name: 'CA Sagar Khatri',
      role: '',            // 'Proprietor' or 'Partner'
      membershipNo: '',    // ICAI membership number
      qualifications: '',  // e.g. 'B.Com., FCA'
      memberSince: '',     // year of ICAI membership
      areas: 'Internal audit, statutory audit, GST, TDS, company law compliance and income-tax',
      photo: ''            // path to a passport-style photograph, e.g. 'people/sagar-khatri.jpg'
    }
  ]
};
