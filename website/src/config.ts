/**
 * SITE_CONFIG — the one place to change links and contact details.
 * Any value can also be overridden with the matching VITE_* env variable
 * (in .env, or Render → Environment).
 */
const env = import.meta.env;

export const SITE_CONFIG = {
  name: "Nirnaya",
  siteUrl: env.VITE_SITE_URL || "https://nirnaya-website.onrender.com",
  /** Prototype. Kept visually secondary to "Book a Demo". */
  demoUrl: env.VITE_DEMO_URL || "https://customer-acquisition-azcp.onrender.com/",

  founderName: "Ayush Singh",
  contactEmail: env.VITE_CONTACT_EMAIL || "apsingh1722@gmail.com",
  phone: env.VITE_CONTACT_PHONE || "+91 78870 04294",

  /**
   * Where the "Book a Demo" form is sent. Default: FormSubmit (free, no account,
   * no API key). The first submission triggers a one-time activation email to
   * contactEmail — click "Activate" and every later lead arrives by email.
   */
  formEndpoint:
    env.VITE_FORM_ENDPOINT ||
    `https://formsubmit.co/ajax/${env.VITE_CONTACT_EMAIL || "apsingh1722@gmail.com"}`,

  /**
   * Recommended: a free Web3Forms access key (https://web3forms.com — enter
   * apsingh1722@gmail.com, the key arrives by email). It is safe to be public.
   * When set, the form uses Web3Forms instead of FormSubmit.
   */
  web3formsKey: env.VITE_WEB3FORMS_KEY || "",

  /** Optional Calendly / Cal.com link, shown beside the form when set. */
  bookingUrl: env.VITE_BOOKING_URL || "",
} as const;

/** Every "Book a Demo" / "Discuss a Pilot" button scrolls to the demo form. */
export const ctaHref = () => "#contact";
export const telHref = `tel:${SITE_CONFIG.phone.replace(/[^+\d]/g, "")}`;
export const mailHref = (subject = "Nirnaya") =>
  `mailto:${SITE_CONFIG.contactEmail}?subject=${encodeURIComponent(subject)}`;
export const isExternal = (href: string) => /^https?:\/\//.test(href);
