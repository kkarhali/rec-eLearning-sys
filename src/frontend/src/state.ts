// URL state: presentation (p), registration (r), day (d), task, cluster (cl), risk filter (f), sort (sort).
export interface AppState {
  p: string; r: string; d: number | null; task: 'A' | 'B'; cl: number | null; f: 'all' | 'above' | 'idle'; sort: string;
}
const KEYS = ['p', 'r', 'd', 'task', 'cl', 'f', 'sort'] as const;
export function readState(): AppState {
  const q = new URLSearchParams(location.search);
  const num = (k: string): number | null => { const v = q.get(k); if (v === null || v === '') return null; const n = Number(v); return Number.isFinite(n) ? Math.trunc(n) : null; };
  const f = q.get('f');
  return {
    p: q.get('p') ?? '', r: q.get('r') ?? '', d: num('d'),
    task: q.get('task') === 'B' ? 'B' : 'A', cl: num('cl'),
    f: f === 'above' || f === 'idle' ? f : 'all', sort: q.get('sort') ?? '-risk',
  };
}
export function writeState(patch: Partial<AppState>, push = false): AppState {
  const next = { ...readState(), ...patch };
  const q = new URLSearchParams(location.search);
  const def: Record<string, unknown> = { task: 'A', f: 'all', sort: '-risk' };
  for (const k of KEYS) {
    const v = next[k];
    if (v === null || v === '' || v === undefined || def[k] === v) q.delete(k); else q.set(k, String(v));
  }
  const url = location.pathname + (q.toString() ? '?' + q.toString() : '');
  try { (push ? history.pushState : history.replaceState).call(history, null, '', url); } catch { /* file:// etc. */ }
  return next;
}
/** Query string carrying the shared state (presentation, day, registration) to another page. */
export function carryQuery(keys: (keyof AppState)[] = ['p', 'd']): string {
  const st = readState(); const q = new URLSearchParams(location.search);
  const out = new URLSearchParams();
  for (const k of keys) { const v = st[k]; if (v !== null && v !== '') out.set(k, String(v)); }
  if (q.get('mock')) out.set('mock', q.get('mock') as string);
  const s = out.toString(); return s ? '?' + s : '';
}
