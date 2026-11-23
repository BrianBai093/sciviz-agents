// sciviz host runtime: loads one agent-written visualization module and gives it a generic,
// library-agnostic interaction layer (selection, details-on-demand, highlighting, parameters).
// Used in two places: the headless verification gate (Playwright) and the web UI (sandboxed iframe).
//
// Contract for modules (see docs/PLAN.md §4.1):
//   export default function render(el, ctx) -> instance
//   ctx = { data, params, width, height, theme, host }
//   host = { select(items, {mode}), hover(item|null), emit(type, payload) }
//   instance (all optional, but update/setSelection/highlight are strongly expected):
//     update(params), setSelection(items), highlight(items), getState(), setState(state), destroy(), pick(x, y)
//   Data-bound marks carry data-id + data-type (single entity) or data-key (JSON grouping predicate).

const cfg = window.__SCIVIZ_CONFIG__ || {};
const state = (window.__sciviz = {
  ready: false, error: null, errors: [], log: [], selection: [], highlighted: [], instance: null,
  params: { ...(cfg.params || {}) },
});

window.addEventListener('error', (e) => state.errors.push(String(e.message || e)));
window.addEventListener('unhandledrejection', (e) =>
  state.errors.push('unhandled rejection: ' + String((e.reason && (e.reason.stack || e.reason)) || e)));

const root = document.getElementById('root');

function post(type, payload) {
  state.log.push({ type, payload, t: Math.round(performance.now()) });
  try { window.parent.postMessage({ source: 'sciviz-view', viewId: cfg.viewId, type, payload }, '*'); } catch (_) {}
}

function itemOf(el) {
  if (!el || !el.getAttribute) return null;
  const type = el.getAttribute('data-type');
  const label = el.getAttribute('data-label') || undefined;
  const id = el.getAttribute('data-id');
  if (id !== null) return { type: type || 'item', id, label };
  const key = el.getAttribute('data-key');
  if (key !== null) {
    let k; try { k = JSON.parse(key); } catch (_) { k = key; }
    return { type: type || 'group', key: k, label };
  }
  return null;
}

function normalize(items) {
  return (items || []).map((x) => (typeof x === 'string' ? { type: 'item', id: x } : x)).filter(Boolean);
}

function same(a, b) {
  if (!a || !b) return false;
  if (a.id !== undefined || b.id !== undefined) return String(a.id) === String(b.id);
  return JSON.stringify(a.key) === JSON.stringify(b.key);
}

function marks() { return Array.from(root.querySelectorAll('[data-id],[data-key]')); }

function applyClasses(items, cls) {
  const active = items.length > 0;
  for (const m of marks()) {
    const on = items.some((x) => same(x, itemOf(m)));
    m.classList.toggle(cls, on);
    m.classList.toggle('sv-dimmed', active && !on);
  }
}

function applySelection() {
  const inst = state.instance || {};
  if (typeof inst.setSelection === 'function') inst.setSelection(state.selection);
  else applyClasses(state.selection, 'sv-selected');
}

const host = {
  select(items, opts = {}) {
    const mode = opts.mode || 'replace';
    const incoming = normalize(items);
    let sel = state.selection.slice();
    if (mode === 'replace') sel = incoming;
    else if (mode === 'add') for (const it of incoming) { if (!sel.some((s) => same(s, it))) sel.push(it); }
    else if (mode === 'toggle') for (const it of incoming) {
      const i = sel.findIndex((s) => same(s, it));
      if (i >= 0) sel.splice(i, 1); else sel.push(it);
    }
    state.selection = sel;
    applySelection();
    post('select', { items: sel, mode });
  },
  hover(item) { post('hover', { item: item || null }); },
  emit(type, payload) { post('emit', { type, payload }); },
};

// ---- generic pointer handling (event delegation on data-bound marks; pick() for canvas) ----
function pickAt(ev) {
  const m = ev.target && ev.target.closest ? ev.target.closest('[data-id],[data-key]') : null;
  if (m && root.contains(m)) return itemOf(m);
  const inst = state.instance || {};
  if (typeof inst.pick === 'function') {
    const r = root.getBoundingClientRect();
    try { return inst.pick(ev.clientX - r.left, ev.clientY - r.top) || null; } catch (_) { return null; }
  }
  return null;
}

root.addEventListener('click', (ev) => {
  if (ev.defaultPrevented) return;
  const it = pickAt(ev);
  if (it) host.select([it], { mode: ev.shiftKey || ev.metaKey || ev.ctrlKey ? 'toggle' : 'replace' });
  else if (cfg.clearOnBackgroundClick !== false && state.selection.length) host.select([], { mode: 'replace' });
});

let lastHover = null;
root.addEventListener('mousemove', (ev) => {
  const it = pickAt(ev);
  const key = it ? JSON.stringify([it.id, it.key]) : null;
  if (key !== lastHover) { lastHover = key; host.hover(it); }
});
root.addEventListener('mouseleave', () => { if (lastHover !== null) { lastHover = null; host.hover(null); } });

// ---- commands (used by Playwright and by the parent UI via postMessage) ----
async function setParams(p) {
  state.params = { ...state.params, ...p };
  const inst = state.instance || {};
  if (typeof inst.update === 'function') await inst.update(state.params);
  else await mount();
  post('params', { params: state.params });
}
function setSelection(items) { state.selection = normalize(items); applySelection(); post('select', { items: state.selection, mode: 'external' }); }
function highlight(items) {
  state.highlighted = normalize(items);
  const inst = state.instance || {};
  if (typeof inst.highlight === 'function') inst.highlight(state.highlighted);
  else applyClasses(state.highlighted, 'sv-highlight');
  post('highlight', { items: state.highlighted });
}
function getState() { const inst = state.instance || {}; return typeof inst.getState === 'function' ? inst.getState() : null; }
function setState(s) { const inst = state.instance || {}; if (typeof inst.setState === 'function') inst.setState(s); }
Object.assign(state, { setParams, setSelection, highlight, getState, setState, marks: () => marks().length });

window.addEventListener('message', async (ev) => {
  const msg = ev.data || {};
  if (msg.target !== 'sciviz-view') return;
  try {
    if (msg.cmd === 'setParams') await setParams(msg.params || {});
    else if (msg.cmd === 'setSelection') setSelection(msg.items);
    else if (msg.cmd === 'highlight') highlight(msg.items);
    else if (msg.cmd === 'getState') post('state', { state: getState() });
    else if (msg.cmd === 'setState') setState(msg.state);
  } catch (e) { state.errors.push(String(e && (e.stack || e))); post('error', { message: String(e) }); }
});

// ---- mount ----
function applyTheme(theme) {
  const mode = cfg.mode || 'light';
  const colors = theme[mode] || theme.light;
  const css = document.documentElement.style;
  css.setProperty('--sv-font', theme.fontFamily);
  for (const [k, v] of Object.entries(colors)) css.setProperty('--sv-' + k.replace(/[A-Z]/g, (c) => '-' + c.toLowerCase()), v);
  css.setProperty('--sv-dim-opacity', colors.dimOpacity);
  return { ...theme, mode, colors };
}

let theme = null, data = null;
async function mount() {
  const inst = state.instance || {};
  if (typeof inst.destroy === 'function') { try { inst.destroy(); } catch (_) {} }
  root.innerHTML = '';
  const mod = await import(cfg.moduleUrl);
  const render = mod.default || mod.render;
  if (typeof render !== 'function') throw new Error('module must export a default render(el, ctx) function');
  state.instance = (await render(root, { data, params: state.params, width: cfg.width, height: cfg.height, theme, host })) || {};
}

function settle(maxMs = 8000, quietMs = 450) {
  return new Promise((resolve) => {
    let timer = null;
    const done = () => { obs.disconnect(); resolve(); };
    const obs = new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(done, quietMs); });
    obs.observe(root, { subtree: true, childList: true, attributes: true, characterData: true });
    timer = setTimeout(done, quietMs);
    setTimeout(done, maxMs);
  });
}

(async () => {
  try {
    root.style.width = cfg.width + 'px';
    root.style.height = cfg.height + 'px';
    theme = applyTheme(await (await fetch(cfg.themeUrl)).json());
    data = {};
    for (const [name, url] of Object.entries(cfg.dataUrls || {})) data[name] = await (await fetch(url)).json();
    await mount();
    await settle();
    state.ready = true;
    post('ready', { marks: marks().length });
  } catch (e) {
    state.error = String((e && (e.stack || e)) || e);
    const box = document.getElementById('sv-error');
    box.style.display = 'block';
    box.textContent = 'Visualization failed to render:\n' + state.error;
    post('error', { message: state.error });
  }
})();
