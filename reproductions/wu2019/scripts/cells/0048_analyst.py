# cell 48 | agent: analyst | original run: failed | artifacts created: none
for e,b0 in p12archive.items():
 assert Path('artifacts/P12/figure.'+e).read_bytes()==b0
 assert Path('artifacts/P17/figure.'+e).read_bytes()==Path('figures/fig4-empirical-stage2.'+e).read_bytes()
 Path('figures/fig4-empirical.'+e).write_bytes(b0)
print(json.loads(Path('artifacts/P17/meta.json').read_text())['parent'])
