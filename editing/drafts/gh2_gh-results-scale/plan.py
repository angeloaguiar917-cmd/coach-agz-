import numpy as np,wave,json,sys
S=sys.argv[1]
w=wave.open(S+'/work/audio16.wav');a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)
st=0.01; n=int(len(a)/16000/st)
db=np.array([20*np.log10(np.sqrt(np.mean(a[int(i*st*16000):int((i+1)*st*16000)]**2))+1) for i in range(n)])
# smooth
k=np.convolve(db,np.ones(3)/3,'same')
quiet=k<51
keeps=[(0.533,9.983),(10.75,78.86),(79.47,110.05)]
FR=1/60
def snap(t): return round(t*60)/60
out=[]
for k0,k1 in keeps:
    cuts=[]; i=int(k0/st)+1
    while i<int(k1/st)-1:
        if quiet[i]:
            j=i
            while j<int(k1/st) and quiet[j]: j+=1
            dur=(j-i)*st
            if dur>=0.26: cuts.append((i*st+0.07,j*st-0.07))
            i=j
        else: i+=1
    t=k0
    for c0,c1 in cuts:
        out.append([snap(t),snap(c0)]); t=c1
    out.append([snap(t),snap(k1)])
out=[s for s in out if s[1]-s[0]>0.05]
json.dump(out,open(S+'/work/segments.json','w'))
tot=sum(b-a for a,b in out); print(len(out),'segments, total %.2f s'%tot)
print(out)
