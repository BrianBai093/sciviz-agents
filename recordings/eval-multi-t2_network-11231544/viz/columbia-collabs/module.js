export default function render(el, ctx) {
  const {network:g, spec:j}=ctx.data, t=ctx.theme, c=t.colors;
  const nodes=[...g.nodes].sort((a,b)=>a.rank-b.rank), edges=[...g.edges].sort((a,b)=>b.shared_works-a.shared_works);
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const N='http://www.w3.org/2000/svg';
  function html(tag,cl,parent,text){const a=document.createElement(tag);if(cl)a.className=cl;if(text!=null)a.textContent=text;parent.append(a);return a;}
  function sv(tag,attrs,parent,text){const a=document.createElementNS(N,tag); for(const [k,v] of Object.entries(attrs))a.setAttribute(k,v);if(text!=null)a.textContent=text;parent.append(a);return a;}
  const root=html('section','cc-root',el);
  const colors=[t.categorical[0]||c.accent,t.categorical[1]||c.highlight,c.textMuted];
  for(const [k,v] of Object.entries({bg:c.background,surface:c.surface,ink:c.text,muted:c.textMuted,grid:c.grid,accent:c.accent}))root.style.setProperty('--'+k,v);
  root.style.fontFamily=t.fontFamily;
  const style=html('style','',root);
  style.textContent=`
  .cc-root{position:relative;display:flex;flex-direction:column;gap:8px;height:100%;width:100%;box-sizing:border-box;padding:14px 18px 10px;background:var(--bg);color:var(--ink);overflow:hidden;font-size:13px;line-height:1.25}
  .cc-root *{box-sizing:border-box}
  .cc-head{display:flex;justify-content:space-between;align-items:end;gap:12px;flex-wrap:wrap}
  .cc-over{font-size:10px;font-weight:750;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:4px}
  .cc-root h1{font-size:clamp(18px,3.35vw,29px);line-height:1.07;margin:0;letter-spacing:-.025em}
  .cc-count{font-size:12px;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums}
  .cc-tools{display:flex;align-items:center;gap:10px;min-height:31px}
  .cc-finder{position:relative;flex:0 1 235px;min-width:120px;z-index:3}
  .cc-root input,.cc-root button{font:inherit;color:var(--ink);background:var(--surface);border:1px solid var(--grid);border-radius:5px;height:30px}
  .cc-root input{padding:0 8px;width:100%}.cc-root input::placeholder{color:var(--muted)}
  .cc-root button{cursor:pointer;padding:0 8px;white-space:nowrap}.cc-root button:hover{border-color:var(--accent)}
  .cc-root button:disabled{opacity:.45;cursor:default}
  .cc-root :is(input,button):focus-visible{outline:2px solid var(--accent);outline-offset:1px}
  .cc-results{position:absolute;top:34px;left:0;width:max(100%,255px);max-height:220px;overflow:auto;background:var(--bg);border:1px solid var(--grid);border-radius:5px;padding:4px;box-shadow:0 4px 12px #0003}
  .cc-results button{display:block;text-align:left;width:100%;height:auto;margin:0;padding:6px;border:0;background:transparent;white-space:normal}
  .cc-results button:hover{background:var(--surface);text-decoration:underline}
  .cc-empty{padding:6px;color:var(--muted)}
  .cc-summary{flex:1;color:var(--muted);line-height:1.2;font-size:12px}.cc-summary strong{color:var(--ink)}
  .cc-zoom{margin-left:auto;display:flex;gap:4px}.cc-zoom button{min-width:29px}
  .cc-plot{flex:1;min-height:0;position:relative;overflow:hidden;isolation:isolate;border-radius:7px;border:1px solid var(--grid);background:var(--surface)}
  .cc-map{width:100%;height:100%;display:block;touch-action:none;cursor:grab}.cc-map.cc-drag,.cc-map.cc-drag *{cursor:grabbing!important}
  .cc-mark{cursor:pointer;outline:none}.cc-wire{transition:stroke-opacity .12s}.cc-dot{transition:opacity .12s}
  .cc-tooltip{position:absolute;z-index:4;pointer-events:none;padding:8px 10px;border-radius:6px;border:1px solid var(--grid);background:var(--bg);box-shadow:0 3px 12px #0003;max-width:min(290px,95%);font-size:12px;line-height:1.35}
  .cc-tooltip strong{display:block;font-size:13px;margin-bottom:3px}.cc-tooltip div{color:var(--muted)}
  .cc-foot{display:flex;flex-direction:column;gap:4px}.cc-legend{display:flex;align-items:center;gap:6px 22px;flex-wrap:wrap}.cc-legend-group{display:flex;align-items:center;gap:6px;font-size:12px;white-space:nowrap}
  .cc-legend strong{font-weight:700}.cc-note{font-size:11px;color:var(--muted)}
  @media(max-width:620px){.cc-root{padding:9px;gap:6px}.cc-head{gap:3px}.cc-count{text-align:left}.cc-tools{flex-wrap:wrap;gap:4px}.cc-summary{flex:1 0 100%;order:3}.cc-legend{gap:3px 12px}}
  `;
  const header=html('header','cc-head',root), titles=html('div','',header);
  html('div','cc-over',titles,'Columbia University  /  2021–2024');
  html('h1','',titles,'Coauthorship among the top 80');
  const count=html('div','cc-count',header);
  const tools=html('div','cc-tools',root), finder=html('div','cc-finder',tools);
  const input=html('input','',finder);input.type='search';input.placeholder='Find a researcher…';input.setAttribute('aria-label','Find a researcher by name, rank, or author ID'); input.autocomplete='off';
  const results=html('div','cc-results',finder);results.hidden=true;results.setAttribute('aria-label','Matching researchers');
  const summary=html('div','cc-summary',tools);summary.setAttribute('aria-live','polite');
  const zoomer=html('div','cc-zoom',tools);
  function button(parent,text,label,fn){const b=html('button','',parent,text);b.type='button';b.setAttribute('aria-label',label);b.title=label;b.onclick=fn;return b;}
  const clear=button(zoomer,'Clear','Clear selection',()=>{selected=[]; paint();ctx.host.select([],{mode:'replace'});});
  const minus=button(zoomer,'−','Zoom out',()=>adjust(.8));
  const plus=button(zoomer,'+','Zoom in',()=>adjust(1.25));
  const reset=button(zoomer,'Fit','Fit entire network',()=>{camera={k:1,x:0,y:0};transform();});
  const plot=html('div','cc-plot',root);
  const {view_bounds:bounds, regions}=j.layout;
  const svg=sv('svg',{class:'cc-map',viewBox:bounds.join(' '),'aria-label':'Force-directed coauthorship network. Tab to authors; select one to make their ties keyboard-accessible. Drag to pan; scroll to zoom.'},plot);
  const scene=sv('g',{},svg);
  const panels=sv('g',{'pointer-events':'none'},scene);
  function panel(ext,color,title,sub,dy){const [x,y,x2,y2]=ext;
    sv('rect',{x,y,width:x2-x,height:y2-y,rx:12,fill:color,'fill-opacity':.035,stroke:color,'stroke-opacity':.37,'stroke-width':1.2},panels);
    sv('text',{x:x+17,y:y+25,fill:c.text,'font-size':20,'font-weight':700},panels,title);
    const subtitle=sv('text',{x:x+17,y:y+45,fill:c.textMuted,'font-size':15},panels,sub);
    if(dy)sv('text',{x:x+17,y:y2-17,fill:c.textMuted,'font-size':14},panels,dy);
    return subtitle;
  }
  const region=(name,pad)=>regions[name].map((v,i)=>v+pad[i]);
  const componentInfo=j.components.filter(x=>!x.is_isolate);
  const subtitles=[
    panel(region('C01',[-28,-62,14,28]),colors[0],'Component 1',''),
    panel(region('C02',[-22,-87,21,35]),colors[1],'Component 2','')
  ];
  panel(region('isolates',[-2,-23,1,28]),colors[2],'Isolates',`${j.isolate_count} researchers · no ties`,'Grid ordered by rank');
  const edgeLayer=sv('g',{},scene), nodeLayer=sv('g',{},scene), labelLayer=sv('g',{'pointer-events':'none'},scene);
  const tip=html('div','cc-tooltip',root);tip.hidden=true;tip.setAttribute('role','tooltip');
  const footer=html('footer','cc-foot',root), legend=html('div','cc-legend',footer);
  const radius=v=>1.04*Math.sqrt(v), width=v=>.9+5.8*(Math.sqrt(v)-1)/(Math.sqrt(j.strongest_pairs[0].shared_works)-1);
  const ink=n=>n.is_isolate?colors[2]:colors[n.component_id==='C01'?0:1];
  function legendGroup(label){const p=html('div','cc-legend-group',legend);html('strong','',p,label);return p;}
  const lg1=legendGroup('Circle area: affiliated works'), ls1=sv('svg',{width:120,height:26,viewBox:'0 0 154 34','aria-label':'Example circle sizes for 75 and 250 works'},lg1);
  [[13,75],[79,250]].forEach(([x,v])=>{sv('circle',{cx:x,cy:17,r:radius(v),fill:colors[0],'fill-opacity':.78},ls1);sv('text',{x:x+radius(v)+5,y:22,'font-size':15,fill:c.textMuted},ls1,v);});
  const lg2=legendGroup('Line width: shared works'), ls2=sv('svg',{width:120,height:24,viewBox:'0 0 145 29','aria-label':'Example tie widths for 1 and 85 shared works'},lg2);
  [[1,1],[68,85]].forEach(([x,v])=>{sv('line',{x1:x,y1:15,x2:x+33,y2:15,stroke:colors[0],'stroke-width':width(v),'stroke-opacity':.82},ls2);sv('text',{x:x+40,y:20,'font-size':14,fill:c.textMuted},ls2,v);});
  html('div','cc-note',footer,'Affiliated works count distinct works where the author lists Columbia or a covered child institution. Ties count shared snapshot works regardless of affiliation.');
  const note=html('div','cc-note',footer);

  let min=1, selected=[], flagged=[], hovered=null, focused=null, camera={k:1,x:0,y:0}, drag=null, suppress=false;
  const nm=new Map(), em=new Map();
  const item=(d,type)=>({type,id:d.id,label:d.label});
  const idOf=o=>typeof o==='string'?o:o?.id;
  const incident=(e,id)=>e.source===id||e.target===id;
  const detailNode=n=>`Rank #${n.rank} · ${n.affiliated_works} affiliated works`;
  const detailEdge=e=>`${e.shared_works} shared ${e.shared_works===1?'work':'works'}`;
  function makeMark(group,type,d,detail){
    group.setAttribute('data-id',d.id);group.setAttribute('data-type',type);group.setAttribute('data-label',d.label);group.setAttribute('aria-label',`${d.label}. ${detail}.`);group.setAttribute('role','button');
    const mark={d,type,group};
    group.addEventListener('pointerenter',ev=>{if(drag?.moved)return;hovered=mark;tooltip(mark,ev);paint();});
    group.addEventListener('pointermove',ev=>{if(hovered===mark&&!drag?.moved)positionTip(ev);});
    group.addEventListener('pointerleave',()=>{if(hovered===mark){hovered=null;if(focused)tooltip(focused);else tip.hidden=true;paint();}});
    group.addEventListener('focus',()=>{focused=mark;if(type==='author')showNode(d);if(!hovered)tooltip(mark);paint();});
    group.addEventListener('blur',()=>{if(focused===mark){focused=null;if(!hovered)tip.hidden=true;paint();}});
    group.addEventListener('click',ev=>{if(ev.ctrlKey||ev.metaKey||ev.shiftKey){const ix=selected.findIndex(x=>idOf(x)===d.id);selected=ix<0?[...selected,item(d,type)]:selected.filter((_,i)=>i!==ix);}else selected=[item(d,type)];paint();});
    group.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();choose(mark,false);}
      if(type==='author'&&ev.key.toLowerCase()==='t'){ev.preventDefault();choose(mark,false);[...em.values()].find(m=>m.d.shared_works>=min&&incident(m.d,d.id))?.group.focus();}
      if(type==='author'&&['ArrowRight','ArrowLeft','ArrowDown','ArrowUp'].includes(ev.key)) {ev.preventDefault();const i=nodes.indexOf(d), delta=['ArrowRight','ArrowDown'].includes(ev.key)?1:-1;nm.get(nodes[(i+delta+nodes.length)%nodes.length].id).group.focus();}
    });
    return mark;
  }
  for(const e of edges){
    const a=byId.get(e.source), b=byId.get(e.target), xy={x1:a.x,y1:a.y,x2:b.x,y2:b.y}, col=ink(a);
    const group=sv('g',{class:'cc-mark',tabindex:-1},edgeLayer), m=makeMark(group,'coauthorship',e,detailEdge(e));
    m.line=sv('line',{...xy,class:'cc-wire',stroke:col,'stroke-width':width(e.shared_works),'stroke-linecap':'round','pointer-events':'none'},group);
    sv('line',{...xy,stroke:'transparent','stroke-width':Math.max(5,width(e.shared_works)+2),'pointer-events':'stroke'},group);em.set(e.id,m);
  }
  for(const n of nodes){
    const r=radius(n.affiliated_works), group=sv('g',{class:'cc-mark',tabindex:0,transform:`translate(${n.x},${n.y})`},nodeLayer), m=makeMark(group,'author',n,detailNode(n));
    m.ring=sv('circle',{class:'cc-dot',r:r+3.5,fill:'none',stroke:c.text,'stroke-width':2,'pointer-events':'none'},group);
    m.dot=sv('circle',{class:'cc-dot',r,fill:ink(n),stroke:c.background,'stroke-width':1.6},group);
    if(n.is_isolate)m.rank=sv('text',{class:'cc-dot',x:0,y:r+14,'text-anchor':'middle','font-size':13,fill:c.textMuted,'pointer-events':'none'},group,`#${n.rank}`);
    nm.set(n.id,m);
  }
  function tooltip(m,ev){
    tip.replaceChildren();html('strong','',tip,m.d.label);
    html('div','',tip,m.type==='author'?detailNode(m.d):detailEdge(m.d));
    if(m.type==='author'){
      const current=edges.filter(e=>e.shared_works>=min&&incident(e,m.d.id)).length;
      html('div','',tip,m.d.is_isolate?'No ties to the other 79 researchers':`${current} ${min>1?'visible ':''}${current===1?'coauthor':'coauthors'} among the top 80${min>1?` (${m.d.degree} before filtering)`:''}`);
    }
    tip.hidden=false;positionTip(ev,m);
  }
  function positionTip(ev,m){const r=root.getBoundingClientRect(), pr=plot.getBoundingClientRect(), b=m?.group.getBoundingClientRect();
    const x=(ev?.clientX??(b.left+b.right)/2)-r.left, y=(ev?.clientY??(b.top+b.bottom)/2)-r.top;
    let tx=x+13, ty=y+14;
    if(tx+tip.offsetWidth>r.width-6)tx=x-tip.offsetWidth-13;
    if(ty+tip.offsetHeight>pr.bottom-r.top-2)ty=y-tip.offsetHeight-12;
    tip.style.left=`${Math.max(5,Math.min(r.width-tip.offsetWidth-5,tx))}px`;tip.style.top=`${Math.max(4,ty)}px`;
  }
  function paint(){
    const sel=new Set(selected.map(idOf).filter(id=>nm.has(id)||em.has(id))), hi=new Set(flagged.map(idOf).filter(id=>nm.has(id)||em.has(id)));
    const act=new Set([...sel,...hi]), transient=(hovered||focused)?.d.id;
    if(transient)act.add(transient);
    const near=new Set(act);
    for(const [id,m] of em){const e=m.d, shown=e.shared_works>=min;
      const active=act.has(id)||act.has(e.source)||act.has(e.target);
      if(shown&&active){near.add(e.source);near.add(e.target);}
      m.line.setAttribute('stroke-opacity',act.size?(active?(act.has(id)?1:.85):.12):(.46+.23*Math.sqrt(e.shared_works/85)));
      m.line.setAttribute('stroke',act.has(id)?c.text:ink(byId.get(e.source)));
      m.group.style.display=shown?'':'none';
      m.group.setAttribute('tabindex',shown&&(sel.has(id)||sel.has(e.source)||sel.has(e.target))?0:-1);
      m.group.setAttribute('aria-pressed',sel.has(id));
    }
    for(const [id,m] of nm){const opacity=!act.size||near.has(id)?1:.25;
      m.dot.setAttribute('opacity',opacity);m.rank?.setAttribute('opacity',opacity);
      m.ring.setAttribute('opacity',act.has(id)?1:0);m.group.setAttribute('aria-pressed',sel.has(id));}
    labelLayer.replaceChildren();
    const focusNode=byId.get(transient)||byId.get([...sel][0])||byId.get([...hi][0]);
    if(focusNode){const n=focusNode, right=n.x>850, xx=n.x+(right?-1:1)*(radius(n.affiliated_works)+8);
      sv('text',{x:xx,y:n.y-2,'text-anchor':right?'end':'start',fill:c.text,stroke:c.surface,'stroke-width':6,'stroke-linejoin':'round','paint-order':'stroke','font-size':17,'font-weight':700},labelLayer,n.label);
    }
    clear.disabled=!sel.size;
    const key=[...sel].join(',')+'|'+min;
    if(summary.dataset.last!==key){summary.dataset.last=key; summary.replaceChildren();
      const n=byId.get([...sel][0]), e=em.get([...sel][0])?.d;
      if(sel.size>1)html('strong','',summary,`${sel.size} selected`);
      else if(n||e){html('strong','',summary,(n||e).label); summary.append(` · ${n?detailNode(n):detailEdge(e)}${e&&e.shared_works<min?' (hidden by filter)':''}`);}
      else summary.textContent='Select a researcher to trace direct ties. Scroll to zoom; drag to pan.';
    }
  }
  function project(x,y){const p=svg.createSVGPoint();p.x=x;p.y=y;return p.matrixTransform(svg.getScreenCTM().inverse());}
  function transform(){scene.setAttribute('transform',`translate(${camera.x},${camera.y}) scale(${camera.k})`);minus.disabled=camera.k<=1;plus.disabled=camera.k>=8;reset.disabled=camera.k===1&&camera.x===0&&camera.y===0;tip.hidden=true;}
  function adjust(f,p){const k=Math.max(1,Math.min(8,camera.k*f));if(k===camera.k)return;
    p=p||{x:bounds[2]/2,y:bounds[3]/2}; const r=k/camera.k;
    camera=k===1?{k:1,x:0,y:0}:{k,x:p.x-(p.x-camera.x)*r,y:p.y-(p.y-camera.y)*r};transform();}
  function showNode(n){const x=n.x*camera.k+camera.x,y=n.y*camera.k+camera.y;
    if(x>=65&&x<=bounds[2]-65&&y>=40&&y<=bounds[3]-40)return;
    camera.x=bounds[2]/2-n.x*camera.k;camera.y=bounds[3]/2-n.y*camera.k;transform();
  }
  function choose(m,find){selected=[item(m.d,m.type)];paint();ctx.host.select(selected,{mode:'replace'});if(find){input.value=m.d.label; results.hidden=true;showNode(m.d);m.group.focus({preventScroll:true});}}
  function matches(){const q=input.value.trim().toLowerCase();return nodes.filter(n=>!q||`${n.label.toLowerCase()} #${n.rank} ${n.id.toLowerCase()}`.includes(q));}
  function list(){const ns=matches();results.replaceChildren();results.hidden=false;
    for(const n of ns)button(results,`#${n.rank} · ${n.label}`,`Select ${n.label}, rank ${n.rank}`,()=>choose(nm.get(n.id),true));
    if(!ns.length)html('div','cc-empty',results,'No matching researcher');
  }
  input.addEventListener('focus',list);input.addEventListener('input',list);
  input.addEventListener('keydown',ev=>{if(ev.key==='Escape'){results.hidden=true;ev.stopPropagation();}if(ev.key==='ArrowDown'){ev.preventDefault();results.querySelector('button')?.focus();}if(ev.key==='Enter'){ev.preventDefault();const n=matches()[0];if(n)choose(nm.get(n.id),true);}});
  finder.addEventListener('focusout',ev=>{if(!finder.contains(ev.relatedTarget))results.hidden=true;});
  results.addEventListener('keydown',ev=>{if(ev.key==='Escape'){input.focus();results.hidden=true;} if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){ev.preventDefault();const target=ev.key==='ArrowDown'?ev.target.nextElementSibling:ev.target.previousElementSibling;(target||input).focus();}});
  root.addEventListener('pointerdown',ev=>{if(!finder.contains(ev.target))results.hidden=true;});
  svg.addEventListener('wheel',ev=>{ev.preventDefault();adjust(Math.exp(Math.max(-300,Math.min(300,-ev.deltaY))*.002),project(ev.clientX,ev.clientY));},{passive:false});
  svg.addEventListener('pointerdown',ev=>{if(ev.button!==0)return;suppress=false;drag={x:ev.clientX,y:ev.clientY,origin:project(ev.clientX,ev.clientY),cx:camera.x,cy:camera.y,moved:false,id:ev.pointerId};});
  svg.addEventListener('pointermove',ev=>{if(!drag||drag.id!==ev.pointerId)return; if(!drag.moved&&Math.hypot(ev.clientX-drag.x,ev.clientY-drag.y)<5)return;
    if(!drag.moved){drag.moved=true;svg.setPointerCapture(ev.pointerId);svg.classList.add('cc-drag');hovered=null;paint();}
    const p=project(ev.clientX,ev.clientY);camera.x=Math.max(-bounds[2]*(camera.k-.2),Math.min(bounds[2]*.8,drag.cx+p.x-drag.origin.x));camera.y=Math.max(-bounds[3]*(camera.k-.2),Math.min(bounds[3]*.8,drag.cy+p.y-drag.origin.y));transform();
  });
  function end(ev){if(!drag||ev.pointerId!==drag.id)return;suppress=drag.moved;drag=null;svg.classList.remove('cc-drag');}
  svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);svg.addEventListener('lostpointercapture',end);
  svg.addEventListener('click',ev=>{if(suppress){ev.stopImmediatePropagation();ev.preventDefault();suppress=false;}},true);
  function update(params){
    min=Number(params?.minSharedWorks)||1;
    const shown=edges.filter(e=>e.shared_works>=min);
    count.textContent=`${j.node_count} researchers  ·  ${min===1?shown.length:`${shown.length} of ${j.edge_count}`} ties${min===1?'':` (≥${min} works)`}`;
    count.setAttribute('aria-live','polite');
    componentInfo.forEach((info,i)=>{const ct=shown.filter(e=>e.component_id===info.id).length;
      subtitles[i].textContent=`${info.node_count} researchers · ${min===1?ct:`${ct} of ${info.edge_count}`} ties`;
    });
    note.textContent=min===1?'Components show reachability, not disciplines. Distances across regions are not meaningful.':'The filter hides ties only; all researchers, original groups and positions stay fixed. Distances across regions are not meaningful.';
    tip.hidden=true;hovered=null;paint();
  }
  update(ctx.params);transform();
  return {update,setSelection(items){selected=items||[];paint();},highlight(items){flagged=items||[];paint();},getState(){return {...camera};},setState(s){if(Number.isFinite(s?.k)&&Number.isFinite(s.x)&&Number.isFinite(s.y)){camera={...s};transform();}},destroy(){root.remove();}};
}
