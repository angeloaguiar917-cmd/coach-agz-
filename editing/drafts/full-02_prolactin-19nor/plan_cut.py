import numpy as np, json
FPS=30
db=np.load('db10ms.npy'); n=len(db)
thr=np.percentile(db,50)-14
q=db<thr; runs=[]; i=0
while i<n:
    if q[i]:
        j=i
        while j<n and q[j]: j+=1
        if (j-i)*0.01>=0.24: runs.append((i*0.01,j*0.01))
        i=j
    else: i+=1
fr=lambda t: round(t*FPS)/FPS
remove=[(0.0,0.0)]
# stumble: "mammary glan-" -> keep "the | mammary gland tissue"
remove.append((fr(41.80),fr(42.60)))
for a,b in runs:
    if a<0.3 or b>103.9: continue
    if 41.6<a<42.8: continue
    ra,rb=fr(a+0.06),fr(b-0.06)
    if rb-ra>=2/FPS: remove.append((ra,rb))
remove=sorted([r for r in remove if r[1]>r[0]])
END=fr(104.30)
keep=[];t=0.0
for a,b in remove:
    if a>t: keep.append((t,a))
    t=max(t,b)
keep.append((t,END))
json.dump({'remove':remove,'keep':keep,'fps':FPS},open('trim.json','w'),indent=1)
print(len(remove),'cuts, removed',round(sum(b-a for a,b in remove),2),'s; out dur',round(sum(b-a for a,b in keep),2))
print(remove)
