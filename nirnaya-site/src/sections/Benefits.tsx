import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";

const cards = [
  { t: "Better retention", d: "Identify customers with a genuine opportunity to return.", i: <><path d="M4 9a8 8 0 0 1 14-3l2 2" /><path d="M20 4v4h-4" /><path d="M20 15a8 8 0 0 1-14 3l-2-2" /><path d="M4 20v-4h4" /></> },
  { t: "Less wasted outreach", d: "Focus attention where an intervention actually makes sense.", i: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /></> },
  { t: "Protect margin", d: "Avoid discounts for customers who would buy without one.", i: <><path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6l-8-3Z" /></> },
  { t: "Measure impact", d: "Understand whether your actions actually changed customer behaviour.", i: <><path d="M4 20V10" /><path d="M10 20V4" /><path d="M16 20v-7" /><path d="M2 20h20" /></> },
];

export function Benefits() {
  return (
    <Section
      id="benefits"
      eyebrow="Benefits"
      title="What better decisions do for your business."
      lede="Less guesswork for your growth and CRM team. More of the right actions, fewer of the wrong ones."
    >
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c, i) => (
          <Reveal key={c.t} delay={i * 70}>
            <article className="h-full rounded-2xl border border-line bg-white p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-pine-soft text-pine">
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{c.i}</svg>
              </span>
              <h3 className="mt-6 text-[17px] font-semibold tracking-tight">{c.t}</h3>
              <p className="mt-2 text-[14.5px] leading-relaxed text-muted">{c.d}</p>
            </article>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
