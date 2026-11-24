# cell 29 | agent: analyst | original run: ok | artifacts created: T49
scripts={}
scripts['core']=r'''
import numpy as np, pandas as pd
from scipy.stats import kstest
from scipy.special import zeta
from scipy.optimize import minimize_scalar
s=load('T2').sort_values('sample_id').reset_index(drop=True); h=load('T5'); c=load('T33').sort_values('sample_id').reset_index(drop=True); annual=load('T32'); edges=load('T3'); meta=load('T45'); rc=load('T46'); rf=load('T47'); audit0=load('J9')
H=[str(i) for i in range(1,11)]+['11-20','21-50','51-100']; groups=[s.stratum.eq(g).to_numpy() for g in H]; w=s.weight.to_numpy(); y=s.publication_year.to_numpy(); x=np.log2(s.authors_count.to_numpy()); N=len(s); small=s.authors_count.le(10).to_numpy(); T=1000
assert s[['work_id','sample_id','stratum','publication_year','authors_count']].equals(c[s[['work_id','sample_id','stratum','publication_year','authors_count']].columns]); assert np.allclose(s.weight,c.weight) and np.allclose(s.pi,c.pi)
assert N==8000 and s.work_id.is_unique and h.N_h.sum()==40541 and np.isclose(w.sum(),40541)
assert s.groupby('stratum').size().sort_index().equals(h.set_index('stratum').n_h.sort_index())
assert np.allclose(s.weight,s.stratum.map(h.set_index('stratum').weight)) and np.allclose(w*s.pi,1)
def arr(col):return c[col].to_numpy(dtype=float,na_value=np.nan)
D,F,U,DF,FF,R=map(arr,['main_D','main_F','main_U','fixed_D','fixed_F','main_simplified_ratio']); valid=np.isfinite(D); strict=valid&(F>0); common=valid&np.isfinite(DF)&(y<=2023)
for p in ['main','fixed']:
 f,i,u,j,k,d=map(arr,[p+'_'+v for v in ['F','n_i','U','n_j','n_k','D']]); mask=np.isfinite(u); assert ((i[mask]>=0)&(j[mask]>=0)&(k[mask]>=0)).all(); assert np.allclose((i+j)[mask],f[mask]) and np.allclose((i+j+k)[mask],u[mask]); assert np.allclose(d[u>0],((i-j)[u>0]/u[u>0])) and (np.abs(d[u>0])<=1).all() and np.isnan(d[u==0]).all()
assert np.isnan(DF[y==2024]).all() and (FF[common]<=F[common]).all()
aa=annual.merge(s[['sample_id','work_id','publication_year']],on=['sample_id','work_id'],validate='many_to_one'); assert len(aa)==len(annual) and not aa.duplicated(['sample_id','citer_year']).any(); aa['lag']=aa.citer_year-aa.publication_year
assert ((aa.lag>=0)&(aa.citer_year<=2026)).all(); assert np.array_equal(aa.groupby('sample_id').F.sum().to_numpy(),F)
afix=aa[aa.lag<=2].groupby('sample_id')[['F','I','U','n_i','n_j','n_k']].sum().reindex(s.sample_id)
for v in afix: assert np.array_equal(afix[v].to_numpy()[y<=2023],arr('fixed_'+v)[y<=2023]); assert np.array_equal(aa.groupby('sample_id')[v].sum().to_numpy(),arr('main_'+v))
assert len(edges)==448173 and not edges.duplicated(['work_id','reference_id']).any(); assert (edges.work_id!=edges.reference_id).all(); assert meta.reference_id.is_unique and set(edges.reference_id)==set(meta.reference_id); assert rc.focal_reference_edges.sum()==len(edges)==rf.reference_edges.sum()
assert np.array_equal(edges.groupby('work_id').size().reindex(s.work_id),s.usable_refs)
rng=np.random.default_rng(20261123); W=np.tile(w,(T+1,1))
for _,z in h.iterrows():
 idx=np.flatnonzero(s.stratum.eq(z.stratum)); n=len(idx); f=n/z.N_h
 if f<1: W[1:,idx]*=1+np.sqrt(1-f)*(rng.multinomial(n-1,np.full(n,1/n),size=T)*n/(n-1)-1)
assert np.allclose(W.sum(axis=1),40541)
def ranker(v,keep):
 out=np.full(W.shape,np.nan)
 for yy in np.unique(y):
  idx=np.flatnonzero((y==yy)&keep&np.isfinite(v)); ix=idx[np.argsort(v[idx],kind='stable')]; starts=np.flatnonzero(np.r_[True,np.diff(v[ix])!=0]) if len(ix) else []
  if not len(ix):continue
  tot=np.add.reduceat(W[:,ix],starts,axis=1); cum=np.cumsum(tot,axis=1); mid=(cum-tot/2)/cum[:,-1:]*100
  out[:,ix]=np.repeat(mid,np.diff(np.r_[starts,len(ix)]),axis=1)
 return out
P=ranker(D,valid); Q=ranker(F,valid); PS=ranker(D,strict); Pc=ranker(D,common); Pf=ranker(DF,common)
for yy in np.unique(y):assert np.allclose(np.average(P[:,valid&(y==yy)],axis=1,weights=W[:,valid&(y==yy)]),50)
def stat(v,m):
 if not m.any():return np.full(T+1,np.nan)
 a=np.asarray(v); ww=W[:,m]; return np.sum(ww*(a[...,m]),axis=1)/ww.sum(axis=1)
def quant(v,m,p=.5):
 ix=np.flatnonzero(m); ix=ix[np.argsort(v[ix],kind='stable')]; cs=np.cumsum(W[:,ix],axis=1); return v[ix[(cs>=p*cs[:,-1:]).argmax(axis=1)]]
def slope(v,m):
 if m.ndim==1:
  ww=W[:,m]; xx=x[m]; vv=v[...,m]; xc=xx-(ww*xx).sum(1)[:,None]/ww.sum(1)[:,None]; return (ww*xc*vv).sum(1)/(ww*xc**2).sum(1)
 ww=W*m; xc=x-(ww*x).sum(1)[:,None]/ww.sum(1)[:,None]; return (ww*xc*np.nan_to_num(v)).sum(1)/(ww*xc**2).sum(1)
def dynmean(v,m):
 ww=W*m; return (ww*np.nan_to_num(v)).sum(1)/ww.sum(1)
def ci(a):
 a=np.asarray(a); ll,uu=np.nanquantile(a[1:],[.025,.975]);return dict(estimate=float(a[0]),lo=float(ll),hi=float(uu))
def row(key,a,m=None,**kw):return dict(metric=key,**ci(a),**({} if m is None else dict(n=int(m.sum()),weighted_n=float(w[m].sum()))),**kw)
def table(rows,title,desc=''):
 d=pd.DataFrame(rows); print(title,d.shape,save_table(d,title,desc)); return d
raw=s[['sample_id','work_id','stratum','publication_year','authors_count','weight','pi']].copy(); raw=raw.assign(D=D,F=F,U=U,D_percentile=P[0],F_percentile=Q[0],strict=strict,main_defined=valid,true_fixed_D=DF,true_fixed_F=FF,common=common,common_main_rank=Pc[0],common_fixed_rank=Pf[0],simplified=R)
rawtab=table(raw,'Stage 1 work-level scores and weighted ranks','One sampled work; main, true fixed and matched-domain percentiles. Missing means undefined/unavailable.')
print(c.main_status.value_counts(),c.fixed_status.value_counts(),h.to_string(index=False),sep='\n')
print(raw.iloc[:5].to_string(index=False))
'''
exec(scripts['core'])
