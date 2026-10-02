import type { ReactNode } from "react";
import { isExternal } from "../config";

type Variant = "primary" | "secondary" | "ghost" | "light" | "outline-light";

const styles: Record<Variant, string> = {
  primary: "bg-ink text-paper hover:bg-ink-3 shadow-[0_1px_0_rgba(255,255,255,.12)_inset,0_6px_20px_-8px_rgba(11,15,14,.5)]",
  secondary: "bg-white text-ink border border-line hover:border-ink/30",
  ghost: "text-ink hover:bg-ink/5",
  light: "bg-paper text-ink hover:bg-white",
  "outline-light": "text-paper border border-white/20 hover:border-white/50",
};

type Props = {
  href: string;
  children: ReactNode;
  variant?: Variant;
  className?: string;
  arrow?: boolean;
  size?: "md" | "lg";
};

export function Button({ href, children, variant = "primary", className = "", arrow = false, size = "md" }: Props) {
  const ext = isExternal(href);
  const sz = size === "lg" ? "h-12 px-6 text-[15px]" : "h-10 px-4 text-sm";
  return (
    <a
      href={href}
      {...(ext ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className={`group inline-flex items-center justify-center gap-2 rounded-full font-medium transition-colors duration-200 ${sz} ${styles[variant]} ${className}`}
    >
      {children}
      {arrow && (
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden="true">
          <path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
      {ext && !arrow && <span className="sr-only">(opens in a new tab)</span>}
    </a>
  );
}
