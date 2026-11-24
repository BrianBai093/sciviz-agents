# cell 36 | agent: analyst | original run: ok | artifacts created: T65
scripts['ref_fit_ci']=r'''
fitrows=[]; par={}; agd={}; alphagrid=np.linspace(1.05,3.5,50001); epsilon=1e-5
for metric in c5f.metric.unique():
 isage=metric.startswith('reference age'); vv=age if isage else pop; ok=ag if isage else pp&(pop>=50); alpha_mean=-(np.log(zeta(alphagrid+epsilon,50))-np.log(zeta(alphagrid-epsilon,50)))/(2*epsilon)
 sums=binwork(ok,vv if isage else np.log(np.maximum(1,vv))); cnt=binwork(ok)
 for frow in c5f[c5f.metric.eq(metric)].itertuples():
  k=groups[H.index(frow.group)]&(cnt>0); ww=W[:,k]; den=ww@cnt[k]; mu=(ww@sums[k])/den
  if isage:
   vvrep=-np.log1p(-1/(1+mu)); fitted=1-np.exp(-vvrep*(frow.gap_threshold+1))
  else:
   vvrep=np.interp(mu,alpha_mean[::-1],alphagrid[::-1]); fitted=1-zeta(vvrep,frow.gap_threshold+1)/zeta(vvrep,50)
  assert abs(vvrep[0]-frow.parameter)<4e-6
  vobs=(ww@binwork(ok&(vv<=frow.gap_threshold))[k])/den
  par[(metric,frow.group)]=vvrep; agd[(metric,frow.group)]=k
  fitrows.append(row('fitted parameter',vvrep,k,distribution=metric,group=frow.group,n_edges=int(cnt[k].sum()),threshold=frow.gap_threshold))
  fitrows.append(row('empirical minus fitted CDF at diagnostic threshold',vobs-fitted,k,distribution=metric,group=frow.group,n_edges=int(cnt[k].sum()),threshold=frow.gap_threshold))
 for gg in ['10','51–100']:
  k=agd[(metric,gg)]|agd[(metric,'1')];fitrows.append(row('fitted parameter difference',par[(metric,gg)]-par[(metric,'1')],k,distribution=metric,group=gg+' minus 1',n_edges=int(cnt[k].sum())))
c5fi=table(fitrows,'C5 fit-parameter intervals and goodness-of-fit diagnostics','Focal-work design replicates re-estimate geometric decay and discrete power-law exponent (fixed count ≥50). CDF gaps use the full-sample-selected diagnostic threshold, held fixed in replicates; intervals are exploratory, not an omnibus test.')
print(c5fi.to_string(index=False))
'''
with threadpool_limits(3):exec(scripts['ref_fit_ci'])
fs=scripts['figures'];fs=fs.replace("headers=['Grouping','Supported / observed','Negative slopes','95% design interval']", "headers=['Grouping','Supported /\\nobserved','Negative\\nslopes','95% design\\ninterval']");fs=fs.replace("bbox=[0.04,0.03,.92,.93]", "colWidths=[.20,.26,.26,.28],bbox=[0,0.02,1,.95]");fs=fs.replace("cell.set_linewidth(.45);cell.set_facecolor", "cell.set_linewidth(.45);cell.set_height(.35 if i==0 else .21);cell.set_facecolor");fs=fs.replace("lw=1.5,ls=['-','--','-.'][k]", "lw=.95,ls=['-','--','-.'][k]");fs=fs.replace("alpha=.29,linewidth=0", "alpha=.38,linewidth=0");fs=fs.replace("ax.set_xlim(0,360000)","ax.set_xlim(0,360000)");scripts['figures']=fs
exec(fs)
