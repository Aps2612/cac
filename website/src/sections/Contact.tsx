import { Reveal } from "../components/Reveal";
import { Button } from "../components/Button";
import { ctaHref, isContactConfigured, SITE_CONFIG } from "../config";

export function Contact() {
  return (
    <section id="contact" className="relative overflow-hidden bg-ink py-20 text-paper sm:py-28">
      <div className="pointer-events-none absolute inset-0 grid-bg-dark [mask-image:radial-gradient(ellipse_at_top,black_20%,transparent_70%)]" aria-hidden="true" />
      <div className="container-x relative">
        <Reveal className="mx-auto max-w-3xl text-center">
          <p className="eyebrow mb-5 !text-mint/80">Retention audit</p>
          <h2 className="text-[2.1rem] leading-[1.08] font-semibold tracking-[-0.03em] sm:text-[3rem]" style={{ textWrap: "balance" }}>
            Want to know where your existing customer base has untapped retention opportunity?
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-[1.05rem] leading-relaxed text-paper/65 sm:text-lg">
            We're working with selected D2C brands to evaluate customer behaviour, identify actionable retention opportunities and test whether better decisioning can create incremental value.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            {isContactConfigured ? (
              <Button href={ctaHref("audit")} variant="light" size="lg" arrow>Book a Retention Audit</Button>
            ) : (
              <p className="rounded-full border border-white/15 px-5 py-3 text-[14px] text-paper/70">
                Audit bookings are opening shortly.
              </p>
            )}
            <Button href={SITE_CONFIG.demoUrl} variant="outline-light" size="lg">Open Product Demo</Button>
          </div>
          {SITE_CONFIG.contactEmail && (
            <p className="mt-6 text-[14px] text-paper/55">
              Or write to <a className="text-paper underline underline-offset-4" href={`mailto:${SITE_CONFIG.contactEmail}`}>{SITE_CONFIG.contactEmail}</a>
            </p>
          )}
          <p className="mt-8 text-[12.5px] text-paper/40">The product demo is an early prototype running on sample data and may take a moment to wake up.</p>
        </Reveal>
      </div>
    </section>
  );
}
