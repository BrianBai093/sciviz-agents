export default function render(el, ctx) {
 const c=ctx.theme.colors, nf=new Intl.NumberFormat('en-US'), fmt=x=>nf.format(x), yrs=[2021,2022,2023,2024];
 const rows=[...ctx.data.fields].sort((a,b)=>a.field_rank-b.field_rank), annual=[...ctx.data.annual].sort((a,b)=>a.publication_year-b.publication_year);
 const gain=ctx.theme.categorical?.[0]||c.accent, loss='#ad5331';
 const signed=(n,d=0)=>`${n>0?'+':n<0?'−':''}${d?Math.abs(n).toFixed(d):fmt(Math.abs(n))}`;
 let params={limit:8,scale:'Relative to 2021',...ctx.params}, selection=[], highlights=[], marks=[];
 const root=document.createElement('div'); el.append(root);
 const css=document.createElement('style'); root.append(css);
 css.textContent=`.fo {box-sizing:border-box;height:100%;width:100%;padding:16px clamp(12px,2.5vw,30px);display:flex;flex-direction:column;overflow:auto;font-size:13px;line-height:1.35} .fo *{box-sizing:border-box} .fo h2{margin:2px 0 4px;font-size:clamp(20px,3vw,30px);line-height:1.1;letter-spacing:-.025em} .fo .kicker{font-size:10px;font-weight:750;letter-spacing:.14em;text-transform:uppercase} .fo p{margin:0} .fo .dek{margin-bottom:12px} .fo .summary{display:grid;grid-template-columns:1.3fr repeat(4,1fr);gap:8px;align-items:center;border-radius:8px;padding:8px 14px;margin-bottom:9px} .fo .summary strong{display:block;font-size:17px;line-height:1.15;font-variant-numeric:tabular-nums} .fo small{font-size:11px} .fo .scroll{overflow:auto;min-height:0;flex:0 1 auto} .fo table{width:100%;border-collapse:separate;border-spacing:0;font-variant-numeric:tabular-nums;min-width:650px} .fo th,.fo td{padding:4px 8px;text-align:right} .fo th{position:sticky;top:0;z-index:1;font-size:11px;font-weight:650;white-space:nowrap} .fo td{height:35px} .fo td:first-child,.fo th:first-child{text-align:left} .fo td:nth-child(2),.fo th:nth-child(2){text-align:center} .fo tbody tr{cursor:pointer} .fo tbody tr:focus-visible{outline:2px solid ${c.accent};outline-offset:-2px} .fo .rank{display:inline-block;min-width:20px;font-size:11px} .fo .field{font-weight:620} .fo .delta{font-weight:720;white-space:nowrap} .fo svg{display:block;margin:auto;width:100%;max-width:116px;height:25px} .fo .foot{padding-top:8px;font-size:11px} .fo-tip{position:fixed;z-index:10;pointer-events:none;padding:8px 10px;border-radius:6px;font-size:12px;box-shadow:0 3px 12px #0002;max-width:300px} .fo-tip b{display:block;margin-bottom:2px}`;
 const panel=document.createElement('div'); panel.className='fo'; Object.assign(panel.style,{fontFamily:ctx.theme.fontFamily,color:c.text,background:c.background}); root.style.height='100%'; root.append(panel);
 const tip=document.createElement('div'); tip.className='fo-tip'; tip.hidden=true; Object.assign(tip.style,{background:c.surface,color:c.text,border:`1px solid ${c.grid}`,fontFamily:ctx.theme.fontFamily}); root.append(tip);
 const make=(tag,parent,text,cls)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==null)e.textContent=text;parent.append(e);return e;};
 function emphasize(){ const matches=(a,r)=>a.some(i=>String(i.id??i.key?.field_id)===String(r.field_id)); for(const {e,r} of marks){const s=matches(selection,r),h=matches(highlights,r);e.style.opacity=(selection.length||highlights.length)&&!(s||h)?(c.dimOpacity??0.45):1;e.style.background=s||h?c.surface:'';e.style.boxShadow=s||h?`inset 3px 0 ${h?c.highlight:c.accent}`:'';} }
 function chart(td, vals, low, high, base, color){
  const ns='http://www.w3.org/2000/svg', svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 116 25');svg.setAttribute('aria-hidden','true'); td.append(svg);
  const s=(tag,attrs)=>{const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));svg.append(e);};
  const y=v=>22-19*(v-low)/(high-low),x=i=>5+i*106/3;
  s('line',{x1:2,x2:114,y1:y(base),y2:y(base),stroke:c.axis,'stroke-opacity':.65,'stroke-dasharray':'2 3'});
  s('polyline',{points:vals.map((v,i)=>`${x(i)},${y(v)}`).join(' '),fill:'none',stroke:color,'stroke-width':1.75,'stroke-linejoin':'round'});
  vals.forEach((v,i)=>s('circle',{cx:x(i),cy:y(v),r:i===3?2.7:1.8,fill:color}));
 }
 function draw(){
  panel.replaceChildren(); tip.hidden=true; marks=[];
  const num=Math.max(1,Math.min(rows.length,Number(params.limit)||8)), shown=rows.slice(0,num), relative=params.scale!=='Work counts';
  make('div',panel,'COLUMBIA UNIVERSITY  /  RESEARCH OUTPUT','kicker').style.color=c.textMuted;
  make('h2',panel,'Publication output by field');
  make('p',panel,`Top ${num} fields by combined 2021–2024 output · one primary field per work`,'dek').style.color=c.textMuted;
  const band=make('div',panel,null,'summary'); band.style.background=c.surface;
  const all=make('div',band,null);make('b',all,'All snapshot works');make('small',all,`${signed(100*(annual[3].n/annual[0].n-1),1)}% vs. 2021`).style.display='block';
  for(const d of annual){const item=make('div',band,null);make('small',item,d.publication_year).style.color=c.textMuted;make('strong',item,fmt(d.n));}
  const series=shown.map(r=>yrs.map(y=>relative?100*(r['y'+y]/r.y2021-1):r['y'+y]));
  const low=relative?Math.min(-25,Math.floor(Math.min(...series.flat())/5)*5):0, high=relative?Math.max(25,Math.ceil(Math.max(...series.flat())/5)*5):Math.ceil(Math.max(...series.flat())/500)*500;
  const sc=make('div',panel,null,'scroll'), t=make('table',sc,null), head=make('tr',make('thead',t,null),null);
  ['Primary research field','Trend',...yrs,'Change vs. 2021'].forEach(label=>{const th=make('th',head,label);th.scope='col';th.style.background=c.background;th.style.color=c.textMuted;th.style.borderBottom=`1px solid ${c.axis}`;});
  const body=make('tbody',t,null);
  shown.forEach((r,i)=>{
   const tr=make('tr',body,null);tr.dataset.id=r.field_id;tr.dataset.type='field';tr.dataset.label=r.field;tr.tabIndex=0;marks.push({e:tr,r});
   const td=make('td',tr,null);make('span',td,r.field_rank,'rank').style.color=c.textMuted;make('span',td,r.field,'field');
   const color=r.change>0?gain:r.change<0?loss:c.textMuted;
   chart(make('td',tr,null),series[i],low,high,0,color);
   yrs.forEach(y=>make('td',tr,fmt(r['y'+y])));make('td',tr,`${signed(r.pct_change,1)}%`,'delta').style.color=color;
   for(const cell of tr.cells)cell.style.borderBottom=`1px solid ${c.grid}`;
   function detail(x,y){ tip.replaceChildren();make('b',tip,r.field);make('div',tip,`${fmt(r.total)} works across 2021–2024`);make('div',tip,`2024 vs. 2021: ${signed(r.change)} works (${signed(r.pct_change,1)}%)`);tip.hidden=false;tip.style.left=`${Math.max(0,Math.min(x+12,window.innerWidth-tip.offsetWidth-8))}px`;tip.style.top=`${Math.max(0,Math.min(y+12,window.innerHeight-tip.offsetHeight-8))}px`; }
   tr.addEventListener('pointermove',e=>detail(e.clientX,e.clientY));tr.addEventListener('pointerleave',()=>tip.hidden=true);
   tr.addEventListener('focus',()=>{const p=tr.getBoundingClientRect();detail(p.left+Math.min(p.width/2,220),p.top);});tr.addEventListener('blur',()=>tip.hidden=true);
   tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();ctx.host.select([{type:'field',id:r.field_id,label:r.field}],{mode:'replace'});}if(e.key==='Escape')tip.hidden=true;});
  });
  make('p',panel,relative?`Trend scale: ${signed(low)}% to ${signed(high)}% · dotted line marks the 2021 baseline.`:`Trend scale: 0 to ${fmt(high)} works · shared across fields.`,'foot').style.color=c.textMuted;
  emphasize();
 }
 draw(); return {update(p){params={...params,...p};draw();},setSelection(items){selection=items||[];emphasize();},highlight(items){highlights=items||[];emphasize();},destroy(){root.remove();}};
}