import { h } from '../dom.js';
/** Side drawer: Esc closes it and focus returns to the opener (UC-07). */
export interface Drawer { el: HTMLElement; body: HTMLElement; open(title: string, opener: HTMLElement): void; close(): void; isOpen(): boolean }
export function Drawer(onClose: () => void): Drawer {
  let opener: HTMLElement | null = null;
  const title = h('h2', { id: 'drawer-title', class: 'drawer__title' });
  const body = h('div', { class: 'drawer__body' });
  const closeBtn = h('button', { class: 'btn btn--icon', type: 'button', 'aria-label': 'إغلاق (Esc)', onclick: () => api.close() }, '×');
  const el = h('aside', { class: 'drawer', role: 'dialog', 'aria-modal': 'false', 'aria-labelledby': 'drawer-title', hidden: true, tabindex: '-1' },
    h('div', { class: 'drawer__head' }, title, closeBtn), body);
  el.addEventListener('keydown', (e) => { if ((e as KeyboardEvent).key === 'Escape') api.close(); });
  const api: Drawer = {
    el, body,
    open(t, o) { opener = o; title.textContent = t; el.hidden = false; document.body.classList.add('has-drawer'); el.focus(); },
    close() { if (el.hidden) return; el.hidden = true; document.body.classList.remove('has-drawer'); onClose(); opener?.focus(); },
    isOpen: () => !el.hidden,
  };
  return api;
}
