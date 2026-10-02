import type { ReactNode } from "react";
import { Reveal } from "./Reveal";

type Props = {
  id?: string;
  eyebrow?: string;
  title: ReactNode;
  lede?: ReactNode;
  children?: ReactNode;
  className?: string;
  dark?: boolean;
  center?: boolean;
};

export function Section({ id, eyebrow, title, lede, children, className = "", dark = false, center = false }: Props) {
  return (
    <section id={id} className={`py-20 sm:py-28 ${dark ? "bg-ink text-paper" : ""} ${className}`}>
      <div className="container-x">
        <Reveal className={`max-w-3xl ${center ? "mx-auto text-center" : ""}`}>
          {eyebrow && <p className={`eyebrow mb-4 ${dark ? "!text-mint/80" : ""}`}>{eyebrow}</p>}
          <h2 className="h-section">{title}</h2>
          {lede && <p className={`lede mt-5 ${dark ? "!text-paper/65" : ""}`}>{lede}</p>}
        </Reveal>
        {children}
      </div>
    </section>
  );
}
