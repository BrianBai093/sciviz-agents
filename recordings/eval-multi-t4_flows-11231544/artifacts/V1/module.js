import {sankey} from 'https://esm.sh/d3-sankey@0.12.3';

export default function render(el, ctx) {
  const W = ctx.width, H = ctx.height, c = ctx.theme.colors;
  const font = ctx.theme.fontFamily || 'system-ui, sans-serif';
  const fmt = new Intl.NumberFormat('en-US');
  const count = n => fmt.format(n);
  const pct = n => `${(n * 100).toFixed(1)}%`;
  const palette = {same_field: '#788dab', cross_field: '#008b83', unclassified: '#a86d28'};
  const kinds = {same_field:'Same field', cross_field:'Cross-field', unclassified:'Unclassified'};
  const all = [...ctx.data.pairs].sort((a,b) => b.citation_count-a.citation_count || a.citing_field_id.localeCompare(b.citing_field_id) || a.cited_field_id.localeCompare(b.cited_field_id));
  const sum = rows => rows.reduce((s,r) => s+r.citation_count,0);
  const allTotal = sum(all), sameTotal = sum(all.filter(d=>d.pair_type==='same_field'));
  const compact = W < 680;
  const short = {
    'Biochemistry, Genetics and Molecular Biology':'Biochem., Genetics & Mol. Biology',
    'Economics, Econometrics and Finance':'Econ., Econometrics & Finance',
    'Earth and Planetary Sciences':'Earth & Planetary Sciences',
    'Agricultural and Biological Sciences':'Agricultural & Biological Sciences',
    'Business, Management and Accounting':'Business, Mgmt. & Accounting',
    'Immunology and Microbiology':'Immunology & Microbiology',
    'Pharmacology, Toxicology and Pharmaceutics':'Pharmacology, Toxicology & Pharm.',
    'Physics and Astronomy':'Physics & Astronomy',
    'Arts and Humanities':'Arts & Humanities'
  };
  const root = document.createElement('div');
  Object.assign(root.style,{position:'relative',boxSizing:'border-box',width:'100%',height:'100%',display:'flex',flexDirection:'column',padding:compact?'12px 13px':'16px 24px 12px',background:c.background,color:c.text,fontFamily:font,overflow:'hidden'});
  el.append(root);
  const html = (tag,parent,style,text) => {const e=document.createElement(tag); Object.assign(e.style,style); if(text!==undefined) e.textContent=text; parent.append(e); return e;};
  const svgEl = (tag,parent,attrs,text) => {const e=document.createElementNS('http://www.w3.org/2000/svg',tag); for(const [k,v] of Object.entries(attrs)) e.setAttribute(k,v); if(text!==undefined) e.textContent=text; parent.append(e); return e;};
  const measure = document.createElement('canvas').getContext('2d');
  let params = {...ctx.params}, selected = [], highlighted = [], hover = null, marks = [], tooltip;
  const dim = typeof c.dimOpacity === 'number' ? Math.min(.24, c.dimOpacity) : .20;
  const keyEq = (a,b) => !!a && !!b && typeof a==='object' && typeof b==='object' && Object.keys(a).length===Object.keys(b).length && Object.keys(a).every(k=>String(a[k])===String(b[k]));
  function matches(it,m) {
    if (it.key) return keyEq(it.key,m.key) || (m.endpoints && m.endpoints.includes(`${it.key.role}:${it.key.field_id}`));
    if (it.id!=null) return (String(it.id)===m.id && (!it.type || it.type==='field')) || (m.endpoints?.includes(String(it.id)) && (!it.type || it.type==='field'));
    return false;
  }
  function related(it,m) {
    return matches(it,m) || (it.endpoints && it.endpoints.includes(m.id)) || (it.key && m.id && [`citing:${it.key.citing_field_id}`,`cited:${it.key.cited_field_id}`].includes(m.id));
  }
  function emphasize() {
    const active = hover ? [hover] : [...selected,...highlighted];
    const any = active.some(it=>marks.some(m=>related(it,m)));
    for(const m of marks) {
      const on = any && active.some(it=>related(it,m));
      m.el.style.opacity = any && !on ? dim : 1;
      if(m.shape) m.shape.setAttribute('fill-opacity',on?'.96':m.alpha);
      if(m.title) m.title.setAttribute('font-weight',on?'760':m.weight);
    }
  }
  function positionTip(x,y) {
    let left = x + 15, top = y+15;
    const tw=tooltip.offsetWidth, th=tooltip.offsetHeight;
    if(left+tw>W-8) left=x-tw-14;
    if(top+th>H-8) top=y-th-14;
    tooltip.style.left=`${Math.max(8,Math.min(left,W-tw-8))}px`;
    tooltip.style.top=`${Math.max(8,Math.min(top,H-th-8))}px`;
  }
  function attach(e,item,title,meta,value,shape,alpha,label,weight) {
    const m = {...item,el:e,shape,alpha,title:label,weight}; marks.push(m);
    if(item.id) e.dataset.id=item.id; else e.dataset.key=JSON.stringify(item.key);
    e.dataset.type=item.type;
    e.dataset.label=item.label;
    e.setAttribute('tabindex','0'); e.setAttribute('aria-label',`${title}. ${meta}. ${value}.`);
    e.style.cursor='pointer';
    function show(ev) {
      hover=item;
      tooltip.replaceChildren();
      html('div',tooltip,{color:c.textMuted,fontSize:'11px',fontWeight:'650'},meta);
      html('div',tooltip,{fontWeight:'740',lineHeight:'1.3',margin:'4px 0'},title);
      html('div',tooltip,{fontVariantNumeric:'tabular-nums'},value);
      tooltip.style.display='block';
      move(ev); emphasize();
    }
    function move(ev) {
      const box=root.getBoundingClientRect();
      const itemBox=e.getBoundingClientRect();
      positionTip((ev.clientX??(itemBox.left+itemBox.width*.5))-box.left,(ev.clientY??(itemBox.top+itemBox.height*.5))-box.top);
    }
    function hide() {hover=null;tooltip.style.display='none';emphasize();}
    e.addEventListener('pointerenter',show);
    e.addEventListener('pointermove',move);
    e.addEventListener('pointerleave',hide);
    e.addEventListener('focus',show);
    e.addEventListener('blur',hide);
    e.addEventListener('keydown',ev=>{
      if(ev.key==='Escape') e.blur();
      if(ev.key!=='Enter' && ev.key!==' ') return;
      ev.preventDefault();
      const {type,id,key,label}=item;
      ctx.host.select([id ? {type,id,label} : {type,key,label}],{mode:ev.shiftKey?'toggle':'replace'});
    });
  }
  function draw() {
    root.replaceChildren(); hover=null; marks=[];
    const cross = params.mode==='Cross-field only';
    const top = Math.max(1,Math.min(100,Math.round(Number(params.topN)||25)));
    const eligible = cross ? all.filter(d=>d.pair_type==='cross_field') : all;
    const rows = eligible.slice(0,top), total = sum(eligible), shown = sum(rows);
    const scope = cross?'Cross-field only':'All links eligible';
    const headline = html('header',root,{flex:'none'});
    html('div',headline,{fontSize:'10px',fontWeight:'760',letterSpacing:'.14em',color:c.accent},'COLUMBIA RESEARCH  /  OPENALEX 2021–2024');
    html('h1',headline,{fontSize:compact?'22px':'26px',fontWeight:'780',letterSpacing:'-.025em',lineHeight:'1.15',margin:'5px 0 5px'},'Citation flows within Columbia research');
    const leader=rows[0];
    html('div',headline,{fontSize:compact?'11px':'12px',lineHeight:'1.4',color:c.textMuted},cross?
      `Largest cross-field flow: ${leader.citing_field} → ${leader.cited_field} (${count(leader.citation_count)}).`:
      `${pct(sameTotal/allTotal)} of all internal citations stay within the same field. Medicine → Medicine is the largest flow (${count(all[0].citation_count)}).`);
    const band = html('section',root,{flex:'none',padding:compact?'7px 9px':'8px 12px',margin:'10px 0 8px',borderRadius:'7px',background:c.surface,border:`1px solid ${c.grid}`});
    const info = html('div',band,{display:'flex',alignItems:'baseline',justifyContent:'space-between',flexWrap:'wrap',columnGap:'12px',rowGap:'3px',fontSize:'12px',lineHeight:'1.35'});
    const infoL=html('div',info,{color:c.textMuted});
    html('strong',infoL,{color:c.text,fontWeight:'740'},scope);
    html('span',infoL,{},`  ·  Top ${rows.length} of ${count(eligible.length)} field-pair links`);
    const cov=html('div',info,{color:c.textMuted,fontVariantNumeric:'tabular-nums'});
    html('strong',cov,{color:c.text,fontWeight:'740'},`${count(shown)} of ${count(total)}`);
    html('span',cov,{},` citations shown (${pct(shown/total)})`);
    const track=html('div',band,{height:'3px',borderRadius:'2px',marginTop:'6px',background:c.grid,overflow:'hidden'});
    html('div',track,{height:'100%',width:pct(shown/total),background:palette.cross_field});
    const head=html('div',root,{display:'flex',alignItems:'center',justifyContent:'space-between',gap:'8px',padding:'4px 1px 6px',flex:'none',fontSize:compact?'10px':'11px'});
    html('strong',head,{letterSpacing:'.07em',whiteSpace:'nowrap'},'CITING FIELD');
    html('span',head,{textAlign:'center',color:c.textMuted},compact?'→  References':'⟶  References  ·  Ribbon width = citation count');
    html('strong',head,{letterSpacing:'.07em',whiteSpace:'nowrap'},'CITED FIELD');
    const chart=html('div',root,{flex:'1 1 0',minHeight:'0',position:'relative',borderTop:`1px solid ${c.grid}`,borderBottom:`1px solid ${c.grid}`});
    const footer=html('footer',root,{flex:'none',fontSize:compact?'10px':'11px',lineHeight:'1.35',color:c.textMuted,paddingTop:'7px'});
    const legend=html('div',footer,{display:'flex',alignItems:'center',columnGap:'14px',rowGap:'3px',flexWrap:'wrap',marginBottom:'4px'});
    for(const k of Object.keys(palette).filter(k=>cross?k==='cross_field':k!=='unclassified'||rows.some(r=>r.pair_type===k))) {
      const sw=html('span',legend,{display:'inline-flex',alignItems:'center',gap:'5px',whiteSpace:'nowrap'});
      html('span',sw,{width:'13px',height:'7px',borderRadius:'1px',background:palette[k],opacity:k==='same_field'?'.52':'.82'});
      html('span',sw,{color:c.text},kinds[k]);
    }
    html('span',legend,{},compact?'Ribbon width = citation count.':cross?'Both fields must be classified and different. Hover for counts.':'Use Flow mode to isolate cross-field links; hover for counts.');
    html('div',footer,{}, 'Counts are distinct Columbia-to-Columbia work pairs. Field is from the OpenAlex primary topic. Widths rescale on filter changes; arrows follow references, not chronology.');
    tooltip=html('div',root,{display:'none',position:'absolute',zIndex:'5',pointerEvents:'none',maxWidth:`${Math.min(310,W-40)}px`,boxSizing:'border-box',padding:'9px 12px',borderRadius:'7px',border:`1px solid ${c.grid}`,background:c.background,color:c.text,fontSize:'12px',boxShadow:'0 4px 18px #0003'});
    const width=chart.clientWidth, height=chart.clientHeight;
    if(width<100 || height<20) return;
    const lane=Math.min(227,Math.round(width*(compact?.29:.245)));
    const fs=compact?11:12;
    const nmap=new Map();
    const ranks=new Map();
    for(const d of [...all.filter(d=>d.pair_type==='same_field'),...all]) for(const f of [d.citing_field_id,d.cited_field_id]) if(!ranks.has(f)) ranks.set(f,ranks.size);
    const links=rows.map((r,i)=>{
      for(const role of ['citing','cited']) {
        const fid=r[`${role}_field_id`], id=`${role}:${fid}`;
        if(!nmap.has(id)) nmap.set(id,{id,fid,role,name:r[`${role}_field`],rank:ranks.get(fid)});
      }
      return {...r,source:`citing:${r.citing_field_id}`,target:`cited:${r.cited_field_id}`,value:r.citation_count,rank:i+1};
    });
    const nodes=[...nmap.values()];
    const columns=[nodes.filter(d=>d.role==='citing'),nodes.filter(d=>d.role==='cited')];
    const maxNodes=Math.max(...columns.map(d=>d.length));
    const pad=Math.min(12,Math.max(3, (height-14)*.50/Math.max(1,maxNodes-1)));
    const layout=sankey().nodeId(d=>d.id).nodeWidth(8).nodePadding(pad).iterations(18).extent([[lane,10],[width-lane,height-10]]);
    if(!cross) layout.nodeSort((a,b)=>a.rank-b.rank);
    layout({nodes,links});
    const svg=svgEl('svg',chart,{width,height,viewBox:`0 0 ${width} ${height}`,role:'group','aria-label':'Sankey diagram of references from citing fields to cited fields',style:'display:block'});
    const ribbons=svgEl('g',svg,{}), guides=svgEl('g',svg,{'pointer-events':'none'}), nodeLayer=svgEl('g',svg,{});
    const makePath=d=>{
      const a=d.source.x1, b=d.target.x0, m=a+(b-a)*.5, v=d.width/2, s=d.y0, t=d.y1;
      return `M${a},${s-v}C${m},${s-v} ${m},${t-v} ${b},${t-v}L${b},${t+v}C${m},${t+v} ${m},${s+v} ${a},${s+v}Z`;
    };
    for(const d of [...links].sort((a,b)=>(a.pair_type==='same_field'?0:1)-(b.pair_type==='same_field'?0:1)||b.value-a.value)) {
      const alpha=d.pair_type==='same_field'?'.40':'.73';
      const p=svgEl('path',ribbons,{d:makePath(d),fill:palette[d.pair_type],'fill-opacity':alpha});
      const label=`${d.source.name} → ${d.target.name}`;
      attach(p,{type:'field_pair',key:{citing_field_id:d.citing_field_id,cited_field_id:d.cited_field_id},label,endpoints:[d.source.id,d.target.id]},label,`${kinds[d.pair_type]} · Rank ${d.rank} in this mode`,`${count(d.value)} citations`,p,alpha);
    }
    measure.font=`600 ${fs}px ${font}`;
    function fit(name,space) {
      if(measure.measureText(name).width<=space) return name;
      let text=short[name]||name;
      if(measure.measureText(text).width<=space) return text;
      while(text.length>1 && measure.measureText(text+'…').width>space) text=text.slice(0,-1);
      return text.trimEnd()+'…';
    }
    for(const col of columns) {
      col.sort((a,b)=>a.y0-b.y0);
      const gap=Math.min(17,(height-18)/Math.max(1,col.length-1));
      const ys=col.map((d,i)=> Math.max((d.y0+d.y1)/2,i*gap+9));
      for(let i=1;i<ys.length;i++) ys[i]=Math.max(ys[i],ys[i-1]+gap);
      for(let i=ys.length-1;i>=0;i--) ys[i]=Math.min(ys[i],i===ys.length-1?height-9:ys[i+1]-gap);
      col.forEach((d,i)=>{
        const left=d.role==='citing', edge=left?d.x0:d.x1, sign=left?-1:1, mid=(d.y0+d.y1)/2, y=ys[i], tx=edge+14*sign;
        svgEl('path',guides,{d:`M${edge},${mid}L${edge+10*sign},${y}`,stroke:c.axis,'stroke-width':'.8','stroke-opacity':'.55',fill:'none'});
        const g=svgEl('g',nodeLayer,{});
        svgEl('rect',g,{x:d.x0,y:d.y0,width:d.x1-d.x0,height:Math.max(0,d.y1-d.y0),rx:'.8',fill:cross?palette.cross_field:c.text,'fill-opacity':'.87'});
        const name=fit(d.name,lane-16);
        const title=svgEl('text',g,{x:tx,y,'dominant-baseline':'central','text-anchor':left?'end':'start',fill:c.text,'font-size':fs,'font-weight':'600'},name);
        const txtw=measure.measureText(name).width;
        svgEl('rect',g,{x:left?tx-txtw-2:tx-2,y:y-gap/2,width:txtw+4,height:gap,fill:'transparent'});
        const label=`${d.name} (${d.role})`;
        attach(g,{type:'field',id:d.id,label},d.name,left?'Citing field · shown links':'Cited field · shown links',`${count(d.value)} ${left?'outgoing':'incoming'} citations shown`,null,null,title,'600');
      });
    }
    emphasize();
  }
  draw();
  return {
    update(next){params={...params,...next};draw();},
    setSelection(items){selected=items||[];emphasize();},
    highlight(items){highlighted=items||[];emphasize();},
    destroy(){root.remove();}
  };
}
