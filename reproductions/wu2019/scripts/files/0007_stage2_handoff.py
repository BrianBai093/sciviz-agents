# Offline evidence index/finding build. Run after analysis_stage2.py in the exported harness.
from pathlib import Path
import json
import pandas as pd
import hashlib
D={i:load(f'T{i}') for i in range(66,87)}
sel={
'C1':[(66,"metric in ['log2 size slope','median F','D percentile','D endpoint difference'] and group in ['1','10','51–100','1–10','51–100 minus 10']")],
'C2':[(67,"(metric in ['KS distance','negative fraction difference'] and group=='10 vs 1') or (metric=='raw D quantile 0.5' and group in ['1','10','51–100'])"),(66,"metric in ['fraction negative','fraction positive'] and group in ['1','10','51–100']")],
'C3':[(68,"metric in ['log2 size slope','high minus low slope']")],
'C4':[(70,None),(69,"level=='journal' and supported")],
'C5':[(74,"metric=='larger minus solo' and group=='10 minus 1'"),(73,"group=='All'"),(77,"metric=='fitted parameter difference' and group=='10 minus 1'")],
'C6':[(78,"metric.str.contains('contrast')")],
'C7':[(79,"metric in ['Unadjusted','Year + topic + author FE']"),(81,None)],
'C8':[(71,"metric.str.contains('slope') and metric not in ['F rank slope']")],
'C9':[(72,"metric.str.contains('slope')")],
}
status={'C1':'partly reproduced: overall, not monotone; single institution','C2':'reproduced locally: distributions differ, not an iid KS test','C3':'partly reproduced: bottom-half only; stronger top gradient not supported','C4':'partly reproduced: majority of supported fields/subfields, not universal; across journals not testable','C5':'partly reproduced: empirical age/popularity and age-decay direction supported; popularity exponent inconclusive and fits imperfect','C6':'partly reproduced: 51–100 earlier than solo on a complete-year share; small/disruptive long-delay not testable','C7':'partly reproduced: comparable-sample FE gradient persists; review contrast imprecise in main; no theory/empirical classification','C8':'partly reproduced: short windows and simplified ratio only','C9':'partly testable: descriptive acknowledgment differences; historical, company-patent and Nobel components not testable'}
chunks=[]; findings={}
for claim,items in sel.items():
 rows=pd.concat([(D[i] if q is None else D[i].query(q,engine='python')).assign(source=f'T{i}',claim=claim,status=status[claim]) for i,q in items],ignore_index=True)
 chunks.append(rows)
 lines=[]
 for r in rows.to_dict('records'):
  lbl=next((r[k] for k in ['group','level'] if isinstance(r.get(k),str)),''); extra='; '.join(r[k] for k in ['metric_name','target','distribution'] if isinstance(r.get(k),str));
  lines.append(f"{r['domain']} {r['metric']} {lbl}{' ('+extra+')' if extra else ''}: {r['estimate']:.6g} [{r['lo']:.6g}, {r['hi']:.6g}], n={r['n']:,} ({r['source']})")
 findings[claim]=record_finding(f"{claim} — {status[claim]}. All intervals 95%. "+'; '.join(lines),json.loads(rows.to_json(orient='records')))
print('FINDINGS',findings)
headid=save_table(pd.concat(chunks,ignore_index=True),'Stage 2 side-by-side headline evidence for C1–C9','T66–T81 carry full results. U>0 uses revised no-FPC intervals, except C7 model estimates use no-FPC clustered intervals. C5 also reconstructs the original all-draw target.')
print('HEADLINE',headid)
coverage=D[82].query("stratum=='All' and publication_year==0"); cv=coverage.iloc[0]; screen=D[83]; refaudit=D[85]; audit=record_finding('Stage 2 audit (counts, not confidence limits). T82: 8,000 draws; main 7,933 F>0, 64 refs-only and 3 union-zero; 2021–23 fixed 5,671 F>0, 339 refs-only, 2 union-zero among 6,012 complete, with 1,988 incomplete 2024 draws. The 5,671 also have main F>0; 5,966 have main F>0 in 2021–23. T83: 55,371 snapshot works; 10,720 with no recorded reference edge and registered count zero (3,507 snapshot-cited, 3,188 with later-year and 482 with dated local evidence; criteria overlap); 4,110 with refs but no positive local proxy; 40,541 kept. T85: strict C5 has 446,323 deduplicated pairs, 373,977 distinct IDs, 7,547 missing reference year, 1,742 negative ages, 10,732 same-year ages, 7,230 missing popularity, and no observed zero popularity. No Stage-2 API calls or spend.',{'coverage':json.loads(D[82].to_json(orient='records')),'screen':json.loads(screen.to_json(orient='records')),'references':json.loads(refaudit.to_json(orient='records')),'requests':0,'usd':0.0})
print('AUDIT',audit)
base=Path('artifacts'); figures=[]
for aid,stage1,stem in [('P15','P3','fig2-team-stage2'),('P19','P1','ext-raw-disruption-stage2'),('P18','P6','fig3-impact-stage2'),('P16','P10','fig3-fields-stage2'),('P17','P12','fig4-empirical-stage2')]:
 md=json.loads((base/aid/'meta.json').read_text()); assert md['status']=='approved'; md['stage1_source']=stage1; md['corrected_files']=[f'figures/{stem}.{e}' for e in ['pdf','png']]; md['immutable_gate_files']=[f'artifacts/{aid}/figure.{e}' for e in ['pdf','png']]; assert all(Path(a).read_bytes()==Path(b).read_bytes() for a,b in zip(md['corrected_files'],md['immutable_gate_files'])); figures.append(md)
for e in ['pdf','png']: assert Path(f'figures/fig4-empirical.{e}').read_bytes()==Path(f'artifacts/P12/figure.{e}').read_bytes()
idx=save_json(dict(figures=figures,earlier_stage2={'P13':'approved; superseded by P19','P14':'needs revision; superseded by P18'},P12_usage='Use P17 immutable figure.pdf or figures/fig4-empirical-stage2.pdf, with its gated caption and T75 curves; present T76/T77 separately. P12 archived bytes under the old stem are deliberately unchanged and contain old FPC ribbons; never embed those for corrected inference. P17 was submitted under the same fig4-empirical slug, but the cross-stage gate returned version 1 with no automatic parent. It explicitly declares P12 as an input/source. P9 is superseded and unused.',findings=findings,headlines=headid,audit=audit),'json','Stage 2 gate and writer handoff index','Exact captions, review outcomes, file paths, provenance, and findings. No report generated.')
print('INDEX',idx)
paths=['analysis_stage2.py','stage2_handoff.py']; codeid=save_json(dict(scripts={p:Path(p).read_text() for p in paths},sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths+['analysis_stage1.py']},entrypoints={'estimates_and_figures':"exec(Path('analysis_stage2.py').read_text())",'figures_only':"STAGE2_RUN=False; exec(Path('analysis_stage2.py').read_text()); render_saved_stage2()",'evidence_handoff':"exec(Path('stage2_handoff.py').read_text())"},prior_code='J12 / analysis_stage1.py; verified byte equality before patching in memory',writer_index=idx),'json','Stage 2 executable offline correction and handoff code','Frozen T32/T33 and T45 plus local snapshot joins; no external calls. Figure gate approvals are harness actions on the staged PDF/PNG, not generated by code.')
print('CODE',codeid)
