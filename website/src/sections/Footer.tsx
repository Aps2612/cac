import { Logo } from "../components/Logo";
import { ctaHref, SITE_CONFIG } from "../config";

export function Footer() {
  return (
    <footer className="border-t border-line bg-paper py-12">
      <div className="container-x flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
        <div className="max-w-sm">
          <Logo />
          <p className="mt-3 text-[13.5px] leading-relaxed text-muted">
            Customer decisioning for D2C brands. Currently validating with selected D2C brands.
          </p>
        </div>
        <nav aria-label="Footer" className="grid grid-cols-2 gap-x-12 gap-y-2 text-[13.5px] sm:grid-cols-3">
          <a className="text-muted hover:text-ink" href="#product">Product</a>
          <a className="text-muted hover:text-ink" href="#how-it-works">How It Works</a>
          <a className="text-muted hover:text-ink" href="#use-cases">Use Cases</a>
          <a className="text-muted hover:text-ink" href="#pilot">Pilot</a>
          <a className="text-muted hover:text-ink" href="#about">About</a>
          <a className="text-muted hover:text-ink" href={ctaHref("audit")}>Contact</a>
          <a className="text-muted hover:text-ink" href={SITE_CONFIG.demoUrl} target="_blank" rel="noopener noreferrer">Product demo ↗</a>
        </nav>
      </div>
      <div className="container-x mt-10 flex flex-col gap-2 border-t border-line pt-6 text-[12px] text-faint sm:flex-row sm:justify-between">
        <p>© {new Date().getFullYear()} Nirnaya. Made in India.</p>
        <p>All customer examples on this site are illustrative.</p>
      </div>
    </footer>
  );
}
