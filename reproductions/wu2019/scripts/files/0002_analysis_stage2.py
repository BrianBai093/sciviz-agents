# Offline Stage 2. Run with harness Python helpers: exec(Path('analysis_stage2.py').read_text()).
from pathlib import Path
import gc, hashlib, json
import numpy as np, pandas as pd
src=load('J12')['code']
assert src==Path('analysis_stage1.py').read_text()
sections={}
for p in src.split('# ---- ')[1:]:
 name,code=p.split(' ----\n',1); sections[name]=code

def replace(q,a,b):
 assert q.count(a)==1,a
 return q.replace(a,b)
core=sections['core']; i=core.index('rng=np.random'); j=core.index('assert np.allclose(W.sum',i)
core=core[:i]+'''rng=np.random.default_rng(20261123); W=np.tile(w,(T+1,1))
for _,z in h.iterrows():
 idx=np.flatnonzero(s.stratum.eq(z.stratum)); n=len(idx)
 W[1:,idx]*=rng.multinomial(n,np.full(n,1/n),size=T)
 assert np.allclose(W[:,idx].sum(1),z.N_h)
PmainU=valid.copy(); fixedU=np.isfinite(DF)&(y<=2023); fixedS=fixedU&(FF>0)
assert np.all((~fixedS)|strict)
valid=strict if domain=='F>0' else PmainU
fixed=fixedS if domain=='F>0' else fixedU
common=valid&fixed
'''+core[j:]
core=replace(core,'PS=ranker(D,strict); ', '')
core=core[:core.index('raw=s[')]
core=replace(core,"def table(rows,title,desc=''):\n d=pd.DataFrame(rows); print(title,d.shape,save_table(d,title,desc)); return d", "def table(rows,title,desc=''):\n return pd.DataFrame(rows)")
core=replace(core,'for yy in np.unique(y):assert np.allclose(np.average(P[:,valid&(y==yy)],axis=1,weights=W[:,valid&(y==yy)]),50)', '''for yy in np.unique(y):assert np.allclose(np.average(P[:,valid&(y==yy)],axis=1,weights=W[:,valid&(y==yy)]),50)
assert np.isclose(D[0],-1/4355) and np.isclose(D[1],-95/27749)
k=valid&(y==y[0]); manual=100*(w[k&(D<D[0])].sum()+.5*w[k&(D==D[0])].sum())/w[k].sum(); assert np.isclose(P[0,0],manual)''')
claims=sections['claims123489']; claims=replace(claims,",row('strict F>0 log2 size slope',slope(PS,small&strict),small&strict,group='1–10')",'')
a=claims.index('k2='); b=claims.index('c8=table',a)
claims=claims[:a]+'''for lab,mask,d,f in [('main standalone all cohorts',valid,D,F),('main standalone 2021–23',valid&(y<=2023),D,F),('fixed standalone 2021–23',fixed,DF,FF)]:
 dp=P if lab=='main standalone all cohorts' else ranker(d,mask)
 fp=Q if lab=='main standalone all cohorts' else ranker(f,mask)
 for nm,rnk in [('D',dp),('F',fp)]:
  C8.append(row(nm+' rank slope',slope(rnk,mask&small),mask&small,group=lab))
  for gg,m in zip(H,groups): C8.append(row(nm+' rank mean',stat(rnk,mask&m),mask&m,group=lab,stratum=gg))
 if lab!='main standalone all cohorts':
  for gg,m in zip(H,groups): C8.append(row('median citing works',quant(f,mask&m),mask&m,group=lab,stratum=gg))
 if lab=='fixed standalone 2021–23': fixedDP=dp[0].copy(); fixedFP=fp[0].copy()
 del dp,fp
for gg,m in zip(H,groups):
 for key,z,k in [('Main rank',Pc,common&m),('Fixed rank',Pf,common&m),('Simplified ratio (pp)',100*R,strict&m)]:C8.append(row(key,stat(z,k),k,group=gg))
for key,z in [('Paired main F rank',ranker(F,common)),('Paired fixed F rank',ranker(FF,common))]:
 for gg,m in zip(H,groups): C8.append(row(key,stat(z,common&m),common&m,group=gg))
del z
'''+claims[b:]
claims=replace(claims,"('mean authors',stat(s.authors_count.to_numpy(),m),m,group=name)","('mean authors',stat(s.authors_count.to_numpy(),k),k,group=name)")
claims=replace(claims,"C9+=[row('acknowledgment minus none slope',sa[1]-sa[0],small&valid,group='contrast'),row('recorded share',stat(ack,np.ones(N,bool)),np.ones(N,bool),group='all sampled')]", "C9+=[row('acknowledgment minus none slope',sa[1]-sa[0],small&valid,group='contrast'),row('recorded share',stat(ack,valid),valid,group='eligible'),row('recorded share',stat(ack,np.ones(N,bool)),np.ones(N,bool),group='all sampled')]+[row('mean authors',stat(s.authors_count.to_numpy(),m),m,group=nm) for nm,m in [('all sampled without acknowledgment',~ack),('all sampled with acknowledgment',ack)]]")
ref,timing=sections['claims56'].split('    lag=aa.pivot',1)
ref=replace(ref,"variants=[('All',np.ones(N,bool))]+list(zip(H,groups)); cmap={}","variants=[('All',refdomain)]+[(g,m&refdomain) for g,m in zip(H,groups)]; cmap={}")
ref=replace(ref,'mm=(groups[0]|groups[H.index(gg)])&elig','mm=(groups[0]|groups[H.index(gg)])&elig&refdomain')
ref=ref[:ref.index("    print('coverage checks'")]
fit=replace(sections['ref_fit_ci'],'k=groups[H.index(frow.group)]&(cnt>0)','k=groups[H.index(frow.group)]&(cnt>0)&refdomain')
timing='with threadpool_limits(3):\n    lag=aa.pivot'+timing
# Strict timing conditional on fixed positive, retaining main D sign labels; early zeros are a separate coverage statistic.
timing=replace(timing,'tbase=(y<=2023)&valid','tbase=fixed if domain==\'F>0\' else (y<=2023)&valid')
timing=replace(timing,"timing.extend([row('no citations in three observed periods (%)',100*stat(total==0,k),k,group=nm),row(","unconditioned=(y<=2023)&valid&m; timing.extend([row('fixed zero among main eligible, complete cohorts (%)',100*stat(total==0,unconditioned),unconditioned,group=nm),row(")
fe=sections['claim7'].split('    A0=dict')[0]
claimcode=core+claims+timing+fe
figcode=sections['figures']+sections['figures_empirical']
figcode=replace(figcode,'labels=H','labels=H; subgroups=[\'1\',\'10\',\'51–100\']')
figcode=replace(figcode,'20 supported OpenAlex fields • teams of 1–10 authors',"{len(fld)} supported OpenAlex fields • teams of 1–10 authors")
figcode=replace(figcode,"ax.set_title('{len(fld)}", "ax.set_title(f'{len(fld)}")
figcode=replace(figcode,'95% design\\ninterval','95% bootstrap\\ninterval')
figcode=replace(figcode,"['1 author (623 works)','10 authors (626 works)','51–100 authors (481 works)']", "[f'{g} '+('author' if g=='1' else 'authors')+f' ({int(sel.loc[(sel.metric_name==sel.metric_name.iloc[0])&(sel.group==g),\"n\"].iloc[0]):,} works)' for g in sels]")
for slug in ('fig2-team','fig3-impact','fig3-fields','ext-raw-disruption','fig4-empirical'):
 figcode=replace(figcode,f"save(fig,'{slug}')",f"save(fig,'{slug}-stage2')")

def run_stage2():
 keys=['c1','c2','c3','c4','c4s','c8','c9','c5cov','c5','c5p','c5f','c5fi','c6','c7m','c7w','c7d']
 datasets={k:[] for k in keys}; ranks=[]
 for domain in ['F>0','U>0']:
  ns={'domain':domain, 'load':load,'sql':sql,'threadpool_limits':__import__('threadpoolctl').threadpool_limits}
  exec(claimcode,ns); ns['refdomain']=ns['valid']; exec(ref+fit,ns)
  for k in keys: datasets[k].append(ns[k].assign(domain=domain));
  ranks.append(pd.DataFrame(dict(sample_id=ns['s'].sample_id,domain=domain,main_eligible=ns['valid'],fixed_eligible=ns['fixed'],paired=ns['common'],main_D_rank=ns['P'][0],main_F_rank=ns['Q'][0],fixed_D_rank=ns['fixedDP'],fixed_F_rank=ns['fixedFP'],paired_main_D_rank=ns['Pc'][0],paired_fixed_D_rank=ns['Pf'][0])))
  if domain=='F>0':
   E=ns['E']; evalid=ns['valid'][ns['ei']]; refaudit=[]
   for label,mask in [('F>0',evalid),('U>0',ns['PmainU'][ns['ei']]),('all draws',np.ones(len(E),bool))]:
    refaudit.append(dict(domain=label,edges=int(mask.sum()),distinct_ids=int(E[mask].reference_id.nunique()),matched_edges=int((mask&E.matched).sum()),missing_year=int((mask&~np.isfinite(ns['age'])).sum()),future_age=int((mask&(ns['age']<0)).sum()),same_year=int((mask&(ns['age']==0)).sum()),missing_citations=int((mask&~ns['pp']).sum()),observed_zero_citations=int((mask&(ns['pop']==0)).sum())))
   exec(figcode,ns)
  else:
   ns['refdomain']=np.ones(ns['N'],bool); exec(ref+fit,ns)
   for k in ['c5cov','c5','c5p','c5f','c5fi']: datasets[k].append(ns[k].assign(domain='all draws (original C5 target)'))
  del ns; gc.collect()
 d={k:pd.concat(v,ignore_index=True) for k,v in datasets.items()}
 # Stage-1 reconciliation: compare point estimates, not old FPC intervals.
 spec={'c1':('T50',['metric','group']),'c2':('T51',['metric','group','threshold']),'c3':('T52',['metric','group','stratum']),'c4':('T53',['level','id']),'c4s':('T54',['level']),'c8':('T55',['metric','group']),'c9':('T56',['metric','group']),'c5cov':('T57',['metric_name','group']),'c5':('T58',['metric','metric_name','group','target']),'c5p':('T59',['metric_name','group','target','threshold']),'c5f':('T60',['metric','group']),'c6':('T61',['metric','group','lag']),'c7m':('T62',['metric']),'c7w':('T63',['metric']),'c7d':('T64',['metric','group']),'c5fi':('T65',['metric','distribution','group'])}
 reconciliation=[]
 for k,(oldid,cols) in spec.items():
  f=d[k]; old=load(oldid); val='parameter' if k=='c5f' else 'estimate'; subset=f[f.domain.str.startswith('all draws') if k.startswith('c5') else f.domain.eq('U>0')]; j=subset.merge(old,on=cols,suffixes=('','_old'),validate='one_to_one'); select=j[val].notna()&j[val+'_old'].notna(); dif=(j[val]-j[val+'_old']).abs(); mex=float(dif[select].max()); assert mex<1e-9,(k,mex); reconciliation.append(dict(table=oldid,stage2=k,matched_rows=len(j),compared_numeric=int(select.sum()),max_abs_difference=mex,unmatched_old_rows=len(old)-len(j)))
  if k=='c7m': assert np.allclose(j[['lo','hi']].to_numpy(),j[['lo_old','hi_old']].to_numpy())
 # Confirm funding frame descriptives and timing zero coverage under unchanged base when mapped explicitly.
 old=load('T56'); new=d['c9']; j=new[(new.domain=='U>0')&new.group.str.startswith('all sampled')].set_index('group'); assert np.isclose(j.loc['all sampled with acknowledgment','estimate'],old.loc[(old.metric=='mean authors')&(old.group=='Acknowledgment recorded'),'estimate'].iloc[0]);
 old=load('T61'); j=d['c6'].query("domain == 'U>0' and metric == 'fixed zero among main eligible, complete cohorts (%)'").merge(old[old.metric.eq('no citations in three observed periods (%)')],on='group'); assert np.allclose(j.estimate_x,j.estimate_y)
 c=load('T33'); h=load('T5'); frame=load('T1'); srcount=sql('select citing_work_id as work_id, count(*) as raw_edges, count(*) filter (where citing_work_id=cited_work_id) as self_edges, count(*) filter (where not regexp_full_match(cited_work_id,\'W[0-9]+\')) as malformed_edges from citations group by 1')
 f=frame.merge(srcount,on='work_id',how='left',validate='one_to_one'); f['reason']=np.select([f.frame_status.ne('no_usable_refs'),f.raw_edges.isna()&f.referenced_works_count.eq(0),f.raw_edges.isna(),f.raw_edges.eq(f.self_edges),f.raw_edges.eq(f.malformed_edges)], [f.frame_status,'no recorded edge; registered reference count zero','no recorded edge despite positive registered reference count','only focal self-edges','only malformed IDs'],default='only a mix of self-edges and malformed IDs'); assert (f.loc[f.frame_status.eq('no_usable_refs'),'usable_refs']==0).all()
 screen=f.groupby(['frame_status','reason'],dropna=False).agg(n=('work_id','size'),snapshot_positive=('snapshot_cited_by_count',lambda z:(z>0).sum()),later_year_positive=('later_year_citations',lambda z:(z>0).sum()),local_dated_positive=('local_later_citations',lambda z:(z>0).sum())).reset_index()
 flags={'main_pos':c.main_F.gt(0),'main_zero_ref_only':c.main_F.eq(0)&c.main_U.gt(0),'main_zero_union':c.main_U.eq(0),'fixed_complete':c.fixed_snapshot_supported,'fixed_pos':c.fixed_F.gt(0),'fixed_zero_ref_only':c.fixed_F.eq(0)&c.fixed_U.gt(0),'fixed_zero_union':c.fixed_U.eq(0),'fixed_incomplete':~c.fixed_snapshot_supported,'paired_pos':c.main_F.gt(0)&c.fixed_F.gt(0),'paired_U':c.main_U.gt(0)&c.fixed_U.gt(0),'main_pos_complete_cohorts':c.main_F.gt(0)&c.fixed_snapshot_supported}
 cv=c[['stratum','publication_year','weight']].copy()
 for k,v in flags.items(): cv[k]=v.fillna(False).astype(int); cv[k+'_weighted']=cv[k]*cv.weight
 cv['draws']=1; cv['weighted_draws']=cv.weight
 by=pd.concat([cv.assign(publication_year=0),cv,cv.assign(stratum='All'),cv.assign(stratum='All',publication_year=0)]).groupby(['stratum','publication_year']).sum().drop(columns='weight').reset_index().merge(h,on='stratum',how='left'); assert (by.main_pos+by.main_zero_ref_only+by.main_zero_union==by.draws).all() and (by.fixed_pos+by.fixed_zero_ref_only+by.fixed_zero_union+by.fixed_incomplete==by.draws).all()
 aids={}; desc='95% pointwise percentile intervals from 1,000 within-original-stratum n_h-out-of-n_h focal-work replacement draws (seed 20261123), no FPC including census; original inverse inclusion weights. C7 FE uses two-way cluster model intervals instead.'
 for k,t in d.items(): aids[k]=save_table(t,'Stage 2 '+dict(c1='C1 team gradients and sign',c2='C2 signed raw D quantiles and empirical CDF/KS',c3='C3 reranked citation-impact contrasts',c4='C4 field, subfield and journal support and slopes',c4s='C4 negative slopes among observed supported groups',c5cov='C5 reference metadata coverage',c5='C5 reference means and contrasts (edge and work targets)',c5p='C5 P12 update curves (edge and work targets)',c5f='C5 separate fit diagnostics',c5fi='C5 separate fit intervals',c6='C6 early citation timing and standardized contrasts',c7m='C7 comparable-sample clustered models',c7w='C7 bootstrap baselines',c7d='C7 article and review contrasts',c8='C8 paired and standalone windows, simplified ratio',c9='C9 recorded funder acknowledgment')[k],desc+(' Explicit P12 template/source; P9 superseded; figures use edge target.' if k=='c5p' else ''))
 for k,t,title in [('coverage',by,'Window and original stratum coverage and weights'),('frame',screen,'Frame exclusions and local positive citation evidence'),('ranks',pd.concat(ranks),'Work-level recalculated main/fixed/paired ranks'),('refaudit',pd.DataFrame(refaudit),'Reference denominator and metadata audit'),('reconcile',pd.DataFrame(reconciliation),'Stage 1 comparator point reconciliation')]: aids[k]=save_table(t,'Stage 2 '+title,'Reproducibility audit; year 0 means all cohorts, All means all strata.')
 print('STAGE2_IDS',aids,flush=True)
 print('TOTALS',by.query("stratum=='All' and publication_year==0").to_string(index=False),flush=True)
 print('SCREEN',screen.to_string(index=False),flush=True)
 return aids

if globals().get('STAGE2_RUN',True): STAGE2_IDS=run_stage2()
