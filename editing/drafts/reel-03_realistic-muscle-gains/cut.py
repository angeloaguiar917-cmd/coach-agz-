import numpy as np, json, subprocess, sys, wave
S=sys.argv[1]; FPS=30
# check header size
w=wave.open(S+'/src/audio48.wav'); n=w.getnframes(); a=np.frombuffer(w.readframes(n),np.int16).reshape(-1,2).astype(np.float32)/32768
SR=48000; mono=a.mean(1)
def rms(t0,t1):
    i0,i1=int(t0*SR),int(t1*SR); return float(np.sqrt(np.mean(mono[i0:i1]**2))+1e-9)
def quiet(lo,hi,win=0.02):
    best=None
    for t in np.arange(lo,hi,0.005):
        r=rms(t-win/2,t+win/2)
        if best is None or r<best[0]: best=(r,t)
    return best[1]
def snap(t): return round(t*FPS)/FPS
segs=[  # (start, end) source seconds, in output order
 (0.0, quiet(49.12,49.30)),
 (quiet(63.15,63.44), quiet(69.22,69.46)),
 (quiet(70.40,70.56), quiet(372.93,373.10)),
 (379.5, quiet(463.66,463.80)),
 (quiet(373.44,373.58), quiet(379.30,379.52)),
 (quiet(463.70,463.82), 464.70),
]
segs=[(snap(s),snap(e)) for s,e in segs]
# dead-air trim inside segments: silence runs >=0.22s (-40 dB, 20ms frames) -> keep 0.12
fr=0.01; thr=10**(-40/20)
pieces=[]
for s,e in segs:
    t=s; cur=s; run=None; cuts=[]
    ts=np.arange(s,e,fr)
    q=[rms(x,x+fr)<thr for x in ts]
    i=0
    while i<len(q):
        if q[i]:
            j=i
            while j<len(q) and q[j]: j+=1
            d=(j-i)*fr
            if d>=0.22 and i>0 and j<len(q): cuts.append((ts[i]+0.06, ts[i]+d-0.06))
            i=j
        else: i+=1
    for c0,c1 in cuts:
        c0,c1=snap(c0),snap(c1)
        if c1-c0>=2/FPS: pieces.append((cur,c0)); cur=c1
    pieces.append((cur,e))
pieces=[p for p in pieces if p[1]-p[0]>=1/FPS]
dur=sum(e-s for s,e in pieces)
print('segments',segs); print('pieces',len(pieces),'dur',round(dur,2))
# timeline: output-time bounds for each piece + source map
out=[];T=0
for s,e in pieces: out.append({'src':[s,e],'out':[round(T,4),round(T+e-s,4)]}); T+=e-s
json.dump({'pieces':out,'segs':segs,'dur':T},open(S+'/build/timeline.json','w'),indent=1)
# audio with 8ms fades at every join
X=8*SR//1000; chunks=[]
for s,e in pieces:
    c=a[int(round(s*SR)):int(round(e*SR))].copy()
    r=np.linspace(0,1,X)[:,None]; c[:X]*=r; c[-X:]*=r[::-1]; chunks.append(c)
A=np.concatenate(chunks); A=(np.clip(A,-1,1)*32767).astype(np.int16)
with wave.open(S+'/build/cut_audio.wav','wb') as o: o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes(A.tobytes())
# video: one trim per piece, concat
fc=''.join(f'[0:v]trim={s:.4f}:{e:.4f},setpts=PTS-STARTPTS,fps=30[v{i}];' for i,(s,e) in enumerate(pieces))
fc+=''.join(f'[v{i}]' for i in range(len(pieces)))+f'concat=n={len(pieces)}:v=1:a=0[v]'
open(S+'/build/fc.txt','w').write(fc)
