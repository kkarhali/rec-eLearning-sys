#!/usr/bin/env node
// Rasterize SVG/HTML files to PNG with the globally installed Playwright (Node) + Chromium.
// Usage: node scripts/svg2png.js in.svg [in2.svg ...] [--out-dir DIR] [--scale 2] [--width 1400]
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

(async () => {
  const args = process.argv.slice(2);
  const opt = { outDir: null, scale: 2, width: 1400 };
  const inputs = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--out-dir") opt.outDir = args[++i];
    else if (args[i] === "--scale") opt.scale = parseFloat(args[++i]);
    else if (args[i] === "--width") opt.width = parseInt(args[++i], 10);
    else inputs.push(args[i]);
  }
  if (!inputs.length) { console.error("no inputs"); process.exit(1); }
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: opt.scale, viewport: { width: opt.width, height: 900 } });
  for (const src of inputs) {
    const dst = path.join(opt.outDir || path.dirname(src), path.basename(src, path.extname(src)) + ".png");
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    let el;
    if (src.toLowerCase().endsWith(".svg")) {
      const svg = fs.readFileSync(src, "utf8");
      await page.setContent(`<!doctype html><html><body style="margin:0;background:#fff;display:inline-block">${svg}</body></html>`);
      el = await page.$("svg");
    } else {
      await page.goto("file://" + path.resolve(src));
      await page.waitForLoadState("networkidle");
      el = await page.$("body");
    }
    await el.screenshot({ path: dst });
    console.log(`${src} -> ${dst}`);
  }
  await browser.close();
})();
