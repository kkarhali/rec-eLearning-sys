import { h, clear } from '../dom.js';
import { ApiError } from '../api.js';

/** Toast: error/info messages announced politely to screen readers. */
let region: HTMLElement | null = null;
export function toast(message: string, kind: 'error' | 'info' = 'info', ms = 6000): void {
  if (!region) { region = h('div', { class: 'toasts', role: 'status', 'aria-live': 'polite' }); document.body.append(region); }
  const t = h('div', { class: 'toast toast--' + kind }, h('span', {}, message),
    h('button', { class: 'btn btn--icon', type: 'button', 'aria-label': 'إغلاق الرسالة', onclick: () => t.remove() }, '×'));
  region.append(t);
  setTimeout(() => t.remove(), ms);
}

export function emptyState(title: string, hint?: string): HTMLElement {
  const el = h('div', { class: 'empty' }, h('p', { class: 'empty__title' }, title), hint ? h('p', { class: 'empty__hint' }, hint) : null);
  return el;
}

export function errorBox(e: unknown, retry?: () => void): HTMLElement {
  const err = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'حدث خطأ غير متوقع.');
  return h('div', { class: 'errorbox', role: 'alert' },
    h('p', { class: 'errorbox__msg' }, err.message),
    h('p', { class: 'errorbox__code' }, 'رمز الخطأ: ', h('bdi', {}, err.code)),
    retry ? h('button', { class: 'btn', type: 'button', onclick: retry }, 'إعادة المحاولة') : null);
}

/** Skeleton placeholders (aria-busy is set on the container by the caller). */
export function skeleton(rows = 3, height = 72): HTMLElement {
  const wrap = h('div', { class: 'skeletons', 'aria-hidden': 'true' });
  for (let i = 0; i < rows; i++) wrap.append(h('div', { class: 'skeleton', style: `height:${height}px` }));
  return wrap;
}
export function setBusy(el: HTMLElement, busy: boolean): void { el.setAttribute('aria-busy', String(busy)); }
export function showSkeleton(el: HTMLElement, rows = 3, height = 72): void {
  clear(el); setBusy(el, true); el.append(skeleton(rows, height));
}
export function showError(el: HTMLElement, e: unknown, retry?: () => void): void {
  clear(el); setBusy(el, false); el.append(errorBox(e, retry));
}
