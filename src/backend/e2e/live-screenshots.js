// تحقق حيّ على الخادم الحقيقي (لا mock) + لقطات: NODE_PATH=$(npm root -g) node src/backend/e2e/live-screenshots.js [base_url]
// يشترط خادماً يعمل (python3 -m src.backend --warm) وواجهة مبنية. يفشل (exit 1) عند أي خطأ JS أو طلب mock أو غياب شارة «تاريخ النموذج».
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = process.argv[2] || 'http://127.0.0.1:8000';
const OUT = path.resolve(__dirname, '../../../deliverables/05-user-guide/screenshots');
const PRES = 'FFF_2013J';
const DAY = 75;
const CHECK_ONLY = !!process.env.CHECK_ONLY;
const ONLY = process.env.SHOTS ? process.env.SHOTS.split(',') : null;   // مثلاً SHOTS=05-instructor,06-instructor-drawer   // يتحقق فقط ولا يكتب لقطات

async function getJson(url) { const r = await fetch(BASE + url); return r.json(); }

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  // D-72: متعلم الدرج والجدول (واللقطات التي تُظهر متعلماً بدرجته) = الأقرب إلى وسيط الدرجات من بين من هم دون العتبة
  // ضمن الصفحة التي يعرضها الجدول فعلاً (أول 100 مرتبين بالتسجيل، بلا مرشّح «فوق العتبة»)؛ الوسيط من الفوج كله.
  const all = [];
  for (let off = 0; ; off += 500) {
    const pg = await getJson(`/api/instructor/learners?presentation=${PRES}&day=${DAY}&sort=reg&limit=500&offset=${off}`);
    all.push(...pg.items); if (off + 500 >= pg.total) break;
  }
  const scores = all.filter((r) => r.risk).map((r) => r.risk.score).sort((x, y) => x - y);
  const n = scores.length, median = n % 2 ? scores[(n - 1) / 2] : (scores[n / 2 - 1] + scores[n / 2]) / 2;
  const shown = all.slice(0, 100);                              // ما يعرضه الجدول عند sort=reg&limit=100
  const mid = shown.filter((r) => r.risk && !r.risk.above_threshold && r.active_days >= 5)
    .sort((x, y) => Math.abs(x.risk.score - median) - Math.abs(y.risk.score - median) || x.registration.localeCompare(y.registration))[0];
  if (!mid) throw new Error('لا متعلم دون العتبة في الصفحة المعروضة');
  const reg = mid.registration;
  console.log(`متعلم اللقطات (D-72): ${reg} · الدرجة ${mid.risk.score} (العتبة ${mid.risk.threshold}) · وسيط الفوج ${median.toFixed(3)} · الفرق ${(Math.abs(mid.risk.score - median)).toFixed(3)} · أيام نشطة ${mid.active_days}`);
  const Q = `p=${PRES}&r=${reg}&d=${DAY}`;
  const problems = [];
  let expect422 = false;   // خطوة d=30 تتوقع 422 day_before_first_snapshot ثم انتقالاً تلقائياً
  const checks = [];
  const browser = await chromium.launch();
  try {
    for (const [name, vp, mobile] of [['desktop', { width: 1440, height: 900 }, false], ['mobile', { width: 375, height: 800 }, true]]) {
      const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: mobile ? 2 : 1, locale: 'ar', isMobile: mobile, hasTouch: mobile });
      const page = await ctx.newPage();
      const apiCalls = [];
      page.on('pageerror', (e) => problems.push(`${name} pageerror: ${e.message}`));
      page.on('console', (m) => { if (m.type() === 'error' && !(expect422 && /422/.test(m.text()))) problems.push(`${name} console.error: ${m.text()}`); });
      page.on('requestfailed', (r) => problems.push(`${name} requestfailed: ${r.url()}`));
      page.on('response', (r) => {
        const u = new URL(r.url());
        if (u.pathname.startsWith('/api/')) { apiCalls.push(`${r.status()} ${u.pathname}`); if (r.status() >= 400 && !(expect422 && r.status() === 422)) problems.push(`${name} HTTP ${r.status()} ${u.pathname}${u.search}`); }
        if (u.pathname.startsWith('/mock/')) problems.push(`${name} طلب mock: ${u.pathname}`);
      });
      const shot = (file, full = true) => (CHECK_ONLY || (ONLY && !ONLY.includes(file))) ? Promise.resolve() : page.screenshot({ path: path.join(OUT, `live-${file}-${name}.png`), fullPage: full });
      const noHScroll = async (label) => {
        const w = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        if (w > 0) problems.push(`${name} ${label}: تمرير أفقي ${w}px`);
      };
      // فحوص نصية وهندسية للواجهة الحية (ملاحظات مراجعة الدليل)
      const uiChecks = async (label) => {
        const txt = await page.evaluate(() => document.body.innerText);
        if (/\bD-\d/.test(txt)) problems.push(`${name} ${label}: رقم قرار داخلي ظاهر`);
        if (/(?<![A-Za-z0-9_])-\s?\d|--/.test(txt)) problems.push(`${name} ${label}: علامة طرح عادية/مزدوجة في رقم سالب`);
        if (/(?<!\d)(?:[3-9]|10) يوماً|\b(?:1[1-9]|[2-9]\d) أيام/.test(txt)) problems.push(`${name} ${label}: صيغة عدد خاطئة`);
        const attrs = await page.evaluate(() => [...document.querySelectorAll('[title],[aria-label]')].map((e) => (e.getAttribute('title') || '') + ' ' + (e.getAttribute('aria-label') || '')).join(' | '));
        if (/\bD-\d/.test(attrs)) problems.push(`${name} ${label}: رقم قرار داخلي في tooltip/aria`);
      };
      const noMockTag = async (label) => {
        if (await page.locator('.mode-tag').count()) problems.push(`${name} ${label}: وسم وضع المحاكاة ظاهر`);
      };

      // 1) الرئيسية
      await page.goto(`${BASE}/index.html?${Q}`); await page.waitForSelector('.choice'); await page.waitForTimeout(500);
      await noHScroll('home'); await noMockTag('home'); await shot('01-home');

      // 2) المتعلم: بطاقات + شارة تاريخ النموذج + لماذا؟
      await page.goto(`${BASE}/learner.html?${Q}`); await page.waitForSelector('.rec', { timeout: 60000 }); await page.waitForTimeout(400);
      const badge = (await page.locator('.ctxbar__model .badge').first().textContent()) || '';
      checks.push(`${name} شارة النموذج: «${badge.trim()}»`);
      if (!badge.includes('تاريخ النموذج')) problems.push(`${name} شارة «تاريخ النموذج» غائبة`);
      const nrec = await page.locator('.rec').count();
      checks.push(`${name} بطاقات التوصية: ${nrec}`);
      if (nrec < 10) problems.push(`${name} أقل من 10 بطاقات (${nrec})`);
      await noHScroll('learner'); await noMockTag('learner'); await uiChecks('learner'); await shot('02-learner');
      await page.locator('.rec button[data-site]').nth(1).click(); await page.waitForSelector('.why'); await page.waitForTimeout(500);
      const why = await page.locator('.why__item').count();
      checks.push(`${name} مكوّنات التفسير: ${why}`);
      if (why < 1) problems.push(`${name} لوحة «لماذا؟» بلا مكوّنات`);
      await uiChecks('learner-why'); await noHScroll('learner-why'); await shot('03-learner-why', false);
      await page.keyboard.press('Escape');

      // 2ب) قبل أول قطع (اليوم 40): شارة «لا قطع بعد» وإشعار
      await page.goto(`${BASE}/learner.html?p=${PRES}&r=${reg}&d=40`); await page.waitForSelector('.rec', { timeout: 60000 }); await page.waitForTimeout(300);
      const badge40 = (await page.locator('.ctxbar__model .badge').first().textContent()) || '';
      checks.push(`${name} شارة اليوم 40: «${badge40.trim()}»`);
      if (!badge40.includes('تاريخ النموذج')) problems.push(`${name} شارة اليوم 40 غائبة`);
      await shot('04-learner-before-first-cut', false);

      // 3) المدرّس: مؤشرات + عناقيد + مدرج + جدول + درج
      await page.goto(`${BASE}/instructor.html?p=${PRES}&d=${DAY}&sort=reg`); await page.waitForSelector('tr.row', { timeout: 60000 }); await page.waitForTimeout(600);
      checks.push(`${name} صفوف جدول المتعلمين: ${await page.locator('tr.row').count()}`);
      await noHScroll('instructor'); await noMockTag('instructor'); await uiChecks('instructor'); await shot('05-instructor');
      // أشرطة الملامح (قيم سالبة) داخل مساراتها وبطاقتها
      const bad = await page.evaluate(() => [...document.querySelectorAll('.prof__row')].filter((row) => {
        const t = row.querySelector('.prof__track').getBoundingClientRect(), card = row.closest('.card').getBoundingClientRect();
        return [...row.querySelectorAll('.prof__range,.prof__med')].some((e) => { const b = e.getBoundingClientRect();
          return b.left < t.left - 1 || b.right > t.right + 1 || b.left < card.left || b.right > card.right; });
      }).length);
      checks.push(`${name} أشرطة ملامح خارج مسارها: ${bad}`);
      if (bad) problems.push(`${name} أشرطة الملامح تتجاوز المسار/البطاقة (${bad})`);
      // عمود الدرجة: بخانتين وغير مقصوص
      const cells = await page.evaluate(() => [...document.querySelectorAll('.riskcell__n')].map((e) => ({ t: e.textContent, clip: e.scrollWidth > e.clientWidth + 1 })));
      const badCells = cells.filter((c) => !/^(0\.\d\d|1\.00)$/.test(c.t) || c.clip);
      checks.push(`${name} خلايا الدرجة: ${cells.length}، مخالفة: ${badCells.length}`);
      if (!cells.length || badCells.length) problems.push(`${name} خلايا الدرجة مقصوصة/بلا خانتين: ${JSON.stringify(badCells.slice(0, 3))}`);
      await page.locator(`tr[data-id="${reg}"]`).first().click(); await page.waitForSelector('.drawer:not([hidden]) .chart', { timeout: 20000 }); await page.waitForTimeout(400);
      await uiChecks('instructor-drawer');
      await page.mouse.move(2, 2);    // لا مؤشر فوق صف (تظليل hover يُلتبس بالصف المحدد)
      const sel = await page.evaluate((r) => ({ active: [...document.querySelectorAll('tr.row--active')].map((t) => t.dataset.id), hover: document.querySelectorAll('tr.row:hover').length, want: !!document.querySelector(`tr[data-id="${r}"]`) }), reg);
      checks.push(`${name} الصف المظلل: ${sel.active.join(',')} (المتعلم ${reg})`);
      if (sel.active.length !== 1 || sel.active[0] !== reg || sel.hover) problems.push(`${name} التظليل ليس على متعلم الدرج وحده: ${JSON.stringify(sel)}`);
      const h2 = await page.locator('#t-learners').textContent();
      const line = await page.locator('#learners p.muted').first().textContent();
      checks.push(`${name} عنوان الجدول: «${h2.trim()}» · ${line.trim().slice(0, 60)}`);
      if (/تنازلياً/.test(h2) && !/تنازلياً/.test(line)) problems.push(`${name} عنوان الجدول لا يعكس الفرز`);
      if (!mobile) {   // مع الدرج مفتوحاً على سطح المكتب: كل أعمدة الجدول (ومنها الدرجة 0.xx) ظاهرة بلا تمرير أفقي
        const fit = await page.evaluate(() => { const w = document.querySelector('#learners .tablewrap'), r = w.getBoundingClientRect();
          return { overflow: w.scrollWidth - w.clientWidth, outside: [...w.querySelectorAll('th')].filter((t) => { const b = t.getBoundingClientRect(); return b.left < r.left - 1 || b.right > r.right + 1; }).length }; });
        checks.push(`${name} الجدول مع الدرج: تجاوز ${fit.overflow}px، أعمدة خارج الإطار ${fit.outside}`);
        if (fit.overflow > 1 || fit.outside) problems.push(`${name} أعمدة الجدول مقصوصة مع الدرج: ${JSON.stringify(fit)}`);
      }
      await shot('06-instructor-drawer', false);

      // 3ب) المدرّس قبل اليوم 56: ينتقل الشريط تلقائياً إلى 56
      expect422 = true;
      await page.goto(`${BASE}/instructor.html?p=${PRES}&d=30`); await page.waitForSelector('tr.row', { timeout: 60000 }); await page.waitForTimeout(500);
      const dnow = await page.locator('#scrub-num').inputValue();
      checks.push(`${name} المدرّس عند d=30 ينتقل إلى d=${dnow}`);
      if (dnow !== '56') problems.push(`${name} لم ينتقل الشريط إلى 56 (${dnow})`);
      expect422 = false;

      // 4) عن النظام
      await page.goto(`${BASE}/about.html`); await page.waitForTimeout(300); await noHScroll('about');

      checks.push(`${name} نداءات API: ${[...new Set(apiCalls)].length} مسارات مختلفة`);
      await ctx.close();
    }
  } finally { await browser.close(); }
  console.log(checks.join('\n'));
  if (problems.length) { console.error('PROBLEMS:\n' + [...new Set(problems)].join('\n')); process.exitCode = 1; }
  else console.log('LIVE OK -> ' + OUT);
}
main().catch((e) => { console.error(e); process.exit(1); });
