import { initApi } from './api.js';
import { $, h, mount, bdi } from './dom.js';
import { readState, writeState } from './state.js';
import { renderHeader, showMode } from './components/Header.js';
import { showError, toast } from './components/feedback.js';
import { DEFAULT_DAY, loadPresentations, makeScrubber, registrationPicker, firstPublished } from './controls.js';
import type { Presentation } from './types.js';

let list: Presentation[] = [];
async function boot(): Promise<void> {
  renderHeader('home');
  await initApi(); showMode();
  const host = $('#wizard');
  try { list = await loadPresentations(); } catch (e) { showError(host, e, () => location.reload()); return; }
  const st = readState();
  const pres = list.find((p) => p.id === st.p && p.status === 'published') ?? firstPublished(list);
  if (pres) writeState({ p: pres.id, d: st.d ?? DEFAULT_DAY });
  render();
}

function links(): HTMLElement {
  const st = readState(); const q = new URLSearchParams();
  if (st.p) q.set('p', st.p); if (st.d !== null) q.set('d', String(st.d));
  const qL = new URLSearchParams(q); if (st.r) qL.set('r', st.r);
  try { if (sessionStorage.getItem('mock') === '1') { q.set('mock', '1'); qL.set('mock', '1'); } } catch { /* ignore */ }
  return h('div', { class: 'cta' },
    h('a', { class: 'btn btn--primary btn--lg', href: 'learner.html?' + qL.toString() }, 'افتح واجهة المتعلم'),
    h('a', { class: 'btn btn--outline btn--lg', href: 'instructor.html?' + q.toString() }, 'افتح لوحة المدرّس'));
}

function render(): void {
  const st = readState(); const host = $('#wizard');
  const pres = list.find((p) => p.id === st.p) as Presentation;
  const presGroup = h('div', { class: 'choices', role: 'radiogroup', 'aria-labelledby': 'step1' });
  for (const p of list) {
    const locked = p.status === 'locked';
    const b = h('button', { class: 'choice' + (p.id === st.p ? ' choice--on' : ''), type: 'button', role: 'radio', 'aria-checked': String(p.id === st.p), disabled: locked,
      onclick: () => { writeState({ p: p.id, r: '' }); render(); } },
      h('strong', {}, bdi(p.id)), h('span', {}, p.label_ar ?? p.role), h('span', { class: 'muted' }, `${p.registrations} تسجيلاً · ${p.length_days} يوماً`),
      locked ? h('span', { class: 'badge badge--warn' }, 'مقفل حتى النشر') : null);
    presGroup.append(b);
  }
  const picker = registrationPicker(st.p, st.r, (reg) => { writeState({ r: reg }); mount($('#cta-slot'), links()); });
  const scr = makeScrubber(pres, st.d ?? DEFAULT_DAY, (d) => { writeState({ d }); mount($('#cta-slot'), links()); });
  mount(host,
    h('section', { class: 'step' }, h('h2', { class: 'h2', id: 'step1' }, h('span', { class: 'step__n' }, '1'), 'اختر العرض'), presGroup),
    h('section', { class: 'step' }, h('h2', { class: 'h2' }, h('span', { class: 'step__n' }, '2'), 'اختر التسجيل (للمتعلم)'), picker.el),
    h('section', { class: 'step' }, h('h2', { class: 'h2' }, h('span', { class: 'step__n' }, '3'), 'حرّك اليوم t'), scr.el),
    h('div', { id: 'cta-slot' }, links()));
  void picker.load().then((v) => { if (v && !readState().r) writeState({ r: v }); mount($('#cta-slot'), links()); });
}
void boot().catch((e) => toast(String(e), 'error'));
