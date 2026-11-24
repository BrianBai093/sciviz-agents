# cell 25 | agent: data | original run: ok | artifacts created: T38, T39, T40
failure_batches={int(k):v.reference_id.tolist() for k,v in mb[mb.status.eq('request_failed')].groupby('batch')}; partial_batches=chunks(mb[mb.status.eq('partial_metadata')].reference_id.tolist()); rescue_requests=[metapar(ids) for ids in failure_batches.values()]+[dict(metapar(ids),select='id,publication_year,publication_date,cited_by_count') for ids in partial_batches]; resc,rt=request_many(rescue_requests,workers=5); print(rt); print([(str(o)[:180] if isinstance(o,Exception) else (o['meta']['count'],len(o['results']),sum(bool(z.get('publication_year')) for z in o['results']),sum(bool(z.get('publication_date')) for z in o['results']))) for o in resc]);
recover=[]
for (ib,ids),o in zip(failure_batches.items(),resc):
 if isinstance(o,Exception):continue
 by={z['id'].rsplit('/',1)[-1]:z for z in o['results']}; assert len(by)==len(o['results'])==o['meta']['count'] and set(by)<=set(ids)
 for rid in ids:
  z=by.get(rid,{}); y=z.get('publication_year'); c=z.get('cited_by_count'); recover.append((rid,ib,y,c,'returned' if z and y is not None and c is not None else ('partial_metadata' if z else 'unmatched'),''))
rc=pd.DataFrame(recover,columns=mb.columns); print(rc.status.value_counts().to_dict()); patch=pd.concat([mb[~mb.reference_id.isin(rc.reference_id)],rc],ignore_index=True); print(patch.status.value_counts().to_dict()); print(save_table(rc,'Recovered metadata request responses','One ID from two transiently failed reference lookup batches.')); print(save_table(patch,'Final bulk reference metadata responses','One nonlocal reference requested at bulk stage including two recovered batches; unsuccessful exact matches and null fields retained.'))
pa=[]
for r in resc[len(failure_batches):]:
 if isinstance(r,Exception):continue
 for z in r['results']:pa.append((z['id'].rsplit('/',1)[-1],z.get('publication_year'),z.get('publication_date'),z.get('cited_by_count')))
print(save_table(pd.DataFrame(pa,columns=['reference_id','publication_year','publication_date','cited_by_count']),'Missing reference publication-year audit','One returned reference missing year in primary metadata batch; checked alternate date field.'))
