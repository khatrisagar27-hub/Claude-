# CA Professional Website

A clean, fast, single-page professional profile site for a practising
Chartered Accountant in India. Built as a static website (HTML + CSS + a little
JavaScript) — free to host, nothing to maintain, and **designed to comply with
ICAI guidelines** on what a CA's website may contain.

```
.
├── index.html                      # The page (edit the [TODO] placeholders here)
├── assets/
│   ├── styles.css                  # Styling — colours, layout, responsiveness
│   ├── script.js                   # Mobile menu, copyright year, "last updated" date
│   ├── ca-logo.svg                 # PLACEHOLDER — replace with the official ICAI CA Logo
│   └── profile-placeholder.svg     # PLACEHOLDER — replace with the proprietor's photo
└── README.md                       # This file
```

The site is built for **Sagar Khatri & Associates, Chartered Accountants**
(Proprietor: **CA Sagar Khatri**, established **2022**). Sections: Profile (with
photo), Services, Knowledge/Articles, FAQ, Firm particulars, Contact.

> By choice, the **ICAI membership number and Firm Registration Number are not
> shown** on this site. (Both are *permitted* by ICAI but not mandatory — you can
> add them later in the "Firm particulars" section if you ever change your mind.)

---

## 1. Fill in the remaining details (10 minutes)

Firm name, proprietor, and year are already filled in. Open `index.html` and
replace the remaining `[…]` placeholders, all marked with `<!-- TODO -->`:

| Placeholder | Where | What to put |
|---|---|---|
| `[Office Address …]`, `[Area]`, `[City]`, `[PIN]` | contact, profile | Office address & city |
| `you@example.com`, `+91 …` | contact, footer | Your email & phone |
| Profile / services text | about, services | Tweak wording to match your practice |
| Knowledge article cards | knowledge | Replace with your own factual notes (or remove) |
| FAQ questions/answers | faq | Edit to suit |
| LinkedIn / Google Business links | contact | Optional, permitted — uncomment & add |

Then open `assets/script.js` and update the **"Last updated" date** whenever you
change the content (ICAI requires this to be shown).

---

## 1a. The CA Logo (important)

The header and footer show a **placeholder** in the CA-logo slot
(`assets/ca-logo.svg`). It is **not** the official mark. To use the real one:

1. Download the official **"CA Logo"** artwork from ICAI — it is provided to
   members (ICAI website → logo / branding guidelines, or your members' login).
2. Save it as `assets/ca-logo.svg` (or `.png`) — overwrite the placeholder. If
   you use a `.png`/`.jpg`, update the two `src="assets/ca-logo.svg"` references
   in `index.html` to the new filename.
3. **Use it exactly as provided** — ICAI's logo guidelines require that you do
   **not** alter its design, colour, font or proportions, do not add effects,
   and do not display it more prominently than the firm name. When in doubt,
   read ICAI's current logo guidelines.

Similarly, replace `assets/profile-placeholder.svg` with a passport-style photo
(save as `assets/profile.jpg` and update the `<img src>` in the Profile section).
Photographs are permitted by ICAI.

---

## 2. ⚖️ ICAI compliance — please read

A CA in practice is bound by the **Chartered Accountants Act, 1949** (Clauses 6
& 7 of Part I of the First Schedule — advertising & solicitation) and the
**ICAI Council Guidelines for posting particulars on a website**. This template
is built to stay within them, but **you are responsible for the final content**.
Keep these rules in mind as you edit:

**The site is built to do this (keep it that way):**
- Acts as a **"pull" service** (people find it; it is not pushed/advertised).
- States facts only — name, qualifications, firm, services, contact.
- Shows a **"last updated" date**.
- Carries a footer disclaimer that it does not solicit or advertise.

**Do NOT add (these breach the guidelines):**
- ❌ Client names / a client list
- ❌ Testimonials, reviews, or endorsements
- ❌ Fees or fee comparisons
- ❌ Superlatives or claims — "best", "expert", "specialist", "leading",
      "No. 1", "renowned", etc.
- ❌ Visitor counters / "hits" displays
- ❌ Photographs of clients, or anything designed mainly to attract attention
- ❌ Pop-ups, banner ads, or links to soliciting sites
- ❌ Pushing the link via mass email / ads to people who didn't ask

> ⚠️ Guidelines are periodically revised by ICAI. Before publishing, please
> check the **current** Council Guidelines (ICAI website) or confirm with your
> Regional Council. When in doubt, leave it out.

---

## 3. The enquiry form — connect Formspree (one step)

The form is already wired up for **Formspree** (free): it submits via AJAX so the
visitor stays on the page and sees an inline "thank you", with a hidden honeypot
field for spam protection. You only need to plug in your form ID:

1. **Create a free account** at https://formspree.io and add a **New form**.
   Set the notification email to the address where you want enquiries to land.
2. Formspree gives you an endpoint like `https://formspree.io/f/abcdwxyz`.
   The part after `/f/` (e.g. `abcdwxyz`) is your **form ID**.
3. In `index.html`, find this line and replace `YOUR_FORM_ID` with your ID:
   ```html
   <form class="enquiry" id="enquiry-form" action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
   ```
4. Commit & push. On the **first** real submission, Formspree emails you a link
   to confirm the address — click it once and the form is live.

Until you do step 3, the form politely tells visitors to email you directly
instead (so it never silently fails). The free tier allows 50 submissions/month.

> Tip: just send me your form ID and I'll drop it in and push for you.

If you'd rather not have a form at all, delete the `<form …>…</form>` block and
keep just the email/phone — equally compliant and simpler.

---

## 4. Buy a domain + put it live

I can build and deploy the code, but **I cannot make purchases for you** — buying
a domain needs your own payment details and account. Here is exactly how to do it
yourself, cheaply and safely.

### A. Buy a domain name (~₹700–₹1,200/year)
Pick a sober, professional name, e.g. `canamelastname.in` or
`yourfirm.com`. Reputable registrars:
- **Cloudflare Registrar** — at-cost pricing, no markup (recommended)
- **Google Domains / Squarespace Domains**, **GoDaddy**, **Namecheap**, **BigRock** (Indian)

> 💡 A registrar only sells you the *name*. Hosting (below) is separate — and free.

### B. Host it for free
This is a static site, so you don't need to pay for hosting. Best free options:

**Option 1 — GitHub Pages (recommended; this repo is already on GitHub)**
1. Push this code to GitHub (your branch is `claude/website-purchase-build-yx2uu8`).
2. In the repo: **Settings → Pages → Build from branch →** select your branch,
   folder `/ (root)` → Save.
3. Your site goes live at `https://<username>.github.io/<repo>/`.
4. To use your bought domain: add it under **Pages → Custom domain**, then at
   your registrar add the DNS records GitHub shows you (an `A`/`CNAME` record).

**Option 2 — Netlify or Cloudflare Pages**
- Connect the GitHub repo, no build command needed (it's plain HTML),
  publish directory = root. Drag-and-drop deploy also works. Free HTTPS included.

### C. Make it secure & findable
- **HTTPS**: all the hosts above give a free SSL certificate automatically.
- **SEO**: the page already has title/description meta tags — keep them factual.

---

## 5. Preview it locally

Just open `index.html` in your browser. Or run a tiny local server:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

---

## Summary of costs
| Item | Cost |
|---|---|
| The website code | Done (free) |
| Domain name | ~₹700–₹1,200 / year |
| Hosting (GitHub Pages / Netlify / Cloudflare) | Free |
| SSL / HTTPS | Free |
| Form service (Formspree, optional) | Free tier |

**Total: roughly ₹1,000 a year for the domain — everything else is free.**
