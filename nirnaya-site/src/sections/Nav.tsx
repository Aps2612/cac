import { useEffect, useState } from "react";
import { Logo } from "../components/Logo";
import { Button } from "../components/Button";
import { SITE_CONFIG } from "../config";

const links = [
  { href: "#how-it-works", label: "How It Works" },
  { href: "#benefits", label: "Benefits" },
  { href: SITE_CONFIG.demoUrl, label: "Demo", external: true },
];

export function Nav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <header className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${scrolled || open ? "border-b border-line bg-paper/90 backdrop-blur-md" : "border-b border-transparent"}`}>
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:rounded-md focus:bg-ink focus:px-3 focus:py-2 focus:text-paper">Skip to content</a>
      <nav className="container-x flex h-16 items-center justify-between" aria-label="Primary">
        <a href="#top" aria-label="Nirnaya home"><Logo /></a>
        <div className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <a key={l.label} href={l.href} {...(l.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
               className="rounded-full px-3.5 py-2 text-[14px] text-muted transition-colors hover:text-ink">
              {l.label}{l.external && <span aria-hidden="true"> ↗</span>}
            </a>
          ))}
          <Button href="#book" className="ml-3">Book a Demo</Button>
        </div>
        <div className="flex items-center gap-1 md:hidden">
          <Button href="#book" className="!h-9 !px-3.5 text-[13px]">Book a Demo</Button>
          <button type="button" className="inline-flex h-10 w-10 items-center justify-center rounded-full"
            aria-expanded={open} aria-controls="mobile-menu" aria-label={open ? "Close menu" : "Open menu"} onClick={() => setOpen((v) => !v)}>
            <svg viewBox="0 0 20 20" className="h-5 w-5" aria-hidden="true">
              {open ? <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                    : <path d="M3 7h14M3 13h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />}
            </svg>
          </button>
        </div>
      </nav>
      {open && (
        <ul id="mobile-menu" className="container-x border-t border-line pb-4 md:hidden">
          {links.map((l) => (
            <li key={l.label}>
              <a href={l.href} onClick={() => setOpen(false)} {...(l.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                 className="block py-3 text-[15px]">{l.label === "Demo" ? "View Product Demo ↗" : l.label}</a>
            </li>
          ))}
        </ul>
      )}
    </header>
  );
}
