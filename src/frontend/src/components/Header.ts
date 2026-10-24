import { h } from '../dom.js';
import { carryQuery } from '../state.js';
import { apiMode } from '../api.js';

type Page = 'home' | 'learner' | 'instructor' | 'about';
export function renderHeader(active: Page): void {
  const host = document.getElementById('site-header');
  if (!host) return;
  const q = carryQuery(['p', 'd']);
  const link = (href: string, text: string, key: Page) =>
    h('a', { class: 'nav__link', href: href + (key === 'home' || key === 'about' ? '' : q), 'aria-current': active === key ? 'page' : null }, text);
  host.append(
    h('div', { class: 'header__inner' },
      h('a', { class: 'brand', href: 'index.html' }, 'موصي التعلّم'),
      h('nav', { class: 'nav', 'aria-label': 'التنقل الرئيسي' },
        link('index.html', 'الرئيسية', 'home'), link('learner.html', 'المتعلم', 'learner'),
        link('instructor.html', 'المدرّس', 'instructor'), link('about.html', 'عن النظام', 'about')),
      h('p', { class: 'replay-badge', id: 'replay-badge' }, 'إعادة تشغيل على بيانات تاريخية (OULAD) — لا جمع حي')));
}
/** Shows whether data comes from the live API or the bundled mock JSON. */
export function showMode(): void {
  const b = document.getElementById('replay-badge');
  if (b && apiMode() === 'mock') b.append(h('span', { class: 'mode-tag' }, ' · وضع المحاكاة'));
}
