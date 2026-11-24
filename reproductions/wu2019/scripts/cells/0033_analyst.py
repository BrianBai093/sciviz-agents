# cell 33 | agent: analyst | original run: ok | artifacts created: T62, T63, T64, J11
script=scripts['claim7']; a0=script.index(' v=v.copy();'); b0=script.index('\ndef csev',a0); scripts['claim7']=script[:a0]+''' from scipy.sparse import csr_matrix,hstack
 from scipy.sparse.linalg import lsmr
 ix=np.arange(len(v)); sw=np.sqrt(wt); Qm=hstack([csr_matrix((sw,(ix,f)),shape=(len(v),f.max()+1)) for f in fe],format='csr'); solve=lsmr(Qm,sw*v,atol=1e-12,btol=1e-12,maxiter=15000); assert solve[1]!=7
 r=v-(Qm@solve[0])/sw; assert max(abs(Qm.T@(sw*r)))<1e-4
 return r
'''+script[b0:]
with threadpool_limits(2):exec(scripts['claim7'])
