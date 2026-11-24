# cell 73 | agent: analyst | original run: ok | artifacts created: none
import json, hashlib
m=json.loads(Path('artifacts/P40/meta.json').read_text()); print(m.keys()); print(m['status']); print(m['reviews'][-1].keys()); print(m['reviews'][-1]['verdict']); print(m['description'][:1050])
