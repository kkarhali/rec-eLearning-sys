import { h } from '../dom.js';
import type { AssessmentInfo } from '../types.js';

export interface ScrubberOpts {
  min: number; max: number; value: number; snapshots: number[]; cutoffs: number[]; assessments: AssessmentInfo[];
  onChange: (day: number) => void;
}
/**
 * DayScrubber: native range input (full keyboard + AT support) over a marks track,
 * plus a numeric field and snapshot step buttons. Day 0 sits at the right edge (RTL).
 */
export interface Scrubber { el: HTMLElement; set(day: number): void; value(): number }
export function DayScrubber(o: ScrubberOpts): Scrubber {
  let cur = o.value; let timer: number | undefined;
  const span = o.max - o.min || 1;
  const pos = (d: number) => `${((d - o.min) / span) * 100}%`;
  const snapOf = (d: number) => { const s = o.snapshots.filter((x) => x <= d); return s.length ? Math.max(...s) : null; };

  const range = h('input', { type: 'range', class: 'scrub__range', min: o.min, max: o.max, step: 1, value: cur, id: 'scrub-range', 'aria-label': 'اليوم t', 'aria-describedby': 'scrub-legend' }) as HTMLInputElement;
  const num = h('input', { type: 'number', class: 'field scrub__num', min: o.min, max: o.max, id: 'scrub-num', value: cur, inputmode: 'numeric' }) as HTMLInputElement;
  const badge = h('output', { class: 'scrub__badge', 'aria-live': 'polite', for: 'scrub-range' });
  const marks = h('div', { class: 'scrub__marks', 'aria-hidden': 'true' });
  for (const d of o.snapshots) marks.append(h('span', { class: 'mark mark--snap', style: `inset-inline-start:${pos(d)}` }));
  for (const d of o.cutoffs) marks.append(h('span', { class: 'mark mark--cut', style: `inset-inline-start:${pos(d)}`, title: `قطع النموذج ${d}` }));
  for (const a of o.assessments) if (a.day !== null && a.day >= o.min && a.day <= o.max)
    marks.append(h('span', { class: 'mark mark--assess', style: `inset-inline-start:${pos(a.day)}`, title: `${a.type} — اليوم ${a.day}` }));

  const label = () => {
    const s = snapOf(cur);
    badge.textContent = `اليوم ${cur}` + (s !== null && s !== cur ? ` · أقرب نقطة تنقل ${s}` : '');
    range.setAttribute('aria-valuetext', badge.textContent);
  };
  const commit = (d: number, immediate = false) => {
    d = Math.min(o.max, Math.max(o.min, Math.round(d) || o.min)); cur = d;
    range.value = String(d); num.value = String(d); label();
    window.clearTimeout(timer);
    if (immediate) o.onChange(d); else timer = window.setTimeout(() => o.onChange(d), 220);
  };
  range.addEventListener('input', () => commit(Number(range.value)));
  num.addEventListener('change', () => commit(Number(num.value), true));
  const step = (dir: 1 | -1) => {
    const t = dir === 1 ? o.snapshots.find((s) => s > cur) : [...o.snapshots].reverse().find((s) => s < (snapOf(cur) === cur ? cur : cur + 1));
    if (t !== undefined) commit(t, true);
  };
  const btn = (text: string, aria: string, dir: 1 | -1) => h('button', { class: 'btn btn--icon', type: 'button', 'aria-label': aria, onclick: () => step(dir) }, text);

  const el = h('div', { class: 'scrub', role: 'group', 'aria-label': 'اختيار اليوم t' },
    h('div', { class: 'scrub__top' },
      h('label', { class: 'scrub__lbl', for: 'scrub-num' }, 'اليوم t'),
      num, badge,
      h('span', { class: 'scrub__steps' }, btn('›', 'نقطة التنقل السابقة', -1), btn('‹', 'نقطة التنقل التالية', 1))),
    h('div', { class: 'scrub__track' }, marks, range),
    h('div', { class: 'scrub__axis', 'aria-hidden': 'true' }, h('span', {}, String(o.min)), h('span', {}, String(o.max))),
    h('p', { class: 'scrub__legend', id: 'scrub-legend' },
      h('span', { class: 'mark mark--snap mark--key' }), ' نقطة تنقل سريع ',
      h('span', { class: 'mark mark--cut mark--key' }), ' قطع النموذج ',
      h('span', { class: 'mark mark--assess mark--key' }), ' موعد تقييم · الأسهم تحرّك اليوم، Home وEnd للحدّين'));
  label();
  return { el, set: (d) => { cur = d; range.value = String(d); num.value = String(d); label(); }, value: () => cur };
}
