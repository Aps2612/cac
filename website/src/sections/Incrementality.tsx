import { Section } from "../components/Section";
import { Reveal } from "../components/Reveal";
import { IllustrativeTag } from "../components/Decision";

export function Incrementality() {
  return (
    <Section
      eyebrow="Measuring impact"
      title="Revenue after a campaign isn't the same as revenue caused by the campaign."
      lede="Many customers who buy after a message would have bought anyway. So we hold back a similar group and compare — that difference is the real impact."
    >
      <Reveal className="mt-12">
        <div className="rounded-3xl border border-line bg-paper-2/60 p-5 sm:p-8">
          <div className="mb-5 flex justify-end">
            <IllustrativeTag>Illustrative experiment</IllustrativeTag>
          </div>
          <div className="grid items-center gap-3 md:grid-cols-[1fr_auto_1fr_auto_1.1fr]">
            <div className="card p-5">
              <p className="text-[15px] font-semibold">Treatment group</p>
              <p className="mt-1 text-[13px] text-muted">25,000 customers · receive Nirnaya's decision</p>
            </div>
            <p className="text-center font-mono text-[13px] text-faint">vs</p>
            <div className="card p-5">
              <p className="text-[15px] font-semibold">Control group</p>
              <p className="mt-1 text-[13px] text-muted">25,000 customers · business as usual</p>
            </div>
            <p className="text-center font-mono text-[13px] text-faint" aria-hidden="true">→</p>
            <div className="rounded-2xl bg-ink p-5 text-paper">
              <p className="text-[15px] font-semibold">Incremental lift</p>
              <p className="mt-1 text-[13px] text-paper/65">The difference in repeat purchase between the two groups</p>
            </div>
          </div>
        </div>
      </Reveal>
    </Section>
  );
}
