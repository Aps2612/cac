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

Everything lives in **`src/config.ts`** (`SITE_CONFIG`). Each value can also be
set without code changes as an environment variable — in `.env`, or in Render →
Environment — and takes effect on the next deploy:

| Variable | Purpose |
|---|---|
| `VITE_BOOKING_URL` | Calendly / Cal.com / Tally / Google Form for "Book a Retention Audit" and "Discuss a Pilot" |
| `VITE_CONTACT_EMAIL` | Used as a `mailto:` fallback when no booking URL is set, and shown in the contact section |
| `VITE_DEMO_URL` | Product demo link (defaults to the current Render prototype) |
| `VITE_SITE_URL` | Public URL, used for canonical + Open Graph tags (update if you add a custom domain) |
| `VITE_FOUNDER_LINKEDIN_URL` | Optional link in the About section |

CTA resolution: booking URL → mailto → on-page `#contact` section.
Until one of the first two is set, the contact section says "Audit bookings
are opening shortly." — **set at least one before sharing the site.**

If you change `VITE_SITE_URL`, also update `public/robots.txt` and
`public/sitemap.xml`.

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
