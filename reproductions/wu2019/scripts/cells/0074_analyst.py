# cell 74 | agent: analyst | original run: ok | artifacts created: J16
from pathlib import Path
import json, shutil, hashlib
ordered=[('P15','P25'),('P16','P35'),('P17','P40'),('P18','P39'),('P19','P30')]
metadata=[]; md=['# Figure captions','The captions below are the exact versions submitted with the delivered figures.']
for old,new in ordered:
    d=json.loads(Path(f'artifacts/{new}/meta.json').read_text()); caption=d['description']; checks={}; export={}; gated={}
    for ext, a in rel['parity'][old].items():
        q=Path(f'artifacts/{new}/figure.{ext}'); dest=Path(f'figures/{d["slug"]}.{ext}'); direct=lambda path: path.read_bytes(); b,c=direct(q),direct(dest)
        get_pixels=rel['pixels'] if ext=='png' else lambda raw: rel['pixels'](rel['render_pdf'](raw)); assert np.array_equal(get_pixels(b),get_pixels(c))
        assert a['original_sha256']==hashlib.sha256(direct(Path(a['original_file']))).hexdigest()
        # Export the exact bytes retained by the gate, including PDF metadata.
        shutil.copyfile(q,dest); export[ext]=str(dest); gated[ext]=str(q)
        checks[ext]={k:v for k,v in a.items() if k not in ('changed_text','output_sha256')}; checks[ext]['gated_sha256']=hashlib.sha256(b).hexdigest(); checks[ext]['export_matches_gate']=True; checks[ext]['text_edit_count']=len(a['changed_text'])
    md += [f'## {d["title"]} [{new}]',caption]
    metadata.append(dict(original=old,figure=new,claim=d['claims'][0],title=d['title'],caption=caption,gate=d['status'],issues=d['reviews'][-1]['issues'],figure_inputs=d['inputs'],supplementary_caption_evidence=['T76','T77'] if old=='P17' else [], files=export,immutable_gate_files=gated,parity=checks))
Path('figure_captions.md').write_text('\n\n'.join(md)+'\n')
handoff=dict(figures=metadata, method='Only text was changed after the original layout pass. The original plot routines rerendered all five originals pixel for pixel. PDF at 150 dpi and native 250 dpi PNG comparisons after hiding the text were also pixel-exact for every original and redraw. Axes, crop, marks, legend keys and displayed numbers were unchanged. No analyses or API calls.', caption_file='figure_captions.md', script_path='relabel_figures.py',script_sha256=hashlib.sha256(Path('relabel_figures.py').read_bytes()).hexdigest(),script=script, source=['J14','J15','J12'])
Path('figure_handoff.json').write_text(json.dumps({k:v for k,v in handoff.items() if k!='script'},indent=2,ensure_ascii=False)+'\n'); jid=save_json(handoff,'json','Figure wording, gate outcomes and parity checks','Five figures with exact captions, original and redrawn paths, gate notes, render comparisons and the figure-only script.'); print(jid); print([(d['original'],d['figure'],d['gate'],d['files']) for d in metadata]); print({p:Path(p).stat().st_size for p in ('figure_captions.md','figure_handoff.json','relabel_figures.py')})
