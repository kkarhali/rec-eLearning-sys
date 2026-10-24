import { api, ApiError, initApi } from './api.js';
import { $, h, mount, bdi } from './dom.js';
import { readState, writeState } from './state.js';
import { renderHeader, showMode } from './components/Header.js';
import { showSkeleton, showError, setBusy, toast, emptyState } from './components/feedback.js';
import { RecCard, CompLegend } from './components/RecCard.js';
import { WhyPanel } from './components/WhyPanel.js';
import { DEFAULT_DAY, firstPublished, loadPresentations, makeScrubber, presentationSelect, registrationPicker } from './controls.js';
import { daysAr, typeAr } from './labels.js';
import type { Presentation, RecommendationResponse, LearnerHistory } from './types.js';
import type { Scrubber } from './components/DayScrubber.js';

let presList: Presentation[] = [];
let scrubber: Scrubber | null = null;
let seq = 0;
let openSite: number | null = null;
let lastBtn: HTMLButtonElement | null = null;

async function boot(): Promise<void> {
  renderHeader('learner');
  await initApi(); showMode();
  const host = $('#controls'); setBusy(host, true);
  try { presList = await loadPresentations(); } catch (e) { showError(host, e, () => location.reload()); return; }
  let st = readState();
  const pres = presList.find((p) => p.id === st.p && p.status === 'published') ?? firstPublished(presList);
  if (!pres) { mount(host, emptyState('لا توجد عروض منشورة.')); return; }
  st = writeState({ p: pres.id, d: st.d ?? DEFAULT_DAY });
  buildControls(pres);
  await selectInitialReg(pres);
  setBusy(host, false);
  window.addEventListener('popstate', () => location.reload());
}

let picker: ReturnType<typeof registrationPicker> | null = null;
function buildControls(pres: Presentation): void {
  const st = readState();
  const host = $('#controls');
  picker = registrationPicker(pres.id, st.r, (reg) => { openSite = null; writeState({ r: reg }); void refresh(); });
  scrubber = makeScrubber(pres, st.d ?? DEFAULT_DAY, (d) => { writeState({ d }); void refresh(); });
  mount(host, h('div', { class: 'controls__row' },
    presentationSelect(presList, pres.id, (id) => {
      const np = presList.find((p) => p.id === id) as Presentation;
      const suffix = readState().r.replace(/^.*-/, '');
      writeState({ p: id, r: suffix ? id + '-' + suffix : '' }); openSite = null;
      buildControls(np); void selectInitialReg(np);
    }), picker.el), scrubber.el);
}
async function selectInitialReg(pres: Presentation): Promise<void> {
  const st = readState();
  const first = await picker?.load();
  const sel = document.getElementById('sel-reg') as HTMLSelectElement | null;
  const want = st.r && sel && [...sel.options].some((o) => o.value === st.r) ? st.r : first;
  if (!want) { mount($('#result'), emptyState('لا تسجيلات في هذا العرض.')); return; }
  if (sel) sel.value = want;
  writeState({ r: want, p: pres.id });
  await refresh();
}

async function refresh(): Promise<void> {
  const st = readState(); const my = ++seq;
  const res = $('#result');
  if (!st.r || st.d === null) return;
  showSkeleton(res, 4, 84);
  try {
    const [rec, hist] = await Promise.all([
      api.recommendations({ registration: st.r, day: st.d, k: 10, task: st.task }),
      api.history({ registration: st.r, day: st.d, window: 28 }).catch(() => null)]);
    if (my !== seq) return;
    render(rec, hist);
  } catch (e) {
    if (my !== seq) return;
    if (e instanceof ApiError && e.code === 'day_before_first_snapshot') {
      const first = Number(e.details['first_day'] ?? presList.find((p) => p.id === st.p)?.snapshots[0] ?? 28);
      toast(`لا توصيات قبل اليوم ${first}؛ نُقل الشريط إلى أول يوم متاح.`, 'info');
      scrubber?.set(first); writeState({ d: first }); void refresh(); return;
    }
    showError(res, e, () => void refresh());
  }
}

function contextBar(r: RecommendationResponse): HTMLElement {
  const c = r.context, na = c.next_assessment, cut = r.provenance.model_cut;
  return h('section', { class: 'ctxbar', 'aria-live': 'polite', 'aria-label': 'سياق التوصية' },
    h('p', { class: 'ctxbar__main' },
      `اليوم ${r.requested_day} (${r.snapshot_day === r.requested_day ? 'الحساب عند اليوم t نفسه' : 'محسوب عند اليوم ' + r.snapshot_day}) · الأسبوع ${c.week} · `,
      na ? `التقييم القادم: ${na.type} بعد ${daysAr(na.days_ahead)}` : 'لا تقييم قادم', ` · أيامك النشطة حتى الآن: ${c.active_days_to_date}`),
    cut !== undefined ? h('p', { class: 'ctxbar__model' },
      h('span', { class: 'badge', title: 'النموذج المستعمل دُرّب عند أقرب قطع لا يتجاوز اليوم t' },
        cut === null ? 'تاريخ النموذج: لا قطع بعد' : 'تاريخ النموذج: اليوم ', cut === null ? null : bdi(cut)),
      r.requested_day < 70 ? h('span', { class: 'note' }, ' لا مكوّن ثقيل قبل اليوم 70؛ أُعيدت معايرة أوزان المكوّنات المتاحة.') : null) : null);
}

function activity(hist: LearnerHistory | null, day: number): HTMLElement {
  const box = h('section', { class: 'card activity', 'aria-labelledby': 'act-t' }, h('h2', { class: 'card__title', id: 'act-t' }, `نشاطي في آخر 28 يوماً حتى اليوم ${day}`));
  if (!hist) { box.append(emptyState('تعذّر تحميل السجل.')); return box; }
  const grid = h('div', { class: 'heat', role: 'img', 'aria-label': `خلايا الأيام الـ28 الأخيرة؛ ${hist.daily.filter((d) => d.clicks > 0).length} منها بنشاط.` });
  for (const d of hist.daily) {
    const lvl = d.clicks === 0 ? 0 : d.clicks < 10 ? 1 : d.clicks < 30 ? 2 : 3;
    grid.append(h('span', { class: 'heat__c heat__c--' + lvl, title: `اليوم ${d.day}: ${d.clicks} نقرة` }, lvl ? '' : ''));
  }
  box.append(grid, h('p', { class: 'heat__key' }, 'أفتح = أقل نشاطاً · أغمق = أكثر؛ المسافة الفارغة = يوم بلا نشاط'));
  box.append(h('p', { class: 'activity__sum' }, `أيام نشطة حتى الآن: ${hist.active_days}`),
    h('h3', { class: 'card__sub' }, 'آخر ما زرتَه'));
  if (!hist.recent.length) box.append(h('p', { class: 'muted' }, 'لا نشاط سابق حتى هذا اليوم.'));
  else box.append(h('ul', { class: 'recent' }, ...hist.recent.map((e) => h('li', {}, typeAr(e.activity_type), ' ', bdi('#' + e.id_site), ` · اليوم ${e.day}`))));
  return box;
}

function render(rec: RecommendationResponse, hist: LearnerHistory | null): void {
  const res = $('#result'); setBusy(res, false);
  const st = readState();
  const taskToggle = h('label', { class: 'toggle' },
    h('input', { type: 'checkbox', checked: st.task === 'B', onchange: (e: Event) => { openSite = null; writeState({ task: (e.target as HTMLInputElement).checked ? 'B' : 'A' }); void refresh(); } }),
    ' بما فيه ما زرتُه (المهمة B)');
  const why = h('div', { id: 'why-slot', class: 'why-slot' });
  const main = h('section', { class: 'recs', 'aria-labelledby': 'recs-t' },
    h('div', { class: 'recs__head' },
      h('div', {}, h('h2', { id: 'recs-t', class: 'h2' }, st.task === 'A' ? 'أفضل 10 موارد لم تزرها بعد' : 'أفضل 10 موارد (بما فيها ما زرتَه)'),
        h('p', { class: 'muted' }, 'مرتبة بدرجة الهجين المجمَّد؛ اضغط «لماذا؟» لرؤية الدليل.')), taskToggle));

  if (rec.status === 'withdrawn') main.append(emptyState('انتهى هذا التسجيل قبل اليوم المختار', 'لا توصيات بعد الانسحاب. اختر يوماً أبكر أو تسجيلاً آخر.'));
  else {
    if (rec.status === 'no_history') main.append(h('p', { class: 'note note--box' }, `لا نشاط سابق لك حتى اليوم ${rec.snapshot_day}؛ هذه أكثر الموارد استخداماً لدى زملائك هذا الأسبوع.`));
    if (!rec.items.length) main.append(emptyState('لا توصيات متاحة لهذا اليوم'));
    const ul = h('ol', { class: 'reclist' });
    for (const it of rec.items) ul.append(RecCard({ item: it, comps: rec.components, active: openSite === it.id_site, onWhy: (b) => void openWhy(rec, it.id_site, b) }));
    main.append(ul, h('p', { class: 'muted center' }, `عُرضت ${rec.items.length} بطاقات (k = 10 افتراضياً).`), CompLegend(rec.components));
  }
  mount(res, contextBar(rec),
    h('div', { class: 'grid2' }, main, h('div', { class: 'side' }, why, activity(hist, rec.requested_day))));
  if (openSite !== null && rec.items.some((i) => i.id_site === openSite)) void openWhy(rec, openSite, null, true);
}

async function openWhy(rec: RecommendationResponse, site: number, btn: HTMLButtonElement | null, silent = false): Promise<void> {
  const slot = document.getElementById('why-slot'); if (!slot) return;
  if (btn) lastBtn = btn;
  openSite = site;
  document.querySelectorAll('.rec').forEach((li) => {
    const b = li.querySelector('button'); const on = b?.getAttribute('data-site') === String(site);
    li.classList.toggle('rec--active', on); b?.setAttribute('aria-expanded', String(on));
    b?.classList.toggle('btn--primary', on); b?.classList.toggle('btn--outline', !on);
  });
  showSkeleton(slot, 1, 180);
  try {
    const d = await api.explanation({ registration: rec.registration, id_site: site, day: rec.requested_day, task: rec.task });
    if (openSite !== site) return;
    const close = () => {
      openSite = null; mount(slot); slot.classList.remove('why-slot--open');
      document.querySelectorAll('.rec').forEach((li) => { li.classList.remove('rec--active'); const b = li.querySelector('button'); b?.setAttribute('aria-expanded', 'false'); b?.classList.remove('btn--primary'); b?.classList.add('btn--outline'); });
      (lastBtn && document.body.contains(lastBtn) ? lastBtn : document.querySelector<HTMLElement>(`[data-site="${site}"]`))?.focus();
    };
    const panel = WhyPanel(d, close);
    mount(slot, panel); setBusy(slot, false); slot.classList.add('why-slot--open');
    if (!silent) { panel.focus(); panel.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); }
  } catch (e) {
    openSite = null; mount(slot);
    toast(e instanceof ApiError ? e.message : 'تعذّر تحميل التفسير', 'error');
  }
}

void boot().catch((e) => toast(String(e), 'error'));
