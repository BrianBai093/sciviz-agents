# cell 3 | agent: data | original run: ok | artifacts created: T4, T5
from urllib.parse import urlencode
from math import ceil
from itertools import islice
from collections import Counter
cut='2026-11-23'
def chunks(ids,m=100): return [list(ids[i:i+m]) for i in range(0,len(ids),m)]
def datefilter(a,b): return f'from_publication_date:{a},to_publication_date:{b}'
def pfilter(ids): return 'cites:'+'|'.join(ids)
def negfilter(ids): return 'cites:!'+'|'.join(ids)
def group(f): return {'filter':f,'group_by':'publication_year','per_page':200}
def count(f): return {'filter':f,'per_page':1,'select':'id'}
def within(p): return len('/works?'+urlencode(p))<=7950
def primary(w):
 f=w.work_id; refs=list(w.refs); d=datefilter(w.start_date,cut); full=[f]+refs
 F=d+','+pfilter([f]); I=F+''.join(','+negfilter(c) for c in chunks(refs)); U=[]; prev=[]
 for i,c in enumerate(chunks(full)):
  U.append(d+','+pfilter(c)+''.join(','+negfilter(x) for x in prev)); prev.append(c)
 return F,I,U
routes=[]
for w in s.itertuples():
 F,I,U=primary(w); routes.append((w.sample_id,w.work_id,w.stratum,w.usable_refs,len(U),max(len(urlencode(group(k))) for k in [F,I,*U])+7,all(within(group(k)) for k in [F,I,*U])))
route=pd.DataFrame(routes,columns=['sample_id','work_id','stratum','usable_refs','union_parts','max_encoded_url','partition_fits']); print(route.groupby('partition_fits').agg(works=('work_id','size'),parts=('union_parts','sum'))); print(route[~route.partition_fits].to_string(index=False)); print('safe calls',sum(route[route.partition_fits].union_parts+2)); print('meta',ceil(len(missing)/100))
print(save_table(route,'Exact filter route footprint','One sampled focal; ordered union partition and conservative percent-encoded URL bound.'))
print(save_table(pd.DataFrame({'stratum':labels,'N_h':N.values,'n_h':n.values,'pi':(n/N).values,'weight':(N/n).values}),'Stratum allocation','One stratum; population and sample sizes and design weights.'))
