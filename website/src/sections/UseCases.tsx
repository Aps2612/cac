import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { StatusTag } from "../components/Decision";

const cases: { t: string; d: string; q: string; s: "focus" | "next" }[] = [
  { t: "Replenishment", d: "Identify customers approaching their expected reorder window.", q: "Who is about to run out?", s: "focus" },
  { t: "No-action decisioning", d: "Identify customers who should not be contacted today, and record why.", q: "Who should we leave alone?", s: "focus" },
  { t: "Channel decisioning", d: "Choose the appropriate channel from behaviour, preference and consent.", q: "Where will they actually see it?", s: "focus" },
  { t: "Discount decisioning", d: "Determine when an incentive may be necessary versus when it may unnecessarily reduce margin.", q: "Do they need an offer at all?", s: "focus" },
  { t: "Reactivation", d: "Identify lapsed customers who may have meaningful reactivation potential.", q: "Who is worth winning back?", s: "next" },
];

export function UseCases() {
  return (
    <Section
      id="use-cases"
      eyebrow="Use cases"
      title="Built around real retention decisions."
      lede="We're starting narrow — repeat purchase for consumable categories — and expanding as each decision type proves itself in pilots."
      className="border-t border-line bg-white"
    >
      <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {cases.map((c, i) => (
          <Reveal key={c.t} delay={i * 60}>
            <article className={`flex h-full flex-col rounded-2xl border p-6 ${c.s === "focus" ? "border-line bg-paper" : "border-dashed border-ink/20 bg-white"}`}>
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-[17px] font-semibold tracking-tight">{c.t}</h3>
                {c.s === "focus" ? <StatusTag>Initial focus</StatusTag> : <StatusTag tone="muted">Coming next</StatusTag>}
              </div>
              <p className="mt-2 text-[14px] leading-relaxed text-muted">{c.d}</p>
              <p className="mt-auto pt-6 font-mono text-[12.5px] text-ink/70">“{c.q}”</p>
            </article>
          </Reveal>
        ))}
        <Reveal delay={320}>
          <div className="flex h-full flex-col justify-center rounded-2xl bg-ink p-6 text-paper">
            <p className="text-[15px] leading-relaxed text-paper/75">
              Initial-focus decisions are rules-based and transparent today, and are the scope we pilot. Learned decisioning builds on top as outcome data accumulates.
            </p>
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
