import json,numpy as np,wave,sys
SP=sys.argv[1]
w=wave.open(SP+'/src/a16.wav'); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
hop=160; n=len(a)//hop; rms=np.sqrt((a[:n*hop].reshape(n,hop)**2).mean(1)); db=20*np.log10(rms+1e-6)
floor=np.percentile(db,10); thr=floor+12
print('floor',floor,'thr',thr)
def t2i(t): return int(t*100)
def snap_in(t):
    i=t2i(t)
    for k in range(i, max(0,i-30), -1):
        if db[k:k+3].max()<thr: return k/100
    return t-0.08
def snap_out(t):
    i=t2i(t)
    for k in range(i, i+35):
        if db[k-2:k+1].max()<thr: return k/100
    return t+0.1
SEG=[(0.0,7.40,'hook'),(7.92,11.22,'breakdown'),(28.80,40.72,'systems'),(42.68,47.22,'anavar mild'),
(53.10,55.62,'barely liver'),(57.40,61.26,'crushes HDL'),(63.74,74.50,'apoB'),(77.42,87.66,'six pack dose'),
(93.04,99.72,'fat builds'),(103.56,108.64,'carcinogen'),(113.30,116.34,'different weapons'),
(132.74,145.32,'simplify'),(147.6,148.88,'very different'),(156.06,164.66,'guy ripping'),
(183.45,190.08,'gas station'),(194.12,196.08,'illegal'),(201.78,210.88,'visible'),(217.34,220.20,'liver kidneys'),
(237.66,241.62,'roadmap'),(244.02,247.34,'test analyze'),(250.26,263.30,'cta')]
keep=[]
for s,e,nm in SEG:
    s2=snap_in(s); e2=snap_out(e)
    # internal silences >=0.25 -> trim to 0.12
    i0,i1=t2i(s2),t2i(e2); sil=db[i0:i1]<thr
    runs=[];k=0
    while k<len(sil):
        if sil[k]:
            j=k
            while j<len(sil) and sil[j]: j+=1
            if j-k>=25 and k>3 and j<len(sil)-3: runs.append(((i0+k)/100,(i0+j)/100))
            k=j
        else: k+=1
    cur=s2
    for r0,r1 in runs:
        keep.append([cur,r0+0.06]); cur=r1-0.06
    keep.append([cur,e2])
    print(f'{nm:18s} {s:7.2f}->{s2:7.2f}  {e:7.2f}->{e2:7.2f}  trims={[(round(a,2),round(b,2)) for a,b in runs]}')
# frame align 30fps
fa=lambda t: round(t*30)/30
keep=[[fa(a),fa(b)] for a,b in keep if fa(b)-fa(a)>=2/30]
json.dump(keep,open(SP+'/build/keep.json','w'))
print('pieces',len(keep),'dur',sum(b-a for a,b in keep))
