import { h } from '../dom.js';
import { NUM } from '../labels.js';

export interface PagerOpts {
  total: number; offset: number; limit: number; label: string; noun: (n: number) => string;
  onPage: (offset: number, which: 'prev' | 'next') => void;
}
/** «عرض a–b من N» (كتلة LTR معزولة داخل النص العربي). */
export function pageRange(total: number, offset: number, limit: number): string {
  const from = total ? offset + 1 : 0, to = Math.min(offset + limit, total);
  return '⁦' + NUM.format(from) + '–' + NUM.format(to) + '⁩';
}
/** Accessible pager (FR-32): native buttons in RTL order (السابق at the start/right, التالي at the end/left),
 *  disabled at the ends, «عرض a–b من N» and «الصفحة x من y». Keyboard: Tab + Enter/Space. */
export function Pager(o: PagerOpts): HTMLElement {
  const pages = Math.max(1, Math.ceil(o.total / o.limit));
  const page = Math.min(pages, Math.floor(o.offset / o.limit) + 1);
  const hasPrev = o.offset > 0, hasNext = o.offset + o.limit < o.total;
  const btn = (which: 'prev' | 'next', text: string, arrow: string, on: boolean, to: number) =>
    h('button', { class: 'btn pager__btn', type: 'button', 'data-page': which, disabled: !on, onclick: () => o.onPage(to, which) },
      which === 'prev' ? h('span', { 'aria-hidden': 'true' }, arrow + ' ') : null, text,
      which === 'next' ? h('span', { 'aria-hidden': 'true' }, ' ' + arrow) : null);
  return h('nav', { class: 'pager', 'aria-label': o.label },
    btn('prev', 'الصفحة السابقة', '→', hasPrev, Math.max(0, o.offset - o.limit)),
    h('p', { class: 'pager__status' }, `عرض ${pageRange(o.total, o.offset, o.limit)} من ${o.noun(o.total)}`,
      h('span', { class: 'pager__page' }, ` · الصفحة ${NUM.format(page)} من ${NUM.format(pages)}`)),
    btn('next', 'الصفحة التالية', '←', hasNext, o.offset + o.limit));
}
/** After a re-render: keep focus on the pressed button, or on its twin when it became disabled at an end. */
export function focusPager(host: ParentNode, which: 'prev' | 'next'): void {
  const want = host.querySelector<HTMLButtonElement>(`.pager__btn[data-page="${which}"]`);
  const other = host.querySelector<HTMLButtonElement>(`.pager__btn[data-page="${which === 'prev' ? 'next' : 'prev'}"]`);
  (want && !want.disabled ? want : other && !other.disabled ? other : null)?.focus();
}
