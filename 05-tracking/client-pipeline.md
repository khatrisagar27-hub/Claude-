# Client Pipeline Tracker — CA Tax Planning Practice

Google Sheets template. One row per prospect.

---

## Sheet 1: Prospect Pipeline

| Column | What to Track |
|---|---|
| A: Name | Full name |
| B: Company | Business name |
| C: Approx. Turnover | ₹ crore (estimate) |
| D: Business Type | Manufacturing / Trading / Services / Mixed |
| E: Source | How they came to you (existing client intro / banker referral / CA referral / LinkedIn / speaking event) |
| F: Referrer Name | Who introduced them (if applicable) |
| G: First Contact Date | Date of first interaction |
| H: Initial Consultation | Date scheduled / completed |
| I: Consultation Outcome | Interested / Follow-up needed / Not a fit / Closed |
| J: Audit Proposed | ₹ amount proposed |
| K: Audit Status | Proposed / Engagement letter sent / Signed / In progress / Delivered |
| L: Annual Engagement | ₹ amount proposed |
| M: Annual Engagement Status | Proposed / Signed / Active / Renewed |
| N: FY of Engagement | FY 25-26 / FY 26-27 etc. |
| O: Total Annual Fee | ₹ amount signed |
| P: Payment Status | % collected (0% / 50% / 75% / 100%) |
| Q: Next Action | What needs to happen next |
| R: Next Action Date | When |
| S: Notes | Any relevant context |

---

## Stage Legend (Column I / K / M)

| Stage | Meaning |
|---|---|
| `Identified` | Prospect identified, no contact yet |
| `Intro Pending` | Referrer has agreed to make introduction |
| `Contacted` | First professional contact made |
| `Consultation Booked` | Initial consultation scheduled |
| `Consultation Done` | Meeting completed — follow-up sent |
| `Audit Proposed` | Audit engagement letter sent |
| `Audit Signed` | Audit payment received, work started |
| `Audit Complete` | Report delivered |
| `Annual Proposed` | Annual engagement letter sent |
| `Annual Active` | Signed and paid — current FY client |
| `Renewal Confirmed` | Next FY confirmed |
| `Not a Fit` | Disqualified — wrong profile or no budget |
| `Cold` | No response after follow-up — check back in 90 days |

---

## Sheet 2: Revenue Tracker

| Column | What to Track |
|---|---|
| A: Client Name | Full name |
| B: Engagement Type | Audit / Annual FY[XX] / Retainer |
| C: Total Fee | ₹ (excluding GST) |
| D: GST | ₹ (18%) |
| E: Invoice 1 Date | Date of 50% invoice |
| F: Invoice 1 Amount | ₹ |
| G: Invoice 1 Paid | Y / N / Date |
| H: Invoice 2 Date | Date of 25% invoice |
| I: Invoice 2 Amount | ₹ |
| J: Invoice 2 Paid | Y / N / Date |
| K: Invoice 3 Date | Date of final invoice |
| L: Invoice 3 Amount | ₹ |
| M: Invoice 3 Paid | Y / N / Date |
| N: Total Received | Sum of paid invoices |
| O: Outstanding | Total fee minus received |
| P: Referrer | Name (to track which referral sources produce revenue) |

---

## Sheet 3: Referral Network Tracker

| Column | What to Track |
|---|---|
| A: Name | Contact name |
| B: Profession | Banker / Lawyer / CS / Insurance / CA / Other |
| C: Organization | Bank/Firm name |
| D: Client Profile | Types of clients they work with |
| E: First Met | Date and context |
| F: Last Value Given | What you shared with them (article, referral back, insight) |
| G: Date | Date of last value given |
| H: Clients Referred | Number of prospects they've sent |
| I: Conversions | How many converted to paying clients |
| J: Revenue from Referrals | Total fee from their referrals |
| K: Notes | Relationship context, preferences, next touchpoint |

---

## Sheet 4: Monthly Dashboard

Review every 1st of the month. 20 minutes.

| Metric | This Month | Last Month | Target |
|---|---|---|---|
| New consultations held | | | 3–4 |
| Audit engagements signed | | | 1 |
| Annual engagements signed | | | 1 |
| Active annual clients (total) | | | 5+ by Month 6 |
| Revenue invoiced | ₹ | ₹ | ₹83,000+ |
| Revenue collected | ₹ | ₹ | — |
| Outstanding | ₹ | ₹ | < 1 month's fees |
| LinkedIn posts published | | | 8 |
| Referral network contacts made/maintained | | | 5 |
| Speaking events done/booked | | | 1/quarter |

---

## Formulas for Google Sheets

**Total annual contracted value:**
`=SUMIF(M:M,"Annual Active",O:O)`

**Monthly revenue run rate (annual fees ÷ 12):**
`=SUMIF(M:M,"Annual Active",O:O)/12`

**Outstanding collections:**
`=SUMPRODUCT((G:G="N")*(F:F)+(I:I="N")*(H:H)+(M:M="N")*(L:L))`

**Revenue by referral source:**
Use SUMIF on column P (Referrer) in the Revenue Tracker sheet.

---

## Red Flags (Review Monthly)

**Less than 2 consultations per month:**
Your referral network isn't activated yet. Who have you spoken to in the last 30 days from the professional network list?

**Consultations happening but not converting:**
Review `initial-consultation.md`. Are you diagnosing specifically enough? Are you proposing the Audit clearly?

**Clients signing but not paying:**
Tighten your payment terms — 50% before work begins, non-negotiable. Add this to the engagement letter.

**No renewals after Year 1:**
Send the year-end summary (see `annual-retainer-system.md`). Make value visible before asking for renewal.
