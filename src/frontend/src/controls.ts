import { h, clear } from './dom.js';
import { api, ApiError, MODEL_CUTS } from './api.js';
import type { Presentation } from './types.js';
import { DayScrubber, type Scrubber } from './components/DayScrubber.js';
import { toast } from './components/feedback.js';

export const DEFAULT_DAY = 75;
export async function loadPresentations(): Promise<Presentation[]> { return api.presentations(); }
export function firstPublished(list: Presentation[]): Presentation | undefined { return list.find((p) => p.status === 'published'); }
export function presLabel(p: Presentation): string {
  return `${p.id} (${p.label_ar ?? p.role})` + (p.status === 'locked' ? ' — مقفل' : '');
}

export function presentationSelect(list: Presentation[], current: string, onChange: (id: string) => void, id = 'sel-pres'): HTMLElement {
  const sel = h('select', { class: 'field', id }) as HTMLSelectElement;
  for (const p of list) sel.append(h('option', { value: p.id, selected: p.id === current, disabled: p.status === 'locked' }, presLabel(p)));
  sel.addEventListener('change', () => onChange(sel.value));
  return h('div', { class: 'ctl' }, h('label', { for: id, class: 'ctl__lbl' }, 'العرض (presentation)'), sel,
    list.some((p) => p.status === 'locked') ? h('span', { class: 'ctl__hint' }, 'عروض 2014 من مجموعة التأكيد؛ نتائجها في الرسالة ولا تُعرض في الواجهة.') : null);
}

export function makeScrubber(pres: Presentation, day: number, onChange: (d: number) => void): Scrubber {
  const first = pres.snapshots[0] ?? 28;
  return DayScrubber({ min: 0, max: pres.length_days, value: day, snapshots: pres.snapshots, cutoffs: pres.cutoffs ?? MODEL_CUTS,
    assessments: pres.assessments ?? [], onChange: (d) => { void first; onChange(d); } });
}

/** Registration picker: search box (by id_student) + listbox. */
export function registrationPicker(presentation: string, current: string, onPick: (reg: string) => void): { el: HTMLElement; load(): Promise<string | null> } {
  const q = h('input', { class: 'field', type: 'search', id: 'reg-q', placeholder: 'ابحث برقم الطالب', inputmode: 'numeric', autocomplete: 'off' }) as HTMLInputElement;
  const sel = h('select', { class: 'field', id: 'sel-reg', 'aria-label': 'التسجيل' }) as HTMLSelectElement;
  let timer: number | undefined;
  async function load(): Promise<string | null> {
    try {
      const page = await api.registrations({ presentation, q: q.value, limit: 100 });
      clear(sel);
      for (const r of page.items) {
        const note = r.status === 'withdrawn' ? ' — منسحب' : r.status === 'no_history' ? ' — بلا نشاط سابق' : '';
        sel.append(h('option', { value: r.registration, selected: r.registration === current }, `${r.id_student}${note}`));
      }
      if (!page.items.length) sel.append(h('option', { value: '' }, 'لا نتائج'));
      return sel.value || null;
    } catch (e) { toast(e instanceof ApiError ? e.message : 'تعذّر تحميل التسجيلات', 'error'); return null; }
  }
  q.addEventListener('input', () => { window.clearTimeout(timer); timer = window.setTimeout(async () => { const v = await load(); if (v) onPick(v); }, 300); });
  sel.addEventListener('change', () => { if (sel.value) onPick(sel.value); });
  const el = h('div', { class: 'ctl' }, h('label', { for: 'sel-reg', class: 'ctl__lbl' }, 'التسجيل (registration)'), q, sel);
  return { el, load };
}
