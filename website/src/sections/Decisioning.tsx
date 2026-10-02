import { Reveal } from "../components/Reveal";

const stages = [
  { n: "Customer context", d: "Purchase history, behaviour, product and channel signals." },
  { n: "Eligibility", d: "Is there a real reason to act today?" },
  { n: "Business rules", d: "Consent, contact frequency, inventory, discount limits." },
  { n: "Decision", d: "The single most appropriate next step — if any." },
];

const noActionReasons = [
  "Purchased three days ago — nothing to remind them of",
  "Already contacted yesterday — another message is fatigue",
  "Preferred channel isn't consented, and no other channel fits",
  "The product they'd reorder is out of stock",
  "No meaningful signal — contact would be noise",
];

export function Decisioning() {
  return (
    <section className="relative overflow-hidden bg-ink py-20 text-paper sm:py-28">
      <div className="pointer-events-none absolute inset-0 grid-bg-dark [mask-image:linear-gradient(to_bottom,transparent,black_30%,black_70%,transparent)]" aria-hidden="true" />
      <div className="container-x relative">
        <Reveal className="max-w-3xl">
          <p className="eyebrow mb-4 !text-mint/80">Decisioning</p>
          <h2 className="h-section">Every customer does not need another campaign.</h2>
          <p className="lede mt-5 !text-paper/65">
            Nirnaya evaluates customer context, eligibility, business constraints and previous outcomes before recommending an action. Consent and safety rules are hard constraints, not suggestions.
          </p>
        </Reveal>

        {/* Flow */}
        <Reveal delay={100} className="mt-14">
          <ol className="grid gap-3 md:grid-cols-4 md:gap-0">
            {stages.map((s, i) => (
              <li key={s.n} className="relative md:pr-6">
                <div className="h-full rounded-xl border border-line-dark bg-ink-2 p-4">
                  <p className="font-mono text-[11px] text-paper/40">0{i + 1}</p>
                  <p className="mt-2 text-[15px] font-semibold">{s.n}</p>
                  <p className="mt-1 text-[13px] leading-snug text-paper/55">{s.d}</p>
                </div>
                {i < stages.length - 1 && (
                  <svg className="absolute top-1/2 right-0 hidden h-3 w-6 -translate-y-1/2 md:block" viewBox="0 0 24 12" aria-hidden="true">
                    <line x1="2" y1="6" x2="20" y2="6" stroke="#7FD4B3" strokeOpacity=".6" strokeWidth="1.5" className="flow-line" />
                    <path d="M17 2.5 21 6l-4 3.5" stroke="#7FD4B3" strokeOpacity=".7" strokeWidth="1.5" fill="none" />
                  </svg>
                )}
              </li>
            ))}
          </ol>

          {/* split */}
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-mint/25 bg-mint/[.06] p-5">
              <p className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.12em] text-mint">
                <span className="h-2 w-2 rounded-full bg-mint" /> Action
              </p>
              <p className="mt-2 text-[15px] text-paper/80">
                The right message, on a consented channel, with an incentive only when it is justified.
              </p>
            </div>
            <div className="rounded-xl border border-paper/70 bg-paper p-5 text-ink">
              <p className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.12em]">
                <span className="h-2 w-2 rounded-full border-[1.5px] border-ink" /> No action
              </p>
              <p className="mt-2 text-[15px] text-ink/75">
                A deliberate, recorded decision to leave the customer alone today.
              </p>
            </div>
          </div>
        </Reveal>

        {/* the moment */}
        <Reveal delay={150} className="mt-20 grid gap-10 border-t border-line-dark pt-16 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
          <p className="text-[2.3rem] leading-[1.05] font-semibold tracking-[-0.03em] sm:text-[3.4rem]" style={{ textWrap: "balance" }}>
            A good decision can also be <span className="whitespace-nowrap rounded-xl bg-paper px-3 text-ink">no action.</span>
          </p>
          <div>
            <p className="text-[15px] leading-relaxed text-paper/65">
              Most retention tools are built to send. Nirnaya is built to decide — and deciding not to contact someone is often the decision that protects the relationship and the margin.
            </p>
            <ul className="mt-6 space-y-2.5">
              {noActionReasons.map((r) => (
                <li key={r} className="flex items-start gap-3 text-[14px] text-paper/80">
                  <span className="mt-[3px] inline-flex h-4 w-4 flex-none items-center justify-center rounded-full border border-paper/40" aria-hidden="true" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
