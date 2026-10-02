import type { ReactNode } from "react";
import { Reveal } from "./Reveal";

type Props = { id?: string; eyebrow?: string; title: ReactNode; lede?: ReactNode; children?: ReactNode; className?: string; center?: boolean };

export function Section({ id, eyebrow, title, lede, children, className = "", center = false }: Props) {
  return (
    <section id={id} className={`py-20 sm:py-28 ${className}`}>
      <div className="container-x">
        <Reveal className={`max-w-2xl ${center ? "mx-auto text-center" : ""}`}>
          {eyebrow && <p className="eyebrow mb-4">{eyebrow}</p>}
          <h2 className="h-section">{title}</h2>
          {lede && <p className="lede mt-5">{lede}</p>}
        </Reveal>
        {children}
      </div>
    </section>
  );
}
