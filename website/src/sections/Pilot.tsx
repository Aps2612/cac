import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { Button } from "../components/Button";
import { ctaHref } from "../config";

const steps = [
  { t: "Share customer/order data", d: "An export is enough to start. No integration project upfront." },
  { t: "Define one retention objective", d: "For example: replenishment for one hero product line." },
  { t: "Run Nirnaya in shadow mode", d: "Decisions are generated and reviewed by your team — nothing is sent." },
  { t: "Launch a controlled intervention", d: "Your channels, your messaging, with a held-back control group." },
  { t: "Measure incremental impact", d: "Compare treatment and control, and decide what to do next together." },
];

export function Pilot() {
  return (
    <Section
      id="pilot"
      eyebrow="Pilot"
      title="Start with one retention problem."
      lede="We don't ask brands to rebuild their marketing stack. Start with one customer segment, one retention use case and a controlled pilot."
      className="border-t border-line bg-white"
    >
      <div className="mt-14 grid gap-10 lg:grid-cols-[1.4fr_1fr] lg:gap-16">
        <ol className="relative space-y-0">
          {steps.map((s, i) => (
            <li key={s.t}>
              <Reveal delay={i * 60} className="relative flex gap-5 pb-8 last:pb-0">
                <div className="flex flex-col items-center">
                  <span className={`flex h-9 w-9 flex-none items-center justify-center rounded-full font-mono text-[12px] ${i === 2 ? "bg-ink text-paper" : "border border-line bg-paper text-ink"}`}>0{i + 1}</span>
                  {i < steps.length - 1 && <span className="mt-1 w-px flex-1 bg-line" aria-hidden="true" />}
                </div>
                <div className="pt-1.5 pb-2">
                  <h3 className="text-[16.5px] font-semibold tracking-tight">{s.t}</h3>
                  <p className="mt-1 text-[14px] leading-relaxed text-muted">{s.d}</p>
                </div>
              </Reveal>
            </li>
          ))}
        </ol>
        <Reveal delay={150}>
          <div className="sticky top-24 rounded-2xl border border-line bg-paper p-6 sm:p-7">
            <p className="eyebrow">What you get from a pilot</p>
            <ul className="mt-4 space-y-3 text-[14.5px] leading-snug">
              <li>A customer-level view of who needs action — and who doesn't</li>
              <li>Every decision with its reason, reviewable before anything is sent</li>
              <li>A measured answer on whether the intervention created incremental value</li>
            </ul>
            <p className="mt-6 border-t border-line pt-5 text-[13px] text-muted">
              Pilot pricing available based on use case and data complexity.
            </p>
            <Button href={ctaHref()} className="mt-5 w-full" size="lg" arrow>Discuss a Pilot</Button>
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
