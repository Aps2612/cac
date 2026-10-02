import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";

const steps = [
  { t: "Understand", d: "Understand each customer's behaviour and context." },
  { t: "Decide", d: "Determine what action makes sense — or none." },
  { t: "Act", d: "Send the decision into the channels you already use." },
  { t: "Learn", d: "Measure the outcome and improve future decisions." },
];

export function HowItWorks() {
  return (
    <Section id="how-it-works" eyebrow="How it works" title="Four steps. One better decision per customer.">
      <ol className="mt-12 grid gap-3 md:grid-cols-4 md:gap-0">
        {steps.map((s, i) => (
          <li key={s.t} className="relative md:pr-8">
            <Reveal delay={i * 70} className="h-full">
              <div className={`h-full rounded-2xl border p-6 ${i === 1 ? "border-ink bg-ink text-paper" : "border-line bg-white"}`}>
                <p className={`font-mono text-[12px] ${i === 1 ? "text-mint" : "text-faint"}`}>0{i + 1}</p>
                <h3 className="mt-6 text-[19px] font-semibold tracking-tight">{s.t}</h3>
                <p className={`mt-2 text-[14.5px] leading-relaxed ${i === 1 ? "text-paper/70" : "text-muted"}`}>{s.d}</p>
              </div>
            </Reveal>
            {i < steps.length - 1 && (
              <svg className="absolute top-1/2 right-1 hidden h-3 w-6 -translate-y-1/2 md:block" viewBox="0 0 24 12" aria-hidden="true">
                <line x1="1" y1="6" x2="19" y2="6" stroke="#0B0F0E" strokeOpacity=".3" strokeWidth="1.5" className="flow-line" />
                <path d="M16 2.5 20 6l-4 3.5" stroke="#0B0F0E" strokeOpacity=".45" strokeWidth="1.5" fill="none" />
              </svg>
            )}
          </li>
        ))}
      </ol>
    </Section>
  );
}
