// Arabic names for OULAD activity types (OULAD has no titles: name = type + id_site).
const TYPES: Record<string, string> = {
  oucontent: 'محتوى', quiz: 'اختبار قصير', forumng: 'منتدى', resource: 'مورد', subpage: 'صفحة فرعية',
  homepage: 'الصفحة الرئيسية', url: 'رابط', page: 'صفحة', glossary: 'مسرد', ouwiki: 'ويكي',
  oucollaborate: 'تعاون', questionnaire: 'استبيان', dataplus: 'بيانات', folder: 'مجلد',
};
export function typeAr(t: string): string { return TYPES[t] ?? t; }
export const NUM = new Intl.NumberFormat('en-US');
/** رقم بعلامة طرح حقيقية (U+2212) وبلا «-0»؛ بلا عزل اتجاهي (للتركيب داخل نطاق أو إشارة). */
function rawNum(n: number, d: number): string {
  const s = n.toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: 0 });
  if (/^-0(\.0*)?$/.test(s)) return s.slice(1);
  return s.startsWith('-') ? '\u2212' + s.slice(1) : s;
}
/** رقم مفرد؛ السالب معزول (LRI…PDI) فلا تنقلب علامته ولا تلتصق بما حوله في سياق RTL. */
export function fmt(n: number, d = 2): string { const s = rawNum(n, d); return s.startsWith('\u2212') ? '\u2066' + s + '\u2069' : s; }
/** نطاق «a – b» كتلة LTR واحدة، مثل «−18 – −8». */
export function range(a: number, b: number, d = 2): string { return '\u2066' + rawNum(a, d) + ' – ' + rawNum(b, d) + '\u2069'; }
export function pct(n: number, d = 0): string { return (n * 100).toLocaleString('en-US', { maximumFractionDigits: d, minimumFractionDigits: d }) + '%'; }
export const COMPONENT_COLORS: Record<string, string> = {
  recent_pop: '#0F766E', wrmf: '#1D4ED8', item_knn: '#7C3AED', sknn: '#6D28D9', cbf: '#0369A1', assess_prox: '#B45309', cluster_pop: '#BE185D', similar_pop: '#BE185D',
};
export function compColor(id: string): string { return COMPONENT_COLORS[id] ?? '#475569'; }
// Hybrid component numbers as in the thesis (1)-(7), used for pattern fills so colour is never the only cue.
export const COMPONENT_NO: Record<string, string> = { recent_pop: '1', wrmf: '2', item_knn: '3', sknn: '4', cbf: '5', assess_prox: '6', cluster_pop: '7', similar_pop: '7' };
export const CLUSTER_COLORS = ['#0F766E', '#1D4ED8', '#B45309', '#7C3AED', '#BE185D', '#0369A1'];
export const CLUSTER_SHAPES = ['circle', 'square', 'triangle', 'diamond', 'cross', 'star'] as const;

/** صيغة العدد والمعدود بالعربية: 1 «يوم واحد»، 2 «يومان»، 3–10 «أيام»، 11+ «يوماً» (والمئات والعشرات على الباقي من 100). */
export function countAr(n: number, one: string, two: string, few: string, many: string, oneWord = true): string {
  const a = Math.abs(Math.trunc(n)), m = a % 100;
  const num = NUM.format(a);
  if (a === 1) return oneWord ? `${one} واحد` : one;
  if (a === 2) return two;
  if (m >= 3 && m <= 10) return `${num} ${few}`;
  if (a === 0) return `0 ${few}`;
  if (a >= 100 && a % 100 === 0) return `${num} ${one}`;   // المئات والآلاف الصحيحة: مفرد بلا تنوين («100 متعلم»)
  return `${num} ${many}`;
}
export const daysAr = (n: number): string => countAr(n, 'يوم', 'يومان', 'أيام', 'يوماً');
export const learnersAr = (n: number): string => countAr(n, 'متعلم', 'متعلمان', 'متعلمين', 'متعلماً');
export const itemsAr = (n: number): string => countAr(n, 'مورد', 'موردان', 'موارد', 'مورداً');
export const registrationsAr = (n: number): string => countAr(n, 'تسجيل', 'تسجيلان', 'تسجيلات', 'تسجيلاً');
/** «في آخر 3 أيام» (ظرف مضاف إلى عدد). */
export const lastDaysAr = (n: number): string => (n === 1 ? 'في آخر يوم' : n === 2 ? 'في آخر يومين' : `في آخر ${daysAr(n)}`);
/** درجة الخطر: دائماً بخانتين (0.98) لا تُقرأ نسبة ولا تُقصّ. */
export function score2(x: number): string { return x.toFixed(2); }

/** عدد بإشارة صريحة داخل نص عربي: LRM يمنع قلب «+» إلى يمين الرقم في سياق RTL. */
export function signed(n: number, d = 1): string { return '\u2066' + (n > 0 ? '+' : '') + rawNum(n, d) + '\u2069'; }
