import { h } from '../dom.js';
export function KpiCard(label: string, value: string, hint?: string, id?: string): HTMLElement {
  return h('div', { class: 'kpi', role: 'group', 'aria-labelledby': id ? id + '-l' : null },
    h('span', { class: 'kpi__label', id: id ? id + '-l' : null }, label),
    h('strong', { class: 'kpi__value num' }, value), hint ? h('span', { class: 'kpi__hint' }, hint) : null);
}
