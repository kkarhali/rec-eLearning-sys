import { h, s } from '../dom.js';
import { CLUSTER_COLORS, CLUSTER_SHAPES, fmt, signed } from '../labels.js';

/** Collapsible data table used as a text alternative for every chart (WCAG 1.1.1). */
export function AltTable(caption: string, head: string[], rows: (string | number)[][]): HTMLElement {
  const t = h('table', { class: 'table table--alt' }, h('caption', { class: 'sr-only' }, caption),
    h('thead', {}, h('tr', {}, ...head.map((x) => h('th', { scope: 'col' }, x)))),
    h('tbody', {}, ...rows.map((r) => h('tr', {}, ...r.map((c) => h('td', {}, String(c)))))));
  return h('details', { class: 'alt' }, h('summary', {}, 'عرض البيانات كجدول'), h('div', { class: 'tablewrap' }, t));
}
function svgRoot(w: number, hgt: number, title: string, desc: string): SVGElement {
  const svg = s('svg', { viewBox: `0 0 ${w} ${hgt}`, class: 'chart', role: 'img', 'aria-labelledby': 'x' });
  const id = 'c' + Math.random().toString(36).slice(2, 8);
  svg.setAttribute('aria-labelledby', id + 't ' + id + 'd');
  svg.append(s('title', { id: id + 't' }, title), s('desc', { id: id + 'd' }, desc));
  return svg;
}

export interface BarDatum { label: string; value: number; flag?: boolean }
export interface BarOpts {
  title: string; desc: string; data: BarDatum[]; xLabel?: string; yLabel?: string;
  threshold?: { x: number; label: string }; // x is a position along the category axis in category units (0..n)
  color?: string; flagColor?: string;
}
/** Vertical bar chart (histogram). Flagged bars get a dark outline plus warm fill, never colour alone. */
export function SvgBarChart(o: BarOpts): HTMLElement {
  const W = 560, H = 280, m = { t: 28, r: 16, b: 56, l: 48 };
  const svg = svgRoot(W, H, o.title, o.desc);
  const max = Math.max(...o.data.map((d) => d.value), 1);
  const pw = W - m.l - m.r, ph = H - m.t - m.b, bw = pw / o.data.length;
  for (let i = 0; i <= 4; i++) {
    const y = m.t + ph - (ph * i) / 4;
    svg.append(s('line', { x1: m.l, x2: W - m.r, y1: y, y2: y, class: 'chart__grid' }),
      s('text', { x: m.l - 6, y: y + 4, class: 'chart__tick', 'text-anchor': 'end' }, fmt((max * i) / 4, 0)));
  }
  // RTL: first category on the right.
  o.data.forEach((d, i) => {
    const x = W - m.r - bw * (i + 1) + bw * 0.08, bh = (d.value / max) * ph;
    svg.append(s('rect', { x, y: m.t + ph - bh, width: bw * 0.84, height: bh, rx: 3, class: d.flag ? 'chart__bar chart__bar--flag' : 'chart__bar' },
      s('title', {}, `${d.label}: ${d.value}`)));
    svg.append(s('text', { x: x + bw * 0.42, y: H - m.b + 16, class: 'chart__tick', 'text-anchor': 'middle' }, d.label));
  });
  if (o.threshold) {
    const x = W - m.r - bw * o.threshold.x;
    svg.append(s('line', { x1: x, x2: x, y1: m.t - 6, y2: m.t + ph, class: 'chart__thr' }),
      s('text', { x: x - 6, y: m.t - 10, class: 'chart__thr-label', 'text-anchor': 'start' }, o.threshold.label));
  }
  if (o.xLabel) svg.append(s('text', { x: W / 2, y: H - 8, class: 'chart__axis', 'text-anchor': 'middle' }, o.xLabel));
  if (o.yLabel) svg.append(s('text', { x: W - 4, y: 14, class: 'chart__axis', 'text-anchor': 'end' }, o.yLabel));
  return h('div', { class: 'chartwrap' }, svg as unknown as Node,
    AltTable(o.title, ['الفئة', 'العدد'], o.data.map((d) => [d.label, d.value])));
}

/** Horizontal paired bars (e.g. catalogue share vs recommendation share by activity type). */
export function SvgHBars(title: string, desc: string, rows: { label: string; a: number; b: number }[], aName: string, bName: string): HTMLElement {
  const rowH = 34, W = 560, H = rows.length * rowH + 36, lw = 120;
  const svg = svgRoot(W, H, title, desc);
  rows.forEach((r, i) => {
    const y = 28 + i * rowH, full = W - lw - 56;
    svg.append(s('text', { x: W - 4, y: y + 12, class: 'chart__tick', 'text-anchor': 'end' }, r.label));
    const bar = (v: number, yy: number, cls: string) => {
      const w = Math.max(2, v * full * 2.2);
      svg.append(s('rect', { x: W - lw - w, y: yy, width: w, height: 10, rx: 2, class: cls }),
        s('text', { x: W - lw - w - 4, y: yy + 9, class: 'chart__tick', 'text-anchor': 'end' }, Math.round(v * 100) + '%'));
    };
    bar(r.a, y, 'chart__bar chart__bar--alt'); bar(r.b, y + 13, 'chart__bar');
  });
  svg.append(s('rect', { x: W - 12, y: 4, width: 10, height: 10, class: 'chart__bar chart__bar--alt' }), s('text', { x: W - 16, y: 13, class: 'chart__tick', 'text-anchor': 'end' }, aName),
    s('rect', { x: W - 150, y: 4, width: 10, height: 10, class: 'chart__bar' }), s('text', { x: W - 154, y: 13, class: 'chart__tick', 'text-anchor': 'end' }, bName));
  return h('div', { class: 'chartwrap' }, svg as unknown as Node,
    AltTable(title, ['النوع', aName, bName], rows.map((r) => [r.label, Math.round(r.a * 100) + '%', Math.round(r.b * 100) + '%'])));
}

export function shapePath(shape: string, cx: number, cy: number, r: number): SVGElement {
  switch (shape) {
    case 'square': return s('rect', { x: cx - r, y: cy - r, width: 2 * r, height: 2 * r });
    case 'triangle': return s('path', { d: `M${cx},${cy - r * 1.2} L${cx + r * 1.1},${cy + r * 0.9} L${cx - r * 1.1},${cy + r * 0.9} Z` });
    case 'diamond': return s('path', { d: `M${cx},${cy - r * 1.3} L${cx + r * 1.3},${cy} L${cx},${cy + r * 1.3} L${cx - r * 1.3},${cy} Z` });
    case 'cross': return s('path', { d: `M${cx - r},${cy - r * 0.4} h${r * 0.6} v-${r * 0.6} h${r * 0.8} v${r * 0.6} h${r * 0.6} v${r * 0.8} h-${r * 0.6} v${r * 0.6} h-${r * 0.8} v-${r * 0.6} h-${r * 0.6} Z` });
    case 'star': return s('path', { d: `M${cx},${cy - r * 1.3} L${cx + r * 0.4},${cy - r * 0.4} L${cx + r * 1.3},${cy - r * 0.3} L${cx + r * 0.6},${cy + r * 0.3} L${cx + r * 0.8},${cy + r * 1.2} L${cx},${cy + r * 0.7} L${cx - r * 0.8},${cy + r * 1.2} L${cx - r * 0.6},${cy + r * 0.3} L${cx - r * 1.3},${cy - r * 0.3} L${cx - r * 0.4},${cy - r * 0.4} Z` });
    default: return s('circle', { cx, cy, r });
  }
}
export function ClusterMarker(i: number, size = 14): SVGElement {
  const svg = s('svg', { width: size, height: size, viewBox: '0 0 14 14', 'aria-hidden': 'true', class: 'marker' });
  const p = shapePath(CLUSTER_SHAPES[i % 6], 7, 7, 4.6); p.setAttribute('fill', CLUSTER_COLORS[i % 6]); svg.append(p); return svg;
}

/** 2-D projection scatter: one colour AND one shape per cluster. */
export function ClusterScatter(title: string, pts: { x: number; y: number; cluster: number }[], selected: number | null): HTMLElement {
  const W = 420, H = 320, p = 20;
  const xs = pts.map((q) => q.x), ys = pts.map((q) => q.y);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const svg = svgRoot(W, H, title, `إسقاط PCA ثنائي الأبعاد لـ ${pts.length} متعلماً (عيّنة)؛ لكل عنقود لون وشكل مختلفان.`);
  svg.append(s('rect', { x: 0, y: 0, width: W, height: H, rx: 8, class: 'chart__bg' }));
  for (const q of pts) {
    const cx = W - p - ((q.x - x0) / (x1 - x0 || 1)) * (W - 2 * p), cy = H - p - ((q.y - y0) / (y1 - y0 || 1)) * (H - 2 * p);
    const el = shapePath(CLUSTER_SHAPES[q.cluster % 6], cx, cy, 4.2);
    el.setAttribute('fill', CLUSTER_COLORS[q.cluster % 6]); el.setAttribute('class', 'dot');
    el.setAttribute('opacity', selected === null || selected === q.cluster ? '0.9' : '0.18');
    svg.append(el);
  }
  const counts = new Map<number, number>(); pts.forEach((q) => counts.set(q.cluster, (counts.get(q.cluster) ?? 0) + 1));
  return h('div', { class: 'chartwrap' }, svg as unknown as Node,
    AltTable(title, ['العنقود', 'عدد النقاط في العيّنة'], [...counts].sort((a, b) => a[0] - b[0]).map(([c, n]) => [c, n])));
}

export interface DonutDatum { label: string; value: number }
export function SvgDonut(title: string, data: DonutDatum[], selected: number | null = null): HTMLElement {
  const R = 70, r = 44, cx = 90, cy = 90, total = data.reduce((a, d) => a + d.value, 0) || 1;
  const svg = svgRoot(180, 180, title, data.map((d) => `${d.label}: ${Math.round((d.value / total) * 100)}%`).join('، '));
  let a0 = -Math.PI / 2;
  data.forEach((d, i) => {
    const a1 = a0 - (d.value / total) * Math.PI * 2; // counter-clockwise: starts at the right, flows leftward (RTL)
    const big = Math.abs(a1 - a0) > Math.PI ? 1 : 0;
    const pt = (rad: number, a: number) => `${cx + rad * Math.cos(a)},${cy + rad * Math.sin(a)}`;
    const path = s('path', { d: `M${pt(R, a0)} A${R},${R} 0 ${big} 0 ${pt(R, a1)} L${pt(r, a1)} A${r},${r} 0 ${big} 1 ${pt(r, a0)} Z`,
      fill: CLUSTER_COLORS[i % 6], stroke: '#fff', 'stroke-width': 2, opacity: selected === null || selected === i ? 1 : 0.3 }, s('title', {}, `${d.label}: ${d.value}`));
    svg.append(path);
    a0 = a1;
  });
  svg.append(s('text', { x: cx, y: cy - 2, class: 'chart__center', 'text-anchor': 'middle' }, fmt(total, 0)), s('text', { x: cx, y: cy + 14, class: 'chart__tick', 'text-anchor': 'middle' }, 'متعلم'));
  return h('div', { class: 'chartwrap chartwrap--donut' }, svg as unknown as Node,
    AltTable(title, ['العنقود', 'العدد', 'النسبة'], data.map((d) => [d.label, d.value, Math.round((d.value / total) * 100) + '%'])));
}

/** Diverging horizontal bars for w*z risk factors (positive raises, negative lowers). */
export function DivergingBars(title: string, data: { name: string; v: number }[]): HTMLElement {
  const W = 360, rowH = 30, H = data.length * rowH + 8, mid = W / 2 + 40, scale = 60 / Math.max(...data.map((d) => Math.abs(d.v)), 1);
  const svg = svgRoot(W, H, title, 'عوامل درجة الخطر النسبية: الموجب يرفع الدرجة والسالب يخفضها.');
  svg.append(s('line', { x1: mid, x2: mid, y1: 0, y2: H, class: 'chart__axisline' }));
  data.forEach((d, i) => {
    const y = 4 + i * rowH, w = Math.abs(d.v) * scale;
    // RTL: positive (raises) extends to the left of the axis, negative to the right.
    const x = d.v >= 0 ? mid - w : mid;
    svg.append(s('rect', { x, y, width: Math.max(w, 2), height: 16, rx: 2, class: d.v >= 0 ? 'chart__bar chart__bar--flag' : 'chart__bar chart__bar--neg' }),
      s('text', { x: d.v >= 0 ? x - 4 : x + w + 4, y: y + 12, class: 'chart__tick', 'text-anchor': d.v >= 0 ? 'end' : 'start' }, signed(d.v, 1)),
      s('text', { x: W - 2, y: y + 12, class: 'chart__tick', 'text-anchor': 'end' }, d.name));
  });
  return h('div', { class: 'chartwrap' }, svg as unknown as Node);
}
