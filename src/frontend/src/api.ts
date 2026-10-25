import type {
  ExplanationDetail, Health, InstructorLearnerDetail, InstructorLearnerRow, InstructorOverview, ClusterSet, LearnerHistory,
  LearnerQuery, Meta, Page, Presentation, RecommendationResponse, RegistrationSummary, ApiErrorBody, HistoryEvent, NextAssessment,
} from './types.js';

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: Record<string, unknown> = {}) { super(message); }
}

type Mode = 'live' | 'mock';
let mode: Mode | null = null;
export function apiMode(): Mode | null { return mode; }

function forcedMock(): boolean {
  try {
    const q = new URLSearchParams(location.search).get('mock');
    if (q === '1') { sessionStorage.setItem('mock', '1'); return true; }
    if (q === '0') { sessionStorage.removeItem('mock'); return false; }
    return sessionStorage.getItem('mock') === '1';
  } catch { return new URLSearchParams(location.search).get('mock') === '1'; }
}

/** Auto-detect: failed or non-JSON GET /api/health -> mock mode. */
export async function initApi(): Promise<Mode> {
  if (mode) return mode;
  if (forcedMock()) { mode = 'mock'; return mode; }
  try {
    const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), 2500);
    const r = await fetch('/api/health', { signal: ctl.signal, headers: { Accept: 'application/json' } });
    clearTimeout(t);
    const j = (await r.json()) as Health;
    mode = r.ok && j && typeof j.status === 'string' ? 'live' : 'mock';
  } catch { mode = 'mock'; }
  return mode;
}

function qs(params: Record<string, string | number | undefined | null>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== '') q.set(k, String(v));
  const s = q.toString(); return s ? '?' + s : '';
}

async function live<T>(path: string): Promise<T> {
  let r: Response;
  try { r = await fetch(path, { headers: { Accept: 'application/json' } }); }
  catch { throw new ApiError(0, 'network_error', 'تعذّر الاتصال بالخادم. تحقّق من الاتصال وأعد المحاولة.'); }
  if (!r.ok) {
    let body: ApiErrorBody | null = null;
    try { body = (await r.json()) as ApiErrorBody; } catch { /* not JSON */ }
    throw new ApiError(r.status, body?.error.code ?? 'http_' + r.status, body?.error.message ?? 'حدث خطأ غير متوقع.', body?.error.details ?? {});
  }
  return (await r.json()) as T;
}

// ---------------------------------------------------------------- mock layer
const cache = new Map<string, Promise<unknown>>();
function mockFile<T>(name: string): Promise<T> {
  let p = cache.get(name);
  if (!p) {
    p = fetch(new URL('mock/' + name, document.baseURI).toString()).then((r) => {
      if (!r.ok) throw new ApiError(r.status, 'mock_missing', 'ملف المحاكاة غير موجود: ' + name);
      return r.json();
    });
    cache.set(name, p);
  }
  return p as Promise<T>;
}
const norm = (reg: string): string => reg.replace(/^[A-Z]{3}_\d{4}[A-Z]-/, 'BBB_2013J-');
const relabel = (reg: string, pres: string): string => reg.replace(/^[A-Z]{3}_\d{4}[A-Z]/, pres);

async function mockCheckDay(presentation: string, day: number): Promise<{ pres: Presentation; snap: number }> {
  const list = await mockFile<Presentation[]>('presentations.json');
  const pres = list.find((x) => x.id === presentation);
  if (!pres) throw new ApiError(404, 'presentation_not_found', 'العرض غير موجود.');
  if (pres.status !== 'published') throw new ApiError(409, 'confirmatory_locked', 'عرض 2014 من مجموعة التأكيد؛ نتائجه في الرسالة ولا يُعرض في الواجهة.');
  if (day > pres.length_days || day < 0) throw new ApiError(422, 'day_out_of_range', 'اليوم خارج مدى العرض.', { max_day: pres.length_days });
  const first = pres.snapshots[0];
  if (day < first) throw new ApiError(422, 'day_before_first_snapshot', `لا لقطة قبل اليوم ${first}.`, { first_day: first });
  const snap = Math.max(...pres.snapshots.filter((s) => s <= day));
  return { pres, snap };
}
function modelCut(day: number, cuts: number[]): number { return Math.max(...cuts.filter((c) => c <= day), cuts[0]); }
function nextAssessment(pres: Presentation, day: number): NextAssessment | null {
  const a = (pres.assessments ?? []).filter((x) => x.day !== null && (x.day as number) >= day).sort((x, y) => (x.day as number) - (y.day as number))[0];
  return a ? { type: a.type, day: a.day as number, days_ahead: (a.day as number) - day } : null;
}
type HistFile = Record<string, { events: HistoryEvent[]; active_days: number }>;

const mock = {
  health: async (): Promise<Health> => mockFile('health.json'),
  meta: async (): Promise<Meta> => mockFile('meta.json'),
  presentations: async (): Promise<Presentation[]> => mockFile('presentations.json'),
  async registrations(p: { presentation: string; q?: string; limit?: number; offset?: number }): Promise<Page<RegistrationSummary>> {
    const f = await mockFile<Page<RegistrationSummary>>('registrations.json');
    const q = (p.q ?? '').trim();
    const items = f.items.filter((x) => !q || String(x.id_student).includes(q)).map((x) => ({ ...x, registration: relabel(x.registration, p.presentation) }));
    const off = p.offset ?? 0; const lim = p.limit ?? 100;
    return { items: items.slice(off, off + lim), total: items.length, limit: lim, offset: off };
  },
  async recommendations(p: { registration: string; day: number; k?: number; task?: 'A' | 'B' }): Promise<RecommendationResponse> {
    const all = await mockFile<Record<string, RecommendationResponse>>('recommendations.json');
    const base = all[norm(p.registration)];
    if (!base) throw new ApiError(404, 'registration_not_found', 'التسجيل غير موجود في هذا العرض.');
    const pid = p.registration.split('-')[0];
    const { pres, snap } = await mockCheckDay(pid, p.day);
    const hist = (await mockFile<HistFile>('history.json'))[norm(p.registration)];
    const out: RecommendationResponse = JSON.parse(JSON.stringify(base));
    out.registration = p.registration; out.presentation = pid; out.requested_day = p.day; out.snapshot_day = snap; out.task = p.task ?? 'A';
    out.provenance.model_cut = modelCut(p.day, pres.cutoffs ?? [28, 56, 112]);
    out.context = {
      week: Math.floor(p.day / 7) + 1, next_assessment: nextAssessment(pres, p.day),
      active_days_to_date: new Set((hist?.events ?? []).filter((e) => e.day <= p.day).map((e) => e.day)).size,
    };
    out.items = out.items.slice(0, p.k ?? 10);
    if (base.status === 'withdrawn') out.status = 'withdrawn';
    return out;
  },
  async explanation(p: { registration: string; id_site: number; day: number; task?: 'A' | 'B' }): Promise<ExplanationDetail> {
    const all = await mockFile<Record<string, ExplanationDetail>>('explanations.json');
    const e = all[`${norm(p.registration)}|${p.id_site}`];
    if (!e) throw new ApiError(404, 'explanation_not_available', 'التفسير غير متاح لهذا المورد (خارج أفضل 20 المخزّنة).');
    const { snap } = await mockCheckDay(p.registration.split('-')[0], p.day);
    return { ...JSON.parse(JSON.stringify(e)), registration: p.registration, day: p.day, snapshot_day: snap };
  },
  async history(p: { registration: string; day: number; window?: number }): Promise<LearnerHistory> {
    const h = (await mockFile<HistFile>('history.json'))[norm(p.registration)];
    if (!h) throw new ApiError(404, 'registration_not_found', 'التسجيل غير موجود في هذا العرض.');
    const win = p.window ?? 28;
    const ev = h.events.filter((e) => e.day <= p.day);
    const daily: { day: number; clicks: number }[] = [];
    for (let d = Math.max(0, p.day - win + 1); d <= p.day; d++) daily.push({ day: d, clicks: ev.filter((e) => e.day === d).reduce((a, e) => a + e.clicks, 0) });
    const recent = [...ev].sort((a, b) => b.day - a.day).slice(0, 3);
    return { registration: p.registration, day: p.day, window: win, active_days: new Set(ev.map((e) => e.day)).size, daily, recent,
      provenance: { run_id: 'mock', role: 'dev', model_cut: modelCut(p.day, [28, 56, 112]) } };
  },
  async overview(p: { presentation: string; day: number }): Promise<InstructorOverview> {
    const { snap } = await mockCheckDay(p.presentation, p.day);
    const o = JSON.parse(JSON.stringify(await mockFile<InstructorOverview>('overview.json'))) as InstructorOverview;
    o.presentation = p.presentation; o.requested_day = p.day; o.snapshot_day = snap;
    const pres = (await mockFile<Presentation[]>('presentations.json')).find((x) => x.id === p.presentation) as Presentation;
    const mc = modelCut(p.day, pres.cutoffs ?? [28, 56, 112]);
    o.provenance.model_cut = mc;
    if (o.risk) o.risk.cut_day = mc;
    return o;
  },
  async clusters(p: { presentation: string; day: number }): Promise<ClusterSet> {
    const { snap } = await mockCheckDay(p.presentation, p.day);
    return { ...(await mockFile<ClusterSet>('clusters.json')), presentation: p.presentation, requested_day: p.day, snapshot_day: snap };
  },
  async learners(p: LearnerQuery): Promise<Page<InstructorLearnerRow>> {
    await mockCheckDay(p.presentation, p.day);
    const f = await mockFile<Page<InstructorLearnerRow>>('learners.json');
    let rows = f.items.map((r) => ({ ...r, registration: relabel(r.registration, p.presentation) }));
    if (p.cluster !== undefined) rows = rows.filter((r) => r.cluster.id === p.cluster);
    if (p.risk === 'above') rows = rows.filter((r) => r.risk?.above_threshold);
    const sort = p.sort ?? '-risk'; const dir = sort.startsWith('-') ? -1 : 1; const key = sort.replace(/^-/, '');
    const val = (r: InstructorLearnerRow): number | string => key === 'risk' ? r.risk?.score ?? -1 : key === 'active_days' ? r.active_days
      : key === 'last_access' ? r.last_access_day ?? -1 : key === 'cluster' ? r.cluster.label : key === 'on_time' ? r.on_time : r.registration;
    rows.sort((a, b) => { const x = val(a), y = val(b); return (x < y ? -1 : x > y ? 1 : 0) * dir; });
    const off = p.offset ?? 0, lim = p.limit ?? 100;
    return { items: rows.slice(off, off + lim), total: rows.length, limit: lim, offset: off };
  },
  async learner(p: { registration: string; day: number }): Promise<InstructorLearnerDetail> {
    const d = (await mockFile<Record<string, InstructorLearnerDetail>>('learner-details.json'))[norm(p.registration)];
    if (!d) throw new ApiError(404, 'registration_not_found', 'التسجيل غير موجود في هذا العرض.');
    const { snap } = await mockCheckDay(p.registration.split('-')[0], p.day);
    return { ...JSON.parse(JSON.stringify(d)), registration: p.registration, day: p.day, snapshot_day: snap };
  },
};

// ---------------------------------------------------------------- public client
async function pick<T>(livePath: string, mockFn: () => Promise<T>): Promise<T> {
  await initApi();
  return mode === 'live' ? live<T>(livePath) : mockFn();
}
export const api = {
  health: () => pick<Health>('/api/health', mock.health),
  meta: () => pick<Meta>('/api/meta', mock.meta),
  presentations: () => pick<Presentation[]>('/api/presentations', mock.presentations),
  registrations: (p: { presentation: string; q?: string; limit?: number; offset?: number }) =>
    pick<Page<RegistrationSummary>>('/api/registrations' + qs(p), () => mock.registrations(p)),
  recommendations: (p: { registration: string; day: number; k?: number; task?: 'A' | 'B' }) =>
    pick<RecommendationResponse>('/api/recommendations' + qs({ k: 10, task: 'A', ...p }), () => mock.recommendations(p)),
  explanation: (p: { registration: string; id_site: number; day: number; task?: 'A' | 'B' }) =>
    pick<ExplanationDetail>(`/api/explanations/${encodeURIComponent(p.registration)}/${p.id_site}` + qs({ day: p.day, task: p.task ?? 'A' }), () => mock.explanation(p)),
  history: (p: { registration: string; day: number; window?: number }) =>
    pick<LearnerHistory>(`/api/learner/${encodeURIComponent(p.registration)}/history` + qs({ day: p.day, window: p.window ?? 28 }), () => mock.history(p)),
  overview: (p: { presentation: string; day: number }) => pick<InstructorOverview>('/api/instructor/overview' + qs(p), () => mock.overview(p)),
  clusters: (p: { presentation: string; day: number }) => pick<ClusterSet>('/api/instructor/clusters' + qs(p), () => mock.clusters(p)),
  learners: (p: LearnerQuery) => pick<Page<InstructorLearnerRow>>('/api/instructor/learners' + qs({ limit: 100, ...p }), () => mock.learners(p)),
  learner: (p: { registration: string; day: number }) =>
    pick<InstructorLearnerDetail>(`/api/instructor/learner/${encodeURIComponent(p.registration)}` + qs({ day: p.day }), () => mock.learner(p)),
};
