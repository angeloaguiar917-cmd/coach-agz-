# Clinical SFX bed for the EQ edit (per BRAND.md: sub hits, scan sweeps, digital ticks,
# one heavy impact per beat; no cartoon tocks/clinks). 48k stereo, length = cut duration.
import numpy as np, wave
SR=48000; DUR=2606/30; n=int(SR*DUR)
L=np.zeros(n); R=np.zeros(n); rng=np.random.default_rng(11)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0.0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; freq=55+60*np.exp(-t*28)
    body=np.sin(2*np.pi*np.cumsum(freq)/SR)*np.exp(-t*(14/weight))
    click=lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5
    y=body+click; return y/np.max(np.abs(y))
def sub(weight=1.0):      # deep sub hit (thick blood)
    m=int(SR*0.5); t=np.arange(m)/SR; freq=40+28*np.exp(-t*20)
    y=np.sin(2*np.pi*np.cumsum(freq)/SR)*np.exp(-t*(6/weight)); return y/np.max(np.abs(y))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; freq=48+90*np.exp(-t*30)
    body=np.sin(2*np.pi*np.cumsum(freq)/SR)*np.exp(-t*7); crack=lp(rng.standard_normal(m),0.6)*np.exp(-t*45)
    y=body+0.55*crack; return y/np.max(np.abs(y))
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220); return y/np.max(np.abs(y))
def digi(up=True):        # short digital confirm blip
    m=int(SR*0.12); t=np.arange(m)/SR; f=(1200 if up else 1800)+( 900 if up else -700)*t/0.12
    y=np.sign(np.sin(2*np.pi*f*t))*0.3*np.exp(-t*26)+np.sin(2*np.pi*f*t)*np.exp(-t*22); return y/np.max(np.abs(y))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0.0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05)
    return y*env/np.max(np.abs(y*env))
def riser(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*(t/d)**2; y=np.zeros(m); acc=0.0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    env=(t/d)**1.5; return y*env/np.max(np.abs(y*env))
def paper(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); hp=nz-lp(nz,0.15)
    env=np.sin(np.pi*np.clip(t/d,0,1))**1.5; return hp*env/np.max(np.abs(hp*env))
dB=lambda x:10**(x/20)
HIT=lambda t,w=1.3,g=-16: place(thud(w),t,gain=dB(g))
SUB=lambda t,g=-14: place(sub(1.2),t,gain=dB(g))
IMP=lambda t,g=-13: place(impact(),t,gain=dB(g))
TK=lambda t,g=-28: place(tick(),t,gain=dB(g))
DG=lambda t,up=True,g=-24: place(digi(up),t,gain=dB(g))
SW=lambda t,d=0.34,g=-28: place(scan(d),t,gain=dB(g))
RS=lambda t,d=1.0,g=-26: place(riser(d),t,gain=dB(g))
PP=lambda t,d=0.4,g=-26: place(paper(d),t,gain=dB(g))

# S1 pedestal
TK(1.06,-30); HIT(1.80,1.5,-16)
for t in (2.88,3.60,4.46): TK(t,-30)
IMP(6.02,-14); TK(8.84,-26)
# S2 stepper
for t in (10.80,12.16): TK(t,-26)
DG(13.10,True,-24)
# S3 lens + S4 graph
SW(14.20,0.4,-27); RS(16.14,1.2,-28); HIT(18.98,1.3,-16)
SW(19.34,0.5,-28); SUB(21.74,-13); TK(25.16,-28)
for t in (27.02,27.66,27.98,28.52,29.00): TK(t,-32)
# S5 gauge
TK(32.42,-28); DG(39.52,True,-22)
# S6 lab
PP(41.40,0.45,-24)
for t in (43.96,44.72,45.40): TK(t,-30)
TK(48.26,-28); IMP(50.78,-12)
# S7 washout
HIT(55.66,1.2,-17); TK(56.32,-26)
for t in (59.14,59.68,60.12): DG(t,False,-26)
# S8 stack
for t in (63.50,64.54,65.52): HIT(t,0.9,-19)
TK(66.64,-26)
# S9 verdict
HIT(67.66,1.1,-17); DG(68.20,True,-24); TK(69.82,-24); RS(71.02,2.0,-28); IMP(73.70,-12)
# S10 CTA
HIT(74.98,1.2,-17); IMP(75.46,-14)

out=np.stack([L,R],1); pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk+1e-9))
w=wave.open('sfx_eq.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out/max(1,pk),-1,1)*32767*min(1,pk)).astype(np.int16).tobytes()); w.close()
print('wrote sfx_eq.wav', DUR)
