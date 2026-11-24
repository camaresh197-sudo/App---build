import json,struct,sys
import numpy as np
def load(p):
    d=open(p,'rb').read();n=struct.unpack('<I',d[12:16])[0];return json.loads(d[20:20+n])
def quat(q):
    x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def glob(g):
    N=g['nodes'];par={}
    for i,n in enumerate(N):
        for c in n.get('children',[]):par[c]=i
    cache={}
    def G(i):
        if i in cache:return cache[i]
        n=N[i];M=np.eye(4)
        if 'matrix' in n:M=np.array(n['matrix']).reshape(4,4).T
        else:
            M[:3,:3]=quat(n.get('rotation',[0,0,0,1]))@np.diag(n.get('scale',[1,1,1]));M[:3,3]=n.get('translation',[0,0,0])
        r=G(par[i])@M if i in par else M;cache[i]=r;return r
    return {n['name']:G(i) for i,n in enumerate(N)},N
A,NA=load_=None,None
a,_=glob(load(sys.argv[1]));b,_=glob(load(sys.argv[2]))
names=sys.argv[3:]
for n in names:
    pa=a.get(n);pb=b.get(n)
    f=lambda m:None if m is None else [round(float(x),3) for x in m[:3,3]]
    print(f"{n:12s} shipped {f(pa)}  wip {f(pb)}")
print("only shipped:",[k for k in a if k not in b][:60])
print("only wip:",[k for k in b if k not in a][:60])
