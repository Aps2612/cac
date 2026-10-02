import { SITE_CONFIG } from "../config";

export type Lead = { name: string; company: string; email: string; phone?: string; message?: string };
export type SendResult = { ok: true } | { ok: false; reason: string };

/**
 * Sends a demo request by email. No backend of our own.
 *  - If SITE_CONFIG.web3formsKey is set → Web3Forms (recommended, most reliable).
 *  - Otherwise → FormSubmit (works only after its one-time activation email is clicked).
 */
export async function sendLead(lead: Lead): Promise<SendResult> {
  const subject = `Nirnaya demo request — ${lead.company || lead.name}`;
  const useWeb3 = Boolean(SITE_CONFIG.web3formsKey);
  const url = useWeb3 ? "https://api.web3forms.com/submit" : SITE_CONFIG.formEndpoint;
  const body = useWeb3
    ? { access_key: SITE_CONFIG.web3formsKey, subject, from_name: "Nirnaya website", replyto: lead.email, ...lead }
    : { ...lead, _subject: subject, _template: "table", _captcha: "false", _replyto: lead.email };

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const json: { success?: boolean | string; message?: string } = await res.json().catch(() => ({}));
    const success = json.success === true || json.success === "true";
    if (res.ok && success) return { ok: true };
    const msg = json.message || `HTTP ${res.status}`;
    if (/activat/i.test(msg)) {
      console.warn("[Nirnaya form] FormSubmit is not activated yet. Click 'Activate Form' in the email sent to", SITE_CONFIG.contactEmail);
    } else {
      console.warn("[Nirnaya form] send failed:", msg);
    }
    return { ok: false, reason: msg };
  } catch (err) {
    console.warn("[Nirnaya form] network error:", err);
    return { ok: false, reason: "network" };
  }
}

/** A mailto: link pre-filled with everything the visitor typed — so a lead is never lost. */
export function leadMailto(lead: Lead): string {
  const lines = [
    `Name: ${lead.name}`,
    `Company: ${lead.company}`,
    `Email: ${lead.email}`,
    lead.phone ? `Phone: ${lead.phone}` : "",
    "",
    lead.message || "",
  ].filter((l, i) => l !== "" || i === 4);
  return `mailto:${SITE_CONFIG.contactEmail}?subject=${encodeURIComponent(`Nirnaya demo request — ${lead.company || lead.name}`)}&body=${encodeURIComponent(lines.join("\n"))}`;
}
