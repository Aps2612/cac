import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { DecisionBadge, IllustrativeTag } from "../components/Decision";

type Kind = "derived" | "constraint" | "context" | "history";
const kindStyle: Record<Kind, string> = {
  derived: "text-pine bg-pine-soft",
  constraint: "text-ink bg-ink/[.07]",
  context: "text-muted bg-paper-2",
  history: "text-amber bg-amber-soft",
};
const kindLabel: Record<Kind, string> = { derived: "Derived", constraint: "Constraint", context: "Context", history: "Learned" };

const rows: { k: string; v: string; kind: Kind }[] = [
  { k: "Lifecycle", v: "Repeat customer", kind: "derived" },
  { k: "Preferred channel", v: "WhatsApp", kind: "derived" },
  { k: "WhatsApp consent", v: "Yes", kind: "constraint" },
  { k: "Price sensitivity", v: "Medium", kind: "derived" },
  { k: "Product affinity", v: "Protein / Wellness", kind: "derived" },
  { k: "Reorder signal", v: "High", kind: "derived" },
  { k: "Inventory", v: "Available", kind: "context" },
  { k: "Previous campaign", v: "No discount required", kind: "history" },
];

const checks = [
  "Inside expected reorder window",
  "WhatsApp consent on record",
  "Not contacted in the last 7 days",
  "Product in stock",
  "History shows no discount needed",
];

export function CustomerState() {
  return (
    <Section
      eyebrow="Customer state"
      title="One working view of each customer — built for making decisions."
      lede="Raw facts (orders, refunds, events, consent) stay as they are. Nirnaya derives a current customer state from them — recency, frequency, value, lifecycle, reorder likelihood — and recomputes it as new data arrives."
    >
      <Reveal className="mt-14">
        <div className="grid gap-4 lg:grid-cols-[1.15fr_1fr]">
          {/* profile */}
          <div className="card overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-3.5">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-paper-2 font-mono text-[12px] text-muted" aria-hidden="true">PK</span>
                <div>
                  <p className="text-[14px] font-semibold">Sample customer</p>
                  <p className="font-mono text-[11px] text-faint">demo · not a real person</p>
                </div>
              </div>
              <IllustrativeTag>Demo illustration</IllustrativeTag>
            </div>

            <div className="grid grid-cols-3 border-b border-line">
              {[
                ["R", "37", "days since order"],
                ["F", "5", "orders"],
                ["M", "₹8,420", "lifetime value"],
              ].map(([l, v, s], i) => (
                <div key={l} className={`px-5 py-4 ${i < 2 ? "border-r border-line" : ""}`}>
                  <p className="font-mono text-[11px] text-faint">{l}</p>
                  <p className="mt-1 text-[22px] font-semibold tracking-tight sm:text-[26px]">{v}</p>
                  <p className="text-[11.5px] text-muted">{s}</p>
                </div>
              ))}
            </div>

            <dl className="divide-y divide-line">
              {rows.map((r) => (
                <div key={r.k} className="flex items-center justify-between gap-3 px-5 py-2.5">
                  <dt className="text-[13px] text-muted">{r.k}</dt>
                  <dd className="flex items-center gap-2.5">
                    <span className="text-right text-[13.5px] font-medium">{r.v}</span>
                    <span className={`hidden w-[78px] rounded px-1.5 py-0.5 text-center font-mono text-[10px] uppercase tracking-[0.06em] sm:inline-block ${kindStyle[r.kind]}`}>{kindLabel[r.kind]}</span>
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          {/* decision */}
          <div className="flex flex-col gap-4">
            <div className="rounded-2xl bg-ink p-6 text-paper">
              <div className="flex items-center justify-between">
                <p className="eyebrow !text-mint/80">Nirnaya decision</p>
                <span className="pulse-dot h-2 w-2 rounded-full bg-mint" aria-hidden="true" />
              </div>
              <dl className="mt-5 space-y-4">
                <div>
                  <dt className="text-[12px] text-paper/50">Action</dt>
                  <dd className="mt-1 text-[22px] font-semibold tracking-tight">Replenishment reminder</dd>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><dt className="text-[12px] text-paper/50">Channel</dt><dd className="mt-1 text-[16px] font-medium">WhatsApp</dd></div>
                  <div><dt className="text-[12px] text-paper/50">Offer</dt><dd className="mt-1 text-[16px] font-medium">None</dd></div>
                </div>
                <div className="border-t border-white/10 pt-4">
                  <dt className="text-[12px] text-paper/50">Reason</dt>
                  <dd className="mt-1 text-[14.5px] leading-relaxed text-paper/85">
                    Customer is entering their expected replenishment window with strong engagement and no incentive requirement.
                  </dd>
                </div>
              </dl>
            </div>
            <div className="card p-5">
              <p className="eyebrow mb-3">Checked before deciding</p>
              <ul className="space-y-2">
                {checks.map((c) => (
                  <li key={c} className="flex items-center gap-2.5 text-[13.5px]">
                    <svg viewBox="0 0 16 16" className="h-4 w-4 flex-none text-pine-2" aria-hidden="true"><path d="M3.5 8.5 6.5 11.5 12.5 4.5" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
                    {c}
                  </li>
                ))}
              </ul>
              <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-line pt-4 text-[12.5px] text-muted">
                If consent were missing: <DecisionBadge kind="none">No action</DecisionBadge> or another consented channel.
              </div>
            </div>
          </div>
        </div>
      </Reveal>
    </Section>
  );
}
