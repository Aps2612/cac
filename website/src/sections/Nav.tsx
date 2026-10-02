import { useEffect, useState } from "react";
import { Logo } from "../components/Logo";
import { Button } from "../components/Button";
import { ctaHref } from "../config";

const links = [
  { href: "#product", label: "Product" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#use-cases", label: "Use Cases" },
  { href: "#for-d2c", label: "For D2C" },
  { href: "#about", label: "About" },
  { href: "#contact", label: "Contact" },
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
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <header className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${scrolled || open ? "border-b border-line bg-paper/90 backdrop-blur-md" : "border-b border-transparent"}`}>
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:rounded-md focus:bg-ink focus:px-3 focus:py-2 focus:text-paper">Skip to content</a>
      <nav className="container-x flex h-16 items-center justify-between" aria-label="Primary">
        <a href="#top" aria-label="Nirnaya home"><Logo /></a>
        <ul className="hidden items-center gap-1 lg:flex">
          {links.map((l) => (
            <li key={l.href}>
              <a href={l.href} className="rounded-full px-3 py-2 text-[13.5px] text-muted transition-colors hover:text-ink">{l.label}</a>
            </li>
          ))}
        </ul>
        <div className="hidden lg:block">
          <Button href={ctaHref()}>Book a Demo</Button>
        </div>
        <button
          type="button"
          className="-mr-2 inline-flex h-10 w-10 items-center justify-center rounded-full lg:hidden"
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          <svg viewBox="0 0 20 20" className="h-5 w-5" aria-hidden="true">
            {open ? (
              <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            ) : (
              <path d="M3 7h14M3 13h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            )}
          </svg>
        </button>
      </nav>
      {open && (
        <div id="mobile-menu" className="container-x pb-6 lg:hidden">
          <ul className="flex flex-col border-t border-line pt-3">
            {links.map((l) => (
              <li key={l.href}>
                <a href={l.href} onClick={() => setOpen(false)} className="block py-3 text-[15px] text-ink">{l.label}</a>
              </li>
            ))}
          </ul>
          <Button href={ctaHref()} className="mt-4 w-full" size="lg">Book a Demo</Button>
        </div>
      )}
    </header>
  );
}
