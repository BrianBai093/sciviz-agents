import * as d3 from 'https://esm.sh/d3@7.9.2';

export default function render(el,ctx) {
  const {width:w,height:h}=ctx, t=ctx.theme, c=t.colors;
  const bg=c.background, surface=c.surface, text=c.text, muted=c.textMuted, border=c.grid, accent=c.accent;
  const colors=[t.categorical[0],t.categorical[1],muted];
  const root=d3.select(el).style('position','relative').style('overflow','hidden').style('background',bg).style('font-family',t.fontFamily);
  const svg=root.append('svg').attr('width',w).attr('height',h).attr('aria-label','Force-directed coauthorship network of Columbia’s 80 most prolific researchers').style('display','block');
  const addText=(g,x,y,s,size=12,fill=muted,weight=400)=>g.append('text').attr('x',x).attr('y',y).attr('fill',fill).attr('font-size',size).attr('font-weight',weight).text(s);
  const nodes=ctx.data.researchers.map(d=>({...d}));
  const by=new Map(nodes.map(d=>[d.id,d]));
  const links=ctx.data.ties.map(d=>({...d,s:by.get(d.source),t:by.get(d.target),key:{source:d.source,target:d.target}})).sort((a,b)=>a.shared-b.shared);
  const margin=22, gap=13, top=115, bottom=h-37, ph=bottom-top;
  const side=Math.max(146,Math.min(278,(w-2*margin)*.277));
  const mw=w-2*margin-side-gap, sx=margin+mw+gap;
  const r=d3.scaleSqrt().domain([71,259]).range([5.3,10.8]);
  const lw=d3.scaleSqrt().domain([1,85]).range([.65,4.1]);
  const panels=[{x:margin,y:top,w:mw,h:ph,k:1,title:'Largest component',sub:'57 researchers'}, {x:sx,y:top,w:side,h:ph*.56,k:2,title:'Second component',sub:'8 researchers'}, {x:sx,y:top+ph*.56+gap,w:side,h:ph*.44-gap,k:3,title:'No links in this cohort',sub:'15 researchers'}];
  addText(svg,margin,24,'COLUMBIA UNIVERSITY  /  OPENALEX · 2021–2024',10,muted,680).attr('letter-spacing','1.25');
  addText(svg,margin,53,'Coauthorship among the top 80',Math.min(28,w*.047),text,720);
  const summary=addText(svg,margin,77,'',12,muted);
  const legend=svg.append('g').attr('transform',`translate(${margin},96)`);
  legend.append('circle').attr('cx',6).attr('r',3.6).attr('fill',colors[0]);
  legend.append('circle').attr('cx',20).attr('r',6).attr('fill',colors[0]);
  addText(legend,32,4,'Node size: Columbia-affiliated works',11);
  legend.append('line').attr('x1',232).attr('x2',253).attr('y1',-3).attr('y2',-3).attr('stroke',muted).attr('stroke-width',.8);
  legend.append('line').attr('x1',232).attr('x2',253).attr('y1',4).attr('y2',4).attr('stroke',muted).attr('stroke-width',3);
  addText(legend,262,4,'Link width: shared works',11);
  const footer=addText(svg,margin,h-15,'Hover a node or link for details · Click to select',10.5,muted);

  function layout(p,ns){
    const inner={x:p.x+20,y:p.y+56,w:p.w-40,h:p.h-67};
    if(p.k===3){
      ns.forEach((n,i)=>{n.x=inner.x+(i%5+.5)*inner.w/5;n.y=inner.y+(Math.floor(i/5)+.5)*inner.h/3;}); return;
    }
    const ls=links.filter(l=>l.s.component===p.k).map(l=>({source:l.source,target:l.target,shared:l.shared}));
    const sim=d3.forceSimulation(ns).randomSource(d3.randomLcg(.314+p.k*.1)).stop()
      .force('ties',d3.forceLink(ls).id(d=>d.id).distance(l=>p.k===1?83-49*Math.sqrt(l.shared/85):64-25*Math.sqrt(l.shared/85)).strength(l=>.15+.38*Math.sqrt(l.shared/85)))
      .force('repel',d3.forceManyBody().strength(p.k===1?-113:-96))
      .force('x',d3.forceX(0).strength(.047)).force('y',d3.forceY(0).strength(.073))
      .force('collide',d3.forceCollide(d=>r(d.works)+5).iterations(3));
    sim.tick(360);
    const [x0,x1]=d3.extent(ns,d=>d.x),[y0,y1]=d3.extent(ns,d=>d.y);
    const scale=Math.min((inner.w-12)/(x1-x0),(inner.h-12)/(y1-y0));
    const xscale=Math.min((inner.w-12)/(x1-x0),scale*1.35);
    const yscale=Math.min((inner.h-12)/(y1-y0),scale*1.22);
    for(const n of ns){n.x=inner.x+inner.w/2+(n.x-(x0+x1)/2)*xscale;n.y=inner.y+inner.h/2+(n.y-(y0+y1)/2)*yscale;}
  }
  for(const p of panels){
    svg.append('rect').attr('x',p.x).attr('y',p.y).attr('width',p.w).attr('height',p.h).attr('rx',9).attr('fill',surface).attr('stroke',border);
    svg.append('circle').attr('cx',p.x+17).attr('cy',p.y+20).attr('r',3.8).attr('fill',colors[p.k-1]);
    addText(svg,p.x+27,p.y+24,p.title,p.w<184?11.5:13,text,680);
    addText(svg,p.x+14,p.y+42,p.sub,11);
    layout(p,nodes.filter(d=>p.k===3?d.component>2:d.component===p.k));
  }
  const names=l=>`${l.s.name} & ${l.t.name}`;
  const edge=svg.append('g').selectAll('line').data(links).join('line')
    .attr('x1',d=>d.s.x).attr('x2',d=>d.t.x).attr('y1',d=>d.s.y).attr('y2',d=>d.t.y)
    .attr('data-key',d=>JSON.stringify(d.key)).attr('data-label',names)
    .attr('stroke-linecap','round').style('cursor','pointer').attr('stroke-width',d=>lw(d.shared));
  const dot=svg.append('g').selectAll('circle').data(nodes).join('circle')
    .attr('cx',d=>d.x).attr('cy',d=>d.y).attr('r',d=>r(d.works))
    .attr('fill',d=>colors[Math.min(d.component,3)-1]).attr('stroke',bg).attr('stroke-width',1.1)
    .attr('data-type','author').attr('data-id',d=>d.id).attr('data-label',d=>d.name).style('cursor','pointer');
  const tip=root.append('div').attr('role','tooltip').style('display','none').style('position','absolute').style('pointer-events','none').style('z-index','10').style('padding','9px 12px').style('background',surface).style('color',text).style('border',`1px solid ${border}`).style('border-radius','8px').style('box-shadow','0 3px 14px #0003').style('font-size','12px').style('max-width',`${Math.min(335,w-24)}px`);
  const tipTitle=tip.append('div').style('font-weight','700');
  const tipBody=tip.append('div').style('margin-top','4px').style('color',muted);
  let selection=[], highlights=[], focus=null, minimum=1;
  function paint(){
    const ids=new Set(), chosen=new Set();
    const edgeKey=k=>`${k.source}|${k.target}`;
    for(const i of [...selection,...highlights]){
      if(i.type==='author') ids.add(i.id);
      if(i.key?.source && i.key?.target) chosen.add(edgeKey(i.key));
    }
    if(focus?.id) ids.add(focus.id);
    if(focus?.key) chosen.add(edgeKey(focus.key));
    const active=ids.size+chosen.size>0;
    const neighbors=new Set(ids);
    const emphasized=l=>ids.has(l.source)||ids.has(l.target)||chosen.has(edgeKey(l.key));
    links.forEach(l=>{if(l.shared>=minimum&&emphasized(l)){neighbors.add(l.source);neighbors.add(l.target);}});
    edge.attr('display',l=>l.shared<minimum?'none':null)
      .attr('stroke',l=>active&&emphasized(l)?accent:colors[l.s.component-1])
      .attr('stroke-opacity',l=>active?(emphasized(l)?.93:.085):(.20+.47*Math.sqrt(l.shared/85)))
      .attr('stroke-width',l=>lw(l.shared)+(active&&emphasized(l)?1:0));
    dot.attr('opacity',d=>!active||neighbors.has(d.id)?1:.27)
      .attr('stroke',d=>ids.has(d.id)?text:bg).attr('stroke-width',d=>ids.has(d.id)?2.3:1.1);
  }
  function move(ev){const [x,y]=d3.pointer(ev,el); const box=tip.node();tip.style('left',`${Math.max(5, Math.min(w-box.offsetWidth-6,x+13))}px`).style('top',`${Math.max(5, Math.min(h-box.offsetHeight-6,y+13))}px`);}
  function over(ev,d,title,body){focus=d;tipTitle.text(title);tipBody.text(body);tip.style('display','block');move(ev);paint();}
  function out(){focus=null;tip.style('display','none');paint();}
  dot.on('pointerenter', (ev,d)=>over(ev,d,d.name,`Rank #${d.rank} · ${d.works} Columbia-affiliated works · ${d.partners} cohort collaborators (all links)`)).on('pointermove',move).on('pointerleave',out);
  edge.on('pointerenter', (ev,d)=>over(ev,d,names(d),`${d.shared} shared ${d.shared===1?'work':'works'}`)).on('pointermove',move).on('pointerleave',out);
  function update(p){minimum=Number(p?.minimum??1);focus=null;tip.style('display','none');const count=links.filter(d=>d.shared>=minimum).length;summary.text(`80 researchers  ·  ${count} of ${links.length} links shown  ·  ${minimum===1?'At least 1 shared work':`At least ${minimum} shared works`}`);footer.text(minimum===1?'Hover for details · Click to select a researcher or collaboration':'Hover for details · Groups reflect the full network; filtering hides links only');paint();}
  update(ctx.params);
  return {update,setSelection(items){selection=items??[];paint();},highlight(items){highlights=items??[];paint();},destroy(){root.selectAll('*').remove();}};
}
