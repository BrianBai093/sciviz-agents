# cell 78 | agent: analyst | original run: ok | artifacts created: J17
import json,copy

def figure_meta(k): return json.loads(Path(f'artifacts/{k}/meta.json').read_text())
selected=copy.deepcopy(prior['figures']); attempts=[]
for old,new in [('P39','P42'),('P40','P41'),('P40','P43')]:
 m=figure_meta(new); r=rows[old]; paths={ext:f'artifacts/{new}/figure.{ext}' for ext in ('pdf','png')}
 for ext in ('pdf','png'):
  assert digest(paths[ext])==digest(r['files'][ext])==digest(r['immutable_gate_files'][ext])==before[old][ext]
 attempts.append(dict(figure=new,previous_figure=m['parent'],claim=m['claims'][0],gate=m['status'],review=m['reviews'][-1],caption=m['description'],immutable_gate_files=paths,sha256=before[old]))
 if new=='P41': continue
 s=next(s for s in selected if s['figure']==old)
 s.update(figure=new,title=m['title'],caption=m['description'],gate=m['status'],issues=m['reviews'][-1]['issues'],immutable_gate_files=paths,replaces=old,caption_only_sha256=before[old],caption_only_bytes_identical=True,review=m['reviews'][-1])
 for unchanged in ('P25','P35','P30'):
  assert next(s for s in selected if s['figure']==unchanged)==rows[unchanged]
scopes={
 'C3':{'figure':'P42','finding':'F13','verdict':'Partly reproduced. Among teams of one to ten authors, disruption rank declined clearly only in the least-cited half. The middle and top estimates and the difference between the top and bottom groups are uncertain. This is not confirmation of a steeper decline among highly cited works.','major_issue_type':'Evidence and linked claim scope.','minor_issue_type':'Clarity in the image. The y-axis gives the full possible percentile scale although the visible plot shows only part of it. The axis label was outside the caption-only remit.','reader_clarification':'Disruption percentiles run from zero to one hundred; the plot shows only part of that scale.'},
 'C5':{'figure':'P43','finding':'F15','verdict':'Partly reproduced. In the groups shown, works with ten or 51–100 authors cited newer and generally more highly cited references than solo works. These are observed comparisons only. The separate age model estimated a steeper drop for ten-author works than for solo works. Neither model fit closely, and the comparison for references with at least 50 citations was inconclusive.','major_issue_type':'Evidence and linked claim scope.','minor_issue_type':'Caption clarity. Explain the spacing of the citation axis in everyday words. The previous note about the meaning of a constant rate was addressed and did not recur.','reader_clarification':'Above one citation, each tenfold increase takes up the same space on the axis.'}}
handoff=dict(figures=selected,scope_and_limits=scopes,gate_attempts=attempts,claim_scope_note='The figure gate accepts existing claim IDs only. It has no separate field for narrowing their wording. The captions state the limits of each figure, and the original C3 and C5 claim text remains unchanged. The report must mention the open issues.',method='Caption-only submissions. The submitted PDF and PNG files match the previous versions byte for byte. The three approved figures and the original files were not changed. No new analysis, external data requests, or spending.',sources=['J16','F13','F15','P39','P40','P41','P42','P43'],caption_file='figure_captions_scoped.md',handoff_file='figure_handoff_scoped.json')
Path(handoff['caption_file']).write_text('# Figure captions\n\nThese are the exact captions submitted with the chosen figures.\n\n'+'\n\n'.join(f"## {s['title']} [{s['figure']}]\n\n{s['caption']}" for s in selected)+'\n')
Path(handoff['handoff_file']).write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n')
print(save_json(handoff,'json','Figure captions and open review notes','Five chosen figures with exact captions and paths, three caption-only review outcomes, remaining evidence and clarity notes, and byte-for-byte file checks.'))
