import { api, ApiError, initApi } from './api.js';
import { $, h, mount, bdi } from './dom.js';
import { readState, writeState } from './state.js';
import { renderHeader, showMode } from './components/Header.js';
import { showSkeleton, showError, setBusy, toast, emptyState } from './components/feedback.js';
import { KpiCard } from './components/KpiCard.js';
import { ClusterMarker, ClusterScatter, DivergingBars, SvgBarChart, SvgDonut, SvgHBars } from './components/charts.js';
import { DataTable } from './components/DataTable.js';
import { Drawer } from './components/Drawer.js';
import { Pager, focusPager, pageRange } from './components/Pager.js';
import { DEFAULT_DAY, firstPublished, loadPresentations, makeScrubber, presentationSelect } from './controls.js';
import { fmt, itemsAr, learnersAr, pct, range, score2, signed, typeAr } from './labels.js';
import type { ClusterSet, InstructorLearnerRow, InstructorOverview, Presentation } from './types.js';
import type { Scrubber } from './components/DayScrubber.js';

let presList: Presentation[] = [];
let scrubber: Scrubber | null = null;
let clusters: ClusterSet | null = null;
let overview: InstructorOverview | null = null;
let seq = 0, tseq = 0;
/** حجم صفحة جدول المتعلمين؛ الإزاحة في حالة الرابط (off). البداية = أول لقطة عناقيد (لا لوحة قبل اليوم 56). */
const PAGE = 100;
const BOARD_FIRST_DAY = 56;
const drawer = Drawer(() => { writeState({ r: '' }); markActive(''); });
/** يظلّل صف المتعلم المفتوح في الدرج وحده (aria-current) ويزيل التظليل عن غيره. */
function markActive(reg: string): void {
  document.querySelectorAll('tr.row').forEach((tr) => {
    const on = reg !== '' && tr.getAttribute('data-id') === reg;
    tr.classList.toggle('row--active', on);
    if (on) tr.setAttribute('aria-current', 'true'); else tr.removeAttribute('aria-current');
  });
}

async function boot(): Promise<void> {
  renderHeader('instructor');
  await initApi(); showMode();
  const host = $('#controls'); setBusy(host, true);
  try { presList = await loadPresentations(); } catch (e) { showError(host, e, () => location.reload()); return; }
  const st = readState();
  const pres = presList.find((p) => p.id === st.p && p.status === 'published') ?? firstPublished(presList);
  if (!pres) { mount(host, emptyState('لا توجد عروض منشورة.')); return; }
  writeState({ p: pres.id, d: st.d ?? DEFAULT_DAY });
  buildControls(pres); setBusy(host, false);
  $('#drawer-slot').append(drawer.el);
  await refresh();
  const r = readState().r; if (r) void openLearner(r, null);
}
function buildControls(pres: Presentation): void {
  const st = readState();
  scrubber = makeScrubber(pres, st.d ?? DEFAULT_DAY, (d) => { writeState({ d }); void refresh(); });
  mount($('#controls'), h('div', { class: 'controls__row' }, presentationSelect(presList, pres.id, (id) => {
    const np = presList.find((p) => p.id === id) as Presentation; writeState({ p: id, cl: null, r: '', off: null }); buildControls(np); void refresh();
  })), scrubber.el);
}

async function refresh(): Promise<void> {
  const st = readState(); const my = ++seq; const d = st.d as number;
  const kpis = $('#kpis'), prof = $('#profiles'), cl = $('#clusters'), risk = $('#risk'), cov = $('#coverage'), tbl = $('#learners');
  showSkeleton(kpis, 1, 90); showSkeleton(cl, 1, 260); showSkeleton(risk, 1, 260); showSkeleton(prof, 1, 160); showSkeleton(cov, 1, 160); showSkeleton(tbl, 4, 48);
  try {
    const [ov, cs] = await Promise.all([api.overview({ presentation: st.p, day: d }), api.clusters({ presentation: st.p, day: d })]);
    if (my !== seq) return;
    overview = ov; clusters = cs;
    renderKpis(ov); renderProfiles(ov); renderClusters(cs); renderRisk(ov); renderCoverage(ov);
    await renderTable();
  } catch (e) {
    if (my !== seq) return;
    if (e instanceof ApiError && e.code === 'day_before_first_snapshot') {
      const first = Number(e.details['first_day'] ?? BOARD_FIRST_DAY);
      toast(`لا تقدير قبل اليوم ${first}؛ نُقل الشريط إلى أول يوم متاح.`, 'info'); scrubber?.set(first); writeState({ d: first }); void refresh(); return;
    }
    for (const el of [kpis, prof, cl, risk, cov, tbl]) showError(el, e, () => void refresh());
  }
}

function renderKpis(o: InstructorOverview): void {
  const k = o.kpis, d = o.requested_day;
  mount($('#kpis'),
    KpiCard(`متعلمون نشطون حتى اليوم ${d}`, fmt(k.active_learners, 0), k.cohort_size !== undefined ? `بيوم نشط واحد على الأقل، من ${fmt(k.cohort_size, 0)} مسجَّلاً لم ينسحب` : 'بيوم نشط واحد على الأقل', 'k1'),
    KpiCard('وسيط الأيام النشطة', fmt(k.median_active_days, 0), undefined, 'k2'),
    KpiCard(`الكتالوج عند اليوم ${o.snapshot_day}`, itemsAr(k.catalogue_size), undefined, 'k3'),
    KpiCard(`اتساع التوصيات عند اليوم ${d}`, `${fmt(o.coverage.covered_items, 0)} من ${itemsAr(o.coverage.catalogue_size)}`, 'موارد ظهرت في أفضل 10 لأحد المتعلمين', 'k4'),
    KpiCard('حصة المتعلمين بدرجة خطر نسبية ≥ العتبة', k.share_above_threshold === null ? 'لا تقدير معروض' : pct(k.share_above_threshold),
      k.share_above_threshold === null ? `تبدأ اللوحة من اليوم ${BOARD_FIRST_DAY}؛ قطع الخطر 28 مبني ولا يُعرض` : 'درجة نسبية غير معايَرة، للعرض لا للتقييم', 'k5'));
  setBusy($('#kpis'), false);
}
function renderProfiles(o: InstructorOverview): void {
  const ul = h('ul', { class: 'prof' });
  for (const p of o.profile_summary) {
    // محور من min(0، p25) إلى max(p75، الوسيط): يعمل مع القيم السالبة (يوم أول وصول قبل بدء العرض) ويبقى داخل المسار
    const lo = Math.min(0, p.p25, p.median), hiRaw = Math.max(p.p75, p.median, lo), hi = hiRaw + (hiRaw - lo) * 0.15 || 1;
    const at = (v: number) => Math.min(100, Math.max(0, ((v - lo) / (hi - lo)) * 100));
    ul.append(h('li', { class: 'prof__row' },
      h('span', { class: 'prof__name' }, p.name),
      h('span', { class: 'prof__track', role: 'img', 'aria-label': `الوسيط ${fmt(p.median)} ${p.unit}، النطاق الربيعي ${range(p.p25, p.p75)}` },
        h('span', { class: 'prof__range', style: `inset-inline-start:${at(p.p25)}%;width:${Math.max(at(p.p75) - at(p.p25), 1)}%` }),
        h('span', { class: 'prof__med', style: `inset-inline-start:${at(p.median)}%` })),
      h('span', { class: 'prof__val num' }, `${fmt(p.median)} ${p.unit}`, h('span', { class: 'muted' }, ` (${range(p.p25, p.p75)})`))));
  }
  mount($('#profiles'), ul, h('p', { class: 'muted' }, 'الوسيط والنطاق الربيعي لملامح السلوك قبل القطع الحالي.')); setBusy($('#profiles'), false);
}
function renderClusters(cs: ClusterSet): void {
  const st = readState(); const host = $('#clusters');
  const cards = h('ul', { class: 'cards' });
  for (const c of cs.clusters) {
    const on = st.cl === c.id;
    const b = h('button', { class: 'ccard' + (on ? ' ccard--on' : ''), type: 'button', 'aria-pressed': String(on), onclick: () => { writeState({ cl: on ? null : c.id, off: null }); renderClusters(cs); void renderTable(); } },
      h('span', { class: 'ccard__t' }, ClusterMarker(c.id), ' ', c.label_ar),
      h('span', { class: 'ccard__m' }, `${learnersAr(c.size)} · أعلى ملمحين: `, c.top_features.map((f) => `${f.name} (${signed(f.z, 1)})`).join('، ')));
    cards.append(h('li', {}, b));
  }
  mount(host,
    h('p', { class: 'muted' }, `k = ${cs.k} · لقطة العناقيد: اليوم ${cs.cluster_day ?? 56}`,
      cs.unstable ? h('span', { class: 'badge badge--warn', title: cs.unstable_reason ?? '' }, 'عناقيد غير مستقرة') : null),
    h('p', { class: 'muted' }, h('strong', {}, 'تشخيص التجميع (مؤشرات داخلية بلا تسميات): '), `silhouette ${fmt(cs.quality.silhouette)} · DBI ${fmt(cs.quality.dbi)} · ARI (ثبات البذور؛ المصدر results/dev2013/learner_clusters.csv) ${cs.quality.ari === null ? 'غير متاح' : fmt(cs.quality.ari)}`),
    cs.unstable && cs.unstable_reason ? h('p', { class: 'note' }, cs.unstable_reason) : null,
    h('div', { class: 'clusters__grid' },
      ClusterScatter('إسقاط PCA للملامح (للعرض فقط)', cs.points, st.cl),
      h('div', {}, SvgDonut('توزيع حجم العناقيد', cs.clusters.map((c) => ({ label: c.label_ar, value: c.size })), st.cl), cards)));
  setBusy(host, false);
}
function renderRisk(o: InstructorOverview): void {
  const host = $('#risk');
  if (!o.risk) { mount(host, emptyState('لا تقدير معروض لهذا اليوم', `تبدأ اللوحة من اليوم ${BOARD_FIRST_DAY} (أول لقطة عناقيد)؛ قطع الخطر 28 مبني ولا يُعرض.`)); setBusy(host, false); return; }
  const r = o.risk;
  const data = r.histogram.map((b) => ({ label: `\u202A${fmt(b.lo, 1)}–${fmt(b.hi, 1)}\u202C`, value: b.count, flag: b.hi > r.threshold }));
  mount(host,
    h('p', { class: 'muted' }, `درجة نسبية غير معايَرة من Logistic L2 على ملامح السلوك حتى اليوم ${r.cut_day}، تميّز «رسوب أو انسحاب» عن «نجاح أو امتياز»؛ العتبة (Youden، 2013) = ${fmt(r.threshold)}`,
      r.provenance === 'oof_2013' || r.provenance === 'lopo_2013' ? h('span', { class: 'badge badge--warn' }, 'تطوير — ترك عرض خارج التدريب (' + r.provenance + ')') : null),
    SvgBarChart({ title: 'توزيع درجة الخطر النسبية', desc: 'مدرج تكراري لدرجة الخطر النسبية في 10 فئات مع خط العتبة؛ الأعمدة فوق العتبة بلون دافئ وإطار داكن.',
      data, xLabel: 'درجة الخطر النسبية غير المعايَرة (لا حكم)؛ الخط المتقطع والإطار الداكن يميّزان ما فوق العتبة لا اللون وحده', yLabel: 'عدد المتعلمين',
      threshold: { x: r.threshold * 10, label: `العتبة ${fmt(r.threshold)}` } }));
  setBusy(host, false);
}
function renderCoverage(o: InstructorOverview): void {
  const c = o.coverage;
  mount($('#coverage'),
    h('p', {}, `غطّت التوصيات ${fmt(c.covered_items, 0)} من ${itemsAr(c.catalogue_size)}.`),
    SvgHBars('حصة أنواع الأنشطة: الكتالوج مقابل التوصيات', 'مقارنة حصة كل نوع نشاط في الكتالوج وفي قوائم أفضل 10.',
      c.by_type.map((t) => ({ label: typeAr(t.activity_type), a: t.catalogue_share, b: t.recs_share })), 'الكتالوج', 'التوصيات'));
  setBusy($('#coverage'), false);
}

// ---------------------------------------------------------------- learners table
// التصفية كلها (العنقود، ≥ العتبة، بلا نشاط 14 يوماً) والفرز والترقيم في الخادم على الفوج كله؛ الواجهة تعرض صفحة واحدة (FR-32، ب-8).
async function renderTable(focus?: 'prev' | 'next'): Promise<void> {
  const st = readState(); const host = $('#learners'); const my = seq, mt = ++tseq;
  try {
    const off = Math.max(0, st.off ?? 0);
    const page = await api.learners({ presentation: st.p, day: st.d as number, cluster: st.cl ?? undefined, risk: st.f === 'above' ? 'above' : 'all',
      idle: st.f === 'idle' || undefined, sort: st.sort, limit: PAGE, offset: off || undefined });
    if (my !== seq || mt !== tseq) return;
    if (!page.items.length && page.total > 0 && off > 0) {   // إزاحة بعد آخر صف (رابط قديم أو تغيّر اليوم): إلى آخر صفحة
      writeState({ off: Math.floor((page.total - 1) / PAGE) * PAGE || null }); return renderTable(focus);
    }
    const rows = page.items;
    const thr = overview?.risk?.threshold;
    const noRisk = overview?.risk === null;
    const cols = [
      { key: 'reg', header: 'التسجيل', sortable: true, cell: (r: InstructorLearnerRow) => bdi(r.registration.replace(/^.*-/, '')) },
      { key: 'cluster', header: 'العنقود', sortable: true, cell: (r: InstructorLearnerRow) => h('span', { class: 'cl' }, ClusterMarker(r.cluster.id), ' ', r.cluster.label) },
      { key: 'active_days', header: 'الأيام النشطة', sortable: true, align: 'num' as const, cell: (r: InstructorLearnerRow) => String(r.active_days) },
      { key: 'last_access', header: 'آخر وصول', sortable: true, align: 'num' as const, cell: (r: InstructorLearnerRow) => r.last_access_day === null ? '—' : 'اليوم ' + fmt(r.last_access_day, 0) },
      { key: 'on_time', header: 'الالتزام', sortable: true, align: 'num' as const, cell: (r: InstructorLearnerRow) => bdi(r.on_time) },
      ...(noRisk ? [] : [
        { key: 'risk', header: 'درجة الخطر', sortable: true, cell: (r: InstructorLearnerRow) => r.risk ? riskCell(r.risk.score, r.risk.above_threshold, thr) : '—' },
        { key: 'factor', header: 'أبرز عامل', wrap: true, cell: (r: InstructorLearnerRow) => r.risk?.top_factor ?? '—' }]),
    ];
    const filt = (st.cl !== null ? ' في العنقود المختار' : '') + (st.f === 'idle' ? ' بلا نشاط 14 يوماً' : st.f === 'above' ? ' بدرجة ≥ العتبة' : '');
    mount(host,
      h('p', { class: 'muted', 'aria-live': 'polite' }, `${learnersAr(page.total)}` + filt + ' · مرتبون حسب ' + sortName(st.sort) + (st.sort.startsWith('-') ? ' تنازلياً' : ' تصاعدياً')
        + (page.total ? ` · عرض ${pageRange(page.total, off, PAGE)}` : '') + ' · Enter أو النقر لفتح الملف · ↑↓ للتنقل'),
      DataTable<InstructorLearnerRow>({ caption: 'جدول المتعلمين مع درجة الخطر النسبية', cols, rows, rowId: (r) => r.registration, sort: st.sort, activeId: st.r || undefined,
        emptyText: 'لا متعلمين يطابقون التصفية الحالية.', onSort: (k) => { const cur = readState().sort; writeState({ sort: cur === '-' + k ? k : '-' + k, off: null }); void renderTable(); },
        onOpen: (r, el) => void openLearner(r.registration, el) }),
      page.total > PAGE || off > 0 ? Pager({ total: page.total, offset: off, limit: PAGE, label: 'صفحات جدول المتعلمين', noun: learnersAr,
        onPage: (o, which) => { writeState({ off: o || null }); void renderTable(which); } }) : null);
    setBusy(host, false);
    if (focus) focusPager(host, focus);
  } catch (e) { showError(host, e, () => void renderTable()); }
}
function sortName(s: string): string { const k = s.replace(/^-/, ''); return ({ risk: 'درجة الخطر', reg: 'التسجيل', cluster: 'العنقود', active_days: 'الأيام النشطة', last_access: 'آخر وصول', on_time: 'الالتزام' } as Record<string, string>)[k] ?? k; }
function riskCell(p: number, above: boolean, thr?: number): HTMLElement {
  return h('span', { class: 'riskcell' + (above ? ' riskcell--above' : ''), title: thr !== undefined ? `العتبة ${fmt(thr)}` : '' },
    h('span', { class: 'riskbar', 'aria-hidden': 'true' }, h('span', { class: 'riskbar__fill', style: `width:${p * 100}%` })),
    h('span', { class: 'num riskcell__n' }, score2(p)), above ? h('span', { class: 'sr-only' }, ' (فوق العتبة)') : null);
}

function filterChips(): void {
  const st = readState();
  const chip = (label: string, on: boolean, fn: () => void) => h('button', { class: 'chipbtn' + (on ? ' chipbtn--on' : ''), type: 'button', 'aria-pressed': String(on), onclick: fn }, label);
  const set = (f: 'all' | 'above' | 'idle') => { writeState({ f, off: null, ...(f === 'all' ? { cl: null } : {}) }); filterChips(); if (clusters) renderClusters(clusters); void renderTable(); };
  mount($('#filters'),
    chip('الكل', st.f === 'all' && st.cl === null, () => set('all')),
    chip('≥ العتبة', st.f === 'above', () => set('above')),
    chip('بلا نشاط 14 يوماً', st.f === 'idle', () => set('idle')),
    st.cl !== null ? chip('عنقود: ' + (clusters?.clusters.find((c) => c.id === st.cl)?.label_ar ?? st.cl) + ' ×', true, () => { writeState({ cl: null, off: null }); filterChips(); if (clusters) renderClusters(clusters); void renderTable(); }) : null);
}

// ---------------------------------------------------------------- drawer
async function openLearner(reg: string, opener: HTMLElement | null): Promise<void> {
  const st = readState(); writeState({ r: reg }); markActive(reg);
  const op = opener ?? (document.querySelector(`tr[data-id="${reg}"]`) as HTMLElement | null) ?? document.body;
  drawer.open('ملف المتعلم ' + reg, op); showSkeleton(drawer.body, 3, 80);
  try {
    const d = await api.learner({ registration: reg, day: st.d as number });
    const body = drawer.body; setBusy(body, false);
    mount(body,
      h('p', {}, h('span', { class: 'cl' }, ClusterMarker(d.cluster.id), ' العنقود: ', d.cluster.label),
        d.risk ? h('span', {}, ` · درجة الخطر النسبية ${score2(d.risk.score)} (قطع اليوم ${d.risk.cut_day}، العتبة ${fmt(d.risk.threshold)})`) : null),
      d.withdrawn_day !== null ? h('p', { class: 'note note--box' }, `انسحب هذا التسجيل في اليوم ${d.withdrawn_day}؛ يُعرض الملف حتى يوم الانسحاب.`) : null,
      d.risk ? h('div', {}, h('h3', { class: 'card__sub' }, 'عوامل الدرجة (w·z)'), DivergingBars('عوامل الدرجة', d.risk.factors.map((f) => ({ name: f.name, v: f.wz }))),
        h('p', { class: 'muted' }, 'الموجب يرفع الدرجة والسالب يخفضها؛ درجة نسبية غير معايَرة لترتيب الأولوية لا حكم.')) : null,
      h('h3', { class: 'card__sub' }, 'الملامح مقابل وسيط العرض'),
      h('div', { class: 'tablewrap' }, h('table', { class: 'table' }, h('thead', {}, h('tr', {}, ...['الملمح', 'القيمة', 'الوسيط', 'z'].map((x) => h('th', { scope: 'col' }, x)))),
        h('tbody', {}, ...d.profile.map((p) => h('tr', {}, h('td', {}, p.name), h('td', { class: 'num' }, fmt(p.value)), h('td', { class: 'num' }, fmt(p.median)), h('td', { class: 'num' }, signed(p.z, 1))))))),
      h('h3', { class: 'card__sub' }, 'توصياته الحالية (أفضل 3)'),
      h('ol', { class: 'recent' }, ...d.top_recs.map((r) => h('li', {}, typeAr(r.activity_type), ' ', bdi('#' + r.id_site), ' — ', r.reason))));
  } catch (e) { showError(drawer.body, e, () => void openLearner(reg, opener)); }
}

filterChips();
void boot().catch((e) => toast(String(e), 'error'));
