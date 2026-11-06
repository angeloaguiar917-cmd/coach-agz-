# Clinical SFX bed, synthesised (original). Reads events.json written by `render.py --events`.
# Usage: python sfx.py events.json out.wav duration
import numpy as np, wave, json, sys
from scipy.signal import lfilter
SR=48000; DUR=float(sys.argv[3]); n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def lp(x,a): return lfilter([a],[1,-(1-a)],x)
def lpv(x,cut):            # time-varying one-pole lowpass (cut per sample)
    y=np.zeros_like(x); acc=0.0
    for k in range(len(x)): acc+=cut[k]*(x[k]-acc); y[k]=acc
    return y
def norm(y): return y/np.max(np.abs(y))
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR
    y=lpv(rng.standard_normal(m),0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2)
    return norm(y*np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2)
def thud(w=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; fr=55+60*np.exp(-t*28)
    body=np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*(14/w)); click=lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5
    return norm(body+click)
def sub():
    m=int(SR*0.30); t=np.arange(m)/SR; fr=42+30*np.exp(-t*20)
    return norm(np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*12)*np.minimum(1,t/0.004))
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    return norm(np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; fr=48+90*np.exp(-t*30)
    return norm(np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*7)+0.55*lp(rng.standard_normal(m),0.6)*np.exp(-t*45))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR
    y=lpv(rng.standard_normal(m),0.05+0.35*(t/d)); y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t)
    return norm(y*np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05))
dB=lambda x:10**(x/20)
def place(sig,t,g):
    i=int(t*SR); s=sig[:max(0,n-i)]*dB(g); L[i:i+len(s)]+=s; R[i:i+len(s)]+=s
for e in json.load(open(sys.argv[1])):
    k=e['kind']; t=e['t']; g=e.get('g',-24)
    if k=='whoosh': place(whoosh(e['d']),max(0,t-e['d']*0.7),g)     # whoosh peaks into the moment
    elif k=='thud': place(thud(e.get('w',1)),t,g)
    elif k=='sub': place(sub(),t,g)
    elif k=='tick': place(tick(),t,g)
    elif k=='impact': place(impact(),t,g)
    elif k=='scan': place(scan(e['d']),t,g)
out=np.stack([L,R],1); print('sfx peak dBFS',round(20*np.log10(np.max(np.abs(out))),2))
w=wave.open(sys.argv[2],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
