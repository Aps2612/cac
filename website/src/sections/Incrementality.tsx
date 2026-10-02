import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { IllustrativeTag, StatusTag } from "../components/Decision";

// Deterministic dot pattern — purely decorative, not data.
function dots(seed: number, density: number) {
  return Array.from({ length: 60 }, (_, i) => {
    const x = Math.sin(i * 12.9898 + seed * 78.233) * 43758.5453;
    return x - Math.floor(x) < density;
  });
}

function Group({ name, sub, filled, tone }: { name: string; sub: string; filled: boolean[]; tone: "treat" | "ctrl" }) {
  return (
    <div className="card p-5">
      <div className="flex items-baseline justify-between">
        <p className="text-[15px] font-semibold">{name}</p>
        <p className="font-mono text-[12px] text-muted">25,000 customers</p>
      </div>
      <p className="mt-0.5 text-[12.5px] text-muted">{sub}</p>
      <div className="mt-4 grid grid-cols-12 gap-1.5" aria-hidden="true">
        {filled.map((f, i) => (
          <span
            key={i}
            className={`aspect-square rounded-full ${f ? (tone === "treat" ? "bg-pine-2" : "bg-ink/55") : "border border-ink/15"}`}
          />
        ))}
      </div>
      <p className="mt-3 flex items-center gap-2 text-[12px] text-muted">
        <span className={`h-2 w-2 rounded-full ${tone === "treat" ? "bg-pine-2" : "bg-ink/55"}`} /> repeat purchase in window
      </p>
    </div>
  );
}

export function Incrementality() {
  return (
    <Section
      eyebrow="Incrementality"
      title="Revenue after a campaign isn't the same as revenue caused by the campaign."
      lede="Many customers who buy after a message would have bought anyway. The only honest way to know what an intervention did is to hold back a comparable group and compare."
    >
      <Reveal className="mt-14">
        <div className="rounded-3xl border border-line bg-paper-2/60 p-5 sm:p-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <p className="text-[15px] font-semibold">How a pilot measures impact</p>
            <div className="flex gap-2">
              <IllustrativeTag>Illustrative experiment</IllustrativeTag>
              <StatusTag tone="muted">Roadmap · in product</StatusTag>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Group name="Treatment group" sub="Receives Nirnaya's decision" filled={dots(1, 0.42)} tone="treat" />
            <Group name="Control group" sub="Held back — business as usual" filled={dots(7, 0.3)} tone="ctrl" />
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-[1fr_1fr_1.3fr]">
            {[
              ["Compare", "Repeat-purchase rate in each group over the same window"],
              ["Estimate", "Lift = treatment rate − control rate"],
              ["Decide", "Keep, change or stop the intervention based on what it actually caused"],
            ].map(([t, d]) => (
              <div key={t} className="rounded-xl bg-white p-4">
                <p className="font-mono text-[11px] uppercase tracking-[0.1em] text-pine">{t}</p>
                <p className="mt-1.5 text-[14px] leading-snug">{d}</p>
              </div>
            ))}
          </div>
          <p className="mt-5 text-[12.5px] text-faint">Dots and group sizes are illustrative and do not represent any real result.</p>
        </div>
      </Reveal>

      <Reveal delay={100} className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-line p-6">
          <p className="eyebrow">Campaign-attributed revenue</p>
          <p className="mt-2 text-[15px] leading-relaxed text-muted">Everyone who purchased after receiving a message. Easy to report — and usually overstated.</p>
        </div>
        <div className="rounded-2xl border border-pine/25 bg-pine-soft/50 p-6">
          <p className="eyebrow !text-pine">Incremental revenue</p>
          <p className="mt-2 text-[15px] leading-relaxed">Purchases that would not have happened without the intervention. This is the number Nirnaya is designed around.</p>
        </div>
      </Reveal>
    </Section>
  );
}
