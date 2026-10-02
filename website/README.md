# Nirnaya — marketing website

Static single-page site for Nirnaya. Independent from the product backend in
this repo (`app/`); nothing here talks to it except an outbound "Open Product
Demo" link.

**Stack:** Vite + React 19 + TypeScript + Tailwind CSS v4. Self-hosted Geist
fonts. No backend, no database, no analytics, no tracking.

## Run locally

```bash
cd website
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production build → website/dist
npm run preview    # serve the production build
```

## Change links / contact details

Everything lives in **`src/config.ts`** (`SITE_CONFIG`): demo URL, founder
name, email, phone, form endpoint and an optional booking (Calendly) link.

## The "Book a Demo" form

Every "Book a Demo" / "Discuss a Pilot" button scrolls to the form at the bottom
of the page. Submissions are emailed to `apsingh1722@gmail.com` through
**FormSubmit** (free, no account, no API key, nothing secret in the code).

**One-time activation:** the first submission makes FormSubmit email
apsingh1722@gmail.com asking you to confirm. Click **Activate**; after that every
lead arrives in that inbox. If sending ever fails, the visitor is shown the email
and phone instead.

## Structure

```
src/
  config.ts            ← links & contact (edit this)
  App.tsx              ← section order
  components/          ← Logo, Button, Section, Reveal, decision badges
  sections/            ← one file per page section
public/                ← favicon, og-image.png, robots.txt, sitemap.xml
scripts/assets.mjs     ← regenerates og-image + PNG favicons (needs Playwright)
```

## Deploy (Render Static Site, free)

Defined in `/render.yaml` at the repo root. Settings if creating by hand:

| Field | Value |
|---|---|
| Type | Static Site |
| Name | `nirnaya-website` |
| Branch | `main` |
| Root directory | `website` |
| Build command | `npm ci && npm run build` |
| Publish directory | `dist` |
| Build filter (included paths) | `website/**` |

Auto-deploy on push to `main` is on by default.
