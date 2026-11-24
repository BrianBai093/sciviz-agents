# cell 80 | agent: analyst | original run: ok | artifacts created: none
from pathlib import Path
from hashlib import sha256
sub={}
for f in j17['figures']:
 if f['figure'] not in ('P42','P43'): continue
 aid=f['figure']
 a=next(a for a in j17['gate_attempts'] if a['figure']==aid)
 assert f['caption']==a['caption']
 hashes={}
 for ext, path in f['files'].items():
  immutable=Path(f['immutable_gate_files'][ext]).read_bytes()
  assert Path(path).read_bytes()==immutable
  hashes[ext]=sha256(immutable).hexdigest()
 assert hashes==a['sha256']
 sub[aid]={'slug':Path(f['files']['pdf']).stem,'title':f['title'],'caption':f['caption'],'claim_ids':[f['claim']],'input_artifacts':f['figure_inputs']}
 print(aid, hashes, sub[aid])
