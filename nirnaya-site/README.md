# Nirnaya — website (v2, simplified)

A short, static marketing site for Nirnaya. It is separate from the product app
(`app/`) and from the first website draft (`website/`), which are untouched.

**Stack:** Vite + React + TypeScript + Tailwind CSS. No backend, no database.

## Run on your computer

```bash
cd nirnaya-site
npm install
npm run dev      # open http://localhost:5173
npm run build    # production files → nirnaya-site/dist
```

## Change contact details / links

Edit **`src/config.ts`**: demo URL, email, phone, form endpoint, optional booking link.

## The "Book a Demo" form

Leads are sent by email to `apsingh1722@gmail.com` through **FormSubmit**
(free, no account, no API key, nothing secret in the code).

**One-time activation:** the first time anyone submits the form, FormSubmit
emails apsingh1722@gmail.com asking you to confirm. Click **Activate**. From then
on every submission arrives in that inbox (reply goes straight to the lead).
Do a test submission yourself right after the site goes live.

If the form service ever fails, visitors are shown your email and phone instead.

## Page sections (src/sections)

Nav → Hero → Problem → NoAction → HowItWorks → Example → Benefits → Tools → BookDemo → Footer

## Deploy on Render (free Static Site)

| Field | Value |
|---|---|
| Name | `nirnaya` |
| Branch | `main` |
| Root directory | `nirnaya-site` |
| Build command | `npm ci && npm run build` |
| Publish directory | `dist` |
| Build filter → included paths | `nirnaya-site/**` |
