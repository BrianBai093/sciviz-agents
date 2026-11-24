# cell 16 | agent: data | original run: ok | artifacts created: none
from pathlib import Path
import json
ks=Path('kernel_log.jsonl').read_text().splitlines(); print(len(ks)); print([(list(json.loads(x)),x[:125]) for x in ks[:3]]); print([str(json.loads(x).keys()) for x in ks[-3:]])
