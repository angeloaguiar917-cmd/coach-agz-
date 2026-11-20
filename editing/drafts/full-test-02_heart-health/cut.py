import numpy as np, json, wave
db=np.load('env_db.npy'); FPS=30; SR=48000
SEGS=[(0.0,13.62),(120.70,227.40)]
TH=-36; MINRUN=0.22; KEEP=0.06
keeps=[]
for a,b in SEGS:
    i0,i1=int(a*100),int(b*100); q=db[i0:i1]<TH
    runs=[];k=0
    while k<len(q):
        if q[k]:
            j=k
            while j<len(q) and q[j]: j+=1
            runs.append((i0+k,i0+j)); k=j
        else: k+=1
    cur=a
    for r0,r1 in runs:
        s,e=r0/100,r1/100
        if e-s<MINRUN: continue
        if s<=a+0.01: cur=max(cur,e-0.10); continue   # lead-in silence
        cs=round((s+KEEP)*FPS)/FPS; ce=round((e-KEEP)*FPS)/FPS
        if ce-cs<2/FPS: continue
        keeps.append((cur,cs)); cur=ce
    keeps.append((cur,round(b*FPS)/FPS))
keeps=[(round(x*FPS)/FPS,round(y*FPS)/FPS) for x,y in keeps if y-x>0.05]
dur=sum(y-x for x,y in keeps)
print(len(keeps),'pieces; out dur',round(dur,2),'removed',round(13.62+106.7-dur,2))
json.dump({'keeps':keeps,'dur':dur},open('cutlist.json','w'))
# audio assembly with 8ms crossfade
a=np.fromfile('raw48.f32',np.float32); out=[]; xf=int(0.008*SR)
for x,y in keeps:
    seg=a[int(round(x*SR)):int(round(y*SR))].copy()
    seg[:xf]*=np.linspace(0,1,xf); seg[-xf:]*=np.linspace(1,0,xf); out.append(seg)
o=np.concatenate(out); o.astype(np.float32).tofile('cut_audio.f32')
w=wave.open('cut16.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
w.writeframes((np.clip(o[::3],-1,1)*32767).astype(np.int16).tobytes()); w.close()
print('audio s',len(o)/SR)
