import { line, curveBundle } from 'https://esm.sh/d3-shape@3.2.0';

export default function render(el, ctx) {
  const {width:W,height:H,theme}=ctx, c=theme.colors;
  let params=ctx.params, selected=[], highlighted=[], hovered=null;
  const svgNS='http://www.w3.org/2000/svg';
  const root=document.createElement('div'); root.className='cb'; el.append(root);
  root.style.cssText=`height:100%;width:100%;box-sizing:border-box;background:${c.background};color:${c.text};font-family:${theme.fontFamily||'system-ui'};padding:15px 18px 11px;display:flex;flex-direction:column;overflow:hidden;position:relative;`;
  const style=document.createElement('style'); style.textContent=`.cb *{box-sizing:border-box}.cb [data-label]{cursor:pointer}.cb .cb-field:hover,.cb .cb-bridge:hover{background:color-mix(in srgb,currentColor 8%,transparent)}.cb .cb-index{min-height:0;overflow:auto;scrollbar-width:thin}.cb .cb-kicker{font-size:10px;letter-spacing:.11em;text-transform:uppercase;font-weight:750}.cb .cb-side{min-height:0;overflow:auto;scrollbar-width:thin}.cb .cb-bridge{padding:5px 0;font-size:11px;line-height:1.2;display:flex;gap:5px;align-items:center;justify-content:space-between}.cb .cb-field{padding:2px 0;line-height:1.22;font-size:11px;display:flex;gap:7px;align-items:center}.cb .cb-field b{flex:0 0 18px;text-align:center;border-radius:4px;font-size:9px;line-height:15px}.cb .cb-field span:last-child{margin-left:auto;font-variant-numeric:tabular-nums}.cb .cb-node text{paint-order:stroke;stroke-width:2px;stroke-linejoin:round}.cb .cb-edge{isolation:auto}`; root.append(style);
  function html(parent,tag,text,styles,cls){const e=document.createElement(tag);if(text!=null)e.textContent=text;if(styles)e.style.cssText=styles;if(cls)e.className=cls;parent.append(e);return e;}
  function sv(parent,tag,a,text){const e=document.createElementNS(svgNS,tag);for(const [k,v] of Object.entries(a||{}))e.setAttribute(k,v);if(text!=null)e.textContent=text;parent.append(e);return e;}
  function bind(m,it){m.setAttribute('data-label',it.label);if(it.id){m.setAttribute('data-type',it.type);m.setAttribute('data-id',it.id);}else{m.setAttribute('data-type','group');m.setAttribute('data-key',JSON.stringify(it.key));}m.addEventListener('mouseenter',()=>{hovered=it;refresh();});m.addEventListener('mouseleave',()=>{if(hovered===it){hovered=null;refresh();}});}
  const byName=(a,b)=>a.localeCompare(b);
  const map=new Map(), fields=[];
  for(const row of ctx.data.authors){const n={...row}; map.set(n.author_id,n);let f=fields.find(f=>f.id===n.field_id);if(!f){f={id:n.field_id,name:n.field,subs:[],count:0};fields.push(f);}let s=f.subs.find(s=>s.id===n.subfield_id);if(!s){s={id:n.subfield_id,name:n.subfield,nodes:[],f};f.subs.push(s);}s.nodes.push(n);f.count++;n.f=f;n.s=s;}
  fields.sort((a,b)=>byName(a.name,b.name));
  const pal=(theme.categorical||[]).length?theme.categorical:['#326b9d','#75518b','#178170','#ad6140'];
  fields.forEach((f,i)=>{f.i=i+1;f.color=pal[i%pal.length];f.item={type:'group', key:{field_id:f.id}, label:f.name};f.subs.sort((a,b)=>byName(a.name,b.name));for(const s of f.subs){s.item={type:'group',key:{field_id:f.id,subfield_id:s.id},label:s.name};s.nodes.sort((a,b)=>byName(a.name.split(' ').at(-1),b.name.split(' ').at(-1))||byName(a.name,b.name));for(const n of s.nodes)n.item={type:'author',id:n.author_id,label:n.name};}});
  const edges=ctx.data.links.map(r=>({...r,a:map.get(r.source),b:map.get(r.target),item:{type:'group',key:{source:r.source,target:r.target},label:`${r.source_name} × ${r.target_name}`}}));
  const count=e=>e.length.toLocaleString();
  const heading=html(root,'div',null,'flex:none;');
  html(heading,'div','COLUMBIA UNIVERSITY  /  RESEARCH COLLABORATION',`color:${c.textMuted};margin-bottom:4px;`,'cb-kicker');
  html(heading,'h1','Who publishes together?','margin:0;font-size:clamp(20px,2.75vw,30px);font-weight:740;letter-spacing:-.035em;line-height:1.08;');
  html(heading,'div',`${map.size} most prolific Columbia-affiliated researchers · 2021–2024`, `font-size:12px;color:${c.textMuted};margin-top:6px;`);
  const narrow=W<620;
  const body=html(root,'div',null,`flex:1;min-height:0;display:grid;grid-template-${narrow?'rows:minmax(0,2fr) minmax(0,1fr)':'columns:minmax(0,1fr) minmax(214px,28%)'};gap:${narrow?5:12}px;margin-top:8px;`);
  const chart=html(body,'div',null,'min-width:0;min-height:0;position:relative;');
  const side=html(body,'aside',null,`border-${narrow?'top':'left'}:1px solid ${c.grid};padding-${narrow?'top':'left'}:12px;`,'cb-side');
  const footer=html(root,'div','OpenAlex snapshot · Names are abbreviated; hover for full names, click to keep a selection.',`margin-top:5px;color:${c.textMuted};font-size:10px;line-height:1.25;flex:none;`);
  const kicker=(p,t)=>html(p,'div',t,`color:${c.textMuted};margin-bottom:5px;`,'cb-kicker');
  const cross='#bd532b', within=c.textMuted;
  kicker(side,'Collaboration links');
  const totals=html(side,'div',null,'font-size:12px;font-weight:650;margin-bottom:5px;');
  function legend(text,color){const r=html(side,'div',null,'font-size:11px;display:flex;align-items:center;gap:6px;line-height:1.45;');html(r,'span',null,`display:inline-block;width:19px;border-top:2px solid ${color};`);return html(r,'span',text);}
  const legCross=legend('Cross-field',cross), legWithin=legend('Within field',within);
  html(side,'div','Thicker links mean more shared works.',`font-size:10px;color:${c.textMuted};margin:3px 0 9px;`);
  const detail=html(side,'div',null,`background:${c.surface};border:1px solid ${c.grid};border-radius:7px;padding:7px 8px;min-height:69px;margin-bottom:9px;`);
  const detailTitle=html(detail,'div','','font-size:11px;font-weight:750;margin-bottom:3px;');
  const detailBody=html(detail,'div','',`font-size:10px;color:${c.textMuted};line-height:1.32;white-space:pre-line;`);
  kicker(side,'Strongest cross-field pairs');
  const bridges=html(side,'div',null,`margin:-3px 0 9px;`);
  kicker(side,'Field index');
  html(side,'div','Numbered arcs = fields · Inner arcs = subfields',`font-size:10px;color:${c.textMuted};margin-bottom:4px;`);
  const fieldList=html(side,'div',null,null,'cb-index');
  for(const f of fields){const r=html(fieldList,'div',null,null,'cb-field');bind(r,f.item);html(r,'b',String(f.i),`background:color-mix(in srgb,${f.color} 18%,${c.background});border-bottom:2px solid ${f.color};`);html(r,'span',f.name);html(r,'span',String(f.count),`color:${c.textMuted};`);f.row=r;}
  const svg=sv(chart,'svg',{width:'100%',height:'100%',role:'img','aria-label':'Radial hierarchical edge bundle of Columbia researchers, arranged by field and subfield'});
  const layers=Object.fromEntries(['edges','subfields','fields','authors'].map(k=>[k,sv(svg,'g',{})]));
  const box=chart.getBoundingClientRect(), w=box.width||W*.7,h=box.height||H*.8;
  svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
  const cx=w/2,cy=h/2;
  const font=Math.max(6,Math.min(9.2,(Math.min(w,h)-115)/49));
  const R=Math.max(35,Math.min(h/2,w/2)-(font*8.7+11));
  const tau=Math.PI*2;
  const p=(a,r)=>[cx+Math.cos(a)*r,cy+Math.sin(a)*r];
  const arc=(r,a,b)=>`M${p(a,r)} A${r},${r} 0 ${b-a>Math.PI?1:0} 1 ${p(b,r)}`;
  const short=name=>{const parts=name.trim().split(/\s+/);return parts.length<2?name:`${parts[0][0]}. ${parts.at(-1)}`;};
  const gaps=fields.length*.035+fields.reduce((n,f)=>n+f.subs.length-1,0)*.017;
  const step=(tau-gaps)/map.size;
  let t=-Math.PI/2;
  for(const f of fields){f.start=t;for(let i=0;i<f.subs.length;i++){const s=f.subs[i];s.start=t;
    for(const n of s.nodes){n.angle=t+step/2;n.xy=p(n.angle,R);t+=step;}
    s.end=t;s.angle=(s.start+t)/2;if(i<f.subs.length-1)t+=.017;
  }f.end=t;f.angle=(f.start+t)/2;t+=.035;}
  for(const e of edges.slice().sort((a,b)=>Number(a.cross_field)-Number(b.cross_field)||a.shared_works-b.shared_works)){
    const g=sv(layers.edges,'g',{'class':'cb-edge'}); bind(g,e.item); e.g=g;
    e.visible=sv(g,'path',{fill:'none',stroke:e.cross_field?cross:within,'pointer-events':'none','stroke-linecap':'round','stroke-width':.48+2.55*Math.sqrt(e.shared_works/85)});
    e.hit=sv(g,'path',{fill:'none',stroke:'transparent','stroke-width':Math.max(3,1+3*Math.sqrt(e.shared_works/85)),'pointer-events':'stroke'});
  }
  for(const f of fields){
    for(const s of f.subs){const g=sv(layers.subfields,'g',{});bind(g,s.item);s.g=g;
      sv(g,'path',{d:arc(R-9,s.start+.006,s.end-.006),fill:'none',stroke:f.color,'stroke-width':3.4,opacity:.76});
      sv(g,'path',{d:arc(R-9,s.start+.004,s.end-.004),fill:'none',stroke:'transparent','stroke-width':8,'pointer-events':'stroke'});
    }
    const g=sv(layers.fields,'g',{});bind(g,f.item);f.g=g;
    sv(g,'path',{d:arc(R+5,f.start+.003,f.end-.003),fill:'none',stroke:f.color,'stroke-width':3.6});
    const [x,y]=p(f.angle,R-22);
    sv(g,'circle',{cx:x,cy:y,r:7.5,fill:c.background,stroke:f.color,'stroke-width':1.35});
    sv(g,'text',{x,y:y+.4,fill:c.text,'text-anchor':'middle','dominant-baseline':'central','font-size':8.5,'font-weight':750,'pointer-events':'none'},f.i);
  }
  for(const n of map.values()){
    const g=sv(layers.authors,'g',{'class':'cb-node'});bind(g,n.item);n.g=g;
    sv(g,'circle',{cx:n.xy[0],cy:n.xy[1],r:2.1,fill:n.f.color,stroke:c.background,'stroke-width':.6});
    sv(g,'circle',{cx:n.xy[0],cy:n.xy[1],r:4,fill:'transparent'});
    const [x,y]=p(n.angle,R+11), flip=Math.cos(n.angle)<0;
    const txt=short(n.name);
    sv(g,'text',{transform:`translate(${x},${y}) rotate(${n.angle*180/Math.PI+(flip?180:0)})`,fill:c.text,stroke:c.background,'dominant-baseline':'central','text-anchor':flip?'end':'start','font-size':font},txt);
  }
  function draw(){
    const route=line().curve(curveBundle.beta(params.bundling??.86));
    for(const e of edges){const {a,b}=e;const points=[a.xy,p(a.s.angle,R*.78)];
      if(a.s!==b.s){points.push(p(a.f.angle,R*.51));if(a.f!==b.f)points.push([cx,cy],p(b.f.angle,R*.51));points.push(p(b.s.angle,R*.78));}
      points.push(b.xy);const path=route(points);e.visible.setAttribute('d',path);e.hit.setAttribute('d',path);
      e.show=e.shared_works>=(params.minimum??1)&&(params.links==='Cross-field only'?e.cross_field:params.links==='Within-field only'?!e.cross_field:true);e.g.style.display=e.show?'':'none';}
    const shown=edges.filter(e=>e.show), crosses=shown.filter(e=>e.cross_field);
    totals.textContent=`${count(shown)} of ${count(edges)} pairs shown`;
    legCross.textContent=`Cross-field · ${count(crosses)}`;legWithin.textContent=`Within field · ${shown.length-crosses.length}`;
    bridges.replaceChildren();
    for(const e of crosses.slice(0,3)){const row=html(bridges,'div',null,`border-bottom:1px solid ${c.grid};`,'cb-bridge');bind(row,e.item);html(row,'span',`${short(e.a.name)} × ${short(e.b.name)}`);html(row,'strong',String(e.shared_works),`color:${cross};white-space:nowrap;`);}
    if(!crosses.length)html(bridges,'div','No cross-field pairs match the filters.',`font-size:10px;color:${c.textMuted};margin-top:5px;`);
    refresh();
  }
  function norm(i){let k=i?.key??{};if(typeof k==='string'){try{k=JSON.parse(k);}catch{k={};}}return k;}
  function nMatch(i,n){const k=norm(i);return i?.id===n.author_id||(k.source&&(k.source===n.author_id||k.target===n.author_id))||(k.field_id===n.field_id&&(!k.subfield_id||k.subfield_id===n.subfield_id));}
  function eMatch(i,e){const k=norm(i);return k.source?(k.source===e.source&&k.target===e.target):nMatch(i,e.a)||nMatch(i,e.b);}
  function refresh(){
    const active=[...selected,...highlighted,...(hovered?[hovered]:[])];
    const hits=new Set();
    for(const e of edges){const match=active.some(i=>eMatch(i,e));e.visible.setAttribute('opacity',active.length?(match?.9:.048):(e.cross_field?.53:.20));if(match&&e.show){hits.add(e.source);hits.add(e.target);}}
    for(const n of map.values()){
      const match=active.some(i=>nMatch(i,n));n.g.style.opacity=active.length&&!match&&!hits.has(n.author_id)?'.28':'1';
      n.g.querySelector('text').setAttribute('font-weight',match?'760':'450');
      n.g.firstChild.setAttribute('r',match?3.6:2.1);
    }
    for(const f of fields){const match=active.some(i=>norm(i).field_id===f.id);f.row.style.fontWeight=match?'750':'400';f.g.style.opacity=active.some(i=>norm(i).field_id)&&!match?'.42':'1';}
    const i=hovered||selected[0]||highlighted[0], k=norm(i);
    const n=map.get(i?.id), e=k.source&&edges.find(e=>eMatch(i,e)), f=k.field_id&&fields.find(f=>f.id===k.field_id), s=f&&k.subfield_id&&f.subs.find(s=>s.id===k.subfield_id);
    if(n){detailTitle.textContent=n.name;detailBody.textContent=`#${n.rank} · ${n.affiliated_works} Columbia-affiliated works\n${n.field} › ${n.subfield}\n${edges.filter(e=>e.show&&(e.source===n.author_id||e.target===n.author_id)).length} of ${n.partners} linked peers shown`;}
    else if(e){detailTitle.textContent=e.item.label;detailBody.textContent=`${e.shared_works} shared ${e.shared_works===1?'work':'works'} · ${e.cross_field?'Cross-field':'Within field'}\n${e.a.field}${e.cross_field?' ↔ '+e.b.field:''}${e.show?'':'\nNot shown with current filters'}`;}
    else if(s){detailTitle.textContent=s.name;detailBody.textContent=`${f.name} · ${s.nodes.length} ${s.nodes.length===1?'researcher':'researchers'}`;}
    else if(f){detailTitle.textContent=f.name;detailBody.textContent=`${f.count} ${f.count===1?'researcher':'researchers'} · ${f.subs.length} ${f.subs.length===1?'subfield':'subfields'}`;}
    else{detailTitle.textContent='Explore the network';detailBody.textContent='Hover a name, arc or link for details.\nClick to keep a selection.';}
  }
  draw();
  return {update(next){params={...params,...next};hovered=null;draw();},setSelection(items){selected=items||[];refresh();},highlight(items){highlighted=items||[];refresh();},destroy(){root.remove();}};
}
