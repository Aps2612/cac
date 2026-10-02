import { useState, type FormEvent } from "react";
import { Reveal } from "../components/Reveal";
import { SITE_CONFIG, mailHref, telHref } from "../config";

type Status = "idle" | "sending" | "sent" | "error";

const input =
  "mt-1.5 w-full rounded-xl border border-white/15 bg-white/[.06] px-3.5 py-3 text-[15px] text-paper placeholder:text-paper/35 outline-none transition-colors focus:border-mint/70 focus:bg-white/[.09]";

function Field({ label, name, type = "text", required = false, placeholder, autoComplete }: {
  label: string; name: string; type?: string; required?: boolean; placeholder?: string; autoComplete?: string;
}) {
  return (
    <label className="block">
      <span className="text-[13px] text-paper/70">{label}{required && <span className="text-mint"> *</span>}</span>
      <input name={name} type={type} required={required} placeholder={placeholder} autoComplete={autoComplete} className={input} />
    </label>
  );
}

export function Contact() {
  const [status, setStatus] = useState<Status>("idle");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries()) as Record<string, string>;
    if (data._honey) return; // spam bot
    setStatus("sending");
    try {
      const res = await fetch(SITE_CONFIG.formEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          ...data,
          _subject: `Nirnaya demo request — ${data.company || data.name}`,
          _template: "table",
          _captcha: "false",
          _replyto: data.email,
        }),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok || json.success === false || json.success === "false") throw new Error("send failed");
      setStatus("sent");
      form.reset();
    } catch {
      setStatus("error");
    }
  }

  return (
    <section id="contact" className="relative overflow-hidden bg-ink py-20 text-paper sm:py-28">
      <div className="pointer-events-none absolute inset-0 grid-bg-dark [mask-image:radial-gradient(ellipse_at_top_left,black_10%,transparent_60%)]" aria-hidden="true" />
      <div className="container-x relative grid gap-12 lg:grid-cols-[1fr_1.1fr] lg:gap-16">
        <Reveal>
          <p className="eyebrow mb-5 !text-mint/80">Book a demo</p>
          <h2 className="text-[2.1rem] leading-[1.08] font-semibold tracking-[-0.03em] sm:text-[2.8rem]" style={{ textWrap: "balance" }}>
            Want to know where your existing customers have untapped retention opportunity?
          </h2>
          <p className="mt-6 max-w-md text-[1.05rem] leading-relaxed text-paper/65">
            Tell us a little about your brand. We'll walk you through how Nirnaya would approach your customers and what a pilot could look like.
          </p>
          <div className="mt-10 space-y-2.5 text-[14.5px]">
            <p className="text-paper/45">Or reach the founder directly</p>
            <p className="font-medium">{SITE_CONFIG.founderName}, Founder</p>
            <p><a href={mailHref("Nirnaya — hello")} className="text-paper/80 underline decoration-white/25 underline-offset-4 hover:text-paper">{SITE_CONFIG.contactEmail}</a></p>
            <p><a href={telHref} className="text-paper/80 underline decoration-white/25 underline-offset-4 hover:text-paper">{SITE_CONFIG.phone}</a></p>
            {SITE_CONFIG.bookingUrl && (
              <p><a href={SITE_CONFIG.bookingUrl} target="_blank" rel="noopener noreferrer" className="text-paper/80 underline decoration-white/25 underline-offset-4 hover:text-paper">Pick a time on the calendar ↗</a></p>
            )}
            <p className="pt-3">
              <a href={SITE_CONFIG.demoUrl} target="_blank" rel="noopener noreferrer" className="text-[13.5px] text-mint hover:text-paper">Open the product demo ↗</a>
            </p>
          </div>
        </Reveal>

        <Reveal delay={100}>
          <div className="rounded-3xl border border-white/10 bg-ink-2 p-6 sm:p-8">
            {status === "sent" ? (
              <div className="flex min-h-[420px] flex-col items-center justify-center text-center" role="status">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-mint/15 text-mint">
                  <svg viewBox="0 0 16 16" className="h-6 w-6" aria-hidden="true"><path d="M3.5 8.5 6.5 11.5 12.5 4.5" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </span>
                <p className="mt-5 text-[20px] font-semibold">Thanks — we've got it.</p>
                <p className="mt-2 max-w-xs text-[14.5px] text-paper/60">We'll get back to you shortly to set up a time.</p>
                <button type="button" onClick={() => setStatus("idle")} className="mt-6 text-[13.5px] text-paper/60 underline underline-offset-4 hover:text-paper">Send another</button>
              </div>
            ) : (
              <form onSubmit={onSubmit} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Name" name="name" required autoComplete="name" />
                  <Field label="Company" name="company" required autoComplete="organization" />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Work email" name="email" type="email" required autoComplete="email" />
                  <Field label="Phone" name="phone" type="tel" autoComplete="tel" placeholder="+91" />
                </div>
                <label className="block">
                  <span className="text-[13px] text-paper/70">What would you like to discuss?</span>
                  <textarea name="message" rows={4} className={`${input} resize-y`} placeholder="e.g. repeat purchase for our hero product, too many discounts, which customers to message…" />
                </label>
                <input type="text" name="_honey" tabIndex={-1} autoComplete="off" className="hidden" aria-hidden="true" />
                <button
                  type="submit"
                  disabled={status === "sending"}
                  className="inline-flex h-12 w-full items-center justify-center rounded-full bg-paper text-[15px] font-medium text-ink transition-colors hover:bg-white disabled:opacity-60"
                >
                  {status === "sending" ? "Sending…" : "Book a Demo"}
                </button>
                {status === "error" && (
                  <p className="text-[13.5px] text-amber-soft" role="alert">
                    Something went wrong sending the form. Please email{" "}
                    <a href={mailHref("Nirnaya demo request")} className="underline">{SITE_CONFIG.contactEmail}</a> or call {SITE_CONFIG.phone}.
                  </p>
                )}
                <p className="text-[12px] text-paper/40">Your details go straight to the founder. We don't share them.</p>
              </form>
            )}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
