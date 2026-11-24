# cell 76 | agent: analyst | original run: failed | artifacts created: none
from pathlib import Path
from hashlib import sha256
rows={r['figure']:r for r in prior['figures']}
def digest(p): return sha256(Path(p).read_bytes()).hexdigest()
before={}
for name in ('P39','P40'):
 r=rows[name]; before[name]={}
 for ext in ('pdf','png'):
  current=digest(r['files'][ext]); frozen=digest(r['immutable_gate_files'][ext]); assert current==frozen==r['parity'][ext]['output_sha256']; before[name][ext]=current
 print(name, before[name]); print(r['caption'])
