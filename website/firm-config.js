// ── FIRM PARTICULARS ──
// The one place to edit what the website says about the firm.
//
// ICAI Website Guidelines: every particular shown must agree with the firm's
// record at the Institute (name, address, members). Do not add client names,
// fees, testimonials, rankings or a firm logo/monogram here.
//
// Optional fields left empty ('') are simply not shown on the page.
window.FIRM = {
  name: 'Sagar Khatri & Associates',
  proprietor: 'CA Sagar Khatri',
  constitution: 'Proprietorship',
  established: '2022',

  // Not shown on the site by choice. Fill in to display it in the particulars
  // card and the footer.
  frn: '',

  // Office address exactly as registered with ICAI, one line per entry.
  address: [
    '18, 2nd Floor, Darshnam Trade Centre 3,',
    'Near Surya Palace, Sayajigunj,',
    'Vadodara, Gujarat'
  ],
  city: 'Vadodara, Gujarat',
  mapQuery: 'Darshnam Trade Centre 3, Sayajigunj, Vadodara',  // what the map link searches for

  phones: ['+91 88662 62545', '+91 97238 07850'],
  whatsapp: '918866262545',   // digits only, with country code; must be one of the phones
  email: 'khatrisagar27@gmail.com',
  hours: '',                  // optional, e.g. 'Monday to Saturday, 10:00 am to 7:00 pm'

  // ISO date. Change it every time the site content changes.
  lastUpdated: '2026-11-19',

  // Proprietor / partners. A photograph must be passport-style.
  // membershipNo, qualifications and memberSince are optional.
  people: [
    {
      name: 'CA Sagar Khatri',
      role: 'Proprietor',
      membershipNo: '',
      qualifications: '',
      memberSince: '',
      areas: 'Internal audit, statutory audit, GST, TDS, company law compliance and income-tax',
      photo: 'assets/profile.jpg'
    }
  ]
};
