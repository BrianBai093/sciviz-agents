export default function render(el, ctx) {
  const {authors, ties, brief, validation, fields} = ctx.data;
  const spec = brief.canvas ? brief : brief[0];
  const qa = validation[0];
  const W=ctx.width, H=ctx.height, small=W<850;
  const theme=ctx.theme.colors, ns='http://www.w3.org/2000/svg';
  const dark=/^#[0-9a-f]{6}$/i.test(theme.background)&&[1,3,5].map(i=>parseInt(theme.background.slice(i,i+2),16)).reduce((a,b)=>a+b,0)<350;
  const palette=dark ? {blue:'#83b8ff',orange:'#ffab76',grey:'#a5b3c5',light:'#232f41',warm:'#372b29',neutral:'#292f3a',edge:'#82a4d0',edge2:'#d6a185',ink:'#deebff'} : {blue:'#1c55a2',orange:'#ad451b',grey:'#5f6d82',light:'#f1f6ff',warm:'#fff3e9',neutral:'#f1f4f8',edge:'#506f9b',edge2:'#a55e3e',ink:'#1d3657'};
  const authorsBy=new Map(authors.map(d=>[d.author_id,d]));
  const adj=new Map(authors.map(d=>[d.author_id,[]]));
  ties.forEach(e=>{e.a=authorsBy.get(e.source_author_id);e.b=authorsBy.get(e.target_author_id);adj.get(e.a.author_id).push([e.b,e]);adj.get(e.b.author_id).push([e.a,e]);});
  const regions=['linked_main','linked_second','isolates'];
  const tint=[palette.light,palette.warm,palette.neutral], panelColor=[palette.blue,palette.orange,palette.grey];
  // Match V2’s field palette and order of first appearance in the radial leaves.
  const fieldPalette=dark?['#d9a5dc','#78cee2','#deb67b','#9caefc','#a4cc81','#da9bb2','#65cdb0','#d2a8ff','#d0bd61','#93abfa','#eea487','#9cd8d7','#d7b4ec','#aacf96']:['#8c5486','#34778e','#976937','#6570aa','#657c32','#a04e72','#267c68','#8b64a6','#8d7027','#4664af','#af5d42','#377c80','#815e93','#567641'];
  const fieldById=new Map(), fieldByAuthor=new Map();
  for(const d of fields.slice().sort((a,b)=>a.leaf_order-b.leaf_order)){
    if(!fieldById.has(d.field_id))fieldById.set(d.field_id,{name:d.field,color:fieldPalette[fieldById.size]});
    fieldByAuthor.set(d.author_id,fieldById.get(d.field_id));
  }
  const fieldOf=d=>fieldByAuthor.get(d.author_id);
  const colorOf=d=>fieldOf(d).color;
  const rad=d=>18*Math.sqrt(d.columbia_affiliated_work_count/259);
  const line=w=>0.61*Math.sqrt(w);
  const normalize=s=>String(s).normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase().replace(/[‐‑–—-]/g,' ');
  const key=e=>({source_author_id:e.source_author_id,target_author_id:e.target_author_id});
  const pair=e=>e.a.display_name+' & '+e.b.display_name;
  const fmt=new Intl.NumberFormat('en-US');
  let params={minShared:1,labels:'Anchors',...ctx.params}, external=[], highlights=[], chosen=null, localPair=null, focusOverride=false;
  let view={z:1,dx:0,dy:0}, drag=null, suppressClick=false;
  function html(tag, parent, cls, text){const q=document.createElement(tag);if(cls)q.className=cls;if(text!=null)q.textContent=text;parent.append(q);return q;}
  function svg(tag,parent,attrs,text){const q=document.createElementNS(ns,tag);Object.entries(attrs||{}).forEach(([k,v])=>q.setAttribute(k,v));if(text!=null)q.textContent=text;parent.append(q);return q;}
  const root=html('section',el,'cc-root');
  const paper=theme.background && theme.background!=='transparent' ? theme.background : (dark?'#19222e':'#ffffff');
  Object.assign(root.style,{'--bg':paper,'--surface':theme.surface || (dark?'#222d3b':'#f7f9fc'),'--text':theme.text,'--muted':theme.textMuted || palette.grey,'--grid':theme.grid || (dark?'#45566d':'#d3dbe6'),'--border':dark?'#526277':'#c5cfdd','--blue':palette.blue,'--ink':palette.ink, fontFamily:ctx.theme.fontFamily,width:W+'px',height:H+'px'});
  const style=html('style',root);style.textContent=`
   .cc-root{position:relative;display:flex;flex-direction:column;box-sizing:border-box;background:var(--bg);color:var(--text);isolation:isolate;font-size:13px;line-height:1.4;overflow:hidden}
   .cc-root *{box-sizing:border-box} .cc-root button,.cc-root input{font:inherit;color:var(--text)}
   .cc-head{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:19px 26px 13px;flex:none}
   .cc-kicker{font-size:10px;letter-spacing:.16em;font-weight:750;color:var(--blue);text-transform:uppercase}
   .cc-head h1{font-size:clamp(20px,3.05vw,39px);letter-spacing:-.045em;line-height:1.09;margin:4px 0 5px;font-weight:740}
   .cc-sub{color:var(--muted);font-size:13px;margin:0}
   .cc-tools{width:min(25%,292px);min-width:177px;position:relative;flex:none;z-index:5;align-self:center}
   .cc-tools label{display:block;font-size:11px;font-weight:700;margin-bottom:4px}
   .cc-search{width:100%;padding:8px 10px;border:1px solid var(--grid);border-radius:7px;background:var(--surface)}
   .cc-results{position:absolute;top:100%;left:0;right:0;background:var(--bg);border:1px solid var(--grid);border-radius:7px;max-height:250px;overflow:auto;box-shadow:0 7px 25px #14233b24}
   .cc-results[hidden],.cc-tip[hidden],.cc-info[hidden]{display:none}
   .cc-results button,.cc-neighbors button{display:block;width:100%;text-align:left;border:0;background:transparent;padding:7px 9px;cursor:pointer}
   .cc-results button:hover,.cc-neighbors button:hover,.cc-results button[aria-selected=true]{background:var(--surface);color:var(--blue)}
   .cc-scene{position:relative;flex:1;min-height:0;margin:0 15px}
   .cc-map{display:block;touch-action:none;outline-offset:-3px;cursor:grab}
   .cc-map:active{cursor:grabbing}.cc-map [data-id],.cc-map [data-key]{cursor:pointer}
   .cc-map [data-id]:focus-visible circle{stroke:var(--text);stroke-width:4}
   .cc-map text{user-select:none}
   .cc-zoom{display:flex;gap:3px;position:absolute;bottom:9px;left:10px;padding:3px;border:1px solid var(--grid);background:var(--bg);border-radius:8px}
   .cc-zoom button,.cc-close{background:var(--surface);border:1px solid transparent;border-radius:5px;padding:3px 9px;cursor:pointer;white-space:nowrap}
   .cc-root button:focus-visible,.cc-root input:focus-visible,.cc-map:focus-visible{outline:2px solid var(--blue);outline-offset:-2px}
   .cc-map:focus:not(:focus-visible){outline:none}.cc-search,.cc-zoom,.cc-tip,.cc-info,.cc-results{border-color:var(--border)}.cc-zoom button,.cc-close{border-color:var(--border)}
   .cc-footer{display:grid;grid-template-columns:1fr 1fr .8fr;gap:18px;border-top:1px solid var(--grid);margin:7px 26px 0;padding:10px 0 11px;flex:none}
   .cc-footunit{display:flex;align-items:center;gap:10px;min-width:0}.cc-footunit svg{flex:none}
   .cc-footunit strong,.cc-reading strong{display:block;font-size:12px;margin-bottom:2px}.cc-footunit p,.cc-reading p{font-size:11px;line-height:1.35;color:var(--muted);margin:0}
   .cc-reading{border-left:1px solid var(--grid);padding-left:14px}
   .cc-fields{flex:none;margin:0 26px;padding:6px 0 9px;border-top:1px solid var(--border);max-height:28%;overflow:auto}
   .cc-fields h2{font-size:12px;line-height:1.4;margin:0 0 4px;font-weight:700}
   .cc-fieldlist{display:grid;grid-template-columns:1.55fr 1.3fr 1fr 1fr;gap:3px 14px;list-style:none;margin:0;padding:0;font-size:11px;line-height:1.25}
   .cc-fieldlist li{display:flex;align-items:baseline;gap:6px;min-width:0}
   .cc-swatch{box-sizing:border-box;width:10px;height:10px;border-radius:50%;display:inline-block;flex:none}
   .cc-fields:focus-visible{outline:2px solid var(--blue);outline-offset:-2px}
   .cc-root.narrow .cc-fields{margin:0 12px}
   .cc-root.narrow .cc-fieldlist{grid-template-columns:1.4fr 1.2fr 1fr}
   .cc-root.tiny .cc-fieldlist{grid-template-columns:1fr 1fr;gap:3px 8px}
   .cc-tip,.cc-info{position:absolute;z-index:4;border-radius:8px;background:var(--bg);border:1px solid var(--grid);box-shadow:0 5px 22px #14233b25;padding:10px 12px;width:max-content;max-width:min(300px,92%);line-height:1.45}
   .cc-tip{pointer-events:none;z-index:6;color:var(--muted);font-size:12px}.cc-tip strong,.cc-info strong{color:var(--text);font-size:13px;display:block;margin-bottom:2px}
   .cc-info{left:10px;top:8px;width:237px;font-size:12px;max-height:60%;overflow:auto;color:var(--muted)}
   .cc-info,.cc-tip,.cc-results,.cc-zoom{background-color:${dark?'#1d2838':'#fff'}}
   .cc-search,.cc-zoom button,.cc-close{background-color:${dark?'#253247':'#f6f8fc'}}
   .cc-root .cc-kicker{color:${palette.blue}} .cc-root .cc-sub,.cc-root .cc-footunit p,.cc-root .cc-reading p{color:${palette.grey}} .cc-footer{border-color:var(--border)}
   .cc-root .cc-neighbors button:hover,.cc-root .cc-results button:hover,.cc-root .cc-results button[aria-selected=true]{background:${palette.light}}
   .cc-close{float:right;font-size:14px;padding:0 6px;margin-left:5px}.cc-neighbors{max-height:145px;overflow:auto;border-top:1px solid var(--grid);margin-top:7px}
   .cc-neighbors button{padding:4px 1px;font-size:11px;display:flex;justify-content:space-between;gap:5px}.cc-neighbors button span:last-child{white-space:nowrap;color:var(--muted)}
   .cc-root.narrow .cc-head{padding:12px 13px 7px;gap:8px}.cc-root.narrow .cc-sub{font-size:11px}.cc-root.narrow .cc-tools{min-width:142px}.cc-root.narrow .cc-scene{margin:0 5px}.cc-root.narrow .cc-footer{margin:5px 12px 0;gap:9px;padding:6px 0}.cc-root.narrow .cc-footunit svg{display:none}
   .cc-root.tiny .cc-head{align-items:stretch;flex-direction:column}.cc-root.tiny .cc-tools{width:100%}.cc-root.tiny .cc-footer{grid-template-columns:1fr 1fr}.cc-root.tiny .cc-reading{display:none}
  `;
  if(small)root.classList.add('narrow');if(W<500)root.classList.add('tiny');
  const head=html('header',root,'cc-head');
  const title=html('div',head);
  html('div',title,'cc-kicker','Research collaboration  /  2021–2024');
  html('h1',title,'','Columbia’s collaboration network');
  const sub=html('p',title,'cc-sub');
  const tools=html('div',head,'cc-tools');
  const inputId='cc-search-'+Math.random().toString(36).slice(2);const resultsId=inputId+'-list';
  const lab=html('label',tools,'','Find a researcher');lab.htmlFor=inputId;
  const search=html('input',tools,'cc-search');search.id=inputId;search.type='search';search.placeholder='Name, rank, or author ID';search.autocomplete='off';
  search.setAttribute('role','combobox');search.setAttribute('aria-controls',resultsId);search.setAttribute('aria-expanded','false');search.setAttribute('aria-autocomplete','list');
  const results=html('div',tools,'cc-results');results.id=resultsId;results.setAttribute('role','listbox');results.hidden=true;
  const scene=html('div',root,'cc-scene');
  const map=svg('svg',scene,{class:'cc-map',tabindex:0,role:'group','aria-label':'Force-directed collaboration network. Use plus or minus to zoom, arrow keys to pan, and 0 to reset.'});
  const panelLayer=svg('g',map,{'pointer-events':'none'}), tieLayer=svg('g',map), nodeLayer=svg('g',map), nameLayer=svg('g',map,{'pointer-events':'none','aria-hidden':'true'});
  const info=html('aside',scene,'cc-info');info.hidden=true;info.setAttribute('aria-live','polite');
  const tip=html('div',scene,'cc-tip');tip.hidden=true;tip.setAttribute('role','tooltip');
  const zoom=html('div',scene,'cc-zoom');zoom.setAttribute('aria-label','Map zoom controls');
  const minus=html('button',zoom,'','−');minus.setAttribute('aria-label','Zoom out');
  const plus=html('button',zoom,'','+');plus.setAttribute('aria-label','Zoom in');
  const reset=html('button',zoom,'','Reset view');
  const foot=html('footer',root,'cc-footer');
  const u1=html('div',foot,'cc-footunit');const k1=svg('svg',u1,{width:88,height:46,viewBox:'0 0 88 46','aria-hidden':'true'});
  [75,250].forEach((w,i)=>{const r=rad({columbia_affiliated_work_count:w})*.80; svg('circle',k1,{cx:i?64:21,cy:30-r,r,fill:palette.grey});svg('text',k1,{x:i?64:21,y:44,'text-anchor':'middle',fill:theme.textMuted,'font-size':10},w);});
  const copy1=html('div',u1);html('strong',copy1,'','Circle area · affiliated works');html('p',copy1,'','Distinct works with Columbia affiliation on the researcher’s own byline.');
  const u2=html('div',foot,'cc-footunit');const k2=svg('svg',u2,{width:82,height:46,viewBox:'0 0 82 46','aria-hidden':'true'});
  [1,10,85].forEach((w,i)=>{const y=8+i*15;svg('line',k2,{x1:3,y1:y,x2:48,y2:y,stroke:palette.edge,'stroke-width':line(w)});svg('text',k2,{x:57,y:y+3.3,fill:theme.textMuted,'font-size':10},w);});
  const copy2=html('div',u2);html('strong',copy2,'','Line width · shared works');html('p',copy2,'','Distinct works per pair, regardless of affiliation. Width uses a square-root scale.');
  const reading=html('div',foot,'cc-reading');html('strong',reading,'','How to explore');html('p',reading,'','Select a researcher to trace direct ties. Drag to pan. Layout distance has no quantitative scale.');
  const fieldLegend=html('section',root,'cc-fields');
  const fieldHeading=html('h2',fieldLegend,'','Circle color · OpenAlex field');fieldHeading.id=inputId+'-fields';
  fieldLegend.setAttribute('aria-labelledby',fieldHeading.id);
  const fieldList=html('ul',fieldLegend,'cc-fieldlist');fieldList.setAttribute('role','list');
  for(const {name,color} of fieldById.values()){
    const entry=html('li',fieldList);
    const swatch=html('span',entry,'cc-swatch');swatch.style.backgroundColor=color;swatch.setAttribute('aria-hidden','true');
    html('span',entry,'',name);
  }
  if(fieldLegend.scrollHeight>fieldLegend.clientHeight)fieldLegend.tabIndex=0;
  const mw=scene.clientWidth, mh=scene.clientHeight;
  map.setAttribute('width',mw);map.setAttribute('height',mh);map.setAttribute('viewBox',`0 0 ${mw} ${mh}`);
  const bounds=[36,18,1408,858];
  const base=Math.min((mw-16)/(bounds[2]-bounds[0]),(mh-14)/(bounds[3]-bounds[1]));
  const cx=(bounds[0]+bounds[2])/2,cy=(bounds[1]+bounds[3])/2;
  const xyz=(x,y)=>[mw/2+view.dx+(x-cx)*base*view.z,mh/2+view.dy+(y-cy)*base*view.z];
  const ss=()=>base*view.z;
  const edges=new Map(), nodes=new Map();
  ties.slice().sort((a,b)=>a.shared_snapshot_work_count-b.shared_snapshot_work_count).forEach(e=>{
    const g=svg('g',tieLayer,{'data-type':'coauthorship','data-key':JSON.stringify(key(e)),'data-label':pair(e),'aria-label':`${pair(e)}: ${e.shared_snapshot_work_count} shared works`});
    const l=svg('line',g,{'stroke-linecap':'round','pointer-events':'none'});
    const hit=svg('line',g,{stroke:'transparent','pointer-events':'stroke'});
    edges.set(e,{g,l,hit});
    g.addEventListener('pointerenter',ev=>{l.setAttribute('stroke-opacity','1');l.setAttribute('stroke',palette.ink);showTip(ev,pair(e),[`${fmt.format(e.shared_snapshot_work_count)} distinct shared works`]);});
    g.addEventListener('pointermove',placeTip);g.addEventListener('pointerleave',()=>{tip.hidden=true;applyFocus();});
    g.addEventListener('click',()=>{if(!suppressClick){chosen=null;localPair=e;focusOverride=true;tip.hidden=true;applyFocus();drawInfo();}});
  });
  authors.forEach(d=>{
    const g=svg('g',nodeLayer,{'data-id':d.author_id,'data-type':'author','data-label':d.display_name,tabindex:0,role:'button','aria-label':`${d.display_name}, rank ${d.prolificness_rank}, ${d.columbia_affiliated_work_count} Columbia-affiliated works, ${d.degree} ties. OpenAlex field: ${fieldOf(d).name}`});
    const ring=svg('circle',g,{fill:'none','pointer-events':'none'});
    const dot=svg('circle',g,{fill:colorOf(d),stroke:theme.background,'stroke-width':1.4});
    nodes.set(d.author_id,{g,ring,dot,d});
    g.addEventListener('pointerenter',ev=>{ring.setAttribute('stroke',colorOf(d));ring.setAttribute('stroke-width',1.8);showTip(ev,d.display_name,authorLines(d));});
    g.addEventListener('pointermove',placeTip);g.addEventListener('pointerleave',()=>{tip.hidden=true;applyFocus();});
    g.addEventListener('click',()=>{if(!suppressClick)choose(d,false,false);});
    g.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();ev.stopPropagation();choose(d,true,false);}});
  });
  function authorLines(d){return [`Rank #${d.prolificness_rank} · ${fmt.format(d.columbia_affiliated_work_count)} Columbia-affiliated works`,d.degree?`${d.degree} direct collaborators within the top 80`:'No ties within the top 80',`OpenAlex field: ${fieldOf(d).name}`];}
  function showTip(ev,title,lines){tip.replaceChildren();html('strong',tip,'',title);lines.forEach(t=>html('div',tip,'',t));tip.hidden=false;placeTip(ev);}
  function placeTip(ev){if(tip.hidden)return;const r=scene.getBoundingClientRect();let x=ev.clientX-r.left+13,y=ev.clientY-r.top+14;if(x+tip.offsetWidth>mw-4)x=ev.clientX-r.left-tip.offsetWidth-12;if(y+tip.offsetHeight>mh-4)y=ev.clientY-r.top-tip.offsetHeight-12;tip.style.left=Math.max(3,x)+'px';tip.style.top=Math.max(3,y)+'px';}
  function geometry(){
    panelLayer.replaceChildren();
    const [ix,iy]=xyz(53,96);info.style.left=Math.max(10,Math.min(ix,mw*.15))+'px';info.style.top=Math.max(8,Math.min(iy,mh*.18))+'px';
    const scale=ss();
    [k1,k2].forEach(k=>k.style.visibility='visible');
    [...k1.querySelectorAll('circle')].forEach((c,i)=>{const r=rad({columbia_affiliated_work_count:i?250:75})*Math.min(1,base);c.setAttribute('r',r);c.setAttribute('cy',34-r);});
    [...k2.querySelectorAll('line')].forEach((l,i)=>l.setAttribute('stroke-width',line([1,10,85][i])*Math.min(1,base)));
    const panelFont=Math.max(9,Math.min(16,15*base));
    const cap=Math.max(8,Math.min(10,10*base));
    const panelSpecs=[['01  /  LARGEST COMPONENT',`${qa.largest_component_size} researchers · 195 ties`],['02  /  SECOND COMPONENT',`${qa.second_component_size} researchers · 13 ties`],['03  /  ISOLATES','No ties within the top 80']];
    regions.forEach((id,i)=>{
      const b=spec.regions[id].panel_bounds.slice();if(i!==2)b[1]=27;if(i===1)b[3]=407;
      const [x,y]=xyz(b[0],b[1]),[x2,y2]=xyz(b[2],b[3]);
      svg('rect',panelLayer,{x,y,width:x2-x,height:y2-y,rx:Math.min(14,13*scale),fill:tint[i],stroke:theme.grid,'stroke-opacity':.65});
      const [tx,ty]=xyz(b[0]+19,b[1]+22);
      svg('text',panelLayer,{x:tx,y:ty,fill:panelColor[i],'font-size':cap,'font-weight':750,'letter-spacing':small?.75:1.25},panelSpecs[i][0]);
      svg('text',panelLayer,{x:tx,y:ty+panelFont+3,fill:theme.text,'font-size':panelFont,'font-weight':690},panelSpecs[i][1]);
      if(i===2)svg('text',panelLayer,{x:tx,y:ty+panelFont+cap+7,fill:theme.textMuted,'font-size':cap+1},`${qa.isolate_count} researchers`);
    });
    edges.forEach(({l,hit},e)=>{
      const [x1,y1]=xyz(e.a.x,e.a.y),[x2,y2]=xyz(e.b.x,e.b.y);
      for(const q of [l,hit])Object.entries({x1,y1,x2,y2}).forEach(([k,v])=>q.setAttribute(k,v));
      const w=line(e.shared_snapshot_work_count)*scale;
      l.setAttribute('stroke-width',w);hit.setAttribute('stroke-width',Math.max(4,w+3));
    });
    nodes.forEach(({d,g,dot,ring})=>{const [x,y]=xyz(d.x,d.y);g.setAttribute('transform',`translate(${x},${y})`);dot.setAttribute('r',rad(d)*scale);ring.setAttribute('r',rad(d)*scale+3);});
    drawNames();
  }
  const anchors=[1,3,4,5,10,17,77,58,47,69,64];
  const more=[2,6,11,12,18,19,21,24,28,31,32,40,46,50,52,54,59,61,65,68,73,74,78,79,80];
  function active(){const list=focusOverride?[]:external;const ids=new Set([...list,...highlights].filter(i=>i.type==='author').map(i=>String(i.id)));if(chosen)ids.add(chosen.author_id);const pairs=[...list,...highlights].filter(i=>i.type==='coauthorship'&&i.key).map(i=>typeof i.key==='string'?JSON.parse(i.key):i.key);if(localPair)pairs.push(key(localPair));return {ids,pairs};}
  function drawNames(){
    nameLayer.replaceChildren();
    const {ids,pairs}=active(), scale=ss();
    pairs.forEach(p=>{ids.add(p.source_author_id);ids.add(p.target_author_id);});
    const names=new Set(params.labels==='None'?[]:small&&params.labels==='Anchors'?[1,3,5,10,77]:params.labels==='More'?[...anchors,...more]:anchors);
    const batch=authors.filter(d=>ids.has(d.author_id)||names.has(d.prolificness_rank)).sort((a,b)=>Number(ids.has(b.author_id))-Number(ids.has(a.author_id))||anchors.indexOf(b.prolificness_rank)-anchors.indexOf(a.prolificness_rank));
    const occupied=authors.map(d=>{const [x,y]=xyz(d.x,d.y),r=rad(d)*scale+3;return [x-r,y-r,x+r,y+r];});
    const intersects=(a,b)=>a[0]<b[2]&&b[0]<a[2]&&a[1]<b[3]&&b[1]<a[3];
    const side=xyz(1052,0)[0];
    const fs=small?10:12;
    const labelStroke=dark?'#253142':'#f5f8ff';
    for(const d of batch){
      const on=ids.has(d.author_id);if(ids.size&&!on)continue;
      const [x,y]=xyz(d.x,d.y), r=rad(d)*scale;
      const region=regions.indexOf(d.layout_region);
      const text=svg('text',nameLayer,{x:0,y:0,fill:palette.ink,stroke:labelStroke,'paint-order':'stroke','stroke-width':3.3,'stroke-linejoin':'round','font-size':fs,'font-weight':on?750:630},d.display_name);
      const w=text.getComputedTextLength();const gap=r+5;
      const placements=[[x+gap,y+fs*.32],[x-gap-w,y+fs*.32],[x-w/2,y+gap+fs],[x-w/2,y-gap]];
      if(!small&&(on||d.prolificness_rank===1||d.prolificness_rank===3)){
        for(const h of [19,34,53,75]) placements.push([x-r-10-w,y-h],[x+r+10,y-h],[x-w/2,y-gap-h],[x+r+10,y+h],[x-r-10-w,y+h]);
      }
      const target=placements.find(([a,b])=>{
        const box=[a-2,b-fs,a+w+2,b+4];
        return box[0]>=4&&box[2]<=mw-4&&box[1]>=4&&box[3]<=mh-4&&(region===0?box[2]<side:box[0]>side)&&!occupied.some(v=>intersects(box,v));
      });
      if(target){
        const [a,b]=target;text.setAttribute('x',a);text.setAttribute('y',b);occupied.push([a-3,b-fs-2,a+w+3,b+5]);
        if(placements.indexOf(target)>=4){const lx=Math.max(a,Math.min(a+w,x)),ly=b-fs*.4,dist=Math.hypot(lx-x,ly-y);if(dist>r+5){const f=(r+2)/dist;const leader=svg('line',nameLayer,{x1:x+f*(lx-x),y1:y+f*(ly-y),x2:lx,y2:ly,stroke:colorOf(d),'stroke-width':.85,'stroke-opacity':.8});nameLayer.insertBefore(leader,text);}}
      }else text.remove();
    }
  }
  function applyFocus(){
    let count=0;
    const {ids,pairs}=active(), focus=!!(ids.size||pairs.length), close=new Set(ids), min=Number(params.minShared)||1;
    edges.forEach(({g,l},e)=>{
      const visible=e.shared_snapshot_work_count>=min;
      g.style.display=visible?'':'none';if(!visible)return;count++;
      const pairFocus=pairs.some(p=>p.source_author_id===e.source_author_id&&p.target_author_id===e.target_author_id);
      const related=pairFocus||ids.has(e.a.author_id)||ids.has(e.b.author_id);
      if(related){close.add(e.a.author_id);close.add(e.b.author_id);}
      l.setAttribute('stroke',focus&&related?(e.a.component_order===1?palette.blue:palette.orange):(e.a.component_order===1?palette.edge:palette.edge2));
      l.setAttribute('stroke-opacity',focus?(related?.87:.11):(dark?.59:.50));
    });
    nodes.forEach(({g,dot,ring,d},id)=>{const selected=ids.has(id), near=close.has(id);dot.setAttribute('opacity',!focus||near?1:.27);ring.setAttribute('stroke',selected?colorOf(d):'none');ring.setAttribute('stroke-width',selected?2:0);g.setAttribute('aria-pressed',selected);});
    sub.textContent=`Top ${qa.selected_author_count} by Columbia-affiliated works · ${count===ties.length?`${ties.length} coauthorship ties`:`${count} of ${ties.length} ties shown`}`;
    drawNames();
  }
  function drawInfo(){
    const {ids,pairs}=active();
    const d=chosen||authorsBy.get([...ids][0]);
    const e=localPair||ties.find(t=>pairs.some(p=>p.source_author_id===t.source_author_id&&p.target_author_id===t.target_author_id));
    info.hidden=!d&&!e;info.replaceChildren();if(info.hidden)return;
    const clear=html('button',info,'cc-close','×');clear.setAttribute('aria-label','Clear focus');clear.onclick=clearFocus;
    if(d){
      html('strong',info,'',d.display_name);authorLines(d).forEach(s=>html('div',info,'',s));
      const visible=adj.get(d.author_id).filter(([,e])=>e.shared_snapshot_work_count>=params.minShared).sort((a,b)=>b[1].shared_snapshot_work_count-a[1].shared_snapshot_work_count);
      if(d.degree){
        const caption=html('div',info,'',visible.length===d.degree?'Direct ties · shared works':`${visible.length} of ${d.degree} direct ties shown`);caption.style.marginTop='6px';caption.style.fontWeight='700';
        if(visible.length){const list=html('div',info,'cc-neighbors');visible.forEach(([other,e])=>{const b=html('button',list);b.type='button';b.title=`Focus ${other.display_name}`;html('span',b,'',other.display_name);html('span',b,'',fmt.format(e.shared_snapshot_work_count));b.setAttribute('aria-label',`${other.display_name}, ${e.shared_snapshot_work_count} shared works. Focus researcher.`);b.onclick=()=>{choose(other,true,true);info.querySelector('.cc-close')?.focus();};});}
      }
    }else{
      html('strong',info,'',pair(e));html('div',info,'',`${fmt.format(e.shared_snapshot_work_count)} distinct shared works`);
      if(e.shared_snapshot_work_count<params.minShared)html('div',info,'','This tie is hidden by the current minimum.');
    }
  }
  function item(d){return {type:'author',id:d.author_id,label:d.display_name};}
  function choose(d,notify,reveal){
    chosen=d;localPair=null;focusOverride=true;tip.hidden=true;
    if(reveal){const [x,y]=xyz(d.x,d.y);if(x<mw*.24||x>mw*.90||y<mh*.13||y>mh*.85){if(view.z>1){view.dx+=mw*.57-x;view.dy+=mh*.48-y;}geometry();}}
    applyFocus();drawInfo();if(notify)ctx.host.select([item(d)],{mode:'replace'});
  }
  function clearFocus(){chosen=null;localPair=null;external=[];highlights=[];focusOverride=false;search.value='';tip.hidden=true;applyFocus();drawInfo();ctx.host.select([],{mode:'replace'});}
  let matches=[], cursor=-1;
  function closeResults(){results.hidden=true;search.setAttribute('aria-expanded','false');search.removeAttribute('aria-activedescendant');cursor=-1;}
  function showResults(){
    const q=normalize(search.value.trim());
    matches=/^#?\d+$/.test(q)?authors.filter(d=>d.prolificness_rank===Number(q.replace('#',''))):authors.filter(d=>[normalize(d.display_name),normalize(d.author_id)].some(s=>s.includes(q)));cursor=-1;
    results.replaceChildren();search.removeAttribute('aria-activedescendant');
    if(!matches.length){const msg=html('div',results,'','No matching researchers');msg.style.padding='8px';}
    matches.forEach((d,i)=>{const b=html('button',results,'',`${d.display_name} · #${d.prolificness_rank}`);b.id=resultsId+'-'+i;b.tabIndex=-1;b.setAttribute('role','option');b.setAttribute('aria-selected','false');b.onpointerdown=ev=>ev.preventDefault();b.onclick=()=>pickResult(d);});
    results.hidden=false;search.setAttribute('aria-expanded','true');
  }
  function pickResult(d){search.value=d.display_name;closeResults();choose(d,true,true);}
  search.addEventListener('input',showResults);search.addEventListener('focus',showResults);
  search.addEventListener('blur',closeResults);
  search.addEventListener('keydown',ev=>{
    if(ev.key==='Escape'){if(!results.hidden){ev.stopPropagation();closeResults();}return;}
    if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){
      ev.preventDefault();if(results.hidden)showResults();if(!matches.length)return;
      cursor=(cursor<0?(ev.key==='ArrowDown'?0:matches.length-1):((cursor+(ev.key==='ArrowDown'?1:-1)+matches.length)%matches.length));
      [...results.children].forEach((b,i)=>b.setAttribute('aria-selected',String(i===cursor)));const b=results.children[cursor];search.setAttribute('aria-activedescendant',b.id);b.scrollIntoView({block:'nearest'});
    }else if(ev.key==='Enter'&&!results.hidden&&matches.length){ev.preventDefault();pickResult(matches[Math.max(0,cursor)]);}
  });
  function scaleAt(f,x=mw/2,y=mh/2){const z=Math.max(1,Math.min(5,view.z*f));const m=z/view.z;view={z,dx:z===1?0:x-mw/2-(x-mw/2-view.dx)*m,dy:z===1?0:y-mh/2-(y-mh/2-view.dy)*m};tip.hidden=true;geometry();}
  plus.onclick=()=>scaleAt(1.32);minus.onclick=()=>scaleAt(1/1.32);reset.onclick=()=>{view={z:1,dx:0,dy:0};tip.hidden=true;geometry();};
  map.addEventListener('wheel',ev=>{ev.preventDefault();const b=map.getBoundingClientRect();scaleAt(Math.exp(-ev.deltaY*.002),ev.clientX-b.left,ev.clientY-b.top);},{passive:false});
  map.addEventListener('keydown',ev=>{const k=ev.key;if(k==='+'||k==='=')scaleAt(1.32);else if(k==='-')scaleAt(1/1.32);else if(k==='0')reset.click();else if(k.startsWith('Arrow')){view.dx+=(k==='ArrowRight'?-38:k==='ArrowLeft'?38:0);view.dy+=(k==='ArrowDown'?-38:k==='ArrowUp'?38:0);geometry();}else if(k==='Escape'){clearFocus();}else{return;}ev.preventDefault();});
  map.addEventListener('pointerdown',ev=>{if(ev.button!==0)return;suppressClick=false;drag={x:ev.clientX,y:ev.clientY,dx:view.dx,dy:view.dy,id:ev.pointerId,moved:false};});
  map.addEventListener('pointermove',ev=>{if(!drag||drag.id!==ev.pointerId)return;if(!drag.moved&&Math.hypot(ev.clientX-drag.x,ev.clientY-drag.y)<5)return;if(!drag.moved){drag.moved=true;map.setPointerCapture(ev.pointerId);}view.dx=drag.dx+ev.clientX-drag.x;view.dy=drag.dy+ev.clientY-drag.y;tip.hidden=true;geometry();});
  function endDrag(){if(drag?.moved){suppressClick=true;setTimeout(()=>suppressClick=false,0);}drag=null;}
  map.addEventListener('pointerup',endDrag);map.addEventListener('pointercancel',endDrag);map.addEventListener('pointerleave',()=>{if(drag&&!drag.moved)drag=null;});
  geometry();applyFocus();
  return {
    update(p){params={...params,...p};applyFocus();drawInfo();},
    setSelection(items){external=items||[];focusOverride=false;chosen=null;localPair=null;applyFocus();drawInfo();},
    highlight(items){highlights=items||[];applyFocus();drawInfo();},
    getState(){return {...view};},setState(s){if(Number.isFinite(s?.z)){view={...s};geometry();}},
    destroy(){root.remove();}
  };
}
