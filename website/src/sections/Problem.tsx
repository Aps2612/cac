import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { DecisionBadge, IllustrativeTag, type DecisionKind } from "../components/Decision";

const sources = ["Orders", "Website behaviour", "WhatsApp", "Email", "Products", "Inventory", "Customer history"];

const customers: { n: string; ctx: string; d: string; k: DecisionKind }[] = [
  { n: "Customer A", ctx: "Day 37 of a ~35-day reorder cycle", d: "Replenishment reminder", k: "action" },
  { n: "Customer B", ctx: "Bought 3 days ago, messaged yesterday", d: "No action", k: "none" },
  { n: "Customer C", ctx: "Regular buyer, quiet for 4 months", d: "Reactivation", k: "action" },
  { n: "Customer D", ctx: "Repeat buyer, strong category affinity", d: "Product recommendation", k: "action" },
  { n: "Customer E", ctx: "Rarely opens email, active on WhatsApp", d: "Different channel", k: "channel" },
];

export function Problem() {
  return (
    <Section
      id="product"
      eyebrow="The problem"
      title="Your brand already has the data. The hard part is deciding what to do with it."
      lede="Orders, events, consent and campaign history sit across your tools. None of them, on their own, tell your team who to act on today — or who to leave alone."
      className="border-t border-line bg-white"
    >
      <div className="mt-14 grid gap-6 lg:grid-cols-[0.9fr_auto_1.35fr] lg:items-center lg:gap-8">
        <Reveal>
          <p className="eyebrow mb-3">What you already have</p>
          <ul className="flex flex-wrap gap-2">
            {sources.map((s) => (
              <li key={s} className="rounded-lg border border-line bg-paper px-3 py-2 text-[13.5px] text-ink">{s}</li>
            ))}
          </ul>
        </Reveal>

        <Reveal delay={100} className="flex justify-center">
          <div className="relative flex flex-col items-center lg:flex-row">
            <span className="h-8 w-px bg-ink/20 lg:h-px lg:w-8" aria-hidden="true" />
            <div className="rounded-2xl bg-ink px-5 py-4 text-center text-paper shadow-lg lg:max-w-[190px]">
              <p className="text-[17px] font-semibold leading-tight tracking-tight">Who should we act on today?</p>
            </div>
            <span className="h-8 w-px bg-ink/20 lg:h-px lg:w-8" aria-hidden="true" />
          </div>
        </Reveal>

        <Reveal delay={200}>
          <div className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
              <p className="eyebrow">Today's decisions</p>
              <IllustrativeTag />
            </div>
            <ul className="divide-y divide-line">
              {customers.map((c) => (
                <li key={c.n} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="text-[14px] font-medium">{c.n}</p>
                    <p className="text-[12.5px] text-muted">{c.ctx}</p>
                  </div>
                  <DecisionBadge kind={c.k} className="self-start sm:self-auto">{c.d}</DecisionBadge>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
