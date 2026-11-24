# cell 34 | agent: analyst | original run: ok | artifacts created: none
scripts['figures']=r'''
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from textwrap import shorten
Path('figures').mkdir(exist_ok=True); plt.rcParams.update({'font.size':9,'axes.labelsize':9,'axes.titlesize':10,'legend.fontsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'}); palette=['#0072B2','#B44A00','#00805D']; markers=['o','s','^']; labels=H

def save(fig,slug):
 for ext in ['pdf','png']:fig.savefig(Path('figures')/f'{slug}.{ext}',dpi=250,bbox_inches='tight',facecolor='white')
 plt.close(fig)
def err(ax,t,b,col,fmt='o',**opts):
 m=t.estimate.to_numpy(); return ax.errorbar(b,m,yerr=np.maximum(0,[m-t.lo.to_numpy(),t.hi.to_numpy()-m]),fmt=fmt,color=col,capsize=2,linewidth=1,markersize=3.5,**opts)
def prep(ax): ax.grid(axis='y',alpha=.22);ax.set_axisbelow(True)
fig,axs=plt.subplots(2,1,figsize=(7.05,5.05),sharex=True,layout='constrained'); b=np.arange(13)
for j,(ax,metric,yl) in enumerate(zip(axs,['D percentile','median F'],['Mean D percentile (0–100)','Median citing works (count)'])):
 t=c1[c1.metric.eq(metric)]; err(ax,t,b,palette[j],fmt='o-'); ax.set_ylabel(yl); prep(ax);ax.set_title(('A  Disruption rank','B  Citation count')[j],loc='left'); ax.axvline(9.5,color='#777777',ls=':',lw=.8)
 if j==0: ax.axhline(50,color='#888888',ls='--',lw=.8);ax.set_ylim(30,67)
axs[-1].set_xticks(b,[f'{g}\n{n}' for g,n in zip(H,c1[c1.metric.eq('D percentile')].n)]);axs[-1].set_xlabel('Team size (authors; sample n below each size band)');save(fig,'fig2-team')
fig,ax=plt.subplots(figsize=(7.05,3.75),layout='constrained'); prep(ax);ax.axhline(50,color='#888888',ls='--',lw=.8);ax.axvline(9.5,color='#777777',ls=':',lw=.8)
for j,lab in enumerate(impnames):
 t=c3[(c3.group==lab)&(c3.metric=='mean D percentile')]; nn=int(t.n.sum()); err(ax,t,b+(j-1)*.15,palette[j],fmt=markers[j]+'-',label=f'{lab} (n={nn:,})')
ax.set_xticks(b,H); ax.set_xlabel('Team size (authors)');ax.set_ylabel('Mean D percentile (0–100)');ax.legend(loc='best',frameon=True,title='Within-year citation impact');save(fig,'fig3-impact')
fld=c4[(c4.level=='field')&c4.supported].sort_values('estimate').copy(); jj=np.arange(len(fld)); fig,ax=plt.subplots(figsize=(7.1,6.18),layout='constrained'); m=fld.estimate.to_numpy();ax.errorbar(m,jj,xerr=np.maximum(0,[m-fld.lo.to_numpy(),fld.hi.to_numpy()-m]),fmt='o',color=palette[0],capsize=2,markersize=3.3,lw=1);ax.axvline(0,color='#555555',ls='--',lw=.8);ax.set_yticks(jj,[f'{v} (n={n:,})' for v,n in zip(fld.group,fld.n)]);ax.invert_yaxis();ax.grid(axis='x',alpha=.22);ax.set_xlabel('Change in mean D percentile per doubling of authors (points)');ax.set_title('20 supported OpenAlex fields • teams of 1–10 authors',loc='left');save(fig,'fig3-fields')
fig,axs=plt.subplots(1,2,figsize=(7.1,3.65),layout='constrained'); sel=c5p[c5p.target.eq('edge')]; subgroups=['1','10','51–100']
for j,(ax,key) in enumerate(zip(axs,sel.metric_name.unique())):
 for k,g in enumerate(subgroups):
  t=sel[(sel.metric_name==key)&(sel.group==g)]; vv=t.threshold.to_numpy(); ax.plot(vv,t.estimate,color=palette[k],label=f'{g}: {t.n_edges.iloc[0]:,} edges',lw=1.5,ls=['-','--','-.'][k]); ax.fill_between(vv,t.lo,t.hi,color=palette[k],alpha=.15,linewidth=0)
 if j:ax.set_xscale('symlog',linthresh=1);ax.set_xticks([1,10,100,1000,10000,100000],['1','10','100','1k','10k','100k']);ax.set_xlim(0,360000)
 else: ax.set_xlim(0,100)
 ax.set_xlabel(['Reference age (years)','Current citations to reference (count)'][j]);ax.set_ylim(0,1.03);ax.yaxis.set_major_formatter(PercentFormatter(1));prep(ax);ax.legend(frameon=True,loc='upper right',title='Authors and available edges',fontsize=7);ax.set_title(['A  Reference age','B  Reference popularity'][j],loc='left')
axs[0].set_ylabel('References above threshold (%)');save(fig,'fig4-references')
fig,ax=plt.subplots(figsize=(7.05,3.75),layout='constrained'); prep(ax)
for j,g in enumerate(subgroups):
 t=c2[(c2.group==g)&(c2.metric=='CDF')]; vv=t.threshold.to_numpy(); ax.step(vv,t.estimate,where='post',color=palette[j],ls=['-','--','-.'][j],lw=1.5,label=f'{g} authors (n={t.n.iloc[0]:,})'); ax.fill_between(vv,t.lo,t.hi,step='post',color=palette[j],alpha=.15,linewidth=0)
ax.axvline(0,color='#666666',ls=':',lw=.8);ax.set_xscale('symlog',linthresh=1e-5);ax.set_xlim(-.1,.1);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('Raw disruption score D (symmetric log scale)');ax.set_ylabel('Works at or below D (%)');ax.legend(loc='lower right');save(fig,'ext-raw-disruption')
'''
exec(scripts['figures'])
print(list(Path('figures').iterdir()))
