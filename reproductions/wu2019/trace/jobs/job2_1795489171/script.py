import time, json, math, re
from urllib.parse import urlencode
start=time.monotonic(); ep=time.time(); b=openalex_usage(); print('START',b,flush=True)
p=load('T8'); p=p[p.method.ne('group')].copy(); s=load('T2').set_index('sample_id'); fp=load('T12').set_index('sample_id').expected_count.to_dict(); refs=load('T3'); long_refs=refs[refs.work_id.isin(s.loc[p.sample_id.unique()].work_id)].groupby('work_id').reference_id.agg(set).to_dict();
state={i:dict(records={},cursor='*',seen=set(),pages=0,err='',complete=False) for i in p.index}; log=[]; calls=0
def getp(r,cursor):
 return {'filter':r.filter,'per_page':200,'cursor':cursor,'select':'id,publication_date'+(',referenced_works' if r.method=='focal_cursor' else '')}
try:
 while True:
  todo=[]
  for i,r in p.iterrows():
   z=state[i]
   if z['err'] or z['complete']:continue
   q=getp(r,z['cursor']); expected=fp[r.sample_id] if r.method=='focal_cursor' else int(r.expected_count)
   if len('/works?'+urlencode(q))>7950 or z['pages']>=max(1,math.ceil(expected/200))+3 or z['cursor'] in z['seen']:
    z['err']='URL, page safety cap, or repeated cursor';continue
   z['seen'].add(z['cursor']);todo.append((i,r,expected,q))
  if not todo:break
  u=openalex_usage(); available=min(u['remaining_session_budget_usd'],u['daily_remaining_usd']+u.get('prepaid_remaining_usd',0)); assert available>=len(todo)*.0002
  ts=time.monotonic(); qq=[('works',q) for _,_,_,q in todo]; rr=openalex_many(qq,workers=16); calls+=len(qq); fails=[j for j,o in enumerate(rr) if isinstance(o,Exception)]; fix=openalex_many([qq[j] for j in fails],workers=12) if fails else [];calls+=len(fix)
  for j,o in zip(fails,fix):rr[j]=o
  dur=time.monotonic()-ts; log.append((len(todo),len(fails),sum(isinstance(o,Exception) for o in rr),dur)); print('wave',len(log),len(todo),round(dur,2),'retry',len(fails),flush=True)
  for (i,r,expected,q),o in zip(todo,rr):
   z=state[i]; z['pages']+=1
   try:
    if isinstance(o,Exception):raise o
    assert int(o['meta']['count'])==expected,f'count drift {o["meta"]["count"]} != {expected}'
    w=s.loc[r.sample_id]; f=w.work_id; d=w.start_date; focal=r.method=='focal_cursor'
    for rec in o['results']:
     id=rec['id'].rsplit('/',1)[-1]; a=rec['publication_date']; assert id not in z['records'] and d<=a<=w.main_end, 'duplicate ID or out-of-window publication_date'
     cites_ref=None
     if focal:
      c={r.rsplit('/',1)[-1] for r in rec['referenced_works']}; assert f in c,'F membership mismatch'; cites_ref=bool(c&long_refs[f]);
     z['records'][id]=(a,cites_ref)
    assert len(z['records'])<=expected,'more IDs than meta.count'
    z['complete']=len(z['records'])==expected; z['cursor']=o['meta'].get('next_cursor');
    if not z['complete']:assert z['cursor'] and len(o['results']), 'truncated pagination'
   except Exception as e:z['err']=str(e)[:600]
finally:
 info=[]; raw=[]
 for i,r in p.iterrows():
  z=state[i]; exp=fp[r.sample_id] if r.method=='focal_cursor' else int(r.expected_count); info.append((i,r.sample_id,r.series,r.part,exp,len(z['records']),z['pages'],z['complete'] and not z['err'],z['err']));raw.extend((i,r.sample_id,r.series,r.part,id,*v) for id,v in z['records'].items())
 print(save_table(pd.DataFrame(info,columns=['request_row','sample_id','series','part','expected_count','unique_citers','pages','complete','error']),'Residual and focal cursor stream checks','One overflow cursor stream; independent count, distinct date-bearing IDs and status.'),flush=True)
 print(save_table(pd.DataFrame(raw,columns=['request_row','sample_id','series','part','citing_work_id','publication_date','cites_reference_if_focal']),'Raw overflow cursor records','One citing ID per overflow stream with date; focal streams classify outgoing edges.'),flush=True)
 print(save_table(pd.DataFrame(log,columns=['submitted','retried','retained_errors','active_seconds']),'Cursor waves and timing','One parallel cursor wave; initial submissions, retries and elapsed active time.'),flush=True)
 print(save_json({'started_epoch':ep,'finished_epoch':time.time(),'wall_seconds':time.monotonic()-start,'start_usage':b,'end_usage':openalex_usage(),'submissions':calls},'json','Cursor collector audit','Wall timing and session-wide budget readings, concurrent with grouped job.'),flush=True)