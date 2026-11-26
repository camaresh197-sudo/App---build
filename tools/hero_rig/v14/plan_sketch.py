import json, math, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
S='/tmp/claude-0/-home-user-App---build/06e83864-e0ef-54c3-9ec4-508030560da5/scratchpad/hero/'
pts=json.load(open(S+'v143_pts.json')); L=json.load(open(S+'v143_landmarks.json')); prof=json.load(open(S+'prof_ours.json'))
def catmull(P,closed=True,n=24):
    P=np.array(P,float); N=len(P); out=[]
    rng=range(N) if closed else range(N-1)
    for i in rng:
        p0=P[(i-1)%N] if closed or i>0 else P[0]; p1=P[i%N]; p2=P[(i+1)%N]; p3=P[(i+2)%N] if closed or i+2<N else P[-1]
        for t in np.linspace(0,1,n,endpoint=False):
            out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t**2+(-p0+3*p1-3*p2+p3)*t**3))
    if not closed: out.append(P[-1])
    return np.array(out)
def superell(cx,cz,a,b,n=2.4,m=120):
    t=np.linspace(0,2*np.pi,m)
    c=np.cos(t); s=np.sin(t)
    return cx+a*np.sign(c)*np.abs(c)**(2/n), cz+b*np.sign(s)*np.abs(s)**(2/n)
def ell(cx,cz,rx,rz,m=80):
    t=np.linspace(0,2*np.pi,m); return cx+rx*np.cos(t), cz+rz*np.sin(t)
fig,ax=plt.subplots(1,2,figsize=(14,9),gridspec_kw={'width_ratios':[1.3,1]})
a=ax[0]
a.scatter([p[0]*1000 for p in pts],[p[2]*1000 for p in pts],s=0.4,c='#ccc')
for sx in (1,-1):
    ex,_,ez=L['eye_l'] if sx>0 else L['eye_r']
    for r,col in [(8,'#7a7aff'),(14,'#5577dd'),(20,'#99aaee')]:
        x,z=ell(ex,ez,r*1.3,r*0.8); a.plot(x,z,color=col,lw=0.9)
    x,z=ell(sx*10.2,1487.5,5.5,3.4); a.plot(x,z,color='darkorange',lw=1.2)
    x,z=ell(sx*10.2,1487.5,9.6,6.6); a.plot(x,z,color='orange',lw=0.9)
for hw,hh,col in [(29,3.0,'red'),(32.5,7.0,'orangered'),(36,11.5,'darkorange'),(40,16.5,'#ffa040')]:
    x,z=superell(0,1466,hw,hh,2.3); a.plot(x,z,color=col,lw=1.1)
right=[(0,1531),(10,1530),(17,1522),(21,1508),(25,1492),(35,1478),(46,1464),(45,1450),(42,1440),(34,1433),(18,1430)]
ctrl=right+[(0,1429.5)]+[(-x,z) for x,z in reversed(right[1:])]
ctrl=[(0,1531)]+right[1:]+[(0,1429.5)]+[(-x,z) for x,z in reversed(right[1:])]
C=catmull(ctrl,True,28); a.plot(C[:,0],C[:,1],color='#00b4d8',lw=2.2,label='nasolabial loop (rounded)')
for sx in (1,-1):
    G=catmull([(sx*57,1518),(sx*54,1500),(sx*52,1482),(sx*50,1466)],False,24); a.plot(G[:,0],G[:,1],color='green',lw=1.5)
    D=catmull([(sx*6.5,1536),(sx*7.5,1520),(sx*8.8,1503),(sx*10,1495)],False,24); a.plot(D[:,0],D[:,1],color='purple',lw=1.1)
jaw=[(-78,1530),(-77,1490),(-74,1458),(-68,1432),(-58,1414),(-44,1402),(-30,1396),(-14,1394.5),(0,1394.3),(14,1394.5),(30,1396),(44,1402),(58,1414),(68,1432),(74,1458),(77,1490),(78,1530)]
J=catmull(jaw,False,12); a.plot(J[:,0],J[:,1],color='navy',lw=1.8,label='jaw / face contour (from the references)')
a.plot([],[],color='green',lw=1.5,label='cheek diagonals'); a.plot([],[],color='red',lw=1.1,label='mouth rings (+/-29 mm wide, rounded ends)'); a.plot([],[],color='purple',lw=1.1,label='nose dorsum flow lines')
a.set_aspect('equal'); a.set_xlim(-75,75); a.set_ylim(1385,1580); a.set_title('Mid-face loops, rounded (front, sketch only)'); a.legend(fontsize=7,loc='lower center')
b=ax[1]
oz=sorted(int(k) for k in prof); op=[-prof[str(z)]-105.0 for z in oz]
b.plot(op,oz,'b-',lw=1.5,label='current profile')
nose=catmull([(2,1533),(10,1515),(18.5,1503),(23,1498),(20,1490),(14,1487),(9,1485)],False,20)
b.plot(nose[:,0],nose[:,1],'r-',lw=2.0,label='rounded dorsum, tip and flat underside')
b.axhline(1487,color='gray',ls=':',lw=0.6); b.set_xlim(-8,35); b.set_ylim(1440,1560)
b.set_xlabel('protrusion from face plane (mm)'); b.set_ylabel('z (mm)'); b.legend(fontsize=7); b.set_title('Nose side view, rounded')
plt.tight_layout(); plt.savefig(S+'midface_plan_round.png',dpi=105); print('ok')
