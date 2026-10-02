import { Reveal } from "../components/Reveal";

/** The one idea we want every visitor to remember. */
export function NoAction() {
  const dots = Array.from({ length: 72 }, (_, i) => [5, 14, 27, 33, 46, 58, 64].includes(i));
  return (
    <section className="relative overflow-hidden bg-ink py-20 text-paper sm:py-28">
      <div className="pointer-events-none absolute inset-0 grid-bg-dark [mask-image:radial-gradient(ellipse_at_70%_50%,black_10%,transparent_65%)]" aria-hidden="true" />
      <div className="container-x relative grid items-center gap-14 lg:grid-cols-[1.2fr_1fr]">
        <Reveal>
          <h2 className="text-[2.3rem] leading-[1.05] font-semibold tracking-[-0.03em] sm:text-[3.3rem]" style={{ textWrap: "balance" }}>
            Not every customer needs another message.
          </h2>
          <p className="mt-6 max-w-lg text-[1.1rem] leading-relaxed text-paper/65">
            Sometimes the right decision is <span className="whitespace-nowrap rounded-md bg-paper px-1.5 font-medium text-ink">no action</span>. No message, no discount, no fatigue — just a customer left alone because they didn't need you today.
          </p>
        </Reveal>
        <Reveal delay={120}>
          <div className="rounded-2xl border border-line-dark bg-ink-2 p-6">
            <div className="grid grid-cols-12 gap-2" aria-hidden="true">
              {dots.map((on, i) => (
                <span key={i} className={`aspect-square rounded-full ${on ? "bg-mint" : "border border-paper/25"}`} />
              ))}
            </div>
            <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-[13px] text-paper/70">
              <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-mint" /> Needs action today</span>
              <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full border border-paper/40" /> Better left alone</span>
            </div>
            <p className="mt-3 font-mono text-[10.5px] uppercase tracking-[0.1em] text-paper/35">Illustration</p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
