import json, math
from collections import Counter

def derive(gid,mid,cid,rid):
    s=load('T2'); p=load('T8'); g=load(gid); cr=load(cid); rr=load(rid); edges=load('T3')
    assert g.request_row.is_unique and cr.request_row.is_unique
    assert set(g.request_row)<=set(p[p.method.eq('group')].index)
    assert set(cr.request_row)<=set(p[p.method.ne('group')].index)
    groups=g.set_index('request_row').to_dict('index'); cursor=cr.set_index('request_row').to_dict('index'); records={int(i):z for i,z in rr.groupby('sample_id')}; out=[]; strata=[]
    years=range(2021,2027); count_names=['F','I','U','n_i','n_j','n_k']
    windows=['main','observed_fixed','fixed']
    def make(F,I,U):
        n_i=I; n_j=F-I; n_k=U-F
        assert 0<=I<=F<=U and n_i+n_j+n_k==U
        D=(n_i-n_j)/U if U else None
        assert D is None or -1<=D<=1
        return dict(zip(count_names+['D','strict_positive_F','simplified_ratio'],[F,I,U,n_i,n_j,n_k,D,F>0,n_i/F if F else None]))
    for sw in s.itertuples(index=False):
        pass
    grouped=p.groupby('sample_id',sort=False)
    annual=[]; outputs=[]
    for sw in s.itertuples(index=False):
        issues=[]; prog={k:Counter() for k in ['F','I','U']}; z=grouped.get_group(sw.sample_id); route='grouped_disjoint' if z.method.eq('group').all() else 'grouped_prefix_plus_cursors'; res={'sample_id':sw.sample_id,'work_id':sw.work_id,'stratum':sw.stratum,'publication_year':sw.publication_year,'authors_count':sw.authors_count,'weight':sw.weight,'pi':sw.pi,'main_end':sw.main_end,'fixed_end':sw.fixed_end,'observed_fixed_end':sw.observed_fixed_end,'fixed_snapshot_supported':sw.fixed_snapshot_supported,'route':route}
        for i,q in z.iterrows():
            if q.method=='group':
                k=groups.get(i)
                if not k or k['status']!='ok':issues.append(f'{q.series}{q.part}: '+(k.get('error','') if k else 'not collected'));continue
                yr={int(y):int(t) for y,t in json.loads(k['year_counts_json']).items()}
                if sum(yr.values())!=k['meta_count'] or any(y<sw.publication_year or y>2026 for y in yr):issues.append(f'{q.series}{q.part}: grouped count or year mismatch')
                prog[q.series].update(yr)
            else:
                k=cursor.get(i)
                if not k or not k['complete']:issues.append(f'{q.series}{q.part}: '+(k.get('error','') if k else 'not collected'))
        if not issues and route!='grouped_disjoint':
            x=records.get(sw.sample_id,rr.iloc[:0]); f=x[x.series.eq('F')]; t=x[x.series.eq('T')];
            prog['F'].update(f.publication_date.str[:4].astype(int))
            prog['I'].update(f.loc[f.cites_reference_if_focal.eq(False),'publication_date'].str[:4].astype(int))
            if t.groupby('citing_work_id').publication_date.nunique().gt(1).any() or set(f.citing_work_id)&set(t.citing_work_id):issues.append('tail inconsistent date or overlap with F')
            prog['U'].update(t.drop_duplicates('citing_work_id').publication_date.str[:4].astype(int))
            res.update({'tail_ids_before_dedup':len(t),'tail_ids_after_dedup':t.citing_work_id.nunique()})
        if not issues:
            try:
                yr={y:make(*(prog[k][y] for k in ['F','I','U'])) for y in years if y>=sw.publication_year}
                a=make(*(sum(prog[k].values()) for k in ['F','I','U'])); cutoff=min(2026,sw.publication_year+2); b=make(*(sum(c for y,c in prog[k].items() if y<=cutoff) for k in ['F','I','U']));
                assert all(0<=b[k]<=a[k] for k in count_names)
                if not sw.fixed_snapshot_supported:assert all(b[k]==a[k] for k in count_names)
                for label,data in [('main',a),('observed_fixed',b),('fixed',b if sw.fixed_snapshot_supported else {})]:
                    res.update({label+'_'+k:v for k,v in data.items()})
                    res[label+'_status']='cutoff_not_yet_observable' if label=='fixed' and not sw.fixed_snapshot_supported else ('complete_zero_union' if data['U']==0 else ('complete_focal_zero' if data['F']==0 else 'complete'))
                for y,d in yr.items():annual.append({'sample_id':sw.sample_id,'work_id':sw.work_id,'citer_year':y,'citer_year_upper_date':sw.main_end if y==2026 else f'{y}-12-31',**d})
            except AssertionError:
                issues.append('annual or nested count identity failed')
        if issues:
            for label in windows:res[label+'_status']='cutoff_not_yet_observable' if label=='fixed' and not sw.fixed_snapshot_supported else 'collection_incomplete'
        res['reason']='; '.join(issues); outputs.append(res)
    d=pd.DataFrame(outputs)
    for label in windows:
        for k in count_names:
            c=label+'_'+k
            if c not in d:d[c]=pd.NA
            d[c]=d[c].astype('Int64')
    if len(annual): print(save_table(pd.DataFrame(annual),'Validated annual D inputs','One fully measured focal and citing publication year under strict main-date filter; missing year within range is represented by zero.'))
    print(save_table(d,'Validated main and fixed disruption inputs with focal coverage','One sampled focal; exact date-window counts where valid, D and strict eligibility, truncation status and reasons.'))
    print(save_table(d.groupby(['stratum','publication_year','main_status','fixed_status'],dropna=False).size().rename('works').reset_index(),'Focal D coverage by stratum and focal year','One stratum/cohort/status combination.'))
    local=load('T10').assign(status='returned',batch=pd.NA,error=''); small=load('T6').assign(source='live_openalex_pilot',error=''); live=load(mid).assign(source='live_openalex_bulk');
    meta=pd.concat([local,small,live],ignore_index=True); assert meta.reference_id.is_unique and set(meta.reference_id)<=set(edges.reference_id)
    absent=pd.Index(edges.reference_id.unique()).difference(meta.reference_id)
    if len(absent):meta=pd.concat([meta,pd.DataFrame({'reference_id':absent,'status':'not_collected','source':'live_openalex_bulk','error':'not collected'})],ignore_index=True)
    meta['matched']=meta.status.eq('returned')&meta.publication_year.notna()&meta.cited_by_count.notna(); meta['true_zero']=meta.matched&meta.cited_by_count.eq(0);
    meta['publication_year']=meta.publication_year.astype('Int64'); meta['cited_by_count']=meta.cited_by_count.astype('Int64');
    print(save_table(meta,'Analysis-ready deduplicated reference metadata','One sampled reference ID; year, global lifetime citations and exact-match/missing statuses. Join T3 on reference_id.'))
    ed=edges.merge(meta[['reference_id','source','status','matched','true_zero']],on='reference_id',how='left',validate='many_to_one'); a=ed.groupby(['stratum','source','status'],dropna=False).agg(focal_reference_edges=('reference_id','size'),distinct_reference_ids=('reference_id','nunique'),matched_edges=('matched','sum'),zero_edges=('true_zero','sum')).reset_index(); a['stratum_edges']=a.stratum.map(ed.groupby('stratum').size()); a['share_of_stratum_edges']=a.focal_reference_edges/a.stratum_edges; a['distinct_ids_in_stratum']=a.stratum.map(ed.groupby('stratum').reference_id.nunique()); a['share_of_distinct_ids_in_stratum']=a.distinct_reference_ids/a.distinct_ids_in_stratum;
    print(save_table(a,'Reference match coverage by stratum and source','One focal team-size stratum/metadata source/status; pair and distinct-ID denominators.'))
    f=ed.groupby('work_id').agg(reference_edges=('reference_id','size'),matched_reference_edges=('matched','sum'),true_zero_edges=('true_zero','sum')).reset_index(); f['matched_fraction']=f.matched_reference_edges/f.reference_edges;
    print(save_table(f,'Reference metadata coverage by focal','One focal; edge-level match counts with denominators.'))
    print(d.main_status.value_counts().to_dict(),d.fixed_status.value_counts().to_dict()); print(meta.groupby(['source','status']).size().to_dict()); print('edges',len(ed),'match',int(ed.matched.sum()),'zero',int(ed.true_zero.sum())); print('tail before/after',d.get('tail_ids_before_dedup',pd.Series()).sum(),d.get('tail_ids_after_dedup',pd.Series()).sum()); print('failed rows',d[d.reason.ne('')][['sample_id','reason']].head(10).to_string(index=False)); return d,meta,a,f
