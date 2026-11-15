import json,subprocess
DUR=121.97
cuts=[]
for line in open('sil.txt'):
    s,e=map(float,line.split())
    if e-s>0.22: cuts.append([s+0.06,e-0.06])
cuts.append([47.50,48.26])          # "uh," between NPP and Deca
cuts.sort(); m=[]
for c in cuts:
    if m and c[0]<=m[-1][1]: m[-1][1]=max(m[-1][1],c[1])
    else: m.append(c)
keep=[];t=0.0
for s,e in m:
    if s>t+0.05: keep.append([round(t,3),round(s,3)])
    t=e
if DUR-t>0.05: keep.append([round(t,3),DUR])
# frame-align to 30fps output by snapping to 1/60 source grid
keep=[[round(a*30)/30,round(b*30)/30] for a,b in keep]
json.dump(keep,open('build/keep.json','w'))
tot=sum(b-a for a,b in keep); print(len(keep),'segments',round(tot,2),'s kept, removed',round(DUR-tot,2))
fc=[]
for i,(a,b) in enumerate(keep):
    fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b-a-0.008:.4f}:d=0.008[a{i}]")
fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(keep)))+f'concat=n={len(keep)}:v=1:a=1[v][a]')
open('build/fc.txt','w').write(';'.join(fc))
pass
