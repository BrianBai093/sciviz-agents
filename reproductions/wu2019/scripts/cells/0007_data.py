# cell 7 | agent: data | original run: ok | artifacts created: T12, T13, T14, T15
extra=[]; xt=[]
for w in long.itertuples():
 f=longplan(w)[0]; extra.append(count(f));xt.append((w.sample_id,'focal_count'))
for w in pilot.itertuples():
 F,I,U=primary(w)
 if w.sample_id==141: extra.append(cursorpar(U[0],edges=True)); xt.append((w.sample_id,'independent_union_edges'))
 if w.publication_year==2024:
  extra.append(count(U[0].replace(cut,'2026-12-31').replace(w.start_date,'2026-11-24')));xt.append((w.sample_id,'future_interval'))
 for y in [w.publication_year,2026]:
  a=max(w.start_date,f'{y}-01-01'); b=min(cut,f'{y}-12-31'); extra.append(count(U[0].replace(cut,b).replace(w.start_date,a)));xt.append((w.sample_id,f'year_{y}_union0_date_count'))
E,eperf=request_many(extra); print(eperf); print([(t,o['meta']['count'] if not isinstance(o,Exception) else str(o)) for t,o in zip(xt,E)])
foc_ct=pd.DataFrame([(t[0],o['meta']['count']) for t,o in zip(xt,E) if t[1]=='focal_count'],columns=['sample_id','expected_count']); print('focal cursor pages',sum(np.maximum(1,np.ceil(foc_ct.expected_count/200)))); print(save_table(foc_ct,'Long-route focal cursor size checks','One URL-overflow focal; independently counted inbound records.'))
vr=[]
for t,o in zip(tags,P):
 if t[2]=='group': vr.extend([(t[0],t[1],t[2],y,c) for y,c in parsegroup(o).items()] or [(t[0],t[1],t[2],None,0)])
 else: vr.append((*t,None,o['meta']['count']))
for t,o in zip(xt,E): vr.append((t[0],'U0' if t[1]!='focal_count' else 'F',t[1],None,o['meta']['count']))
w=next(pilot[pilot.sample_id==141].itertuples()); Ue=E[xt.index((141,'independent_union_edges'))]; edges=[]
for rec in Ue['results']:
 refs={id.rsplit('/',1)[-1] for id in rec['referenced_works']}; f=w.work_id in refs; r=bool(refs.intersection(w.refs)); assert f or r; edges.append((rec['id'].rsplit('/',1)[-1],rec['publication_date'],f,r))
assert len(edges)==Ue['meta']['count'] and len({a[0] for a in edges})==len(edges)
ed=pd.DataFrame(edges,columns=['citer_id','publication_date','cites_focal','cites_reference']); print(ed.assign(y=ed.publication_date.str[:4]).groupby(['y','cites_focal','cites_reference']).size()); print(save_table(ed,'Independent cursor edge classification for focal 141','One citing work; exact outbound-edge membership by publication date.'))
print(save_table(pd.DataFrame(vr,columns=['sample_id','series','test','year','count']),'Grouped endpoint validation observations','One query-year result or plain-count comparison, including missing/zero, date-year and future checks.'))
# Check each comparison programmatically.
checks=[]
for t,o in zip(tags,P):
 if t[2]=='group': continue
 g=parsegroup(P[tags.index((t[0],t[1],'group'))]); w=s.iloc[t[0]-1]; limit={'main_count':2026,'fixed_count':w.publication_year+2,'pre_2026_count':2025}[t[2]]; checks.append((t[0],t[1],t[2],sum(c for y,c in g.items() if y<=limit),o['meta']['count']))
for t,o in zip(xt,E):
 if not t[1].startswith('year_'):continue
 checks.append((t[0],'U0',t[1],parsegroup(P[tags.index((t[0],'U0','group'))]).get(int(t[1].split('_')[1]),0),o['meta']['count']))
for k,b in [('F',ed.cites_focal),('I',ed.cites_focal & ~ed.cites_reference),('U0',ed.cites_focal|ed.cites_reference)]:
 g=parsegroup(P[tags.index((141,k,'group'))]); gc=ed[b].groupby(ed.publication_date.str[:4].astype(int)).size().to_dict()
 for y in range(2021,2027):checks.append((141,k,f'edge_records_{y}',g.get(y,0),gc.get(y,0)))
ck=pd.DataFrame(checks,columns=['sample_id','series','test','group_count','independent_count']); ck['match']=ck.group_count.eq(ck.independent_count); print(ck.match.value_counts()); print(save_table(ck,'Independent grouped-count validation results','One exact grouped-versus-plain or cursor-classification comparison.'))
