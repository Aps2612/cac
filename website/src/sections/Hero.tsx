import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { DecisionBadge, IllustrativeTag } from "../components/Decision";
import { ctaHref, SITE_CONFIG } from "../config";

type Sample = {
  id: string;
  label: string;
  signals: { k: string; v: string; tone?: "good" | "warn" | "muted" }[];
  checks: { k: string; ok: boolean }[];
  action: string;
  none?: boolean;
  channel: string;
  offer: string;
  reason: string;
};

const samples: Sample[] = [
  {
    id: "C-1042",
    label: "Customer A",
    signals: [
      { k: "Last order", v: "37 days ago" },
      { k: "Usual reorder", v: "32–38 days", tone: "good" },
      { k: "Engagement", v: "High", tone: "good" },
      { k: "WhatsApp consent", v: "Yes", tone: "good" },
      { k: "Inventory", v: "Available", tone: "good" },
      { k: "Past offers", v: "Bought without discount" },
    ],
    checks: [
      { k: "Eligible", ok: true },
      { k: "Consent", ok: true },
      { k: "Fatigue cap", ok: true },
    ],
    action: "Replenishment reminder",
    channel: "WhatsApp",
    offer: "None",
    reason: "Entering expected reorder window with strong engagement. No incentive needed.",
  },
  {
    id: "C-2318",
    label: "Customer B",
    signals: [
      { k: "Last order", v: "3 days ago" },
      { k: "Reorder signal", v: "None", tone: "muted" },
      { k: "Customer value", v: "High", tone: "good" },
      { k: "Last contacted", v: "Yesterday", tone: "warn" },
      { k: "Consent", v: "Email, WhatsApp" },
      { k: "Inventory", v: "Available" },
    ],
    checks: [
      { k: "Eligible", ok: false },
      { k: "Consent", ok: true },
      { k: "Fatigue cap", ok: false },
    ],
    action: "No action",
    none: true,
    channel: "—",
    offer: "—",
    reason: "Just purchased and contacted yesterday. Another message adds fatigue, not value.",
  },
];

function useReducedMotion() {
  const [r, setR] = useState(false);
  useEffect(() => {
    const m = window.matchMedia("(prefers-reduced-motion: reduce)");
    setR(m.matches);
    const on = () => setR(m.matches);
    m.addEventListener("change", on);
    return () => m.removeEventListener("change", on);
  }, []);
  return r;
}

function DecisionVisual() {
  const [i, setI] = useState(0);
  const [paused, setPaused] = useState(false);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (paused || reduced) return;
    const t = setInterval(() => setI((x) => (x + 1) % samples.length), 5200);
    return () => clearInterval(t);
  }, [paused, reduced]);
  const s = samples[i];

  return (
    <div
      className="relative"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
    >
      <div className="absolute -inset-6 -z-10 rounded-[2rem] grid-bg [mask-image:radial-gradient(ellipse_at_center,black_40%,transparent_75%)]" />
      <div className="card overflow-hidden shadow-[0_30px_80px_-40px_rgba(11,15,14,.35)]">
        {/* header */}
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 sm:px-5">
          <div className="flex items-center gap-1 rounded-full bg-paper-2 p-1" role="tablist" aria-label="Example customers">
            {samples.map((x, idx) => (
              <button
                key={x.id}
                role="tab"
                aria-selected={idx === i}
                onClick={() => { setI(idx); setPaused(true); }}
                className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium transition-colors ${idx === i ? "bg-white text-ink shadow-sm" : "text-muted hover:text-ink"}`}
              >
                {x.label}
              </button>
            ))}
          </div>
          <span className="hidden sm:inline-flex"><IllustrativeTag>Sample data</IllustrativeTag></span><span className="sm:hidden"><IllustrativeTag>Sample</IllustrativeTag></span>
        </div>

        <div key={s.id} className="fade-swap p-4 sm:p-5">
          {/* context */}
          <div className="mb-2 flex items-baseline justify-between">
            <p className="eyebrow">Customer context</p>
            <p className="font-mono text-[11px] text-faint">{s.id}</p>
          </div>
          <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-line bg-line">
            {s.signals.map((g) => (
              <div key={g.k} className="bg-white px-3 py-2.5">
                <dt className="text-[11px] text-faint">{g.k}</dt>
                <dd className={`mt-0.5 text-[13px] font-medium ${g.tone === "good" ? "text-pine" : g.tone === "warn" ? "text-amber" : g.tone === "muted" ? "text-muted" : "text-ink"}`}>{g.v}</dd>
              </div>
            ))}
          </dl>

          {/* engine */}
          <div className="relative flex justify-center py-1" aria-hidden="true">
            <svg width="2" height="22"><line x1="1" y1="0" x2="1" y2="22" stroke="#0B0F0E" strokeOpacity=".35" strokeWidth="1.5" className="flow-line" /></svg>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-ink px-3.5 py-3 text-paper">
            <span className="flex items-center gap-2 text-[13px] font-semibold tracking-tight">
              <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-mint" /> Nirnaya
            </span>
            <span className="flex flex-wrap gap-1.5">
              {s.checks.map((c) => (
                <span key={c.k} className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-mono text-[10.5px] ${c.ok ? "bg-white/10 text-paper/85" : "bg-white/5 text-paper/45 line-through decoration-paper/30"}`}>
                  {c.ok ? "✓" : "×"} {c.k}
                </span>
              ))}
            </span>
          </div>
          <div className="relative flex justify-center py-1" aria-hidden="true">
            <svg width="2" height="22"><line x1="1" y1="0" x2="1" y2="22" stroke="#0B0F0E" strokeOpacity=".35" strokeWidth="1.5" className="flow-line" /></svg>
          </div>

          {/* decision */}
          <div className={`rounded-xl border p-4 ${s.none ? "border-ink bg-paper-2" : "border-pine/20 bg-pine-soft/60"}`}>
            <div className="flex items-center justify-between">
              <p className="eyebrow">Decision</p>
              <DecisionBadge kind={s.none ? "none" : "action"}>{s.action}</DecisionBadge>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-3 text-[13px]">
              <div><dt className="text-[11px] text-faint">Channel</dt><dd className="font-medium">{s.channel}</dd></div>
              <div><dt className="text-[11px] text-faint">Offer</dt><dd className="font-medium">{s.offer}</dd></div>
            </dl>
            <p className="mt-3 border-t border-ink/10 pt-3 text-[13px] leading-snug text-muted">
              <span className="font-medium text-ink">Reason · </span>{s.reason}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden pt-28 pb-20 sm:pt-36 sm:pb-28">
      <div className="container-x grid items-center gap-14 lg:grid-cols-[1.05fr_1fr] lg:gap-16">
        <div>
          <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1 text-[12.5px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-pine-2" />
            Customer decisioning for D2C brands
          </p>
          <h1 className="text-[2.6rem] leading-[1.02] font-semibold tracking-[-0.035em] sm:text-[3.6rem] lg:text-[4.1rem]" style={{ textWrap: "balance" }}>
            Turn customer data into better retention decisions.
          </h1>
          <p className="lede mt-6 max-w-xl">
            Nirnaya helps D2C brands identify which customers need an intervention, decide what action makes sense, and measure whether it actually created incremental value.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button href={ctaHref("audit")} size="lg" arrow>Book a Retention Audit</Button>
            <Button href="#how-it-works" size="lg" variant="secondary">See How It Works</Button>
          </div>
          <p className="mt-6 text-[13px] text-faint">
            Currently validating with selected D2C brands ·{" "}
            <a href={SITE_CONFIG.demoUrl} target="_blank" rel="noopener noreferrer" className="underline decoration-line underline-offset-4 hover:text-ink hover:decoration-ink/40">
              Open product demo<span className="sr-only"> (opens in a new tab)</span>
            </a>
          </p>
        </div>
        <DecisionVisual />
      </div>
    </section>
  );
}
