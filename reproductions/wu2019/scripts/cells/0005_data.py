# cell 5 | agent: data | original run: ok | artifacts created: T6, T7
long=s[s.sample_id.isin(route.loc[~route.partition_fits,'sample_id'])]; longids=pd.Index(sorted(set(r for refs in long.refs for r in refs))); longmissing=longids.difference(loc.index)
def metapar(ids): return {'filter':'ids.openalex:'+'|'.join(ids),'per_page':100,'select':'id,publication_year,cited_by_count'}
def cursorpar(f,cursor='*',edges=False): return {'filter':f,'per_page':200,'cursor':cursor,'select':'id,publication_date'+(',referenced_works' if edges else '')}
meta_specs=[list(missing[:100])]+chunks(longmissing.difference(missing[:100])); mp,mpperf=request_many(list(map(metapar,meta_specs[1:]))); mp=[P[-1]]+mp; print(mpperf,'long ids',len(longids),'metadata',len(meta_specs)); print('batch status',Counter('error' if isinstance(o,Exception) else ('complete' if o['meta']['count']==len(o['results']) else 'fail') for o in mp));
metraw=[]
for ib,(ids,o) in enumerate(zip(meta_specs,mp)):
 assert not isinstance(o,Exception) and o['meta']['count']==len(o['results']); by={j['id'].rsplit('/',1)[-1]:j for j in o['results']}; assert set(by)<=set(ids)
 for id in ids:
  j=by.get(id,{}); metraw.append((id,ib,j.get('publication_year'),j.get('cited_by_count'),'returned' if j else 'unmatched'))
refcheck=pd.DataFrame(metraw,columns=['reference_id','batch','publication_year','cited_by_count','status']); print(refcheck.status.value_counts(),(refcheck.cited_by_count==0).sum()); print(save_table(refcheck,'Reference API batch checks and raw long-list metadata','One requested reference; 100-ID max batch, unmatched distinguished from zero.'))
meta_scores=refcheck.set_index('reference_id').cited_by_count.combine_first(loc.snapshot_cited_by_count)
def longplan(w):
 d=datefilter(w.start_date,cut); f=w.work_id; rr=sorted(w.refs,key=lambda x:(-int(meta_scores.get(x,0)) if pd.notna(meta_scores.get(x,0)) else 0,x))
 # Include F in the prefix; reserve URL space for one 100-ID tail filter and a cursor token.
 def exclusion(c): return ''.join(','+negfilter(x) for x in chunks(c))
 for m in range(min(520,len(rr)),0,-1):
  pre=[f]+rr[:m]; tail=chunks(rr[m:]); ex=exclusion(pre); tails=[d+','+pfilter(c)+ex for c in tail]
  if all(len(urlencode(cursorpar(t)))+7<=7300 for t in tails):break
 pref=[]; prev=[]
 for c in chunks(pre):
  pref.append(d+','+pfilter(c)+''.join(','+negfilter(p) for p in prev)); prev.append(c)
 return d+','+pfilter([f]),pref,tails,m
longspec=[(w.sample_id,k,filtertext) for w in long.itertuples() for k,filtertext in enumerate(longplan(w)[2])]; lp,lperf=request_many([count(q[2]) for q in longspec]); print(lperf)
lcheck=pd.DataFrame([(i,k,o['meta']['count'] if not isinstance(o,Exception) else None,str(o)[:160] if isinstance(o,Exception) else '') for (i,k,_),o in zip(longspec,lp)],columns=['sample_id','part','residual_count','error']); lcheck['pages']=np.ceil(lcheck.residual_count/200); print(lcheck.groupby('sample_id').agg(parts=('part','size'),residual=('residual_count','sum'),pages=('pages','sum')).to_string()); print('total pages',lcheck.pages.sum(),lcheck.error.value_counts()); print(save_table(lcheck,'Measured prefix-excluded tail footprint','One tail stream, based on independent count after excluding popular-reference prefix.'))
