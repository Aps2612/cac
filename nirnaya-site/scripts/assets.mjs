// Regenerates public/og-image.png and PNG favicons. Needs Playwright (not a site dependency):
//   npx -y -p playwright node scripts/assets.mjs
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";
const dir = path.dirname(fileURLToPath(import.meta.url));
const launch = { ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}), ...(process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {}) };
const b = await chromium.launch(launch);
const ctx = await b.newContext({ ignoreHTTPSErrors: true });
const p = await ctx.newPage();
await p.setViewportSize({ width: 1200, height: 630 });
await p.goto("file://" + path.join(dir, "og.html"), { waitUntil: "networkidle" });
await p.evaluate(() => document.fonts.ready);
await p.screenshot({ path: path.join(dir, "../public/og-image.png") });
for (const [s, f] of [[32, "favicon-32.png"], [180, "apple-touch-icon.png"]]) {
  const q = await ctx.newPage();
  await q.setViewportSize({ width: s, height: s });
  await q.setContent(`<style>body{margin:0}</style><img src="file://${path.join(dir, "../public/favicon.svg")}" width="${s}" height="${s}">`);
  await q.screenshot({ path: path.join(dir, "../public", f), omitBackground: true });
}
await b.close();
