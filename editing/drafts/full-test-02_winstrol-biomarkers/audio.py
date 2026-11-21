import numpy as np, soundfile as sf, subprocess, os
SR=48000
sp,_=sf.read('cut_a.wav'); 
if sp.ndim==1: sp=np.stack([sp,sp],1)
N=len(sp)
bed=np.zeros((N,2),np.float32)
rng=np.random.default_rng(7)
def place(t,sig,gain):
    i=int(t*SR); j=min(N,i+len(sig)); 
    s=sig[:j-i]
    bed[i:j,0]+=s*gain; bed[i:j,1]+=s*gain
def env(n,a,d): 
    e=np.ones(n); ai=int(a*SR); di=int(d*SR)
    e[:ai]=np.linspace(0,1,ai); e[-di:]*=np.linspace(1,0,di); return e
def sub(f0,dur,a=0.004,d=0.12):
    n=int(dur*SR); t=np.arange(n)/SR
    f=np.linspace(f0,f0*0.5,n)
    s=np.sin(2*np.pi*np.cumsum(f)/SR); return (s*env(n,a,d)).astype(np.float32)
def tick(dur=0.05):
    n=int(dur*SR); t=np.arange(n)/SR
    s=np.sin(2*np.pi*2200*t)*np.exp(-t*90); return (s*0.6).astype(np.float32)
def impact(dur=0.5):
    n=int(dur*SR); t=np.arange(n)/SR
    body=np.sin(2*np.pi*np.linspace(90,45,n)/SR*np.arange(n))
    noise=rng.standard_normal(n)*np.exp(-t*30)
    s=body*env(n,0.001,0.4)+noise*0.3*np.exp(-t*18); return (s).astype(np.float32)
def sweep(dur=0.6):
    n=int(dur*SR); t=np.arange(n)/SR
    f=np.linspace(400,2600,n); s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*4)
    return (s*0.25*env(n,0.01,0.2)).astype(np.float32)
# hook
place(0.25,sweep(),0.5)
# scene entries (sub hits)
for t in [20.6,31.8,40.0,53.5,65.8,85.9]: place(t,sub(120,0.45),1.0)
place(27.2,impact(0.55),0.5)          # HDL collapse
for t in [47.1,47.5]: place(t,sub(160,0.2),0.5)  # enzyme bars
for t in [54.9,55.6,56.1,56.6]: place(t,tick(),0.5)  # lab rows
place(68.6,sub(140,0.3),0.6)          # ring
for t in [88.4,88.95,89.8]: place(t,tick(0.06),0.6)  # roadmap
place(99.9,impact(0.6),0.7)           # CTA pill
# gentle lowpass on bed
from numpy.fft import rfft,irfft,rfftfreq
for ch in range(2):
    X=rfft(bed[:,ch]); fr=rfftfreq(N,1/SR); X[fr>5000]*=0.25; bed[:,ch]=irfft(X,N)
bed*=0.5
mix=sp.astype(np.float32)+bed
pk=np.abs(mix).max(); 
if pk>0.99: mix*=0.99/pk
sf.write('premix.wav',mix,SR)
print('peak',pk)
