import { h } from '../dom.js';
import type { ComponentInfo, RecItem } from '../types.js';
import { compColor, fmt, typeAr } from '../labels.js';

export interface RecCardOpts { item: RecItem; comps: ComponentInfo[]; active: boolean; onWhy: (btn: HTMLButtonElement) => void }
export function RecCard(o: RecCardOpts): HTMLElement {
  const { item, comps } = o;
  const total = Object.values(item.contributions).reduce((a, b) => a + b, 0) || 1;
  const bar = h('div', { class: 'contribbar', role: 'img',
    'aria-label': 'مساهمة المكوّنات: ' + comps.filter((c) => item.contributions[c.id]).map((c) => `${c.label} ${fmt((item.contributions[c.id] / total) * 100, 0)}%`).join('، ') });
  for (const c of comps) {
    const v = item.contributions[c.id]; if (!v) continue;
    bar.append(h('span', { class: 'contribbar__seg', style: `flex:${v};background:${compColor(c.id)}`, title: `${c.label}: ${fmt(v, 3)}` }));
  }
  const btn = h('button', { class: 'btn ' + (o.active ? 'btn--primary' : 'btn--outline'), type: 'button', 'aria-expanded': String(o.active), 'aria-controls': 'why-panel',
    'aria-label': `لماذا التوصية ${item.rank}؟ المورد ${item.id_site}`, 'data-site': item.id_site }, 'لماذا؟') as HTMLButtonElement;
  btn.addEventListener('click', () => o.onWhy(btn));
  return h('li', { class: 'rec' + (o.active ? ' rec--active' : '') },
    h('span', { class: 'rec__rank', 'aria-label': 'الرتبة ' + item.rank }, String(item.rank)),
    h('div', { class: 'rec__body' },
      h('div', { class: 'rec__head' },
        h('span', { class: 'chip' }, typeAr(item.activity_type), ' ', h('bdi', {}, `(${item.activity_type})`)),
        h('span', { class: 'rec__id' }, h('bdi', {}, '#' + item.id_site)),
        h('span', { class: 'rec__score', title: 'الدرجة المدمجة للهجين المجمَّد' }, 'الدرجة ', h('bdi', { class: 'num' }, fmt(item.relevance, 2)))),
      h('p', { class: 'rec__reason' }, item.reason + (item.reason_secondary ? ' · ' + item.reason_secondary : ''))),
    h('div', { class: 'rec__side' }, h('span', { class: 'rec__bar-label' }, 'مساهمة المكوّنات'), bar), btn);
}

export function CompLegend(comps: ComponentInfo[]): HTMLElement {
  const ul = h('ul', { class: 'legend', 'aria-label': 'مفتاح المكوّنات' });
  for (const c of comps) ul.append(h('li', {}, h('span', { class: 'legend__sw', style: `background:${compColor(c.id)}`, 'aria-hidden': 'true' }), h('bdi', {}, c.label), ` (${fmt(c.weight, 2)})`));
  return ul;
}
