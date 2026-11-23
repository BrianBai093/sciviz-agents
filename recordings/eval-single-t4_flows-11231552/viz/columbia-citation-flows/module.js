import { sankey, sankeyLinkHorizontal } from 'd3-sankey@0.12.3';

export default function render(el, ctx) {
  const c = ctx.theme.colors, a = ctx.data.audit[0], nf = new Intl.NumberFormat('en-US');
  const num=n=>nf.format(n), pct=(n,d)=>(100*n/d).toFixed(1)+'%';
  const W=ctx.width, H=ctx.height, pad=W<600?14:24;
  const color={same:'#637fb4',cross:'#148b83',unknown:'#8a8994'};
  const names={same:'Same field',cross:'Different fields',unknown:'Unclassified endpoint'};
  const base={same:.60,cross:.47,unknown:.68};
  const labels=new Map([['other','Other fields'],['unknown','Unclassified']]);
  const flows=ctx.data.flows;
  for(const r of flows){labels.set(r.source_id,r.source);labels.set(r.target_id,r.target);}
  const short={'13':'Biochemistry, Genetics & Molecular Biology','19':'Earth & Planetary Sciences','20':'Economics, Econometrics & Finance','11':'Agricultural & Biological Sciences','12':'Arts & Humanities','31':'Physics & Astronomy','14':'Business, Management & Accounting','30':'Pharmacology, Toxicology & Pharmaceutics','16':'Chemistry','34':'Veterinary','29':'Nursing'};
  // Short forms are used only when the chart is narrow; every mark retains the full name.
  const canvas=document.createElement('canvas').getContext('2d');
  const wrap=(label,width,size)=>{
    canvas.font=`500 ${size}px ${ctx.theme.fontFamily || 'sans-serif'}`;
    const out=[]; let line='';
    for(const word of label.split(' ')) { const next=line?line+' '+word:word; if(line&&canvas.measureText(next).width>width){out.push(line);line=word;}else line=next; }
    if(line)out.push(line); return out;
  };
  let P={...ctx.params}, sel=[], hi=[], over=null, marks=[], tip;
  const root=document.createElement('div'); el.appendChild(root);
  Object.assign(root.style,{position:'relative',width:'100%',height:'100%',background:c.background,color:c.text,fontFamily:ctx.theme.fontFamily||'sans-serif',overflow:'hidden'});
  const add=(parent,tag,attrs={},text)=>{
    const node=document.createElementNS('http://www.w3.org/2000/svg',tag);
    for(const [k,v] of Object.entries(attrs))node.setAttribute(k,v);
    if(text!==undefined)node.textContent=text;
    parent.appendChild(node);return node;
  };
  const freezeKey=o=>JSON.stringify(Object.keys(o||{}).sort().map(k=>[k,o[k]]));
  function matches(m,i){
    if(i.type==='field' && i.id!=null) return m.ids.includes(String(i.id));
    if(i.key && m.key && freezeKey(i.key)===freezeKey(m.key))return true;
    if(i.key){
      const {source_id,target_id,flow}=i.key;
      if(!flow && m.kind==='link' && ((source_id&&m.ids[0]===source_id)||(target_id&&m.ids[1]===target_id)))return true;
      if(flow && m.kind==='node' && m.ids[0]===(m.side==='left'?source_id:target_id))return true;
    }
    return false;
  }
  function related(m,o){
    if(m===o)return true;
    if(o.kind==='node')return m.kind==='node'?m.ids[0]===o.ids[0]:(o.side==='left'?m.ids[0]:m.ids[1])===o.ids[0];
    return m.kind==='node'&&(m.side==='left'?o.ids[0]:o.ids[1])===m.ids[0];
  }
  function style(){
    for(const m of marks){
      const isSel=sel.some(i=>matches(m,i)), isHi=hi.some(i=>matches(m,i));
      const active=isSel||isHi||(over&&related(m,over));
      m.visual.setAttribute('opacity',active?(m.kind==='node'?1:.94):(over||sel.length||hi.length)?m.alpha*.20:m.alpha);
      if(m.kind==='node'&&m.caption)m.caption.setAttribute('font-weight',active?700:500);
    }
  }
  function position(event){
    const b=root.getBoundingClientRect();
    const x=event.clientX-b.left,y=event.clientY-b.top;
    tip.style.left=Math.max(6,Math.min(W-tip.offsetWidth-6,x+13))+'px';
    tip.style.top=Math.max(6,Math.min(H-tip.offsetHeight-6,y+16))+'px';
  }
  function mark(element,m,label,detail){
    marks.push(m);
    element.setAttribute('data-label',label);
    if(m.key){element.setAttribute('data-type','group');element.setAttribute('data-key',JSON.stringify(m.key));}
    else{element.setAttribute('data-type','field');element.setAttribute('data-id',m.ids[0]);}
    element.setAttribute('aria-label',`${label}: ${detail}`);
    element.style.cursor='pointer';
    element.addEventListener('pointerenter',e=>{over=m;tip.replaceChildren();const strong=document.createElement('strong');strong.textContent=label;tip.append(strong,document.createElement('br'),document.createTextNode(detail));tip.hidden=false;position(e);style();});
    element.addEventListener('pointermove',position);
    element.addEventListener('pointerleave',()=>{over=null;tip.hidden=true;style();});
  }
  function draw(){
    root.replaceChildren();marks=[];over=null;
    const mode=P.mode||'All citations', cross=mode==='Cross-field only', same=mode==='Same-field only';
    const fields=Number(P.fields)||8;
    const rows=flows.filter(r=>r.mode===mode && r.fields===fields);
    const total=rows.reduce((sum,r)=>sum+r.n,0);
    const ls=rows.map(r=>({source:'L'+r.source_id,target:'R'+r.target_id,s:r.source_id,t:r.target_id,kind:r.flow,value:r.n}));
    const sideNodes=(key,side,prefix)=>Array.from(new Map(rows.map(r=>[r[key+'_id'],r[key+'_rank']]))).sort((a,b)=>a[1]-b[1]).map(([fid])=>({id:prefix+fid,fid,side}));
    const nodes=[...sideNodes('source','left','L'),...sideNodes('target','right','R')];
    const svg=add(root,'svg',{width:W,height:H,viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Sankey diagram of internal Columbia citation flows',style:'display:block'});
    const txt=(x,y,s,attrs={},parent=svg)=>add(parent,'text',{x,y,fill:c.text,'font-size':12,...attrs},s);
    const compact=W<600, tight=H<500;
    txt(pad,23,'OPENALEX  /  2021–2024',{'font-size':10,'font-weight':700,'letter-spacing':1.4,fill:c.textMuted});
    txt(pad,51,'Citation flows within Columbia',{'font-size':compact?21:26,'font-weight':700});
    const known=a.same_field+a.cross_field;
    const stat=txt(pad,76,'',{'font-size':compact?11:13,fill:c.textMuted});
    add(stat,'tspan',{'font-weight':700,fill:c.text},num(total));
    add(stat,'tspan',{}, (cross?' cross-field links shown':same?' same-field links shown':' internal citation links')+(compact?'':`  ·  ${pct(a.same_field,known)} of classified links stay in the same field`));
    const legendKeys=cross?['cross']:same?['same']:['same','cross','unknown'];
    let lx=pad;
    for(const key of legendKeys){add(svg,'rect',{x:lx,y:91,width:13,height:8,rx:2,fill:color[key],opacity:.84});txt(lx+19,99,compact&&key==='unknown'?'Unclassified':names[key],{'font-size':compact?10:11,fill:c.textMuted});lx+=(key==='same'?96:key==='cross'?116:0);}
    const headY=125;
    const footer=H-16, footer2=H-34;
    add(svg,'line',{x1:pad,x2:W-pad,y1:headY+8,y2:headY+8,stroke:c.grid});
    txt(pad,headY,'CITING FIELD',{'font-size':10,'font-weight':700,'letter-spacing':1.05});
    txt(W-pad,headY,'CITED FIELD',{'font-size':10,'font-weight':700,'letter-spacing':1.05,'text-anchor':'end'});
    txt(W/2,headY,'REFERENCES  →',{'font-size':10,fill:c.textMuted,'letter-spacing':1,'text-anchor':'middle'});
    const gutter=Math.min(220, Math.round(W*(compact?.30:.235)));
    const y0=headY+19,y1=Math.max(y0+48,footer2-22);
    const nw=compact?8:12;
    const gg=sankey().nodeId(d=>d.id).nodeSort(null).nodeWidth(nw).nodePadding(Math.max(4,Math.min(15,(y1-y0)*.40/(fields+2)))).extent([[gutter,y0],[W-gutter,y1]])({nodes,links:ls});
    tip=document.createElement('div');root.appendChild(tip);tip.hidden=true;
    Object.assign(tip.style,{position:'absolute',zIndex:'2',maxWidth:'290px',pointerEvents:'none',padding:'8px 11px',border:`1px solid ${c.grid}`,borderRadius:'6px',background:c.surface||c.background,color:c.text,boxShadow:'0 3px 14px #0003',fontSize:'12px',lineHeight:'1.45'});
    const pl=sankeyLinkHorizontal();
    for(const l of gg.links.sort((a,b)=>b.width-a.width)){
      const visual=add(svg,'path',{d:pl(l),fill:'none',stroke:color[l.kind],'stroke-width':l.width,'pointer-events':'stroke'});
      const label=`${labels.get(l.s)} → ${labels.get(l.t)}`;
      mark(visual,{kind:'link',key:{source_id:l.s,target_id:l.t,flow:l.kind},ids:[l.s,l.t],visual,alpha:base[l.kind]},label,`${num(l.value)} citations · ${pct(l.value,total)} of shown links · ${names[l.kind]}`);
    }
    // Labels follow the node order, with a short leader if a small node needs extra room.
    const fontSize=tight||compact?10.5:12, lh=fontSize+1.5;
    for(const side of ['left','right']){
      const isLeft=side==='left';
      const packed=gg.nodes.filter(n=>n.side===side).map(n=>{
        const center=(n.y0+n.y1)/2;
        const words=wrap((compact&&short[n.fid])||labels.get(n.fid),gutter-pad-13,fontSize);
        return {n,center,words,h:words.length*lh,y:center};
      });
      const min=y0-3,max=y1+8;
      const gap=Math.max(1,Math.min(5,(max-min-packed.reduce((d,b)=>d+b.h,0))/Math.max(1,packed.length-1)));
      let cursor=min;
      for(const p of packed){p.y=Math.max(p.center,cursor+p.h/2);cursor=p.y+p.h/2+gap;}
      cursor=max;
      for(const p of packed.slice().reverse()){p.y=Math.min(p.y,cursor-p.h/2);cursor=p.y-p.h/2-gap;}
      for(const p of packed){
        const {n,center,words,y,h}=p, label=labels.get(n.fid), x=isLeft?n.x0:n.x1, off=isLeft?-1:1;
        const g=add(svg,'g');
        const vis=add(g,'g');
        add(vis,'path',{d:`M${x},${center} L${x+off*4},${center} L${x+off*10},${y}`,stroke:c.textMuted,'stroke-opacity':.55,fill:'none'});
        add(vis,'rect',{x:n.x0,y:n.y0,width:nw,height:Math.max(.6,n.y1-n.y0),rx:1,fill:n.fid==='other'||n.fid==='unknown'?c.textMuted:c.text,opacity:.88});
        add(g,'rect',{x:isLeft?pad:x+7,y:y-h/2-1,width:gutter-pad-7,height:h+2,fill:'transparent'});
        const xx=x+off*12;
        const caption=txt(xx,y-(words.length-1)*lh/2,'',{'font-size':fontSize,'font-weight':500,'dominant-baseline':'central','text-anchor':isLeft?'end':'start','pointer-events':'none'},vis);
        words.forEach((word,i)=>add(caption,'tspan',{x:xx,dy:i?lh:0},word));
        mark(g,{kind:'node',side,ids:[n.fid],key:n.fid==='other'||n.fid==='unknown'?{[isLeft?'source_id':'target_id']:n.fid}:null,visual:vis,caption,alpha:1},label,`${num(n.value)} citations ${isLeft?'made':'received'} · ${pct(n.value,total)} of shown links`);
      }
    }
    add(svg,'line',{x1:pad,x2:W-pad,y1:footer2-11,y2:footer2-11,stroke:c.grid});
    txt(pad,footer2+2,compact?'Ribbon width = citations. Smaller fields are grouped.':'Ribbon width = citation count. Other fields groups smaller fields without dropping their links.',{'font-size':compact?10:11,fill:c.textMuted});
    txt(pad,footer,compact?'Hover for counts. Click to select.':'Hover for counts and shares. Select a field to trace its links, or select a ribbon to isolate the route.',{'font-size':compact?10:11,fill:c.textMuted});
    style();
  }
  draw();
  return {update(params){P={...P,...params};draw();},setSelection(items){sel=items||[];style();},highlight(items){hi=items||[];style();},destroy(){root.remove();}};
}
