# cell 47 | agent: analyst | original run: ok | artifacts created: none
print(d[75].query("target=='edge' and threshold==0 and domain=='F>0'")[['metric_name','group','n','n_edges']].to_string(index=False)); print(d[68].query("metric in ['log2 size slope','high minus low slope']")[['domain','group','estimate','lo','hi','n']].to_string(index=False)); import hashlib
p12archive={e:Path('figures/fig4-empirical.'+e).read_bytes() for e in ['png','pdf']}; print({e:hashlib.sha256(b).hexdigest() for e,b in p12archive.items()}); print({e:Path('artifacts/P12/figure.'+e).read_bytes()==b for e,b in p12archive.items()});
for e in p12archive: Path('figures/fig4-empirical.'+e).write_bytes(Path('figures/fig4-empirical-stage2.'+e).read_bytes())
