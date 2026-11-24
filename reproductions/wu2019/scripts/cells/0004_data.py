# cell 4 | agent: data | original run: ok | artifacts created: none
def request_many(ps,workers=12):
 t=time.monotonic(); b=openalex_usage(); a=openalex_many([('works',p) for p in ps],workers=workers); e=openalex_usage(); return a,{'elapsed_s':time.monotonic()-t,'submitted':len(ps),**{k:e[k]-b[k] for k in ['requests','cache_hits','errors','usd']},'after':e}
def parsegroup(o):
 if isinstance(o,Exception): raise o
 g={int(x['key']):int(x['count']) for x in o['group_by']}; assert len(g)==len(o['group_by'])==int(o['meta']['groups_count']); assert sum(g.values())==int(o['meta']['count']), (g,o['meta']['count']); return g
# Validation includes one-ref, usual route, >100, conservative near limit and all 2024 cutoffs where feasible.
sel=[int(s[s.usable_refs.eq(1)].sample_id.iloc[0]),int(s[(s.publication_year==2024)&(s.usable_refs.between(35,40))].sample_id.iloc[0]),int(s[(s.publication_year==2023)&(s.usable_refs.between(101,110))].sample_id.iloc[0]),int(route[route.partition_fits].nlargest(1,'max_encoded_url').sample_id.iloc[0])]
pilot=s[s.sample_id.isin(sel)]; print(pilot[['sample_id','work_id','usable_refs','publication_year','stratum']]);
queries=[]; tags=[]
for w in pilot.itertuples():
 F,I,U=primary(w)
 for k,f in [('F',F),('I',I),*[(f'U{i}',x) for i,x in enumerate(U)]]:
  queries.append(group(f)); tags.append((w.sample_id,k,'group'))
  queries.append(count(f)); tags.append((w.sample_id,k,'main_count'))
  if w.fixed_snapshot_supported:
   queries.append(count(f.replace(cut,w.fixed_end)));tags.append((w.sample_id,k,'fixed_count'))
  if w.publication_year==2024:
   queries.append(count(f.replace(cut,'2025-12-31')));tags.append((w.sample_id,k,'pre_2026_count'))
rqs={'filter':'ids.openalex:'+'|'.join(missing[:100]),'per_page':100,'select':'id,publication_year,cited_by_count'}
P,perf=request_many(queries+[rqs]); print(perf); print([(tag,str(x)[:250]) for tag,x in zip(tags,P) if isinstance(x,Exception)]); print('reference',str(P[-1])[:250]);
for w in pilot.itertuples():
 print(w.sample_id,[(tag[1:],parsegroup(o) if tag[2]=='group' else o['meta']['count'])  for tag,o in zip(tags,P) if tag[0]==w.sample_id and not isinstance(o,Exception)])
