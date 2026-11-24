# cell 41 | agent: analyst | original run: ok | artifacts created: J12, J13, F10
qc=r'''
assert (int(c.main_n_i.iloc[0]),int(c.main_n_j.iloc[0]),int(c.main_n_k.iloc[0]))==(0,1,4354)
assert np.isclose(D[0],-1/4355) and np.isclose(D[1],(12-107)/27749)
k=valid&(y==2022); manual=(w[k&(D<0)].sum()+.5*w[k&(D==0)].sum())/w[k].sum()*100; assert abs(P[0,3]-manual)<1e-10
''';exec(qc);scripts['hand_checks']=qc
from pathlib import Path
ss=scripts['figures']; ia=ss.index("fig,axs=plt.subplots(1,2,figsize=(7.1,4.70)"); ib=ss.index("fig,ax=plt.subplots(figsize=(7.05,3.75)",ia);scripts['figures']=ss[:ia]+ss[ib:]
seq=['core','hand_checks','claims123489','claims56','claim7','ref_fit_ci','figures','figures_empirical','findings']; code='''# Stage-1 Columbia team-size reproduction, no network calls.\n# Run in a kernel with sql, load, save_table, save_json, record_finding.\n# Input artifacts T2, T5, T33, T32, T3, T45, T46, T47 and J9 and local SQL tables.\nfrom threadpoolctl import threadpool_limits\n'''
import textwrap
for k in seq:
 code+='\n# ---- '+k+' ----\n'+('with threadpool_limits(3):\n'+textwrap.indent(scripts[k].strip(),'    ') if k in ['claims56','claim7','ref_fit_ci'] else scripts[k])+'\n'
compile(code,'analysis_stage1.py','exec');Path('analysis_stage1.py').write_text(code); print(save_json({'path':'analysis_stage1.py','code':code,'inputs':['T2','T5','T33','T32','T3','T45','T46','T47','J9'],'execution_order':seq},'json','Stage 1 executable analysis and figure code','Executable Python using the persistent harness helpers; no network calls or API spend.'))
gate=[dict(id=id,slug=sl,claims=cl,gate='approved',earlier=older,files=[f'figures/{sl}.{ext}' for ext in ['pdf','png']]) for id,sl,cl,older in [('P3','fig2-team',['C1'],[]),('P1','ext-raw-disruption',['C2'],[]),('P6','fig3-impact',['C3'],['P2 needs revision']),('P10','fig3-fields',['C4'],['P5 needs revision','P7 needs revision']),('P12','fig4-empirical',['C5'],['P4 needs revision','P8 needs revision','P9 accepted with open issues on superseded slug fig4-references','P11 needs revision'])]]
print(save_json({'deliverable_figures':gate,'note':'P9 has open issues and is superseded by P12; the deliverable figure set includes only independently approved figures.'},'json','Stage 1 independent figure gate index','Approved figure artifact IDs, file locations, earlier revision history and claim mapping.'))
print(record_finding('Audit: 8,000 sampled, weighted frame 40,541; 7,997 defined main D (64 F=0), 3 U=0; 6,012 eligible true-fixed cohorts with 6,010 defined pairs; 1,988 partial 2024 excluded. Zero additional API spend. Exact audit counts have no sampling intervals.',A0))
