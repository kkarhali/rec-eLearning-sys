import { h, clear } from '../dom.js';

export interface Col<T> {
  key: string; header: string; sortable?: boolean; align?: 'num'; wrap?: boolean; headWrap?: boolean;
  cell: (row: T) => Node | string;
}
export interface TableOpts<T> {
  caption: string; cols: Col<T>[]; rows: T[]; rowId: (r: T) => string; sort: string;
  onSort: (key: string) => void; onOpen: (r: T, el: HTMLElement) => void; emptyText: string; activeId?: string;
}
/** Accessible table: sortable headers (aria-sort), rows open with click or Enter, horizontal scroll inside its wrapper. */
export function DataTable<T>(o: TableOpts<T>): HTMLElement {
  const dirKey = o.sort.replace(/^-/, ''), desc = o.sort.startsWith('-');
  const head = h('tr', {}, ...o.cols.map((c) => {
    const th = h('th', { scope: 'col', class: (c.align === 'num' ? 'num' : '') + (c.headWrap ? ' th--wrap' : ''), 'aria-sort': c.sortable ? (dirKey === c.key ? (desc ? 'descending' : 'ascending') : 'none') : null });
    if (c.sortable) th.append(h('button', { class: 'thbtn', type: 'button', onclick: () => o.onSort(c.key) }, c.header,
      h('span', { class: 'sortmark', 'aria-hidden': 'true' }, dirKey === c.key ? (desc ? ' ▼' : ' ▲') : ' ↕')));
    else th.append(c.header);
    return th;
  }));
  const body = h('tbody');
  if (!o.rows.length) body.append(h('tr', {}, h('td', { colspan: o.cols.length, class: 'table__empty' }, o.emptyText)));
  for (const r of o.rows) {
    const id = o.rowId(r);
    const tr = h('tr', { class: 'row' + (o.activeId === id ? ' row--active' : ''), tabindex: '0', 'data-id': id, 'aria-label': 'فتح ملف المتعلم ' + id },
      ...o.cols.map((c) => { const td = h('td', { class: (c.align === 'num' ? 'num ' : '') + (c.wrap ? 'cell--wrap' : '') }); td.append(c.cell(r)); return td; }));
    tr.addEventListener('click', () => o.onOpen(r, tr));
    tr.addEventListener('keydown', (e) => {
      const k = (e as KeyboardEvent).key;
      if (k === 'Enter' || k === ' ') { e.preventDefault(); o.onOpen(r, tr); }
      else if (k === 'ArrowDown') { e.preventDefault(); (tr.nextElementSibling as HTMLElement | null)?.focus(); }
      else if (k === 'ArrowUp') { e.preventDefault(); (tr.previousElementSibling as HTMLElement | null)?.focus(); }
    });
    body.append(tr);
  }
  const wrap = h('div', { class: 'tablewrap', tabindex: '0', role: 'region', 'aria-label': o.caption },
    h('table', { class: 'table' }, h('caption', { class: 'sr-only' }, o.caption), h('thead', {}, head), body));
  return wrap;
}
export function replace(host: HTMLElement, ...n: Node[]): void { clear(host); host.append(...n); }
