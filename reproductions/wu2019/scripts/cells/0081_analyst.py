# cell 81 | agent: analyst | original run: ok | artifacts created: J18
results=[]
for old,new,note in [('P42','P44','Optional: state earlier that the middle and top groups show no clear decline and that the top-versus-bottom comparison allows either a stronger or weaker decline.'),('P43','P45','Optional: clarify that the share fell faster as the reference-age cutoff rose, not as calendar time passed.')]:
 f=next(f for f in j17['figures'] if f['figure']==old)
 expected=next(a['sha256'] for a in j17['gate_attempts'] if a['figure']==old)
 gated={ext:f'artifacts/{new}/figure.{ext}' for ext in ('pdf','png')}
 for ext,p in gated.items():
  assert Path(p).read_bytes()==Path(f['immutable_gate_files'][ext]).read_bytes()==Path(f['files'][ext]).read_bytes()
  assert sha256(Path(p).read_bytes()).hexdigest()==expected[ext]
 results.append({'previous_review':old,'current_review':new,'status':'approved','claim':f['claim'],'figure_inputs':f['figure_inputs'],'exact_title':f['title'],'exact_caption':f['caption'],'previous_immutable_files':f['immutable_gate_files'],'current_immutable_files':gated,'submission_source_files':f['files'],'sha256':expected,'byte_identical':True,'submissions':1,'optional_gate_note':note})
 print(old,new,gated)
print(save_json({'figures':results,'criterion':'Whether the figure tests the study claim, not whether the evidence confirms it.','provenance':'Exact title, caption, claim and inputs from the prior handoff. For both formats, the previous immutable file, source submitted to the gate, and new immutable file are byte-identical.','actions':'No redraws, edits, analyses, external data requests, or draft changes. Both optional notes were left untouched.'},'json','Independent figure review handoff','Two approval records with immutable PDF and PNG paths, SHA-256 hashes, unchanged captions, and optional review notes.'))
