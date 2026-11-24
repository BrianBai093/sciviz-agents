# cell 61 | agent: analyst | original run: failed | artifacts created: none
script=script.replace("    exec(load('J15')['scripts']['analysis_stage2.py'],ns)","    source=load('J15')['scripts']['analysis_stage2.py']\n    exec(source.replace('    exec(figcode,ns)','    ns[\\\"write_words\\\"]=write_words; exec(figcode,ns)').replace(' exec(figcode,ns)',' ns[\\\"write_words\\\"]=write_words; exec(figcode,ns)'),ns)")
# The archived routine uses one-space indentation.
script=script.replace("source.replace('    exec(figcode,ns)','    ns[\"write_words\"]=write_words; exec(figcode,ns)').replace(' exec(figcode,ns)',' ns[\"write_words\"]=write_words; exec(figcode,ns)')", "source.replace(' exec(figcode,ns)',' ns[\"write_words\"]=write_words; exec(figcode,ns)')")
def test_relabel():
 Path('relabel_figures.py').write_text(script); r={'load':load,'__name__':'relabel_figures'}; exec(script,r); r['render_relabels'](); print([(p,{e:(a['original_rerender_pixel_exact'],a['changed_pixels']) for e,a in v.items()}) for p,v in r['parity'].items()]); return r
rel=test_relabel()
