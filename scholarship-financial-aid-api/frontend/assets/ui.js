export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) {
    if (name === 'class') node.className = value;
    else if (name.startsWith('on')) node.addEventListener(name.slice(2), value);
    else node.setAttribute(name, value);
  }
  node.append(...children);
  return node;
}

const paths = {
  book: '<path d="M12 6c-3-2-6-2.4-10-1v14c4-1.4 7-1 10 1 3-2 6-2.4 10-1V5c-4-1.4-7-1-10 1Zm0 0v14"/>',
  home: '<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
  file: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h4M9 12h6M9 15h6"/>',
  people: '<circle cx="9" cy="8" r="3.3"/><path d="M2 20v-2c0-6 14-6 14 0v2M16 5a3.4 3.4 0 0 1 0 6M18 14q4 1 4 6"/>',
  cap: '<path d="m2 9 10-5 10 5-10 5zM6 11v5q6 5 12 0v-5M22 9v6"/>',
  external: '<path d="M6 18 18 6M6 6h12v12"/>',
  arrow: '<path d="M4 12h15m-6-6 6 6-6 6"/>',
  chevron: '<path d="m9 6 6 6-6 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  key: '<circle cx="8" cy="8" r="5"/><path d="m12 12 8 8 2-2-2-2-1 1-2-2 1-1"/>',
  close: '<path d="m6 6 12 12M18 6 6 18"/>',
};

export function icon(name, size = 17) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  for (const [key, value] of Object.entries({
    viewBox: '0 0 24 24', width: size, height: size, fill: 'none', stroke: 'currentColor',
    'stroke-width': '1.65', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true',
  })) svg.setAttribute(key, value);
  svg.innerHTML = paths[name]; // Only fixed icon paths are used here.
  return svg;
}

const pesos = new Intl.NumberFormat('en-PH', {
  style: 'currency', currency: 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 2,
});
export const money = amount => amount == null ? '—' : pesos.format(amount);
export const date = value => value ? new Date(value + 'T00:00:00').toLocaleDateString('en-US', {
  month: 'short', day: 'numeric', year: 'numeric',
}) : '—';
export const status = value => el('span', {class: 'status ' + value.toLowerCase()}, value);
