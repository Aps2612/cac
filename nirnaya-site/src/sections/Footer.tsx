import { Logo } from "../components/Logo";
import { SITE_CONFIG, mailHref, telHref } from "../config";

export function Footer() {
  return (
    <footer className="bg-paper py-12">
      <div className="container-x flex flex-col gap-8 md:flex-row md:justify-between">
        <div className="max-w-xs">
          <Logo />
          <p className="mt-3 text-[13.5px] leading-relaxed text-muted">
            Customer decisioning for D2C brands.
            <br />
            <span className="text-faint">Nirnaya (निर्णय) — decision.</span>
          </p>
        </div>
        <div className="grid grid-cols-1 gap-x-14 gap-y-8 text-[13.5px] sm:grid-cols-2">
          <div className="space-y-2">
            <p className="text-faint">Product</p>
            <a className="block text-muted hover:text-ink" href="#how-it-works">How It Works</a>
            <a className="block text-muted hover:text-ink" href="#benefits">Benefits</a>
            <a className="block text-muted hover:text-ink" href={SITE_CONFIG.demoUrl} target="_blank" rel="noopener noreferrer">Product demo ↗</a>
          </div>
          <div className="space-y-2">
            <p className="text-faint">Contact</p>
            <p className="text-muted">{SITE_CONFIG.founderName}, Founder</p>
            <a className="block text-muted hover:text-ink" href={telHref}>{SITE_CONFIG.phone}</a>
            <a className="block text-muted hover:text-ink" href={mailHref()}>{SITE_CONFIG.contactEmail}</a>
          </div>
        </div>
      </div>
      <div className="container-x mt-10 flex flex-col gap-2 border-t border-line pt-6 text-[12px] text-faint sm:flex-row sm:justify-between">
        <p>© {new Date().getFullYear()} Nirnaya. Made in India.</p>
        <p>Currently validating with selected D2C brands. Examples are illustrative.</p>
      </div>
    </footer>
  );
}
