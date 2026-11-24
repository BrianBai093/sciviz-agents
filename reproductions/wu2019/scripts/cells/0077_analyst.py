# cell 77 | agent: analyst | original run: ok | artifacts created: none
for name in ('P39','P40'):
 r=rows[name]; before[name]={}
 for ext in ('pdf','png'):
  current=digest(r['files'][ext]); frozen=digest(r['immutable_gate_files'][ext]); assert current==frozen; before[name][ext]=current
 print(name, before[name]); print(r['caption'])
