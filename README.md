# CA Professional Website

A clean, fast, single-page professional profile site for a practising
Chartered Accountant in India. Built as a static website (HTML + CSS + a little
JavaScript) — free to host, nothing to maintain, and **designed to comply with
ICAI guidelines** on what a CA's website may contain.

```
.
├── index.html        # The page (edit the [TODO] placeholders here)
├── assets/
│   ├── styles.css    # Styling — colours, layout, responsiveness
│   └── script.js     # Mobile menu, copyright year, "last updated" date
└── README.md         # This file
```

---

## 1. Fill in your details (10 minutes)

Open `index.html` and replace every `[…]` placeholder. They are marked with
`<!-- TODO -->` comments. The main ones:

| Placeholder | Where | What to put |
|---|---|---|
| `[Your Name]` | title, header, hero, footer | Your full name |
| `[Firm Name]` | hero, credentials | Your firm's name |
| `ICAI Membership No. [XXXXXX]` | hero, credentials | Your membership number |
| `Firm Registration No. [XXXXXXC]` | credentials | Your FRN |
| `[City]`, `[Office Address]` | about, contact | Your location & address |
| `you@example.com`, `+91 …` | contact, footer | Your email & phone |
| Profile / services text | about, services | Edit to match your practice |

Then open `assets/script.js` and update the **"Last updated" date** whenever you
change the content (ICAI requires this to be shown).

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

## 3. The enquiry form (optional)

The contact form is static, so it needs a free form-handling service to deliver
messages to your email. Easiest option — **Formspree** (free tier):

1. Sign up at https://formspree.io and create a form; you'll get an endpoint URL.
2. In `index.html`, change the form tag:
   ```html
   <form class="enquiry" action="https://formspree.io/f/YOUR_ID" method="POST">
   ```

If you'd rather not have a form, delete the `<form …>…</form>` block and just
keep the email/phone — equally compliant and simpler.

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
