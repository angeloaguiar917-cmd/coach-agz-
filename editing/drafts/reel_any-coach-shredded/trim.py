import json,sys,wave,numpy as np
W=json.load(open(sys.argv[1])); FPS=30
w=wave.open('../src/a16.wav'); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; SR=16000
hop=160; n=len(a)//hop; rms=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)+1e-12) for i in range(n)]); db=20*np.log10(rms)
floor=np.percentile(db,8); speech=np.percentile(db,70); thr=floor+0.35*(speech-floor)
print('floor',round(floor,1),'speech',round(speech,1),'thr',round(thr,1))
rem=[]
for i in range(len(W)-1):
    g0,g1=W[i]['e'],W[i+1]['s']
    if g1-g0<0.18: continue
    lo,hi=int((g0-0.12)*100),int((g1+0.12)*100)
    q=db[lo:hi]<thr; best=(0,0); run=None
    for k,v in enumerate(list(q)+[False]):
        if v and run is None: run=k
        if not v and run is not None:
            if k-run>best[1]-best[0]: best=(run,k)
            run=None
    qs,qe=(lo+best[0])/100,(lo+best[1])/100
    if qe-qs>=0.26:
        cs,ce=qs+0.06,qe-0.06
        cs=round(cs*FPS)/FPS; ce=round(ce*FPS)/FPS
        if ce-cs>=2/FPS: rem.append([round(cs,4),round(ce,4),W[i]['w'],W[i+1]['w']])
tot=sum(r[1]-r[0] for r in rem); print(len(rem),'cuts',round(tot,2),'s')
for r in rem: print(r)
dur=120.7; keep=[];p=0
for c in rem: keep.append([p,c[0]]); p=c[1]
keep.append([p,dur])
json.dump({'remove':[r[:2] for r in rem],'keep':keep},open('trim.json','w'))
