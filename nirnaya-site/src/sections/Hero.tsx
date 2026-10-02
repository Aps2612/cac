import { Button } from "../components/Button";
import { DecisionBadge } from "../components/Decision";

const signals = [
  ["Last purchase", "37 days ago"],
  ["Previous orders", "5"],
  ["Engagement", "High"],
  ["WhatsApp consent", "Yes"],
  ["Product", "In stock"],
];

function Flow() {
  return (
    <div className="flex justify-center py-1.5" aria-hidden="true">
      <svg width="2" height="24"><line x1="1" y1="0" x2="1" y2="24" stroke="#0B0F0E" strokeOpacity=".35" strokeWidth="1.5" className="flow-line" /></svg>
    </div>
  );
}

function HeroVisual() {
  return (
    <div className="relative mx-auto w-full max-w-[440px]">
      <div className="absolute -inset-8 -z-10 grid-bg [mask-image:radial-gradient(ellipse_at_center,black_35%,transparent_72%)]" aria-hidden="true" />

      {/* customer */}
      <div className="card p-4 shadow-[0_24px_60px_-36px_rgba(11,15,14,.35)] sm:p-5">
        <div className="mb-3 flex items-center justify-between">
          <p className="eyebrow">Customer</p>
          <span className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-faint">Example</span>
        </div>
        <dl className="divide-y divide-line">
          {signals.map(([k, v]) => (
            <div key={k} className="flex items-center justify-between py-2 text-[13.5px]">
              <dt className="text-muted">{k}</dt>
              <dd className="font-medium">{v}</dd>
            </div>
          ))}
        </dl>
      </div>

      <Flow />
      <div className="mx-auto flex w-fit items-center gap-2 rounded-full bg-ink px-4 py-2 text-[13px] font-semibold text-paper">
        <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-mint" /> Nirnaya decides
      </div>
      <Flow />

      {/* decision */}
      <div className="rounded-2xl border border-pine/20 bg-pine-soft/70 p-4 sm:p-5">
        <div className="flex items-center justify-between gap-2">
          <p className="eyebrow !text-pine">Decision</p>
          <DecisionBadge kind="action">Replenishment reminder</DecisionBadge>
        </div>
        <dl className="mt-3 grid grid-cols-2 gap-3 text-[13.5px]">
          <div><dt className="text-[11.5px] text-muted">Channel</dt><dd className="font-medium">WhatsApp</dd></div>
          <div><dt className="text-[11.5px] text-muted">Offer</dt><dd className="font-medium">None needed</dd></div>
        </dl>
      </div>

      {/* the other answer */}
      <div className="mt-3 flex items-center justify-between gap-3 rounded-2xl border border-line bg-white px-4 py-3">
        <p className="text-[13px] text-muted">Another customer · bought 3 days ago</p>
        <DecisionBadge kind="none">No action</DecisionBadge>
      </div>
    </div>
  );
}

export function Hero() {
  return (
    <section id="top" className="overflow-x-clip pt-28 pb-20 sm:pt-36 sm:pb-28">
      <div className="container-x grid items-center gap-14 lg:grid-cols-[1.1fr_1fr] lg:gap-20">
        <div>
          <p className="mb-6 text-[13px] text-muted">
            <span className="font-medium text-ink">Nirnaya</span> — better decisions for every customer.
          </p>
          <h1 className="text-[2.55rem] leading-[1.03] font-semibold tracking-[-0.035em] sm:text-[3.4rem] lg:text-[3.7rem]" style={{ textWrap: "balance" }}>
            Decide who to reach. What to offer. <span className="text-muted/70">When to do nothing.</span>
          </h1>
          <p className="lede mt-6 max-w-xl">
            Nirnaya is a customer decisioning layer for D2C brands. It reads each customer's behaviour and your business context, and tells you the next best action — including when the best action is none.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Button href="#book" size="lg" arrow>Book a Demo</Button>
            <Button href="#how-it-works" size="lg" variant="secondary">See How It Works</Button>
          </div>
          <p className="mt-6 text-[13px] text-faint">Built for Indian D2C brands in beauty, wellness, nutrition, food, pet and other repeat-purchase categories.</p>
        </div>
        <HeroVisual />
      </div>
    </section>
  );
}
