// Tiny DOM helpers (no framework).
type Attrs = Record<string, string | number | boolean | null | undefined | EventListener>;
export function h<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Attrs = {}, ...kids: (Node | string | null | undefined | false)[]): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (typeof v === 'function') el.addEventListener(k.replace(/^on/, '').toLowerCase(), v as EventListener);
    else if (k === 'class') el.className = String(v);
    else if (k === 'text') el.textContent = String(v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  for (const kid of kids) if (kid !== null && kid !== undefined && kid !== false) el.append(kid);
  return el;
}
const SVG_NS = 'http://www.w3.org/2000/svg';
export function s(tag: string, attrs: Record<string, string | number> = {}, ...kids: (Node | string)[]): SVGElement {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  for (const kid of kids) el.append(kid);
  return el;
}
export function clear(el: Element): void { while (el.firstChild) el.removeChild(el.firstChild); }
export function mount(el: Element, ...kids: (Node | string | null | undefined | false)[]): void { clear(el); for (const k of kids) if (k !== null && k !== undefined && k !== false) el.append(k); }
/** Latin identifiers are isolated with <bdi> to keep RTL order correct. */
export function bdi(text: string | number): HTMLElement { return h('bdi', {}, String(text)); }
export function $(sel: string, root: ParentNode = document): HTMLElement {
  const el = root.querySelector<HTMLElement>(sel);
  if (!el) throw new Error('missing element ' + sel);
  return el;
}
