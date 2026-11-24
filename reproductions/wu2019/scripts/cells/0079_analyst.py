# cell 79 | agent: analyst | original run: ok | artifacts created: none
j17=load('J17')
for f in j17['figures']:
 if f['figure'] in ('P42','P43'):
  print({k:v for k,v in f.items() if k not in ('caption','issues')})
for a in j17['gate_attempts']:
 if a['figure'] in ('P42','P43'):
  print({k:v for k,v in a.items() if k not in ('caption','review')})
