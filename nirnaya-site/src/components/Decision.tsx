export type DecisionKind = "action" | "none" | "incentive" | "channel" | "neutral";

const map: Record<DecisionKind, string> = {
  action: "bg-pine-soft text-pine border-pine/15",
  incentive: "bg-amber-soft text-amber border-amber/20",
  channel: "bg-paper-2 text-ink border-line",
  neutral: "bg-paper-2 text-muted border-line",
  none: "bg-ink text-paper border-ink",
};

export function DecisionBadge({ kind, children, className = "" }: { kind: DecisionKind; children: React.ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 font-mono text-[11px] font-medium uppercase tracking-[0.06em] ${map[kind]} ${className}`}>
      {kind === "none" ? (
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" aria-hidden="true"><circle cx="6" cy="6" r="4.2" fill="none" stroke="currentColor" strokeWidth="1.5" /></svg>
      ) : (
        <span className={`h-1.5 w-1.5 rounded-full ${kind === "action" ? "bg-pine-2" : kind === "incentive" ? "bg-amber" : "bg-ink/60"}`} />
      )}
      {children}
    </span>
  );
}

export function StatusTag({ children, tone = "pine" }: { children: React.ReactNode; tone?: "pine" | "muted" | "amber" }) {
  const t = tone === "pine" ? "text-pine bg-pine-soft" : tone === "amber" ? "text-amber bg-amber-soft" : "text-muted bg-paper-2";
  return <span className={`inline-flex rounded-md px-2 py-0.5 font-mono text-[10.5px] font-medium uppercase tracking-[0.08em] ${t}`}>{children}</span>;
}

export function IllustrativeTag({ dark = false, children = "Illustrative" }: { dark?: boolean; children?: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border border-dashed px-2 py-0.5 font-mono text-[10.5px] uppercase tracking-[0.08em] ${dark ? "border-white/25 text-paper/60" : "border-ink/25 text-muted"}`}>
      <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" aria-hidden="true"><path d="M6 1.5v9M1.5 6h9" stroke="currentColor" strokeWidth="1.3" /></svg>
      {children}
    </span>
  );
}
