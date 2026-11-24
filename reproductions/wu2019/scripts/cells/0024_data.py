# cell 24 | agent: data | original run: ok | artifacts created: none
mb=load('T30'); print(mb[mb.status.eq('request_failed')].groupby(['batch','error']).size()); print(mb[mb.status.eq('partial_metadata')][['publication_year','cited_by_count']].isna().sum()); print(mb[mb.status.eq('partial_metadata')].head(5).to_string(index=False)); print(openalex_usage()); print(load('J8') if False else '')
