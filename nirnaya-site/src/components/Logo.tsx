type Props = { className?: string; invert?: boolean };

/** Mark: one input forks into two outcomes — act (filled) or don't (ring). */
export function LogoMark({ className = "h-6 w-6", invert = false }: Props) {
  const fg = invert ? "#FAFAF7" : "#0B0F0E";
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="8" fill={fg} />
      <circle cx="9" cy="16" r="2.6" fill={invert ? "#0B0F0E" : "#FAFAF7"} />
      <path d="M11.5 16 H15 C17 16 17.5 10 20.5 10" stroke={invert ? "#0B0F0E" : "#FAFAF7"} strokeWidth="1.8" fill="none" strokeLinecap="round" />
      <path d="M15 16 C17 16 17.5 22 20.5 22" stroke={invert ? "#0B0F0E" : "#FAFAF7"} strokeWidth="1.8" fill="none" strokeLinecap="round" opacity=".55" />
      <circle cx="23" cy="10" r="2.6" fill="#7FD4B3" />
      <circle cx="23" cy="22" r="2.2" fill="none" stroke={invert ? "#0B0F0E" : "#FAFAF7"} strokeWidth="1.6" opacity=".8" />
    </svg>
  );
}

export function Logo({ className = "", invert = false }: Props) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <LogoMark invert={invert} />
      <span className={`text-[17px] font-semibold tracking-[-0.02em] ${invert ? "text-paper" : "text-ink"}`}>Nirnaya</span>
    </span>
  );
}
