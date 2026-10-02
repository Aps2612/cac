import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";

const inputs = ["Shopify / commerce platform", "Customer database", "CRM", "WhatsApp", "Email", "Inventory"];
const outputs = ["WhatsApp provider", "Email platform", "SMS", "CRM audiences"];
const layer = ["Customer state", "Eligibility & consent", "Business rules", "Decision log", "Measurement"];

function Col({ title, items, sub }: { title: string; items: string[]; sub: string }) {
  return (
    <div>
      <p className="eyebrow">{title}</p>
      <p className="mt-1 mb-3 text-[12.5px] text-faint">{sub}</p>
      <ul className="space-y-2">
        {items.map((i) => (
          <li key={i} className="rounded-lg border border-line bg-white px-3.5 py-2.5 text-[13.5px]">{i}</li>
        ))}
      </ul>
    </div>
  );
}

function Arrow() {
  return (
    <div className="flex items-center justify-center py-2 lg:py-0" aria-hidden="true">
      <svg viewBox="0 0 48 16" className="h-4 w-12 rotate-90 lg:rotate-0">
        <line x1="2" y1="8" x2="42" y2="8" stroke="#0B0F0E" strokeOpacity=".35" strokeWidth="1.5" className="flow-line" />
        <path d="M38 3.5 43 8l-5 4.5" stroke="#0B0F0E" strokeOpacity=".5" strokeWidth="1.5" fill="none" />
      </svg>
    </div>
  );
}

export function Stack() {
  return (
    <Section
      eyebrow="Existing stack"
      title="Work with the stack you already have."
      lede="Nirnaya is the decisioning layer between your customer data and the channels you already use. Your team keeps its tools, its brand voice and control of strategy. Nirnaya decides who, what, when, and whether."
    >
      <Reveal className="mt-14">
        <div className="grid items-center gap-2 rounded-3xl border border-line bg-paper-2/60 p-5 sm:p-8 lg:grid-cols-[1fr_auto_1.1fr_auto_1fr] lg:gap-6">
          <Col title="Your data" sub="What you already collect" items={inputs} />
          <Arrow />
          <div className="rounded-2xl bg-ink p-5 text-paper shadow-[0_24px_60px_-30px_rgba(11,15,14,.6)]">
            <p className="flex items-center gap-2 text-[15px] font-semibold"><span className="pulse-dot h-1.5 w-1.5 rounded-full bg-mint" /> Nirnaya</p>
            <p className="mt-1 text-[12.5px] text-paper/55">Decisioning layer</p>
            <ul className="mt-4 space-y-1.5">
              {layer.map((l) => (
                <li key={l} className="rounded-md bg-white/[.06] px-3 py-2 font-mono text-[12px] text-paper/80">{l}</li>
              ))}
            </ul>
          </div>
          <Arrow />
          <Col title="Your activation" sub="Where decisions are delivered" items={outputs} />
        </div>
        <p className="mt-4 text-[12.5px] text-faint">
          Data connections are set up per pilot, starting from exports or the access you already have. We list specific integrations only once they're live.
        </p>
      </Reveal>
    </Section>
  );
}
