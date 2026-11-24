# cell 6 | agent: data | original run: ok | artifacts created: T8, T9, T10, T11
from datetime import datetime,timezone
print(datetime.now(timezone.utc), datetime.fromtimestamp(openalex_usage()['started_at'],timezone.utc)); print(P[-1]['meta']['count']);
# Reference match audit: compare overlapping local/live values in a deduplicated 100-ID batch.
local_audit_ids=list(unique.intersection(loc.index)[::54][:100]); aud,audperf=request_many([metapar(local_audit_ids)]); print(audperf)
# Build full reproducible request specs now. Pilot specs are identical and cached.
plan=[]
for w in s.itertuples():
 if w.sample_id in set(long.sample_id):
  F,pre,tails,m=longplan(w)
  plan += [(w.sample_id,'F',0,F,'focal_cursor',None)]+[(w.sample_id,'U',k,f,'group',None) for k,f in enumerate(pre)]+[(w.sample_id,'T',k,f,'tail_cursor',int(lcheck.set_index(['sample_id','part']).loc[(w.sample_id,k),'residual_count'])) for k,f in enumerate(tails)]
 else:
  F,I,U=primary(w); plan.extend([(w.sample_id,'F',0,F,'group',None),(w.sample_id,'I',0,I,'group',None)]+[(w.sample_id,'U',k,f,'group',None) for k,f in enumerate(U)])
plan=pd.DataFrame(plan,columns=['sample_id','series','part','filter','method','expected_count']); print(plan.method.value_counts()); print(save_table(plan,'Exact request manifest for disruption','One focal/filter component; group partitions and preflighted tail cursors.'))
cover_meta=missing.difference(refcheck.reference_id); print('metadata remaining',len(cover_meta),ceil(len(cover_meta)/100)); print(save_table(pd.DataFrame({'reference_id':cover_meta}),'Remaining nonlocal reference metadata manifest','One nonlocal reference not already requested by the stage-1 pilot, sorted.'))
localmeta=loc.loc[unique.intersection(loc.index)].reset_index().rename(columns={'work_id':'reference_id','snapshot_cited_by_count':'cited_by_count'}); localmeta['source']='local_snapshot'; print(save_table(localmeta,'Snapshot reference metadata','One requested reference matched in snapshot; global citation total at snapshot vintage.'))
audit=pd.DataFrame([(id,j.get('publication_year'),j.get('cited_by_count')) for j in aud[0]['results'] for id in [j['id'].rsplit('/',1)[-1]]],columns=['reference_id','live_year','live_cited_by_count']).merge(localmeta,on='reference_id',how='right'); audit=audit[audit.reference_id.isin(local_audit_ids)]; print(audit[['live_year','publication_year','live_cited_by_count','cited_by_count']].notna().sum()); print('exact year',sum(audit.live_year==audit.publication_year),'exact ct',sum(audit.live_cited_by_count==audit.cited_by_count)); print(save_table(audit,'Local versus live reference metadata audit','One sampled locally matched reference; comparison of year and global lifetime citation count.'))
