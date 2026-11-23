const NS = 'http://www.w3.org/2000/svg';
const years = [2021, 2022, 2023, 2024];
const num = n => Number(n).toLocaleString('en-US');
const signed = (n, digits = 1) => `${n < 0 ? '−' : n > 0 ? '+' : ''}${Math.abs(n).toLocaleString('en-US', {minimumFractionDigits: digits, maximumFractionDigits: digits})}`;
const pct = n => `${signed(n)}%`;
function node(parent, tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  parent.append(n); return n;
}
function svg(parent, tag, attrs) {
  const n = document.createElementNS(NS, tag);
  for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,v);
  parent.append(n); return n;
}
function mark(n, type, id, label) {
  n.setAttribute('data-type',type);
  n.setAttribute('data-id',id);
  n.setAttribute('data-label',label);
  n.setAttribute('aria-label',label);
}

export default function render(el, ctx) {
  const { data, theme, host, width, height } = ctx;
  const colors = theme.colors || {};
  const fields = [...data.fields].sort((a,b) => a.rank-b.rank);
  const annual = new Map(fields.map(f => [String(f.field_id), data.annual.filter(a => String(a.field_id) === String(f.field_id)).sort((a,b) => a.publication_year-b.publication_year)]));
  const latest = data.context.find(r => r.publication_year === 2024);
  const root = node(el,'section','ct-root');
  root.setAttribute('aria-label','Columbia publication trends');
  const swatches = {bg: colors.background || '#fff', surface: colors.surface || '#f5f7fa', ink: colors.text || '#182335', muted: colors.textMuted || '#546578', grid: colors.grid || '#d5dee7', accent: colors.accent || '#2768aa', high: colors.highlight || colors.accent || '#2768aa'};
  Object.entries(swatches).forEach(([k,v]) => root.style.setProperty('--'+k,v));
  root.style.color = 'var(--ink)';
  root.style.fontFamily = theme.fontFamily || 'system-ui, sans-serif';
  root.style.setProperty('--ui', `${Math.max(12, Math.min(15, Number.parseFloat(theme.fontSize) || 13))}px`);
  const style = node(root,'style');
  style.textContent = `
    .ct-root{height:100%;width:100%;position:relative;background:var(--bg);font-size:var(--ui);box-sizing:border-box;font-variant-numeric:tabular-nums;line-height:1.25}
    .ct-root *{box-sizing:border-box}
    .ct-scroll{height:100%;overflow:auto;padding:17px var(--pad) 12px}
    .ct-kicker{color:var(--muted);font-size:10px;font-weight:750;letter-spacing:.13em;text-transform:uppercase;margin:0 0 5px}
    .ct-title{margin:0;color:var(--ink);font-weight:740;letter-spacing:-.025em;font-size:clamp(20px,3.1vw,31px);line-height:1.1}
    .ct-context{font-size:.96em;margin:7px 0 11px;color:var(--muted);line-height:1.4}
    .ct-context strong{color:var(--ink)}
    .ct-guide{margin:0 0 7px;color:var(--muted);font-size:.9em;line-height:1.35}
    .ct-guide strong{color:var(--ink)}
    .ct-matrix{min-width:var(--matrix-min);width:100%}
    .ct-head,.ct-row{display:grid;grid-template-columns:var(--field) minmax(115px,1fr) var(--counts) var(--change);align-items:center;column-gap:var(--gap)}
    .ct-head{border-bottom:1px solid var(--grid);color:var(--muted);font-size:.85em;font-weight:700;min-height:23px;padding-bottom:5px}
    .ct-years{display:flex;justify-content:space-between;padding:0 var(--inset)}
    .ct-years span{width:0;display:flex;justify-content:center;white-space:nowrap}
    .ct-row{min-height:var(--row);border-bottom:1px solid color-mix(in srgb,var(--grid),transparent 30%);position:relative}
    .ct-row[data-keyrow='true']{background:color-mix(in srgb,var(--accent) 5%,var(--bg))}
    .ct-row.ct-hot{background:color-mix(in srgb,var(--accent) 11%,var(--bg))}
    .ct-row.ct-em{background:color-mix(in srgb,var(--high) 13%,var(--bg));box-shadow:inset 3px 0 var(--accent)}
    .ct-row.ct-dim .ct-series{opacity:.25}
    .ct-name{cursor:pointer;width:100%;text-align:left;display:grid;grid-template-columns:23px 1fr;align-items:center;gap:4px;border:0;background:none;color:var(--ink);padding:2px 1px;font:inherit;font-weight:600;line-height:1.12}
    .ct-name:hover .ct-full{text-decoration:underline;text-underline-offset:2px}
    .ct-rank{color:var(--muted);font-size:.8em;text-align:center;font-weight:500}
    .ct-key .ct-name,.ct-key .ct-delta{font-weight:760}
    .ct-key .ct-series{color:var(--accent)}
    .ct-track{display:block;width:100%;height:var(--row);overflow:visible}
    .ct-series{color:var(--ink);transition:opacity .12s}
    .ct-focusbox{fill:transparent;stroke:transparent;cursor:pointer}
    .ct-point:hover .ct-focusbox,.ct-point:focus-visible .ct-focusbox{stroke:var(--accent);stroke-width:1.6;fill:color-mix(in srgb,var(--accent) 9%,transparent)}
    .ct-point.ct-picked .ct-dot{stroke:var(--accent);stroke-width:2.4;r:4.5px}
    .ct-point{outline:none}
    .ct-name:focus-visible{outline:2px solid var(--accent);outline-offset:-2px;border-radius:3px}
    .ct-count,.ct-delta{text-align:right;white-space:nowrap}
    .ct-count{color:var(--ink);font-size:.9em}
    .ct-delta{padding-right:4px;font-size:.96em;font-weight:600}
    .ct-foot{margin:8px 0 0;color:var(--muted);font-size:.84em;line-height:1.35}
    .ct-tip{position:absolute;z-index:2;pointer-events:none;width:max-content;max-width:min(272px,95%);background:var(--bg);color:var(--ink);border:1px solid var(--grid);border-radius:7px;box-shadow:0 4px 18px #0003;padding:9px 11px;font-size:.93em;line-height:1.4}
    .ct-tip strong{display:block;margin-bottom:3px}
    .ct-tip div:last-child{color:var(--muted)}
  `;
  const compact = width < 720;
  root.style.setProperty('--pad', compact ? '12px' : '22px');
  root.style.setProperty('--matrix-min', '480px');
  root.style.setProperty('--field', compact ? 'minmax(148px, 32%)' : 'minmax(223px, 28%)');
  root.style.setProperty('--counts', compact ? '97px' : '119px');
  root.style.setProperty('--change', compact ? '64px' : '93px');
  root.style.setProperty('--gap', compact ? '7px' : '15px');
  const inset = 19;
  root.style.setProperty('--inset', inset+'px');
  const rowH = Math.max(compact ? 37 : 35, Math.min(53, Math.floor((height-(compact ? 188 : 172))/10)));
  root.style.setProperty('--row',rowH+'px');
  const scroll = node(root,'div','ct-scroll');
  node(scroll,'p','ct-kicker','Columbia University · OpenAlex works');
  node(scroll,'h1','ct-title','How Columbia’s largest fields changed');
  const context = node(scroll,'p','ct-context');
  context.append('University-wide output rebounded to ');
  node(context,'strong',null,`${num(latest.snapshot_work_count)} works in 2024`);
  context.append(`, up ${pct(latest.snapshot_yoy_pct_change).replace('+','')} from 2023 but ${Math.abs(latest.snapshot_pct_change_vs_2021).toFixed(1)}% below 2021.`);
  const guide = node(scroll,'p','ct-guide');
  const matrix = node(scroll,'div','ct-matrix');
  const head = node(matrix,'div','ct-head');
  node(head,'span',null,'Field · 4-year rank');
  const yearHeader = node(head,'div','ct-years');
  years.forEach(y => node(yearHeader,'span',null,y));
  node(head,'span','ct-count','2021 → 2024 works');
  const changeHeader = node(head,'span','ct-delta','% change');
  changeHeader.title = 'Percent change from 2021 to 2024';
  const foot = node(scroll,'p','ct-foot');
  node(foot,'strong',null,'Source: OpenAlex · ');
  foot.append('Columbia University (I78577930) and defined child institutions. Fixed top 10 by total works in 2021–2024. Each work is counted once by primary topic field; all work types included.');
  const tip = node(root,'div','ct-tip');
  tip.hidden = true;
  tip.setAttribute('role','tooltip');
  const rows = [];
  let selection = [], highlights = [], currentMode = '', hovered = null;
  function selected(id, itemList, year) {
    return itemList.some(i => i && ((i.type === 'field' && String(i.id) === id && year === undefined) || (i.type === 'field_year' && (year === undefined ? String(i.id).startsWith(id+':') : String(i.id) === `${id}:${year}`))));
  }
  function emphasize() {
    const all = [...selection,...highlights];
    const active = rows.some(r => selected(r.id,all));
    for (const r of rows) {
      const match = selected(r.id,all);
      r.row.classList.toggle('ct-em',match);
      r.row.classList.toggle('ct-dim',active && !match);
      r.name.setAttribute('aria-pressed',String(selected(r.id,selection)));
      r.points.forEach(([g,a]) => g.classList.toggle('ct-picked',selected(r.id,all,a.publication_year)));
    }
  }
  function showTip(row, anchor, label, lines) {
    if (hovered && hovered !== row) hovered.classList.remove('ct-hot');
    row.classList.add('ct-hot'); hovered = row;
    tip.replaceChildren(); node(tip,'strong',null,label);
    for (const line of lines) node(tip,'div',null,line);
    tip.hidden = false;
    const r = root.getBoundingClientRect(), a = anchor.getBoundingClientRect();
    const x = a.left-r.left + a.width/2;
    const above = a.top-r.top-tip.offsetHeight-6;
    tip.style.left = `${Math.max(4,Math.min(r.width-tip.offsetWidth-4,x+10))}px`;
    tip.style.top = `${above < 4 ? Math.min(r.height-tip.offsetHeight-4,a.bottom-r.top+6) : above}px`;
  }
  function hideTip() {
    tip.hidden = true;
    if (hovered) hovered.classList.remove('ct-hot');
    hovered = null;
  }
  function bind(node, row, item, lines) {
    const show = () => showTip(row,node,item.label,lines());
    node.addEventListener('pointerenter',show);
    node.addEventListener('pointerleave',hideTip);
    node.addEventListener('focus',show);
    node.addEventListener('blur',hideTip);
    node.addEventListener('keydown',e => {
      if (e.key === 'Escape') { hideTip(); return; }
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        host.select([item], {mode:e.shiftKey ? 'toggle' : 'replace'});
        show();
      }
    });
  }
  for (const f of fields) {
    const id = String(f.field_id), values = annual.get(id);
    const keyrow = Math.abs(f.pct_change_2021_to_2024) >= 20;
    const row = node(matrix,'div',keyrow ? 'ct-row ct-key' : 'ct-row');
    row.dataset.keyrow = String(keyrow);
    const name = node(row,'button','ct-name'); name.type='button';
    mark(name,'field',id,f.field_name);
    node(name,'span','ct-rank',f.rank);
    node(name,'span','ct-full',f.field_name);
    bind(name,row,{type:'field',id,label:f.field_name},() => [
      `Rank ${f.rank} · ${num(f.total_2021_2024)} works across four years`,
      ...values.map(a => `${a.publication_year}: ${num(a.work_count)} works`),
      `2021 → 2024: ${signed(f.change_2021_to_2024,0)} works (${pct(f.pct_change_2021_to_2024)})`
    ]);
    const chart = svg(row,'svg',{class:'ct-track',height:rowH,'aria-label':`${f.field_name}: annual trend`});
    const grid = svg(chart,'g',{'aria-hidden':'true'});
    const series = svg(chart,'g',{class:'ct-series'});
    node(row,'span','ct-count',`${num(f.works_2021)} → ${num(f.works_2024)}`);
    node(row,'span','ct-delta',pct(f.pct_change_2021_to_2024));
    rows.push({id,values,row,name,chart,grid,series,points:[]});
  }
  function draw() {
    hideTip();
    const counts = currentMode === 'Counts';
    guide.replaceChildren();
    node(guide,'strong',null,counts ? 'Works published' : 'Index · 2021 = 100');
    guide.append(counts ? ' · Shared scale: 0–4,200 works per row. ' : ' · Shared scale: 65–125 per row; dashed line marks 100. ');
    guide.append('Hover or focus a year for exact values; select a field to emphasize it.');
    for (const r of rows) {
      r.grid.replaceChildren(); r.series.replaceChildren(); r.points = [];
      const w = r.chart.clientWidth || 200;
      const x = i => inset+(w-2*inset)*i/3;
      const min = counts ? 0 : 65, max = counts ? 4200 : 125;
      const top = 4, bottom = rowH-4;
      const y = v => bottom-(v-min)/(max-min)*(bottom-top);
      const at = a => y(counts ? a.work_count : a.index_2021_100);
      for (let i=0;i<4;i++) svg(r.grid,'line',{x1:x(i),x2:x(i),y1:top,y2:bottom,stroke:'var(--grid)','stroke-opacity':'.63'});
      svg(r.grid,'line',{x1:x(0),x2:x(3),y1:y(counts?0:100),y2:y(counts?0:100),stroke:'var(--muted)','stroke-opacity':'.55','stroke-dasharray':counts?'none':'4 3'});
      svg(r.series,'path',{d:r.values.map((a,i)=>`${i?'L':'M'}${x(i)},${at(a)}`).join(' '),fill:'none',stroke:'currentColor','stroke-width':r.row.dataset.keyrow==='true'?2.4:1.6,'stroke-linecap':'round','stroke-linejoin':'round','pointer-events':'none','aria-hidden':'true'});
      for (const [i,a] of r.values.entries()) {
        const id = `${r.id}:${a.publication_year}`;
        const label = `${a.field_name} · ${a.publication_year}`;
        const g = svg(r.series,'g',{class:'ct-point',role:'button',tabindex:'0'});
        mark(g,'field_year',id,label);
        g.setAttribute('aria-label',`${label}: ${num(a.work_count)} works; index ${a.index_2021_100.toFixed(2)}`);
        svg(g,'rect',{class:'ct-focusbox',x:x(i)-14,y:1,width:28,height:rowH-2,rx:4});
        svg(g,'circle',{class:'ct-dot',cx:x(i),cy:at(a),r:3,fill:'var(--bg)',stroke:'currentColor','stroke-width':1.6,'pointer-events':'none'});
        bind(g,r.row,{type:'field_year',id,label},() => [
          `${num(a.work_count)} works · index ${a.index_2021_100.toFixed(2)}`,
          `vs. 2021: ${pct(a.index_2021_100 - 100)}`,
          a.yoy_change == null ? 'First year of comparison' : `vs. prior year: ${signed(a.yoy_change,0)} works (${pct(a.yoy_pct_change)})`
        ]);
        r.points.push([g,a]);
      }
    }
    emphasize();
  }
  const update = params => {
    const mode = params?.mode === 'Counts' ? 'Counts' : 'Index';
    if (mode !== currentMode) {currentMode=mode; draw();}
  };
  update(ctx.params);
  scroll.addEventListener('scroll',hideTip,{passive:true});
  return {
    update,
    setSelection(items) {selection=items || []; emphasize();},
    highlight(items) {highlights=items || []; emphasize();},
    destroy() {root.remove();}
  };
}
