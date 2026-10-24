// Screenshots in mock mode: node screenshots.js  (requires ./build.sh first; Playwright available globally)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = __dirname;
const OUT = path.resolve(ROOT, '../../deliverables/05-user-guide/screenshots');
const PORT = 8765;
const BASE = `http://127.0.0.1:${PORT}`;
const Q = 'p=BBB_2013J&r=BBB_2013J-28400&d=75';

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const srv = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1', '-d', path.join(ROOT, 'dist')], { stdio: 'ignore' });
  await new Promise((r) => setTimeout(r, 1200));
  const browser = await chromium.launch();
  const errors = [];
  try {
    for (const [name, vp, mobile] of [['desktop', { width: 1440, height: 900 }, false], ['mobile', { width: 375, height: 800 }, true]]) {
      const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: mobile ? 2 : 1, locale: 'ar', isMobile: mobile, hasTouch: mobile });
      const page = await ctx.newPage();
      page.on('pageerror', (e) => errors.push(name + ' pageerror: ' + e.message));
      page.on('console', (m) => { if (m.type() === 'error' && !/\/api\/health/.test(m.text()) && !/404/.test(m.text())) errors.push(name + ' console: ' + m.text()); });
      const shot = async (file, full = true) => { await page.screenshot({ path: path.join(OUT, `${file}-${name}.png`), fullPage: full }); };
      const hScroll = async (label) => {
        const w = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        if (w > 0) errors.push(`${name} ${label}: horizontal overflow ${w}px`);
      };

      await page.goto(`${BASE}/index.html?${Q}`); await page.waitForSelector('.choice'); await page.waitForTimeout(400);
      await hScroll('home'); await shot('01-home');

      await page.goto(`${BASE}/learner.html?${Q}`); await page.waitForSelector('.rec'); await page.waitForTimeout(300);
      await hScroll('learner'); await shot('02-learner');
      await page.locator('.rec button[data-site]').nth(2).click(); await page.waitForSelector('.why'); await page.waitForTimeout(500);
      await hScroll('learner-why'); await shot('03-learner-why', false);
      await page.keyboard.press('Escape');

      await page.goto(`${BASE}/instructor.html?${Q.replace(/&r=[^&]*/, '')}`); await page.waitForSelector('tr.row'); await page.waitForTimeout(500);
      await hScroll('instructor'); await shot('04-instructor');
      await page.locator('tr.row').first().click(); await page.waitForSelector('.drawer:not([hidden]) .chart'); await page.waitForTimeout(400);
      await shot('05-instructor-drawer', false);

      await page.goto(`${BASE}/learner.html?p=BBB_2013J&r=BBB_2013J-28400&d=20`); await page.waitForTimeout(800);
      await shot('06-learner-day-before-snapshot', false);

      await ctx.close();
    }
  } finally { await browser.close(); srv.kill(); }
  if (errors.length) { console.error('PROBLEMS:\n' + errors.join('\n')); process.exitCode = 1; } else console.log('screenshots OK ->', OUT);
}
main();
