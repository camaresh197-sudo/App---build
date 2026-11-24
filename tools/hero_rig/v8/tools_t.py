import json,sys
import numpy as np
exec(open('/home/claude/tools_glbcmp.py').read().split("A,NA=")[0])
g,_=glob(load(sys.argv[1]));d=json.load(open(sys.argv[2]))
rows=[]
for n,v in d.items():
    if n in g:
        t=np.array(v[9:12])-g[n][:3,3];rows.append((float(np.linalg.norm(t)),n,[round(float(x),3) for x in t]))
rows.sort(reverse=True)
big=[r for r in rows if r[0]>0.01]
print(len(rows),"joints;",len(big),"off by >1 cm")
for r in rows[:int(sys.argv[3]) if len(sys.argv)>3 else 30]:print(f"{r[1]:12s} {r[0]*100:5.1f} cm  {r[2]}")
