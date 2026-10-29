import { h } from '../dom.js';
import type { Evidence, ExplanationDetail } from '../types.js';
import { compColor, daysAr, fmt, learnersAr, lastDaysAr, typeAr } from '../labels.js';

export function evidenceText(e: Evidence | null): string | null {
  if (!e) return null;
  if (e.type === 'count') return e.scope === 'similar'
    ? `استخدمه ${learnersAr(e.n)} بنمط مشابه لنمطك ${lastDaysAr(e.window)}.`
    : `استخدمه ${learnersAr(e.n)} ${lastDaysAr(e.window)}.`;
  if (e.type === 'item') return `${typeAr(e.activity_type)} #${e.id_site} — زرتَه في ${daysAr(e.days)}، آخرها اليوم ${fmt(e.last_day, 0)}.`;
  return `${e.assessment_type} بعد ${daysAr(e.days_ahead)}.`;
}

/** Explanation panel: contributions (w_m * r~_m) sorted descending, plus the concrete evidence. */
export function WhyPanel(d: ExplanationDetail, onClose: () => void): HTMLElement {
  const max = Math.max(...d.components.map((c) => c.contribution), 0.0001);
  const list = h('ol', { class: 'why__list' });
  for (const c of d.components) {
    const ev = evidenceText(c.evidence);
    list.append(h('li', { class: 'why__item' },
      h('div', { class: 'why__row' }, h('strong', {}, h('bdi', {}, c.label ?? c.id)), h('span', { class: 'num' }, fmt(c.contribution, 2))),
      h('div', { class: 'why__track', role: 'img', 'aria-label': `المساهمة ${fmt(c.contribution, 2)} من ${fmt(d.relevance, 2)}` },
        h('span', { class: 'why__fill', style: `width:${(c.contribution / max) * 100}%;background:${compColor(c.id)}` })),
      h('p', { class: 'why__sentence' }, c.sentence),
      h('p', { class: 'why__formula' }, `الوزن ${fmt(c.weight, 2)} × الرتبة المطبَّعة ${fmt(c.r_tilde, 2)}`),
      ev ? h('p', { class: 'why__evidence' }, h('strong', {}, 'الدليل: '), ev) : null));
  }
  const root = h('section', { class: 'why', id: 'why-panel', tabindex: '-1', 'aria-labelledby': 'why-title' },
    h('div', { class: 'why__head' },
      h('h2', { id: 'why-title', class: 'why__title' }, 'لماذا ', typeAr(d.activity_type), ' ', h('bdi', {}, '#' + d.id_site), '؟'),
      h('button', { class: 'btn btn--icon', type: 'button', 'aria-label': 'إغلاق التفسير (Esc)', onclick: onClose }, '×')),
    h('p', { class: 'why__sum' }, 'الدرجة ', h('bdi', { class: 'num' }, fmt(d.relevance, 2)), ' = مجموع (الوزن × الرتبة المطبَّعة)'),
    list,
    ...(d.notes ?? []).map((n) => h('p', { class: 'note' }, n)));
  root.addEventListener('keydown', (e) => { if ((e as KeyboardEvent).key === 'Escape') { e.stopPropagation(); onClose(); } });
  return root;
}
