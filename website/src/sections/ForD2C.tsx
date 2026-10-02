import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";

const categories = ["Beauty", "Skincare", "Haircare", "Wellness", "Supplements", "Nutrition", "Pet products", "Food", "Other consumables"];
const fit = [
  "A meaningful existing customer base with repeat-purchase potential",
  "Order and customer data you can export or share",
  "Active CRM — WhatsApp, email or SMS — already running",
  "A founder or growth/CRM lead who owns retention",
];

export function ForD2C() {
  return (
    <Section
      id="for-d2c"
      eyebrow="Who it's for"
      title="Built first for Indian D2C brands where customers come back."
      lede="Replenishment-heavy categories are where timing, channel and incentive decisions matter most — and where a wrong decision costs real margin."
    >
      <div className="mt-14 grid gap-4 lg:grid-cols-2">
        <Reveal className="card p-6 sm:p-7">
          <p className="eyebrow mb-4">Categories</p>
          <ul className="flex flex-wrap gap-2">
            {categories.map((c) => (
              <li key={c} className="rounded-full border border-line bg-paper px-3.5 py-1.5 text-[13.5px]">{c}</li>
            ))}
          </ul>
          <p className="eyebrow mt-8 mb-3">Who we talk to</p>
          <p className="text-[15px] leading-relaxed">
            Founders and co-founders, and Heads of Growth, CRM or Retention.
            <span className="text-muted"> Technical teams come in once a pilot is scoped.</span>
          </p>
        </Reveal>
        <Reveal delay={100} className="card p-6 sm:p-7">
          <p className="eyebrow mb-4">A good fit if you have</p>
          <ul className="space-y-3.5">
            {fit.map((f) => (
              <li key={f} className="flex gap-3 text-[15px] leading-snug">
                <svg viewBox="0 0 16 16" className="mt-[3px] h-4 w-4 flex-none text-pine-2" aria-hidden="true"><path d="M3.5 8.5 6.5 11.5 12.5 4.5" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
                {f}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </Section>
  );
}
