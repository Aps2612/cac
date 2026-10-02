import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { SITE_CONFIG } from "../config";

export function About() {
  return (
    <Section id="about" eyebrow="About" title="Building the decisioning layer for D2C customer growth.">
      <Reveal className="mt-10 grid gap-8 lg:grid-cols-[1.4fr_1fr] lg:gap-16">
        <div className="space-y-4 text-[16px] leading-relaxed text-muted">
          <p>
            <span className="text-ink">Nirnaya</span> (निर्णय) means <em>decision</em>. We started it because D2C brands are rich in customer data but short on clear, accountable answers to the daily question of who to act on, how, and whether at all.
          </p>
          <p>
            We're early, and we're building this seriously: a working decisioning slice, a clear product principle — that no action is a valid decision — and a commitment to measuring incremental impact rather than attributed revenue. We're currently validating with selected D2C brands.
          </p>
        </div>
        <div className="card self-start p-6">
          <p className="eyebrow">Founder</p>
          <p className="mt-3 text-[17px] font-semibold">Built by Ayush Singh</p>
          <p className="mt-1.5 text-[14px] leading-relaxed text-muted">
            Engineer working on customer data, decisioning systems and retention for D2C.
          </p>
          {SITE_CONFIG.founderLinkedInUrl && (
            <a href={SITE_CONFIG.founderLinkedInUrl} target="_blank" rel="noopener noreferrer" className="mt-4 inline-block text-[14px] underline underline-offset-4">LinkedIn</a>
          )}
        </div>
      </Reveal>
    </Section>
  );
}
