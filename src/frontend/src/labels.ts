// Arabic names for OULAD activity types (OULAD has no titles: name = type + id_site).
const TYPES: Record<string, string> = {
  oucontent: 'محتوى', quiz: 'اختبار قصير', forumng: 'منتدى', resource: 'مورد', subpage: 'صفحة فرعية',
  homepage: 'الصفحة الرئيسية', url: 'رابط', page: 'صفحة', glossary: 'مسرد', ouwiki: 'ويكي',
  oucollaborate: 'تعاون', questionnaire: 'استبيان', dataplus: 'بيانات', folder: 'مجلد',
};
export function typeAr(t: string): string { return TYPES[t] ?? t; }
export const NUM = new Intl.NumberFormat('en-US');
export function fmt(n: number, d = 2): string { return (n < 0 ? '\u200E' : '') + n.toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: 0 }); }
export function pct(n: number, d = 0): string { return (n * 100).toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: d }) + '%'; }
export const COMPONENT_COLORS: Record<string, string> = {
  recent_pop: '#0F766E', wrmf: '#1D4ED8', item_knn: '#7C3AED', sknn: '#6D28D9', cbf: '#0369A1', assess_prox: '#B45309', cluster_pop: '#BE185D', similar_pop: '#BE185D',
};
export function compColor(id: string): string { return COMPONENT_COLORS[id] ?? '#475569'; }
// Hybrid component numbers as in the thesis (1)-(7), used for pattern fills so colour is never the only cue.
export const COMPONENT_NO: Record<string, string> = { recent_pop: '1', wrmf: '2', item_knn: '3', sknn: '4', cbf: '5', assess_prox: '6', cluster_pop: '7', similar_pop: '7' };
export const CLUSTER_COLORS = ['#0F766E', '#1D4ED8', '#B45309', '#7C3AED', '#BE185D', '#0369A1'];
export const CLUSTER_SHAPES = ['circle', 'square', 'triangle', 'diamond', 'cross', 'star'] as const;
