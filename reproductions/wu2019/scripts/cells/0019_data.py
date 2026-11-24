# cell 19 | agent: data | original run: ok | artifacts created: T24, T25
alts=[]; altags=[]
for w in pilot[pilot.sample_id.isin([428,7890])].itertuples():
 d=datefilter(w.start_date,cut); prev=[]
 for i,c in enumerate(chunks([w.work_id]+list(w.refs)[::-1])):
  f=d+','+pfilter(c)+''.join(','+negfilter(p) for p in prev); prev.append(c); alts.append(group(f)); altags.append((w.sample_id,i))
# Independent outbound classification for a small residual stream of largest-list design.
from collections import defaultdict
resql=lcheck[lcheck.residual_count.between(1,200)].iloc[0]; sid=int(resql.sample_id); part=int(resql.part); w=next(long[long.sample_id.eq(sid)].itertuples()); _,_,ts,_=longplan(w); rquery=cursorpar(ts[part],edges=True)
AA,aaperf=request_many(alts+[rquery],workers=8); print(aaperf); print([(t,parsegroup(o)) for t,o in zip(altags,AA)]); print(sid,part,resql.residual_count,AA[-1]['meta']['count']); er=AA[-1]['results']; chunks_code=ts[part].split(',')[2:]; pos=set(chunks_code[0][6:].split('|')); neg={r for f in chunks_code[1:] for r in f[7:].split('|')}; cls=[]
for o in er:
 r={z.rsplit('/',1)[-1] for z in o['referenced_works']};cls.append((sid,part,o['id'].rsplit('/',1)[-1],o['publication_date'],bool(r&pos),bool(r&neg)))
cl=pd.DataFrame(cls,columns=['sample_id','part','citing_work_id','publication_date','matched_tail','matched_excluded_prefix']); assert len(cl)==AA[-1]['meta']['count']==resql.residual_count and cl.matched_tail.all() and not cl.matched_excluded_prefix.any(); print(save_table(cl,'Independent overflow-tail outbound check','One residual citer; classifier verifies tail membership and exclusion of assigned prefix.'))
altchk=[]
for sid in [428,7890]:
 old=Counter(); rev=Counter();
 for t,o in zip(tags,P):
  if t[0]==sid and t[1].startswith('U') and t[2]=='group':old.update(parsegroup(o))
 for t,o in zip(altags,AA):
  if t[0]==sid:rev.update(parsegroup(o))
 assert old==rev
 for y in sorted(old.keys()|rev.keys()):altchk.append((sid,y,old[y],rev[y]))
print(save_table(pd.DataFrame(altchk,columns=['sample_id','year','original_count','reverse_order_count']),'Long partition order invariance checks','One focal/year; verifies union totals after reversing the chunk assignment order.'))
