import {line, curveBundle} from 'd3-shape@3.2.0';

export default function render(el, ctx) {
  const {authors, hierarchy, ties, summary}=ctx.data;
  const colors=ctx.theme.colors, W=ctx.width,H=ctx.height;
  const narrow=W<660, tau=2*Math.PI;
  const dark=/^#[\da-f]{6}$/i.test(colors.background||'') && [1,3,5].reduce((a,i)=>a+parseInt(colors.background.slice(i,i+2),16),0)<350;
  const cross=dark?'#aebcff':'#414fa6', within=dark?'#a5adbf':'#788091', ink=colors.text||(dark?'#edf1fb':'#18243a');
  const paper=colors.background&&colors.background!=='transparent'?colors.background:'#fff';
  const palette=dark?['#d9a5dc','#78cee2','#deb67b','#9caefc','#a4cc81','#da9bb2','#65cdb0','#d2a8ff','#d0bd61','#93abfa','#eea487','#9cd8d7','#d7b4ec','#aacf96']:['#8c5486','#34778e','#976937','#6570aa','#657c32','#a04e72','#267c68','#8b64a6','#8d7027','#4664af','#af5d42','#377c80','#815e93','#567641'];
  const A=authors.slice().sort((a,b)=>a.leaf_order-b.leaf_order), authorBy=new Map(A.map(a=>[a.author_id,a]));
  const hierBy=new Map(hierarchy.map(h=>[h.hierarchy_id,h]));
  const F=hierarchy.filter(h=>h.level==='field').sort((a,b)=>a.leaf_order_start-b.leaf_order_start);
  const S=hierarchy.filter(h=>h.level==='subfield');
  const fieldBy=new Map(F.map((f,i)=>[String(f.field_id),{...f,index:i+1,color:palette[i]}]));
  const subBy=new Map(S.map(s=>[s.hierarchy_id,s]));
  const pairs=summary.filter(s=>s.scope==='full_network'&&s.row_type==='field_pair').sort((a,b)=>a.pair_display_order-b.pair_display_order);
  const main=summary.find(s=>s.scope==='largest_component'&&s.row_type==='scope_total');
  const kEdge=e=>({source_author_id:e.source_author_id,target_author_id:e.target_author_id});
  const kPair=p=>({field_a_id:String(p.field_a_id),field_b_id:String(p.field_b_id)});
  const pairCode=(a,b)=>[String(a),String(b)].sort().join('|');
  const byPair=new Map(pairs.map(p=>[pairCode(p.field_a_id,p.field_b_id),p]));
  const eName=e=>`${e.source_display_name} × ${e.target_display_name}`;
  const aItem=a=>({type:'author',id:a.author_id,label:a.display_name});
  const eItem=e=>({type:'coauthorship',key:kEdge(e),label:eName(e)});
  const fItem=f=>({type:'field',key:{field_id:String(f.field_id)},label:f.label});
  const sItem=s=>({type:'subfield',key:{field_id:String(s.field_id),subfield_id:String(s.subfield_id)},label:s.label});
  const pItem=p=>({type:'field_pair',key:kPair(p),label:p.label});
  const isCross=e=>e.relationship==='inter_field';
  let params={minShared:1,tieVisibility:'All ties',bundleStrength:78,...ctx.params};
  let chosen=null, selected=[], highlighted=[], hovering=null, tab='Field pairs', query='', focusOverride=false;
  let shown=ties, shownCross=94;
  const html=(tag,parent,cls,text)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(text!=null)x.textContent=text;parent.append(x);return x;};
  const svg=(tag,parent,attrs,text)=>{const x=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs||{}))x.setAttribute(k,v);if(text!=null)x.textContent=text;parent.append(x);return x;};
  function mark(x,item){x.dataset.type=item.type;x.dataset.label=item.label;if(item.id!=null)x.dataset.id=item.id;else x.dataset.key=JSON.stringify(item.key);return x;}
  const root=html('section',el,'cb'+(narrow?' cb-stack':''));
  Object.assign(root.style,{width:W+'px',height:H+'px',fontFamily:ctx.theme.fontFamily});
  for(const [k,v] of Object.entries({paper,surface:colors.surface||(dark?'#242d40':'#f4f6fa'),ink,muted:colors.textMuted||(dark?'#acb8cc':'#536178'),grid:colors.grid||(dark?'#414d62':'#dce2ed'),cross,within}))root.style.setProperty('--'+k,v);
  const style=html('style',root);
  style.textContent=`
  .cb{box-sizing:border-box;display:flex;flex-direction:column;isolation:isolate;position:relative;overflow:hidden;background:var(--paper);color:var(--ink);font-size:13px;line-height:1.35}
  .cb *{box-sizing:border-box}.cb [hidden]{display:none!important}.cb button,.cb input{font:inherit;color:inherit}.cb button{cursor:pointer}.cb button:focus-visible,.cb input:focus-visible,.cb [tabindex]:focus-visible{outline:2px solid var(--cross);outline-offset:-2px}
  .cb-head{padding:17px 22px 11px;border-bottom:1px solid var(--grid);flex:none}.cb-eyebrow{color:var(--cross);font-weight:750;font-size:10px;letter-spacing:.14em;text-transform:uppercase}.cb h1{font-size:clamp(21px,3vw,33px);line-height:1.08;letter-spacing:-.036em;margin:4px 0 7px}.cb-stats{display:flex;align-items:center;flex-wrap:wrap;gap:4px 13px;color:var(--muted);font-size:12px}.cb-stats b{color:var(--ink)}.cb-stats .cb-em b{color:var(--cross)}
  .cb-body{display:grid;grid-template-columns:minmax(0,1fr) clamp(245px,32%,335px);flex:1;min-height:0}.cb-stage{min-width:0;min-height:0;display:flex;flex-direction:column;position:relative}.cb-legend{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:4px 14px;padding:10px 8px 0;color:var(--muted);font-size:11px;flex:none}.cb-legend span{white-space:nowrap}.cb-legend i{display:inline-block;vertical-align:middle;margin-right:5px}.cb-swatch{width:18px;border-top:2px solid var(--cross)}.cb-swatch.cb-within{border-color:var(--within);opacity:.65}.cb-open{width:8px;height:8px;border:1.4px solid var(--muted);border-radius:50%}
  .cb-scene{flex:1;min-height:0;position:relative}.cb-map{display:block;width:100%;height:100%;position:absolute;inset:0}.cb-map [data-type]{cursor:pointer}.cb-map text{pointer-events:none;user-select:none}.cb-map [data-type]:focus-visible{outline:none}.cb-map .cb-field:focus-visible path,.cb-map .cb-subfield:focus-visible path{stroke:var(--ink)}.cb-map .cb-dot:focus-visible .cb-node{stroke-width:2.5;stroke:var(--ink)}
  .cb-caption{flex:none;text-align:center;margin:0;padding:2px 10px 10px;color:var(--muted);font-size:11px}.cb-caption b{color:var(--ink);font-weight:650}
  .cb-side{border-left:1px solid var(--grid);padding:12px 13px 7px;min-height:0;display:flex;flex-direction:column;overflow:auto}.cb-sidehead{display:flex;align-items:center;justify-content:space-between;gap:5px;margin-bottom:7px}.cb h2{font-size:15px;margin:0;letter-spacing:-.015em}.cb-clear{background:var(--surface);border:1px solid var(--grid);border-radius:5px;padding:2px 7px;font-size:11px!important}.cb-tabs{display:flex;gap:3px;border:1px solid var(--grid);background:var(--surface);border-radius:7px;padding:3px;flex:none}.cb-tabs button{flex:1;white-space:nowrap;border:0;background:transparent;padding:4px 3px;border-radius:4px;font-weight:650;font-size:11px}.cb-tabs button[aria-pressed=true]{background:var(--paper);color:var(--cross);box-shadow:0 0 0 1px var(--grid)}
  .cb-detail{margin-top:8px;padding:7px 8px;border-left:3px solid var(--cross);background:var(--surface);font-size:11px;overflow:auto;max-height:37%;flex:none}.cb-detail b,.cb-tip b{display:block;color:var(--ink);font-size:12px;margin-bottom:2px}.cb-detail div,.cb-tip div{color:var(--muted)}.cb-detailrows{margin-top:5px}
  .cb-note{color:var(--muted);font-size:11px;margin:8px 0 5px;flex:none}.cb-search{width:100%;border:1px solid var(--grid);border-radius:5px;padding:5px 7px;background:var(--paper);margin:0 0 4px;flex:none}.cb-list{min-height:50px;overflow:auto;scrollbar-width:thin;flex:1}.cb-row{width:100%;display:flex;align-items:center;text-align:left;gap:7px;padding:6px 4px;border:0;border-bottom:1px solid var(--grid);background:transparent;font-size:11.5px!important;line-height:1.25;position:relative;isolation:isolate}.cb-row:hover,.cb-row:focus-visible,.cb-row[aria-pressed=true]{background:var(--surface);color:var(--cross)}.cb-label{flex:1;overflow-wrap:anywhere}.cb-count{font-size:11px;font-weight:750;font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--ink)}.cb-indexes{display:flex;gap:2px;flex:none}.cb-index{min-width:17px;padding:1px 2px;font-size:10px;font-weight:750;text-align:center;border-radius:3px;color:var(--idx);border:1px solid currentColor}.cb-rowbar{position:absolute;bottom:0;left:0;height:2px;background:var(--cross);opacity:.24;z-index:-1}.cb-empty{color:var(--muted);font-size:11px;padding:6px 3px}
  .cb-foot{border-top:1px solid var(--grid);padding:7px 22px 8px;flex:none;color:var(--muted);font-size:11px}.cb-foot b{color:var(--ink)}.cb-tip{position:absolute;z-index:4;pointer-events:none;background:var(--paper);border:1px solid var(--grid);border-radius:6px;box-shadow:0 4px 15px #11182724;padding:7px 9px;max-width:min(280px,calc(100% - 12px));font-size:11px}
  .cb-stack{overflow:auto}.cb-stack .cb-body{display:block;flex:none}.cb-stack .cb-side{border-left:0;border-top:1px solid var(--grid);height:290px}.cb-stack .cb-head,.cb-stack .cb-foot{padding-left:12px;padding-right:12px}.cb-stack .cb-legend{padding-top:7px}
  `;
  const head=html('header',root,'cb-head');
  html('div',head,'cb-eyebrow','Columbia coauthorship / 2021–2024');
  html('h1',head,'','Collaborations across fields');
  const stats=html('div',head,'cb-stats');stats.setAttribute('aria-live','polite');
  const body=html('div',root,'cb-body');
  const stage=html('div',body,'cb-stage');
  const legend=html('div',stage,'cb-legend');
  for(const [cls,txt] of [['cb-swatch','Cross-field tie'],['cb-swatch cb-within','Within-field tie'],['cb-open','Isolated researcher']]){const q=html('span',legend);html('i',q,cls);q.append(txt);}
  const scene=html('div',stage,'cb-scene');
  if(narrow)scene.style.height=Math.min(W-8,Math.max(226,Math.round(H*.55)))+'px';
  const map=svg('svg',scene,{class:'cb-map',role:'group','aria-label':'Radial network. Researchers sit inside the subfield and numbered field rings; use Explore to find exact counts and focus ties.'});
  const tip=html('div',root,'cb-tip');tip.hidden=true;tip.setAttribute('role','tooltip');
  const cap=html('p',stage,'cb-caption');cap.innerHTML='<b>Outer ring:</b> fields · <b>Inner ring:</b> subfields · <b>Line width:</b> shared works';
  const side=html('aside',body,'cb-side');side.setAttribute('aria-label','Explore collaboration counts');
  const sideHead=html('div',side,'cb-sidehead');html('h2',sideHead,'','Explore the network');
  const clear=html('button',sideHead,'cb-clear','Clear focus');clear.hidden=true;
  const tabs=html('div',side,'cb-tabs');tabs.setAttribute('aria-label','Explorer mode');
  const buttons=new Map();
  for(const mode of ['Field pairs','Fields','People']){const b=html('button',tabs,'',mode);buttons.set(mode,b);b.onclick=()=>{tab=mode;drawList(true);if(mode==='People')search.focus();};}
  const detail=html('div',side,'cb-detail');detail.hidden=true;detail.setAttribute('aria-live','polite');
  const note=html('p',side,'cb-note');
  const search=html('input',side,'cb-search');search.type='search';search.placeholder='Search name, field, subfield or ID';search.setAttribute('aria-label','Search researchers');search.hidden=true;
  const list=html('div',side,'cb-list');
  const foot=html('footer',root,'cb-foot');
  foot.innerHTML=`<b>Largest component:</b> ${main.scope_cross_field_tie_count} of ${main.scope_tie_count} ties cross fields (unfiltered). Groups use authors’ plurality OpenAlex field, then subfield within that field, based on primary topics of Columbia-affiliated works—not the topic of a shared work.`;

  const mw=scene.clientWidth||W, mh=scene.clientHeight||(narrow?250:H-175);
  const R=Math.max(28,Math.min(mw,mh)/2-36), cx=mw/2, cy=mh/2;
  map.setAttribute('viewBox',`0 0 ${mw} ${mh}`);
  const xy=d=>[cx+R*d.x_norm,cy+R*d.y_norm], polar=(a,r)=>[cx+r*Math.sin(a),cy-r*Math.cos(a)];
  function span(h){const i=h.leaf_order_start,j=h.leaf_order_end;return [(A[i].angle_rad+(i?A[i-1].angle_rad:A.at(-1).angle_rad-tau))/2,(A[j].angle_rad+(j<A.length-1?A[j+1].angle_rad:A[0].angle_rad+tau))/2];}
  function arc(a,b,r){const p=polar(a,r),q=polar(b,r);return `M${p.join(',')} A${r},${r} 0 ${b-a>Math.PI?1:0} 1 ${q.join(',')}`;}
  const links=svg('g',map), ringLayer=svg('g',map), nodeLayer=svg('g',map), labels=svg('g',map,{'aria-hidden':'true','pointer-events':'none'});
  const edgeMarks=[], nodeMarks=[], ringMarks=[];
  const widths=e=>.6+.16*Math.sqrt(e.shared_snapshot_work_count);
  function normalizeItem(i){if(!i)return null;let key=i.key;if(typeof key==='string'){try{key=JSON.parse(key);}catch{key={};}}return {...i,key:key||{}};}
  function signature(i){if(!i)return ''; const k=i.key||{};switch(i.type){case 'author':return 'a'+i.id;case 'coauthorship':return 'e'+pairCode(k.source_author_id,k.target_author_id);case 'field_pair':return 'p'+pairCode(k.field_a_id,k.field_b_id);case 'field':return 'f'+k.field_id;case 'subfield':return 's'+k.field_id+':'+k.subfield_id;default:return '';}}
  const edgeBy=new Map(ties.map(e=>[signature(eItem(e)),e]));
  function match(i,e){const k=i.key||{};switch(i.type){case 'author':return e.source_author_id===i.id||e.target_author_id===i.id;case 'coauthorship':return signature(eItem(e))===signature(i);case 'field_pair':return pairCode(e.source_field_id,e.target_field_id)===pairCode(k.field_a_id,k.field_b_id);case 'field':return [e.source_field_id,e.target_field_id].some(f=>String(f)===String(k.field_id));case 'subfield':return ['source','target'].some(x=>String(e[x+'_subfield_id'])===String(k.subfield_id)&&String(e[x+'_field_id'])===String(k.field_id));default:return false;}}
  function authorMatch(i,a){const k=i.key||{};switch(i.type){case 'author':return a.author_id===i.id;case 'field':return String(a.field_id)===String(k.field_id);case 'subfield':return String(a.field_id)===String(k.field_id)&&String(a.subfield_id)===String(k.subfield_id);case 'coauthorship':return [k.source_author_id,k.target_author_id].includes(a.author_id);default:return false;}}
  function content(i){
    const k=i.key||{}, count=ties.filter(e=>match(i,e)).length, visible=shown.filter(e=>match(i,e)).length;
    const tieCount=(total=count)=>visible===total?`${total} coauthor ${total===1?'pair':'pairs'}`:`${visible} of ${total} coauthor pairs shown`;
    if(i.type==='author'){const a=authorBy.get(String(i.id));if(a)return [a.display_name,[`Field: ${a.field}`,`Subfield: ${a.subfield}`,a.is_isolate?'Isolated in this cohort':tieCount(),`Affiliated-works rank: ${a.prolificness_rank}`]];}
    if(i.type==='coauthorship'){const e=edgeBy.get(signature(i));if(e)return [eName(e),[`${e.shared_snapshot_work_count} shared ${e.shared_snapshot_work_count===1?'work':'works'} · ${isCross(e)?'cross-field':e.relationship==='same_subfield'?'same subfield':'same field, different subfields'}`,`${e.source_display_name}: ${e.source_field} / ${e.source_subfield}`,`${e.target_display_name}: ${e.target_field} / ${e.target_subfield}`,...(visible?[]:['Hidden by current filters'])]];}
    if(i.type==='field_pair'){const p=byPair.get(pairCode(k.field_a_id,k.field_b_id));if(p)return [p.label,[tieCount(p.tie_count),'Cross-field · grouped by author labels']];}
    if(i.type==='field'){const f=fieldBy.get(String(k.field_id));if(f)return [`${f.index}. ${f.label}`,[`${f.descendant_author_count} researchers · ${S.filter(s=>String(s.field_id)===String(f.field_id)).length} subfields`,`${tieCount()} touching this field`]];}
    if(i.type==='subfield'){const s=subBy.get(`subfield:${k.field_id}:${k.subfield_id}`);if(s)return [s.label,[`Field: ${fieldBy.get(String(s.field_id)).label}`,`${s.descendant_author_count} ${s.descendant_author_count===1?'researcher':'researchers'} · ${tieCount()} touching this subfield`]];}
    return [i.label||'Selection',[]];
  }
  function fillDetail(el,i){el.replaceChildren();const [title,lines]=content(i);html('b',el,'',title);for(const t of lines)html('div',el,'',t);}
  function placeTip(ev){const b=root.getBoundingClientRect();const x=ev.clientX-b.left+root.scrollLeft+12,y=ev.clientY-b.top+root.scrollTop+12;tip.style.left=Math.max(5,Math.min(x,W-tip.offsetWidth-5))+'px';tip.style.top=Math.max(root.scrollTop+3,Math.min(y,root.scrollTop+H-tip.offsetHeight-5))+'px';}
  function showTip(ev,item){fillDetail(tip,item);tip.hidden=false;placeTip(ev);}
  function choose(i){chosen=i;focusOverride=true;hovering=null;tip.hidden=true;drawDetail();syncRows();paint();}
  function wire(x,item,{inMap=false,keyboard=false}={}){
    mark(x,item);
    if(inMap){const [title,lines]=content(item);x.setAttribute('aria-label',[title,...lines].join('. '));}
    if(keyboard){x.setAttribute('tabindex',0);x.setAttribute('role','button');x.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();choose(item);ctx.host.select([item],{mode:'replace'});}});}
    x.addEventListener('click',()=>choose(item));
    x.addEventListener('pointerenter',ev=>{hovering=item;if(inMap)showTip(ev,item);paint();});
    if(inMap)x.addEventListener('pointermove',placeTip);
    x.addEventListener('pointerleave',()=>{hovering=null;tip.hidden=true;paint();});
    if(inMap&&keyboard){x.addEventListener('focus',()=>{hovering=item;paint();});x.addEventListener('blur',()=>{hovering=null;paint();});}
  }
  const relationOrder={same_subfield:0,within_field_between_subfields:1,inter_field:2};
  for(const e of ties.slice().sort((a,b)=>relationOrder[a.relationship]-relationOrder[b.relationship]||b.shared_snapshot_work_count-a.shared_snapshot_work_count)){
    const g=svg('g',links,{class:'cb-link'}), p=svg('path',g,{class:'cb-path',fill:'none','stroke-linecap':'round','pointer-events':'none'}), hit=svg('path',g,{fill:'none',stroke:'transparent','pointer-events':'stroke','stroke-width':Math.max(3,widths(e))});
    const route=(Array.isArray(e.route_ids_json)?e.route_ids_json:JSON.parse(e.route_ids_json)).map(id=>xy(hierBy.get(id)));
    const item=eItem(e);wire(g,item,{inMap:true});edgeMarks.push({e,g,p,hit,route});
  }
  for(const h of [...F,...S]){
    const isField=h.level==='field', f=fieldBy.get(String(h.field_id));
    const item=isField?fItem(f):sItem(h), [a,b]=span(h);
    const g=svg('g',ringLayer,{class:isField?'cb-field':'cb-subfield'});
    const p=svg('path',g,{d:arc(a+(isField?.012:.008),b-(isField?.012:.008),R+(isField?16:7)),fill:'none',stroke:f.color,'stroke-width':isField?8:5,'stroke-opacity':isField?1:.57});
    wire(g,item,{inMap:true,keyboard:true});ringMarks.push({h,g,p,item,isField});
    if(isField){const [x,y]=polar((a+b)/2,R+27);svg('text',labels,{x,y,'dominant-baseline':'central','text-anchor':'middle',fill:f.color,'font-weight':750,'font-size':11},f.index);}
  }
  for(const a of A){
    const [x,y]=xy(a), f=fieldBy.get(String(a.field_id));
    const g=svg('g',nodeLayer,{class:'cb-dot'});
    svg('circle',g,{cx:x,cy:y,r:Math.min(6,Math.max(3.7,R*.028)),fill:'transparent'});
    const p=svg('circle',g,{class:'cb-node',cx:x,cy:y,r:Math.min(3.45,Math.max(2.1,R*.017)),fill:a.is_isolate?paper:f.color,stroke:a.is_isolate?f.color:paper,'stroke-width':a.is_isolate?1.3:.65,'pointer-events':'none'});
    wire(g,aItem(a),{inMap:true,keyboard:true});nodeMarks.push({a,g,p});
  }
  const focusLayer=svg('g',map,{'pointer-events':'none','aria-hidden':'true'});
  function paint(){
    const active=hovering?[hovering,...highlighted]:[...(chosen?[chosen]:[]),...(focusOverride?[]:selected),...highlighted];
    const touching=new Set();
    for(const m of edgeMarks){
      if(!m.visible)continue;
      const on=active.some(i=>match(i,m.e));const crossField=isCross(m.e);
      if(on){touching.add(m.e.source_author_id);touching.add(m.e.target_author_id);}
      m.p.setAttribute('stroke',crossField?cross:within);
      m.p.setAttribute('stroke-opacity',active.length?(on?(crossField?.92:.83):.052):(crossField?(dark?.54:.49):.27));
      m.p.setAttribute('stroke-width',widths(m.e)+(on?.65:0));
    }
    focusLayer.replaceChildren();
    for(const {a,g} of nodeMarks){
      const direct=active.some(i=>authorMatch(i,a)), linked=touching.has(a.author_id);
      g.setAttribute('opacity',!active.length||direct||linked?1:.27);
      if(active.some(i=>i.type==='author'&&a.author_id===i.id)){const [x,y]=xy(a);svg('circle',focusLayer,{cx:x,cy:y,r:6.3,fill:'none',stroke:ink,'stroke-width':1.4});}
    }
    for(const {h,p,isField,item} of ringMarks){
      const on=active.some(i=>signature(i)===signature(item)||isField&&i.type==='field_pair'&&[i.key.field_a_id,i.key.field_b_id].map(String).includes(String(h.field_id)));
      p.setAttribute('stroke-opacity',on?1:isField?.96:.57);p.setAttribute('stroke-width',on?(isField?10:7):(isField?8:5));
    }
  }
  function updateGeometry(){const draw=line().curve(curveBundle.beta(params.bundleStrength/100));for(const {route,p,hit} of edgeMarks){const d=draw(route);p.setAttribute('d',d);hit.setAttribute('d',d);}}
  function row(parent,item,label,ids,count,bar){
    const b=html('button',parent,'cb-row'); b.type='button';if(ids.length){const badges=html('span',b,'cb-indexes');for(const id of ids){const f=fieldBy.get(String(id));if(f){const t=html('span',badges,'cb-index',f.index);t.style.setProperty('--idx',f.color);t.setAttribute('aria-hidden','true');}}}
    html('span',b,'cb-label',label);if(count!=null)html('span',b,'cb-count',count);if(bar){const q=html('span',b,'cb-rowbar');q.style.width=bar+'%';}
    wire(b,item);b._item=item;b.setAttribute('aria-pressed',String(isFocused(item)));return b;
  }
  const isFocused=i=>[chosen,...(focusOverride?[]:selected)].some(j=>j&&signature(i)===signature(j));
  function syncRows(){for(const b of root.querySelectorAll('.cb-row'))b.setAttribute('aria-pressed',String(isFocused(b._item)));}
  const norm=x=>String(x).normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase();
  const alphabetical=A.slice().sort((a,b)=>a.display_name.localeCompare(b.display_name));
  function drawList(reset=false){
    const st=reset?0:list.scrollTop;
    list.replaceChildren();for(const [mode,b] of buttons)b.setAttribute('aria-pressed',String(tab===mode));
    search.hidden=tab!=='People';
    if(tab==='Field pairs'){
      note.textContent=shown.length===ties.length?`${pairs.length} cross-field combinations · unweighted coauthor pairs. Select to trace.`:'Cross-field pairs · shown / original counts.';
      for(const p of pairs){const i=pItem(p), n=shown.filter(e=>match(i,e)).length;row(list,i,p.label,[p.field_a_id,p.field_b_id],n===p.tie_count?`${n}`:`${n} / ${p.tie_count}`,100*n/pairs[0].tie_count);}
    }else if(tab==='Fields'){
      note.textContent='Numbered outer sectors · researcher counts. Select a field to list its subfields.';
      for(const f of fieldBy.values())row(list,fItem(f),f.label,[f.field_id],`${f.descendant_author_count}`);
    }else{
      const q=norm(query).trim();const people=alphabetical.filter(a=>!q||norm([a.display_name,a.field,a.subfield,a.author_id].join(' ')).includes(q));
      note.textContent=`${people.length} of ${A.length} researchers · select a name to trace direct ties.`;
      for(const a of people)row(list,aItem(a),a.display_name,[a.field_id],a.is_isolate?'Isolate':null);
      if(!people.length)html('div',list,'cb-empty','No matching researchers.');
    }
    list.scrollTop=st;
  }
  function drawDetail(){
    const i=chosen||(!focusOverride?selected[0]:null);clear.hidden=!i;detail.hidden=!i;
    if(!i){detail.replaceChildren();return;}
    fillDetail(detail,i);
    if(i.type==='field'){
      const sub=html('div',detail,'cb-detailrows');for(const s of S.filter(s=>String(s.field_id)===String(i.key.field_id)))row(sub,sItem(s),s.label,[],`${s.descendant_author_count}`);
    }else if(i.type==='author'){
      const sub=html('div',detail,'cb-detailrows');const neighbors=shown.filter(e=>match(i,e)).sort((a,b)=>b.shared_snapshot_work_count-a.shared_snapshot_work_count);
      for(const e of neighbors){const a=authorBy.get(e.source_author_id===i.id?e.target_author_id:e.source_author_id);row(sub,eItem(e),a.display_name,[a.field_id],`${e.shared_snapshot_work_count} works`);}
    }
  }
  function updateCounts(){
    shown=ties.filter(e=>e.shared_snapshot_work_count>=params.minShared&&(params.tieVisibility==='All ties'||(params.tieVisibility==='Cross-field only'?isCross(e):!isCross(e))));
    const visible=new Set(shown);shownCross=shown.filter(isCross).length;
    for(const m of edgeMarks){m.visible=visible.has(m.e);m.g.style.display=m.visible?'':'none';}
    stats.innerHTML=`<span><b>${A.length}</b> researchers</span><span><b>${A.filter(a=>a.is_isolate).length}</b> isolates</span><span><b>${shown.length}${shown.length===ties.length?'':` / ${ties.length}`}</b> ties${shown.length===ties.length?'':' shown'}</span><span class="cb-em"><b>${shownCross}</b> cross-field${shown.length===ties.length?'':' shown'}</span>`;
  }
  search.addEventListener('input',()=>{query=search.value;drawList(true);});
  search.addEventListener('keydown',ev=>{if(ev.key==='Enter'){const b=list.querySelector('button');if(b){ev.preventDefault();choose(b._item);ctx.host.select([b._item],{mode:'replace'});}}});
  clear.onclick=()=>{chosen=null;selected=[];focusOverride=false;hovering=null;tip.hidden=true;drawDetail();syncRows();paint();ctx.host.select([],{mode:'replace'});};
  updateCounts();updateGeometry();drawList();paint();
  return {
    update(next){const geometry=next.bundleStrength!=null&&next.bundleStrength!==params.bundleStrength;params={...params,...next};hovering=null;tip.hidden=true;updateCounts();if(geometry)updateGeometry();drawDetail();drawList();paint();},
    setSelection(items){const next=items.map(normalizeItem).filter(i=>signature(i));if(chosen&&!next.some(i=>signature(i)===signature(chosen)))chosen=null;selected=next;focusOverride=false;drawDetail();syncRows();paint();},
    highlight(items){highlighted=items.map(normalizeItem).filter(i=>signature(i));paint();},
    destroy(){root.remove();}
  };
}
