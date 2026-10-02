import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";

const steps = [
  { t: "Understand", d: "Bring together customer, order, product and behavioural context." },
  { t: "Filter", d: "Apply consent, eligibility and business constraints." },
  { t: "Decide", d: "Determine the appropriate action — or no action." },
  { t: "Activate", d: "Send the decision into the brand's existing engagement stack." },
  { t: "Measure", d: "Compare outcomes and learn what actually worked." },
];

export function HowItWorks() {
  return (
    <Section id="how-it-works" eyebrow="How it works" title="Five steps from customer data to a measured decision." className="border-t border-line bg-white">
      <ol className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-5">
        {steps.map((s, i) => (
          <li key={s.t} className="bg-white">
            <Reveal delay={i * 60} className="h-full p-6">
              <p className="font-mono text-[12px] text-faint">0{i + 1}</p>
              <h3 className="mt-8 text-[19px] font-semibold tracking-tight">{s.t}</h3>
              <p className="mt-2 text-[14px] leading-relaxed text-muted">{s.d}</p>
            </Reveal>
          </li>
        ))}
      </ol>
    </Section>
  );
}
