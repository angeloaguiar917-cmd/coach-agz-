import json, numpy as np, wave
FPS=30
HEAD=1.04; TAIL=107.56
SIL=[(9.414,9.6585),(40.515,40.774),(50.384,50.639),(53.752,53.992),(67.30,67.5426),(68.316,68.551),(70.995,71.251),(85.403,85.650),(99.578,99.925),(102.666,102.922),(104.917,105.188),(106.193,106.531)]
rem=[(s+0.06,e-0.06) for s,e in SIL]
keep=[];cur=HEAD
for a,b in rem: keep.append([cur,a]); cur=b
keep.append([cur,TAIL])
# snap keep lengths to whole output frames
k2=[];
for a,b in keep:
    n=round((b-a)*FPS); k2.append([round(a,4),round(a+n/FPS,4)])
dur=sum(b-a for a,b in k2)
json.dump({'keep':k2,'dur':dur,'fps':FPS},open('cut.json','w'),indent=1)
print(len(k2),'segments, dur',round(dur,3),'removed',round(108.413-dur,2))
w=wave.open('src48.wav'); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)
xf=int(0.008*sr); out=[]
for i,(a,b) in enumerate(k2):
    s=x[int(a*sr):int(b*sr)].copy()
    if i>0: s[:xf]*=np.linspace(0,1,xf)[:,None]
    if i<len(k2)-1: s[-xf:]*=np.linspace(1,0,xf)[:,None]
    out.append(s)
y=np.concatenate(out)
o=wave.open('cut_voice.wav','wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(sr); o.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes()); o.close()
print('audio sec',len(y)/sr)
