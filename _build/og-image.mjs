// Renders /og-image.png (1200x630), the image shown when the site is shared.
// Run from the repo root after changing the entity name or headline:
//   node _build/og-image.mjs            (needs Node and the playwright package)
// Set CHROMIUM_PATH to use a specific Chromium build.
import { chromium } from 'playwright';

const ENTITY = '[ENTITY NAME]'; // keep in step with ENTITY in build.py
const SPRIG = `<svg width="40" height="40" viewBox="0 0 28 28" fill="none" stroke="#7A2E2A" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 26V5"/><path d="M14 21C10 21 7.5 18.5 7 15C10.5 15.2 13 17.5 14 21Z"/><path d="M14 21C18 21 20.5 18.5 21 15C17.5 15.2 15 17.5 14 21Z"/><path d="M14 14C10.5 14 8.5 11.8 8 8.8C11 9 13.2 11 14 14Z"/><path d="M14 14C17.5 14 19.5 11.8 20 8.8C17 9 14.8 11 14 14Z"/><path d="M14 7.5C12.5 6.5 12.2 4.5 14 2.5C15.8 4.5 15.5 6.5 14 7.5Z"/></svg>`;
const og = `<!doctype html><html><head><link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=IBM+Plex+Sans:wght@500&display=swap" rel="stylesheet"></head>
<body style="margin:0;width:1200px;height:630px;background:#F6F1E7;color:#22201C;box-sizing:border-box;padding:56px 80px;display:flex;flex-direction:column;justify-content:space-between">
<div style="display:flex;align-items:center;gap:14px;padding-bottom:22px;border-bottom:4px double #22201C">${SPRIG}<span style="font-family:Newsreader;font-weight:500;font-size:34px">${ENTITY}</span></div>
<div style="font-family:Newsreader;font-size:70px;line-height:1.06;letter-spacing:-0.015em;max-width:1000px">Your practice. Your clients. <em style="color:#7A2E2A;white-space:nowrap">A partner</em> who'll still be there.</div>
<div style="font-family:'IBM Plex Sans';font-weight:500;font-size:17px;letter-spacing:.12em;text-transform:uppercase;color:#5A544A;padding-top:22px;border-top:1px solid #D8CFBE">Elder law · Estate planning · Probate · New York area and northern New Jersey</div>
</body></html>`;
const b = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
await p.setContent(og, { waitUntil: 'networkidle' });
await p.evaluate(() => document.fonts.ready);
await p.screenshot({ path: 'og-image.png' });
await b.close();
