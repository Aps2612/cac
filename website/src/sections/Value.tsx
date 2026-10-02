import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";

const icons = {
  outreach: <path d="M4 12h4l2-5 4 10 2-5h4" />,
  margin: <><path d="M12 3v18" /><path d="M16.5 7.5c0-1.7-2-3-4.5-3s-4.5 1.3-4.5 3S9.5 10.3 12 11s4.5 1.8 4.5 3.5-2 3-4.5 3-4.5-1.3-4.5-3" /></>,
  repeat: <><path d="M4 9a8 8 0 0 1 14-3l2 2" /><path d="M20 4v4h-4" /><path d="M20 15a8 8 0 0 1-14 3l-2-2" /><path d="M4 20v-4h4" /></>,
  measure: <><path d="M4 20V10" /><path d="M10 20V4" /><path d="M16 20v-7" /><path d="M2 20h20" /></>,
};

const cards = [
  { t: "Reduce wasted outreach", d: "Identify customers who actually need intervention instead of treating the entire customer base equally.", i: icons.outreach },
  { t: "Protect margin", d: "Use incentives when they are justified instead of automatically discounting.", i: icons.margin },
  { t: "Increase repeat revenue", d: "Find meaningful opportunities for replenishment, reactivation and repeat purchase.", i: icons.repeat },
  { t: "Measure incremental impact", d: "Measure whether interventions actually changed customer behaviour — not just what happened after them.", i: icons.measure },
];

export function Value() {
  return (
    <Section
      eyebrow="Why it matters"
      title="Better decisions show up in your retention economics."
      lede="You've already paid to acquire these customers. The question is how much of that value you keep — and how much you give away in unnecessary messages and discounts."
      className="border-t border-line bg-white"
    >
      <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c, idx) => (
          <Reveal key={c.t} delay={idx * 70}>
            <article className="h-full rounded-2xl border border-line bg-paper p-6 transition-colors hover:border-ink/25">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-ink text-paper">
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{c.i}</svg>
              </span>
              <h3 className="mt-6 text-[17px] font-semibold tracking-tight">{c.t}</h3>
              <p className="mt-2 text-[14px] leading-relaxed text-muted">{c.d}</p>
            </article>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
