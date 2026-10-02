/**
 * SITE_CONFIG — change links and contact details here.
 * (Any value can also be overridden with the matching VITE_* env variable.)
 */
const env = import.meta.env;

export const SITE_CONFIG = {
  siteUrl: env.VITE_SITE_URL || "https://nirnaya.onrender.com",

  /** Existing product prototype. Secondary to "Book a Demo". */
  demoUrl: env.VITE_DEMO_URL || "https://customer-acquisition-azcp.onrender.com/",

  founderName: "Ayush",
  contactEmail: env.VITE_CONTACT_EMAIL || "apsingh1722@gmail.com",
  phone: env.VITE_CONTACT_PHONE || "+91 78870 04294",

  /**
   * Where the "Book a Demo" form is sent. Default: FormSubmit (free, no account,
   * no API key). The very first submission triggers a one-time activation email
   * to contactEmail — click the link in it and every later lead arrives by email.
   * After activating, you can replace the email in this URL with the random alias
   * FormSubmit gives you, to keep the address out of the page source.
   */
  formEndpoint:
    env.VITE_FORM_ENDPOINT ||
    `https://formsubmit.co/ajax/${env.VITE_CONTACT_EMAIL || "apsingh1722@gmail.com"}`,

  /** Optional: a Calendly / Cal.com link. When set, it's shown next to the form. */
  bookingUrl: env.VITE_BOOKING_URL || "",
} as const;

export const telHref = `tel:${SITE_CONFIG.phone.replace(/[^+\d]/g, "")}`;
export const mailHref = (subject = "Nirnaya") =>
  `mailto:${SITE_CONFIG.contactEmail}?subject=${encodeURIComponent(subject)}`;
export const isExternal = (href: string) => /^https?:\/\//.test(href);
