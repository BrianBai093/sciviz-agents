import time, os, json, traceback
from math import ceil
from urllib.parse import urlencode
start=time.monotonic(); started_epoch=time.time(); b=openalex_usage(); print('START',b,flush=True)
plan=load('T8'); ids=load('T9').reference_id.tolist(); samp=load('T2')
grp=plan[plan.method=='group'].copy(); batches=[ids[i:i+100] for i in range(0,len(ids),100)]
def gp(f):return {'filter':f,'group_by':'publication_year','per_page':200}
def mp(ids):return {'filter':'ids.openalex:'+'|'.join(ids),'per_page':100,'select':'id,publication_year,cited_by_count'}
def checkguard(k):
 u=openalex_usage(); available=min(u['remaining_session_budget_usd'],u['daily_remaining_usd']+u.get('prepaid_remaining_usd',0)); assert available+1e-8>=max(.0001*k,.01),u
reqs=0; logs=[]; outg=[]; outm=[]
def batch(seq,kind):
 global reqs
 if not seq:return
 pp=[('works',x[1]) for x in seq]; checkguard(2*len(pp)); before=openalex_usage(); t=time.monotonic()
 res=openalex_many(pp,workers=32); fails=[i for i,r in enumerate(res) if isinstance(r,Exception)]; reqs+=len(pp)
 if fails:
  rr=openalex_many([pp[i] for i in fails],workers=12); reqs+=len(rr)
  for i,r in zip(fails,rr): res[i]=r
 after=openalex_usage(); logs.append((kind,len(pp),len(fails),after['requests']-before['requests'],after['cache_hits']-before['cache_hits'],after['errors']-before['errors'],after['usd']-before['usd'],time.monotonic()-t)); print(kind,len(pp),'initial_failed',len(fails),'usd',round(after['usd'],6),'sec',round(time.monotonic()-t,2),flush=True)
 for (key,_),o in zip(seq,res):
  try:
   if isinstance(o,Exception):raise o
   total=int(o['meta']['count'])
   if kind=='reference':
    lookup={z['id'].rsplit('/',1)[-1]:z for z in o['results']}; assert len(lookup)==len(o['results'])==total and set(lookup)<=set(batches[key]), 'incomplete batch or unsolicited IDs'
    for rid in batches[key]:
     z=lookup.get(rid,{}); y=z.get('publication_year'); c=z.get('cited_by_count'); st='returned' if z and y is not None and c is not None else ('partial_metadata' if z else 'unmatched'); outm.append((rid,key,y,c,st,''))
   else:
    g={int(z['key']):int(z['count']) for z in o['group_by']}; assert len(g)==len(o['group_by'])==o['meta']['groups_count'] and sum(g.values())==total and all(2021<=y<=2026 and c>=0 for y,c in g.items()),'group integrity'
    outg.append((key,total,json.dumps(g,sort_keys=True),'ok',''))
  except Exception as e:
   if kind=='reference':outm.extend((rid,key,None,None,'request_failed',str(e)[:600]) for rid in batches[key])
   else:outg.append((key,None,'','request_failed',str(e)[:600]))
try:
 # Representative first wave: up to two focals per stratum plus exact validation/cache records.
 first_ids=set(samp.groupby('stratum',sort=False).head(2).sample_id)|{141,428,469,7890}; first=grp[grp.sample_id.isin(first_ids)]; todo=grp[~grp.sample_id.isin(first_ids)];
 batch([(i,gp(r.filter)) for i,r in first.iterrows()],'representative_group'); batch([(i,mp(batches[i])) for i in range(20)],'reference')
 for k in range(0,max(ceil(len(todo)/500),ceil((len(batches)-20)/75))):
  z=todo.iloc[500*k:500*(k+1)]; batch([(i,gp(r.filter)) for i,r in z.iterrows()],'group'); batch([(i,mp(batches[i])) for i in range(20+75*k,min(len(batches),20+75*(k+1)))],'reference')
except Exception:
 traceback.print_exc(); raise
finally:
 print(save_table(pd.DataFrame(outg,columns=['request_row','meta_count','year_counts_json','status','error']).merge(grp.reset_index(names='request_row')[['request_row','sample_id','series','part']],on='request_row',how='left'),'Raw annual grouped counts','One grouped request; annual sparse counts, request ID, total and integrity status.'),flush=True)
 print(save_table(pd.DataFrame(outm,columns=['reference_id','batch','publication_year','cited_by_count','status','error']),'Raw bulk reference metadata','One nonlocal reference requested; distinguish unmatched, missing metrics, request failure and true zero.'),flush=True)
 print(save_table(pd.DataFrame(logs,columns=['kind','submitted','retried','backend_requests','cache_hits','errors','usd','active_seconds']),'Group and metadata API batch timing and billing','One completed API batch; actual incremental spend and elapsed active time.'),flush=True)
 print(save_json({'started_epoch':started_epoch,'finished_epoch':time.time(),'wall_seconds':time.monotonic()-start,'start_usage':b,'end_usage':openalex_usage(),'submissions':reqs},'json','Group and reference collector timing','Background job wall time and audit billing snapshots.'),flush=True)