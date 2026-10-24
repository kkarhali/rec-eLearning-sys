import { api, ApiError, initApi } from './api.js';
import { $, h, mount, bdi } from './dom.js';
import { readState, writeState } from './state.js';
import { renderHeader, showMode } from './components/Header.js';
import { showSkeleton, showError, setBusy, toast, emptyState } from './components/feedback.js';
import { KpiCard } from './components/KpiCard.js';
import { ClusterMarker, ClusterScatter, DivergingBars, SvgBarChart, SvgDonut, SvgHBars } from './components/charts.js';
import { DataTable } from './components/DataTable.js';
import { Drawer } from './components/Drawer.js';
import { DEFAULT_DAY, firstPublished, loadPresentations, makeScrubber, presentationSelect } from './controls.js';
import { fmt, pct, typeAr } from './labels.js';
import type { ClusterSet, InstructorLearnerRow, InstructorOverview, Presentation } from './types.js';
import type { Scrubber } from './components/DayScrubber.js';

let presList: Presentation[] = [];
let scrubber: Scrubber | null = null;
let clusters: ClusterSet | null = null;
let overview: InstructorOverview | null = null;
let seq = 0;
const drawer = Drawer(() => writeState({ r: '' }));

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
    const np = presList.find((p) => p.id === id) as Presentation; writeState({ p: id, cl: null, r: '' }); buildControls(np); void refresh();
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
      const first = Number(e.details['first_day'] ?? 28);
      toast(`لا تقدير قبل اليوم ${first}؛ نُقل الشريط إلى أول يوم متاح.`, 'info'); scrubber?.set(first); writeState({ d: first }); void refresh(); return;
    }
    for (const el of [kpis, prof, cl, risk, cov, tbl]) showError(el, e, () => void refresh());
  }
}

function renderKpis(o: InstructorOverview): void {
  const k = o.kpis, d = o.requested_day;
  mount($('#kpis'),
    KpiCard(`متعلمون نشطون حتى اليوم ${d}`, fmt(k.active_learners, 0), undefined, 'k1'),
    KpiCard('وسيط الأيام النشطة', fmt(k.median_active_days, 0), undefined, 'k2'),
    KpiCard(`الكتالوج عند اللقطة ${o.snapshot_day}`, fmt(k.catalogue_size, 0) + ' مورداً', undefined, 'k3'),
    KpiCard('Coverage@10 للتوصيات', fmt(k.coverage_at_10, 2), 'نسبة الكتالوج الموصى به', 'k4'),
    KpiCard('درجة الخطر ≥ العتبة (نسبية)', k.share_above_threshold === null ? 'لا تقدير قبل اليوم 28' : pct(k.share_above_threshold), 'قيم توضيحية', 'k5'));
  setBusy($('#kpis'), false);
}
function renderProfiles(o: InstructorOverview): void {
  const ul = h('ul', { class: 'prof' });
  for (const p of o.profile_summary) {
    const max = Math.max(p.p75 * 1.3, p.median * 1.6, 1e-6), at = (v: number) => (v / max) * 100;
    ul.append(h('li', { class: 'prof__row' },
      h('span', { class: 'prof__name' }, p.name),
      h('span', { class: 'prof__track', role: 'img', 'aria-label': `الوسيط ${fmt(p.median)} ${p.unit}، النطاق الربيعي من ${fmt(p.p25)} إلى ${fmt(p.p75)}` },
        h('span', { class: 'prof__range', style: `inset-inline-start:${at(p.p25)}%;width:${at(p.p75) - at(p.p25)}%` }),
        h('span', { class: 'prof__med', style: `inset-inline-start:${at(p.median)}%` })),
      h('span', { class: 'prof__val num' }, `${fmt(p.median)} ${p.unit}`, h('span', { class: 'muted' }, ` (${fmt(p.p25)}–${fmt(p.p75)})`))));
  }
  mount($('#profiles'), ul, h('p', { class: 'muted' }, 'الوسيط والنطاق الربيعي لملامح السلوك قبل القطع الحالي.')); setBusy($('#profiles'), false);
}
function renderClusters(cs: ClusterSet): void {
  const st = readState(); const host = $('#clusters');
  const cards = h('ul', { class: 'cards' });
  for (const c of cs.clusters) {
    const on = st.cl === c.id;
    const b = h('button', { class: 'ccard' + (on ? ' ccard--on' : ''), type: 'button', 'aria-pressed': String(on), onclick: () => { writeState({ cl: on ? null : c.id }); renderClusters(cs); void renderTable(); } },
      h('span', { class: 'ccard__t' }, ClusterMarker(c.id), ' ', c.label_ar),
      h('span', { class: 'ccard__m' }, `${fmt(c.size, 0)} متعلماً · أعلى ملمحين: `, c.top_features.map((f) => `${f.name} (${f.z > 0 ? '+' : ''}${fmt(f.z, 1)})`).join('، ')));
    cards.append(h('li', {}, b));
  }
  mount(host,
    h('p', { class: 'muted' }, `k = ${cs.k} عند اللقطة ${cs.snapshot_day} · silhouette ${fmt(cs.quality.silhouette)} · DBI ${fmt(cs.quality.dbi)} · ARI ${fmt(cs.quality.ari)}`,
      cs.unstable ? h('span', { class: 'badge badge--warn' }, 'عناقيد غير مستقرة') : null),
    h('div', { class: 'clusters__grid' },
      ClusterScatter('إسقاط PCA للملامح (للعرض فقط)', cs.points, st.cl),
      h('div', {}, SvgDonut('توزيع حجم العناقيد', cs.clusters.map((c) => ({ label: c.label_ar, value: c.size })), st.cl), cards)));
  setBusy(host, false);
}
function renderRisk(o: InstructorOverview): void {
  const host = $('#risk');
  if (!o.risk) { mount(host, emptyState('لا تقدير قبل اليوم 28', 'تبدأ درجة الخطر النسبية عند أول قطع للنموذج.')); setBusy(host, false); return; }
  const r = o.risk;
  const data = r.histogram.map((b) => ({ label: `\u202A${fmt(b.lo, 1)}–${fmt(b.hi, 1)}\u202C`, value: b.count, flag: b.hi > r.threshold }));
  mount(host,
    h('p', { class: 'muted' }, `تقدير Logistic L2 (قطع اليوم ${r.cut_day})، عتبة Youden المجمَّدة من 2013 = ${fmt(r.threshold)}`,
      r.provenance === 'oof_2013' || r.provenance === 'lopo_2013' ? h('span', { class: 'badge badge--warn' }, 'تطوير — ترك عرض خارج التدريب (' + r.provenance + ')') : null),
    SvgBarChart({ title: 'توزيع درجة الخطر النسبية', desc: 'مدرج تكراري لدرجة الخطر النسبية في 10 فئات مع خط العتبة؛ الأعمدة فوق العتبة بلون دافئ وإطار داكن.',
      data, xLabel: 'درجة الخطر النسبية غير المعايَرة (لا حكم)؛ الخط المتقطع والإطار الداكن يميّزان ما فوق العتبة لا اللون وحده', yLabel: 'عدد المتعلمين',
      threshold: { x: r.threshold * 10, label: `العتبة ${fmt(r.threshold)}` } }));
  setBusy(host, false);
}
function renderCoverage(o: InstructorOverview): void {
  const c = o.coverage;
  mount($('#coverage'),
    h('p', {}, `غطّت التوصيات ${fmt(c.covered_items, 0)} من ${fmt(c.catalogue_size, 0)} مورداً (Coverage@10 = ${fmt(c.at_10)}).`),
    SvgHBars('حصة أنواع الأنشطة: الكتالوج مقابل التوصيات', 'مقارنة حصة كل نوع نشاط في الكتالوج وفي قوائم أفضل 10.',
      c.by_type.map((t) => ({ label: typeAr(t.activity_type), a: t.catalogue_share, b: t.recs_share })), 'الكتالوج', 'التوصيات'));
  setBusy($('#coverage'), false);
}

// ---------------------------------------------------------------- learners table
async function renderTable(): Promise<void> {
  const st = readState(); const host = $('#learners'); const my = seq;
  try {
    const page = await api.learners({ presentation: st.p, day: st.d as number, cluster: st.cl ?? undefined, risk: st.f === 'above' ? 'above' : 'all', sort: st.sort, limit: 100 });
    if (my !== seq) return;
    let rows = page.items;
    if (st.f === 'idle') rows = rows.filter((r) => r.last_access_day === null || (st.d as number) - r.last_access_day >= 14);
    const thr = overview?.risk?.threshold;
    const noRisk = overview?.risk === null;
    const cols = [
      { key: 'reg', header: 'التسجيل', sortable: true, cell: (r: InstructorLearnerRow) => bdi(r.registration.replace(/^.*-/, '')) },
      { key: 'cluster', header: 'العنقود', sortable: true, cell: (r: InstructorLearnerRow) => h('span', { class: 'cl' }, ClusterMarker(r.cluster.id), ' ', r.cluster.label) },
      { key: 'active_days', header: 'الأيام النشطة', sortable: true, align: 'num' as const, cell: (r: InstructorLearnerRow) => String(r.active_days) },
      { key: 'last_access', header: 'آخر وصول', sortable: true, align: 'num' as const, cell: (r: InstructorLearnerRow) => r.last_access_day === null ? '—' : 'اليوم ' + r.last_access_day },
      { key: 'on_time', header: 'الالتزام', sortable: true, align: 'num' as const, cell: (r: InstructorLearnerRow) => bdi(r.on_time) },
      ...(noRisk ? [] : [
        { key: 'risk', header: 'درجة الخطر النسبية', sortable: true, cell: (r: InstructorLearnerRow) => r.risk ? riskCell(r.risk.score, r.risk.above_threshold, thr) : '—' },
        { key: 'factor', header: 'أبرز عامل', cell: (r: InstructorLearnerRow) => r.risk?.top_factor ?? '—' }]),
    ];
    mount(host,
      h('p', { class: 'muted', 'aria-live': 'polite' }, `${rows.length} متعلماً` + (st.cl !== null ? ' في العنقود المختار' : '') + ' · مرتبون حسب ' + sortName(st.sort) + ' · Enter أو النقر لفتح الملف · ↑↓ للتنقل'),
      DataTable<InstructorLearnerRow>({ caption: 'جدول المتعلمين مع درجة الخطر النسبية', cols, rows, rowId: (r) => r.registration, sort: st.sort, activeId: st.r || undefined,
        emptyText: 'لا متعلمين يطابقون التصفية الحالية.', onSort: (k) => { const cur = readState().sort; writeState({ sort: cur === '-' + k ? k : '-' + k }); void renderTable(); },
        onOpen: (r, el) => void openLearner(r.registration, el) }));
    setBusy(host, false);
  } catch (e) { showError(host, e, () => void renderTable()); }
}
function sortName(s: string): string { const k = s.replace(/^-/, ''); return ({ risk: 'درجة الخطر', reg: 'التسجيل', cluster: 'العنقود', active_days: 'الأيام النشطة', last_access: 'آخر وصول', on_time: 'الالتزام' } as Record<string, string>)[k] ?? k; }
function riskCell(p: number, above: boolean, thr?: number): HTMLElement {
  return h('span', { class: 'riskcell' + (above ? ' riskcell--above' : ''), title: thr !== undefined ? `العتبة ${fmt(thr)}` : '' },
    h('span', { class: 'riskbar', 'aria-hidden': 'true' }, h('span', { class: 'riskbar__fill', style: `width:${p * 100}%` })),
    h('span', { class: 'num' }, fmt(p)), above ? h('span', { class: 'sr-only' }, ' (فوق العتبة)') : null);
}

function filterChips(): void {
  const st = readState();
  const chip = (label: string, on: boolean, fn: () => void) => h('button', { class: 'chipbtn' + (on ? ' chipbtn--on' : ''), type: 'button', 'aria-pressed': String(on), onclick: fn }, label);
  const set = (f: 'all' | 'above' | 'idle') => { writeState({ f, ...(f === 'all' ? { cl: null } : {}) }); filterChips(); if (clusters) renderClusters(clusters); void renderTable(); };
  mount($('#filters'),
    chip('الكل', st.f === 'all' && st.cl === null, () => set('all')),
    chip('≥ العتبة', st.f === 'above', () => set('above')),
    chip('بلا نشاط 14 يوماً', st.f === 'idle', () => set('idle')),
    st.cl !== null ? chip('عنقود: ' + (clusters?.clusters.find((c) => c.id === st.cl)?.label_ar ?? st.cl) + ' ×', true, () => { writeState({ cl: null }); filterChips(); if (clusters) renderClusters(clusters); void renderTable(); }) : null);
}

// ---------------------------------------------------------------- drawer
async function openLearner(reg: string, opener: HTMLElement | null): Promise<void> {
  const st = readState(); writeState({ r: reg });
  const op = opener ?? (document.querySelector(`tr[data-id="${reg}"]`) as HTMLElement | null) ?? document.body;
  drawer.open('ملف المتعلم ' + reg, op); showSkeleton(drawer.body, 3, 80);
  try {
    const d = await api.learner({ registration: reg, day: st.d as number });
    const body = drawer.body; setBusy(body, false);
    mount(body,
      h('p', {}, h('span', { class: 'cl' }, ClusterMarker(d.cluster.id), ' العنقود: ', d.cluster.label),
        d.risk ? h('span', {}, ` · درجة الخطر النسبية ${fmt(d.risk.score)} (قطع اليوم ${d.risk.cut_day}، العتبة ${fmt(d.risk.threshold)})`) : null),
      d.withdrawn_day !== null ? h('p', { class: 'note note--box' }, `انسحب هذا التسجيل في اليوم ${d.withdrawn_day}؛ يُعرض الملف حتى يوم الانسحاب.`) : null,
      d.risk ? h('div', {}, h('h3', { class: 'card__sub' }, 'عوامل الدرجة (w·z)'), DivergingBars('عوامل الدرجة', d.risk.factors.map((f) => ({ name: f.name, v: f.wz }))),
        h('p', { class: 'muted' }, 'الموجب يرفع الدرجة والسالب يخفضها؛ درجة نسبية غير معايَرة لترتيب الأولوية لا حكم.')) : null,
      h('h3', { class: 'card__sub' }, 'الملامح مقابل وسيط العرض'),
      h('div', { class: 'tablewrap' }, h('table', { class: 'table' }, h('thead', {}, h('tr', {}, ...['الملمح', 'القيمة', 'الوسيط', 'z'].map((x) => h('th', { scope: 'col' }, x)))),
        h('tbody', {}, ...d.profile.map((p) => h('tr', {}, h('td', {}, p.name), h('td', { class: 'num' }, fmt(p.value)), h('td', { class: 'num' }, fmt(p.median)), h('td', { class: 'num' }, (p.z > 0 ? '+' : '') + fmt(p.z, 1))))))),
      h('h3', { class: 'card__sub' }, 'توصياته الحالية (أفضل 3)'),
      h('ol', { class: 'recent' }, ...d.top_recs.map((r) => h('li', {}, typeAr(r.activity_type), ' ', bdi('#' + r.id_site), ' — ', r.reason))));
  } catch (e) { showError(drawer.body, e, () => void openLearner(reg, opener)); }
}

filterChips();
void boot().catch((e) => toast(String(e), 'error'));
