# Tool Stack Setup Guide

**Total monthly cost after setup: Under $5 (Stripe fees only)**  
**One-time annual cost: $19 (Carrd.co)**  
**Setup time: 6–8 hours, Week 1 only**

---

## Setup Order (Follow This Sequence)

1. Stripe (payment processing — set this up first, you need the link before anything else)
2. Calendly (scheduling — needed for all CTAs)
3. MailerLite (email — needed before Tally)
4. Tally.so (lead capture — connect to MailerLite after MailerLite is ready)
5. Carrd.co (landing page — uses all the above links)
6. Google Sheets (pipeline tracker — independent, set up any time)

---

## 1. Stripe

**URL:** stripe.com  
**Cost:** Free — 2.9% + $0.30 per transaction  
**Setup time:** 30 minutes (ID verification required)

### Steps:
1. Create account → Complete identity verification (takes 1–2 days to fully activate)
2. Go to: Dashboard → Products → Add Product
3. Create your offer: Name = "The Strategy Sprint" | Price = $2,500 | One-time payment
4. Click "Share payment link" → Copy the link
5. Save this link somewhere accessible — it goes in every email and conversation

**Your Stripe payment link:** _________________________ (fill in after setup)

### Create a High-Ticket Tier:
Repeat steps 3–4 with:
- Name = "Strategy Sprint — Full Implementation"
- Price = $5,000

**Your $5K link:** _________________________

### Optional — Create a Retainer Product (Month 2):
- Name = "Strategy Retainer"
- Price = $1,500/month
- Billing = Recurring, Monthly

---

## 2. Calendly

**URL:** calendly.com  
**Cost:** Free tier (limited to 1 event type — sufficient for now)  
**Setup time:** 20 minutes

### Steps:
1. Create account
2. Create one Event Type: "Free 20-Minute Strategy Call"
3. Settings to configure:
   - Duration: 20 minutes
   - Available hours: Your actual open windows (be specific — don't open every hour)
   - Buffer time: 10 minutes before and after (prevents back-to-back calls)
   - Max events per day: 3 (prevents burn-out)
4. Add this question to the booking form: "What's the #1 challenge you're hoping this call helps clarify?" (gives you pre-call context)
5. Copy your Calendly link

**Your Calendly link:** _________________________ (fill in after setup)

### Confirmation Email (Auto-Send):
Calendly sends a confirmation automatically. Add this to the confirmation email body:
```
Looking forward to our call, [Name].

To make the most of our 20 minutes, come prepared to share:
- The specific challenge you're dealing with
- What you've already tried
- What solving it would be worth to you

See you then.
[Your Name]
```

---

## 3. MailerLite

**URL:** mailerlite.com  
**Cost:** Free up to 1,000 subscribers  
**Setup time:** 1 hour

### Steps:
1. Create account → Verify your email
2. Go to Subscribers → Groups → Create Group: "Sprint Leads"
3. Create Group: "Scorecard Downloads"
4. Go to Campaigns → Automations → Create Automation: "Scorecard Welcome"
   - Trigger: When subscriber is added to group "Scorecard Downloads"
   - Email 1: Welcome email (immediate) — copy from `email-sequences.md` Sequence B
   - Email 2: Day 3 follow-up
   - Email 3: Day 7 follow-up
5. Create Automation: "Post-Call Follow-Up"
   - Trigger: Manual (you add them to "Sprint Leads" after each call)
   - Email 1: Same day
   - Email 2: Day 3
   - Email 3: Day 7

**Your MailerLite account login:** _________________________ (fill in)

---

## 4. Tally.so

**URL:** tally.so  
**Cost:** Free  
**Setup time:** 45 minutes

### Steps:
1. Create account
2. New Form → Blank
3. Add fields:
   - Short Answer: "First Name"
   - Short Answer: "Last Name"
   - Email: "Email Address"
   - Optional: "What's your biggest strategic challenge right now?" (Long answer)
4. On Thank You page: Add your PDF link (Google Drive) and the text:
   ```
   Your scorecard is ready. Download it below.
   [PDF LINK]
   
   If you score under 35, let's talk:
   [YOUR CALENDLY LINK]
   ```
5. Go to Integrations → MailerLite → Connect → Map fields:
   - Email → Email
   - First Name → First Name
   - Add to Group: "Scorecard Downloads"
6. Publish the form → Copy the URL

**Your Tally form URL:** _________________________ (fill in after setup)

---

## 5. Carrd.co

**URL:** carrd.co  
**Cost:** $19/year (Pro Lite — required for custom domain)  
**Setup time:** 90 minutes with copy from `landing-page-copy.md`

### Steps:
1. Create account → Choose Pro Lite plan ($19/year)
2. New Site → Start from Scratch → One Page
3. Build sections using the copy from `03-conversion/landing-page-copy.md`
4. Add your button: Link type = URL → Paste your Calendly link
5. Go to Settings → Custom Domain → Add your domain (or use the free carrd.co subdomain to start)
6. Publish

**Your landing page URL:** _________________________ (fill in after setup)

---

## 6. Google Sheets — Pipeline Tracker

Use the template in `05-tracking/pipeline-tracker.md`.

**URL:** sheets.google.com (free)  
**Setup time:** 20 minutes

---

## LinkedIn Profile Optimization Checklist

Before sending a single DM, your LinkedIn profile must convert.

### Headline (most important field)
**Formula:** "I help [ICP] achieve [outcome] in [timeframe] | Strategy Sprint"

**Your headline:** _________________________

❌ Don't use: "Founder | Consultant | Speaker | Coach"  
❌ Don't use: "Helping businesses grow"  
✓ Use: Specific ICP + specific outcome + one call to action

### Profile Photo
- [ ] Professional headshot (not a selfie, not a logo)
- [ ] Light background
- [ ] Face takes up 60% of the frame
- [ ] You're smiling or look approachable

### Banner Image
Create in Canva. Content:
- Your value proposition (headline text)
- One CTA: "Book a Free Call → [your Calendly link]"
- Clean design, 2 colors max

### About Section (first 2 lines are visible without "See more")
```
I help [ICP] achieve [specific outcome] in 90 days.

If you're a [ICP type] dealing with [problem], here's how I can help:
[2–3 short bullets]

[CTA]: Book a free 20-minute call: [Calendly link]
```

### Featured Section
Add 2 items:
1. Link to your landing page
2. Link to your Tally scorecard form

### Experience Section
Write your most recent role as outcome-based, not task-based:
```
[Role Title] | [Company]
Achieved [specific measurable outcome] by [what you did — brief].
```
