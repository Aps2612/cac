/**
 * SITE_CONFIG — the one place to change links and contact details.
 *
 * Each value can be set here directly, or overridden at build time with the
 * matching VITE_* environment variable (see .env, or Render → Environment).
 *
 * Primary CTA resolution ("Book a Retention Audit" / "Discuss a Pilot"):
 *   1. bookingUrl   (Calendly / Cal.com / Tally / Google Form)   if set
 *   2. mailto:contactEmail                                       if set
 *   3. the on-page #contact section                              otherwise
 */
const env = import.meta.env;

export const SITE_CONFIG = {
  name: "Nirnaya",
  siteUrl: env.VITE_SITE_URL || "https://nirnaya-website.onrender.com",
  /** Prototype. Kept visually secondary to the audit CTA. */
  demoUrl: env.VITE_DEMO_URL || "https://customer-acquisition-azcp.onrender.com/",
  /** e.g. "https://cal.com/your-handle/retention-audit". Leave empty until real. */
  bookingUrl: env.VITE_BOOKING_URL || "",
  /** e.g. "founder@yourdomain.com". Leave empty until real. */
  contactEmail: env.VITE_CONTACT_EMAIL || "",
  /** Optional. Shown in the About section when set. */
  founderLinkedInUrl: env.VITE_FOUNDER_LINKEDIN_URL || "",
} as const;

export type CtaIntent = "audit" | "pilot";

const SUBJECTS: Record<CtaIntent, string> = {
  audit: "Retention Audit — Nirnaya",
  pilot: "Pilot discussion — Nirnaya",
};

export function ctaHref(intent: CtaIntent = "audit"): string {
  if (SITE_CONFIG.bookingUrl) return SITE_CONFIG.bookingUrl;
  if (SITE_CONFIG.contactEmail) {
    return `mailto:${SITE_CONFIG.contactEmail}?subject=${encodeURIComponent(SUBJECTS[intent])}`;
  }
  return "#contact";
}

export const isContactConfigured = Boolean(SITE_CONFIG.bookingUrl || SITE_CONFIG.contactEmail);
export const isExternal = (href: string) => /^https?:\/\//.test(href);
