import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { DecisionBadge, type DecisionKind } from "../components/Decision";

const data = ["Orders", "Website", "WhatsApp", "Email", "Products", "Inventory"];

const rows: { c: string; s: string; d: string; k: DecisionKind }[] = [
  { c: "A", s: "Ready to reorder", d: "Send reminder", k: "action" },
  { c: "B", s: "Purchased recently", d: "Do nothing", k: "none" },
  { c: "C", s: "Likely to return anyway", d: "No discount", k: "incentive" },
  { c: "D", s: "Going quiet", d: "Reactivate", k: "action" },
  { c: "E", s: "Prefers WhatsApp, no consent", d: "Not on WhatsApp", k: "channel" },
];

export function Problem() {
  return (
    <Section
      eyebrow="The problem"
      title="Your brand has the data. The hard part is deciding what to do with it."
      className="border-t border-line bg-white"
    >
      <div className="mt-12 grid grid-cols-1 items-center gap-8 lg:grid-cols-[1fr_auto_1.25fr] lg:gap-10 [&>*]:min-w-0">
        <Reveal>
          <ul className="flex flex-wrap gap-2">
            {data.map((d) => <li key={d} className="rounded-lg border border-line bg-paper px-3.5 py-2 text-[14px]">{d}</li>)}
          </ul>
        </Reveal>
        <Reveal delay={80} className="flex justify-center">
          <div className="flex flex-col items-center lg:flex-row">
            <span className="h-6 w-px bg-ink/20 lg:h-px lg:w-6" aria-hidden="true" />
            <p className="rounded-2xl bg-ink px-5 py-3.5 text-center text-[16px] font-semibold leading-tight text-paper lg:max-w-[180px]">Who should we act on today?</p>
            <span className="h-6 w-px bg-ink/20 lg:h-px lg:w-6" aria-hidden="true" />
          </div>
        </Reveal>
        <Reveal delay={160}>
          <ul className="card divide-y divide-line overflow-hidden">
            {rows.map((r) => (
              <li key={r.c} className="flex items-center justify-between gap-3 px-4 py-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-paper-2 font-mono text-[11px] text-muted">{r.c}</span>
                  <span className="text-[13.5px] leading-snug sm:text-[14px]">{r.s}</span>
                </div>
                <DecisionBadge kind={r.k}>{r.d}</DecisionBadge>
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </Section>
  );
}
