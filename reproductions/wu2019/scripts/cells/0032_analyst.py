# cell 32 | agent: analyst | original run: failed | artifacts created: none
scripts['claim7']=r'''
import scipy.stats as st
au=sql('select distinct work_id,author_id from authorships where is_columbia and author_id is not null'); au=au.merge(s[['work_id','sample_id','primary_topic_id','publication_year']],on='work_id',validate='many_to_one'); au['x']=x[au.sample_id-1]; au=au.loc[(small&valid)[au.sample_id-1]].copy(); au['topic']=au.primary_topic_id.replace('', 'Missing').fillna('Missing')
keep=au.groupby('author_id').x.agg(['min','max','size']); keep=keep[(keep['size']>=2)&(keep['max']>keep['min'])]; au=au[au.author_id.isin(keep.index)].copy(); au['wi']=w[au.sample_id-1]/au.groupby('sample_id').sample_id.transform('size'); mi=s.sample_id.isin(au.sample_id).to_numpy(); assert np.allclose(au.groupby('sample_id').wi.sum().to_numpy(),w[mi]); au['out']=P[0,au.sample_id-1]
wt=au.wi.to_numpy(); a=au.x.to_numpy(); b=au.out.to_numpy(); ai=pd.factorize(au.author_id)[0]; wi=pd.factorize(au.sample_id)[0]; ti=pd.factorize(au.topic)[0]; yi=pd.factorize(au.publication_year)[0]; inter=pd.factorize(pd.MultiIndex.from_frame(au[['sample_id','author_id']]))[0]
def resids(v,fe):
 if not fe:return v-np.average(v,weights=wt)
 v=v.copy(); totals=[np.bincount(f,weights=wt) for f in fe]
 for it in range(3000):
  old=v.copy()
  for f,su in zip(fe,totals):v-= (np.bincount(f,weights=wt*v)/su)[f]
  if max(abs(v-old))<1e-9:return v
 raise RuntimeError('FE absorption failed to converge')
def csev(va,g):
 vals=np.bincount(g,weights=va);n=len(vals);return n/(n-1)*np.dot(vals,vals)
C7m=[]
for key,fe in [('Unadjusted',[]),('Year FE',[yi]),('Year + topic FE',[yi,ti]),('Year + author FE',[yi,ai]),('Year + topic + author FE',[yi,ti,ai])]:
 ax=resids(a,fe); by=resids(b,fe); bread=np.dot(wt,ax**2); beta=np.dot(wt,ax*by)/bread; score=wt*ax*(by-beta*ax); av=csev(score,ai); wv=csev(score,wi); iv=csev(score,inter); var=av+wv-iv; se=np.sqrt(var if var>0 else max(av,wv))/bread; zz=st.t.ppf(.975,min(len(keep),mi.sum())-1); C7m.append(dict(metric=key,estimate=beta,lo=beta-zz*se,hi=beta+zz*se,se=se,n=int(mi.sum()),n_authors=len(keep),n_rows=len(au),weighted_n=float(w[mi].sum()),residual_x_ss=float(bread),cluster_fallback=bool(var<=0)))
assert abs(C7m[0]['estimate']-slope(P,mi)[0])<1e-10
c7m=table(C7m,'C7 comparable-sample year, topic and focal-author models','Size 1–10; work weight split over supported Columbia authors. Two-way author/work cluster sandwich, fixed percentile outcome, no finite population correction in this model-based inference.')
c7w=table([row('same-sample design baseline',slope(P,mi),mi),row('full size 1–10 design baseline',slope(P,valid&small),valid&small)],'C7 design-based baseline comparison','Ranks recalculated with replicates.')
C7d=[]; dt=[]; dtm=[]
for typ in ['article','review']:
 m=small&valid&s.type.eq(typ).to_numpy(); design=slope(P,m); dt.append(design);dtm.append(m);C7d.append(row('log2 size slope',design,m,group=typ,n_size1_2=int((m&(x<=1)).sum()),n_size5_10=int((m&(x>=np.log2(5))).sum())))
C7d.append(row('review minus article slope',dt[1]-dt[0],dtm[0]|dtm[1],group='contrast'));c7d=table(C7d,'C7 OpenAlex article versus review gradients','Restricted to OpenAlex article or review types; no theory or empirical label; design-based pointwise intervals.')
print(c7m.to_string(index=False));print(c7d.to_string(index=False))
A0=dict(sampled=N,weighted_frame=float(w.sum()),main_defined=int(valid.sum()),F_positive=int(strict.sum()),F_zero_U_positive=int((valid&~strict).sum()),U_zero=int((U==0).sum()),true_fixed_complete=int((y<=2023).sum()),true_fixed_defined=int(np.isfinite(DF).sum()),paired_defined=int(common.sum()),partial_2024_excluded=int((y==2024).sum()),raw_min=float(np.nanmin(D)),raw_max=float(np.nanmax(D)),reference_edges=len(E),reference_distinct=meta.reference_id.nunique(),shared_ref_ids=int((E.reference_id.value_counts()>1).sum()),missing_ref_year=int((~np.isfinite(age)).sum()),future_ref_age=int((age<0).sum()),same_year_age=int((age==0).sum()),missing_ref_pop=int((~pp).sum()),zero_ref_pop=int((pop==0).sum()),author_fe_supported_works=int(mi.sum()),author_fe_supported_authors=len(keep),collection_usd=audit0['usage']['usd'],additional_api_spend_usd=0,bootstrap_replicates=T,seed=20261123)
print(save_json(A0,'json','Stage 1 analysis and join audit','Verified joins, coverage, counts and ranges.'),A0)
'''
exec(scripts['claim7'])
