# cell 37 | agent: analyst | original run: ok | artifacts created: none
new4=r'''
fig,axs=plt.subplots(1,2,figsize=(7.15,3.35),layout='constrained',sharey=True)
styles=['-','--','-.']; sels=['1','10','51–100']; sel=c5p[c5p.target.eq('edge')]; handles=[]
for j,(ax,key) in enumerate(zip(axs,sel.metric_name.unique())):
 for k,g in enumerate(sels):
  t=sel[(sel.metric_name==key)&(sel.group==g)]; vv=t.threshold.to_numpy(); handle=ax.plot(vv,t.estimate,color=palette[k],ls=styles[k],lw=1.0)[0]; ax.fill_between(vv,t.lo,t.hi,color=palette[k],alpha=.42,linewidth=0)
  if j==0: handles.append(handle)
 if j:
  ax.set_xscale('symlog',linthresh=1);ax.set_xticks([0,1,10,100,1000,10000,100000],['0','1','10','100','1k','10k','100k']);ax.set_xlim(0,360000)
 else:ax.set_xlim(0,100)
 ax.set_ylim(0,1);ax.set_yticks(np.linspace(0,1,6));ax.yaxis.set_major_formatter(PercentFormatter(1));prep(ax);ax.set_xlabel(['Reference age (years)','Current reference citations (count; symlog)'][j]); ax.set_title(['A  Reference age','B  Reference popularity'][j],loc='left');
axs[0].set_ylabel('Weighted share of edges above threshold'); fig.suptitle('References used by solo and larger teams',fontsize=11,y=1.04); fig.legend(handles,['1 author (623 works)','10 authors (626 works)','51–100 authors (481 works)'],loc='outside upper center',ncol=3,frameon=False);save(fig,'fig4-empirical')
'''
scripts['figures_empirical']=new4
exec(new4)
