import numpy as np, json
from PIL import Image
im=np.array(Image.open('/root/.claude/uploads/06e83864-e0ef-54c3-9ec4-508030560da5/9b9252ba-image.jpg').convert('RGB')).astype(int)
H,W,_=im.shape
print('IMG', W, H)
bg=np.array([58,58,58])
# skin-ish: reddish/warm and not near background grey; restrict to side view (right half) and above the legend
r,g,b=im[...,0],im[...,1],im[...,2]
skin=(r>g+8)&(r>b+8)&(r>110)
mask=np.zeros_like(skin); mask[:, 380:]=skin[:,380:]
mask[505:,560:]=False   # legend box
rows={}
for y in range(0,H):
    xs=np.where(mask[y])[0]
    if len(xs)>5: rows[y]=(xs.min(), xs.max())
ys=sorted(rows)
print('IMG rows', ys[0], ys[-1])
json.dump({str(k):v for k,v in [(y,[int(rows[y][0]),int(rows[y][1])]) for y in ys]}, open('/tmp/claude-0/-home-user-App---build/06e83864-e0ef-54c3-9ec4-508030560da5/scratchpad/hero/chart_rows.json','w'))
for y in range(ys[0], ys[-1], 30):
    if y in rows: print('ROW', y, rows[y])
