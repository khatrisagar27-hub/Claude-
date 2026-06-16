# Pipeline Tracker — Google Sheets Template

Copy this structure into a new Google Sheet. One row per LinkedIn target.

---

## Sheet 1: Outreach Pipeline

| Column | What to Track |
|---|---|
| A: Name | Full name |
| B: LinkedIn URL | Direct profile link |
| C: Title | Their job title |
| D: Company | Company name |
| E: Company Size | Employee count (est.) |
| F: ICP Score | 1–5 (how well they match your ICP) |
| G: Connection Sent | Date you sent the request |
| H: Connected | Date they accepted (leave blank until accepted) |
| I: DM 1 Sent | Date of first DM |
| J: DM 1 Reply | Their reply (Yes/No/Partial/No Response) |
| K: DM 2 Sent | Day-5 follow-up date |
| L: DM 2 Reply | Reply status |
| M: DM 3 Sent | Day-10 final follow-up date |
| N: Status | Current stage (see Stage Legend below) |
| O: Call Booked | Date of scheduled discovery call |
| P: Call Outcome | Closed / Follow-up / Not a fit / Ghost |
| Q: Email Seq | Which MailerLite sequence they're in (A or B) |
| R: Revenue | Amount paid if converted |
| S: Referred By | Name of referrer (if applicable) |
| T: Notes | Any personal context, objections, next steps |

---

## Stage Legend (Column N)

Use these exact labels for filtering:

| Stage | Meaning |
|---|---|
| `Queued` | Identified but connection not yet sent |
| `Connected` | Accepted — DM not yet sent |
| `DM Sent` | First DM sent, awaiting reply |
| `Replied` | They replied — conversation active |
| `Call Booked` | Discovery call scheduled |
| `Call Done` | Call completed — in email sequence |
| `Closed` | Paid. Sprint underway. |
| `Retainer` | Converted to monthly retainer |
| `Not a Fit` | Disqualified (budget, ICP mismatch, wrong timing) |
| `No Reply` | No response after all 3 DMs |
| `Nurture` | Long-term follow-up (check back in 60–90 days) |

---

## Sheet 2: Revenue Tracker

| Column | What to Track |
|---|---|
| A: Client Name | Full name |
| B: Offer | Strategy Sprint ($2,500) / Full Sprint ($5,000) / Retainer ($1,500) |
| C: Date Paid | Stripe payment date |
| D: Amount | Actual payment received |
| E: Sprint Start | Session 1 date |
| F: Sprint End | Session 3 date (or ongoing for retainers) |
| G: Retainer Month | Month number (1, 2, 3...) for retainer clients |
| H: Testimonial | Got it (Y/N) |
| I: Referral Asked | Date you sent referral ask |
| J: Referred | Who they referred (name, if anyone) |

---

## Sheet 3: Weekly Metrics Dashboard

Review this every Monday. 15 minutes. Keep you focused.

| Metric | This Week | Last Week | Target |
|---|---|---|---|
| Connections sent | | | 50/week |
| Connections accepted | | | 15–20 |
| DMs sent | | | 33 |
| DM replies | | | 5 |
| Calls booked | | | 2 |
| Calls completed | | | 2 |
| Clients closed | | | 1 |
| Revenue this week | | | $2,500 |
| Revenue MTD | | | — |
| Active retainers | | | — |

---

## Formulas to Add (Google Sheets)

**Connection acceptance rate:**
`=COUNTIF(H:H,"<>")/COUNTIF(G:G,"<>")` → Format as %

**DM reply rate:**
`=COUNTIF(J:J,"<>")/COUNTIF(I:I,"<>")` → Format as %

**Call-to-close rate:**
`=COUNTIF(P:P,"Closed")/COUNTIF(O:O,"<>")` → Format as %

**Total monthly revenue:**
`=SUMPRODUCT((MONTH(C:C)=MONTH(TODAY()))*(D:D))`

---

## Weekly Review Checklist (Every Monday, 15 Min)

- [ ] Update Stage column for every active lead
- [ ] Check who needs a Day-5 or Day-10 follow-up DM today
- [ ] Check MailerLite for email sequence activity
- [ ] Update revenue tracker with any new payments from Stripe
- [ ] Identify any "Nurture" leads to reconnect with (60+ days since last contact)
- [ ] Plan this week's 50 connection requests and 33 DMs
- [ ] Log last week's LinkedIn post performance (impressions, comments, DM inquiries)

---

## When the Numbers Break Down

**Low connection acceptance (<15%):**  
Your ICP is wrong or your profile isn't optimized. Audit your LinkedIn headline and photo first.

**Low DM reply rate (<10%):**  
Your opener isn't personalized enough, or your first DM is too long. Cut the length in half and add one specific observation about them.

**Low call-to-close rate (<20%):**  
Price objections = guarantee isn't strong enough. Trust objections = you need more proof in the call. Revisit `discovery-call-script.md`.

**No-shows on discovery calls:**  
Add a reminder sequence in Calendly: 24-hour reminder + 1-hour reminder. Reduce call frequency if too many no-shows — it often means the ICP quality is too low.
