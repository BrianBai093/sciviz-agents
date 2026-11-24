# cell 53 | agent: analyst | original run: ok | artifacts created: none
from pathlib import Path
j14,j15=load('J14'),load('J15'); print(Path.cwd()); print(j15['entrypoints']); print([(f['id'],f['slug'],f.get('files')) for f in j14['figures']]); src=j15['scripts']['analysis_stage2.py']; print(src[src.find('def plots'): ] if 'def plots' in src else src[-13000:]); print(list(Path('figures').glob('*stage2*')))
