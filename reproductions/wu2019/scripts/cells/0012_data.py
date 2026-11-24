# cell 12 | agent: data | original run: ok | artifacts created: none
from pathlib import Path
k1=Path('jobs/job1/script.py').read_text().replace('gp(r.filter)','gp(r["filter"])').replace('workers=32','workers=24'); k2=Path('jobs/job2/script.py').read_text().replace("'filter':r.filter","'filter':r['filter']"); print(k1[:250],k2[:250]); Path('stage1_bulk.py').write_text(k1); Path('stage1_cursors.py').write_text(k2);
print(Path('jobs/job1/log.txt').read_text()[-3500:]); print(Path('jobs/job2/log.txt').read_text()[-1500:]); print(openalex_usage())
