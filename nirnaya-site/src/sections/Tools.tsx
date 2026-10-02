import { Reveal } from "../components/Reveal";

function Box({ title, items }: { title: string; items: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white px-5 py-4 text-center">
      <p className="text-[15px] font-semibold">{title}</p>
      <p className="mt-1 text-[13px] text-muted">{items}</p>
    </div>
  );
}

function Arrow() {
  return (
    <div className="flex justify-center" aria-hidden="true">
      <svg viewBox="0 0 40 16" className="h-4 w-10 rotate-90 md:rotate-0">
        <line x1="2" y1="8" x2="34" y2="8" stroke="#0B0F0E" strokeOpacity=".3" strokeWidth="1.5" className="flow-line" />
        <path d="M30 3.5 35 8l-5 4.5" stroke="#0B0F0E" strokeOpacity=".45" strokeWidth="1.5" fill="none" />
      </svg>
    </div>
  );
}

export function Tools() {
  return (
    <section className="border-t border-line bg-white py-20 sm:py-24">
      <div className="container-x">
        <Reveal className="max-w-2xl">
          <p className="eyebrow mb-4">Your existing stack</p>
          <h2 className="h-section">Works with the tools you already use.</h2>
          <p className="lede mt-5">
            Nirnaya is a decisioning layer. It doesn't ask you to replace your existing CRM, WhatsApp, email or commerce stack — it decides, and your tools deliver.
          </p>
        </Reveal>
        <Reveal delay={100} className="mt-12">
          <div className="grid items-center gap-3 rounded-3xl bg-paper-2/70 p-5 sm:p-7 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
            <Box title="Your customer data" items="Orders, customers, website, products" />
            <Arrow />
            <div className="rounded-2xl bg-ink px-5 py-5 text-center text-paper shadow-lg">
              <p className="flex items-center justify-center gap-2 text-[15px] font-semibold"><span className="pulse-dot h-1.5 w-1.5 rounded-full bg-mint" /> Nirnaya</p>
              <p className="mt-1 text-[13px] text-paper/60">Decides</p>
            </div>
            <Arrow />
            <Box title="Your existing channels" items="WhatsApp, email, SMS, CRM" />
          </div>
        </Reveal>
      </div>
    </section>
  );
}
