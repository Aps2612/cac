/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_SITE_URL?: string;
  readonly VITE_DEMO_URL?: string;
  readonly VITE_BOOKING_URL?: string;
  readonly VITE_CONTACT_EMAIL?: string;
  readonly VITE_FOUNDER_LINKEDIN_URL?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
