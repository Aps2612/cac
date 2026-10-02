import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { DecisionBadge } from "../components/Decision";

const meera = [
  ["Recent order", "37 days ago"],
  ["Typical reorder", "32–38 days"],
  ["Engagement", "High"],
  ["WhatsApp", "Consented"],
  ["Inventory", "Available"],
  ["Previous discount", "Not required"],
];

function Field({ k, v, dark = false }: { k: string; v: string; dark?: boolean }) {
  return (
    <div>
      <dt className={`text-[12px] ${dark ? "text-paper/50" : "text-muted"}`}>{k}</dt>
      <dd className="mt-0.5 text-[16px] font-medium">{v}</dd>
    </div>
  );
}

export function Example() {
  return (
    <Section
      eyebrow="Example"
      title="One customer. One decision."
      lede="This is what Nirnaya produces — a clear, explainable decision for each customer."
      className="border-t border-line bg-white"
    >
      <Reveal className="mt-12">
        <div className="grid overflow-hidden rounded-3xl border border-line lg:grid-cols-2">
          {/* customer */}
          <div className="bg-paper p-6 sm:p-8">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-[15px] font-semibold ring-1 ring-line" aria-hidden="true">M</span>
              <div>
                <p className="text-[17px] font-semibold">Meera</p>
                <p className="text-[12.5px] text-muted">Customer · sample profile</p>
              </div>
            </div>
            <dl className="mt-7 grid grid-cols-2 gap-x-6 gap-y-5">
              {meera.map(([k, v]) => <Field key={k} k={k} v={v} />)}
            </dl>
          </div>
          {/* decision */}
          <div className="relative bg-ink p-6 text-paper sm:p-8">
            <p className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-mint">
              <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-mint" /> Nirnaya decides
            </p>
            <p className="mt-5 text-[1.75rem] leading-tight font-semibold tracking-tight">Replenishment reminder</p>
            <dl className="mt-6 grid grid-cols-2 gap-5">
              <Field dark k="Channel" v="WhatsApp" />
              <Field dark k="Offer" v="None" />
            </dl>
            <div className="mt-6 border-t border-white/10 pt-5">
              <p className="text-[12px] text-paper/50">Reason</p>
              <p className="mt-1 text-[15px] leading-relaxed text-paper/85">Meera is entering her usual reorder window and has never needed a discount to buy.</p>
            </div>
          </div>
        </div>
      </Reveal>

      <Reveal delay={100} className="mt-4">
        <div className="flex flex-col gap-4 rounded-3xl border border-line bg-paper p-6 sm:flex-row sm:items-center sm:justify-between sm:p-7">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 flex-none items-center justify-center rounded-full bg-white text-[15px] font-semibold ring-1 ring-line" aria-hidden="true">R</span>
            <div>
              <p className="text-[15px] font-semibold">Rohan <span className="font-normal text-muted">· purchased 4 days ago</span></p>
              <p className="mt-0.5 text-[14px] text-muted">Reason: purchased recently and doesn't need an intervention right now.</p>
            </div>
          </div>
          <DecisionBadge kind="none" className="self-start !px-4 !py-2 !text-[12.5px] sm:self-auto">No action</DecisionBadge>
        </div>
        <p className="mt-3 text-[12px] text-faint">Meera and Rohan are illustrative examples, not real customers.</p>
      </Reveal>
    </Section>
  );
}
