# Clinical SFX bed for Reel 02 (output timeline). writes work/sfx.wav
import numpy as np, wave, math, sys
S=sys.argv[1]; SR=48000; DUR=94.634; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def place(sig,t,gain=1.0,pan=0.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def norm(y): return y/np.max(np.abs(y))
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2
    y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    return norm(y*np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2)
def thud(w=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    return norm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/w))+lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5)
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    return norm(np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220))
def beep(fr=1000,d=0.07):
    m=int(SR*d); t=np.arange(m)/SR; return np.sin(2*np.pi*fr*t)*np.minimum(1,t/0.004)*np.minimum(1,(d-t)/0.01)
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30)
    return norm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.55*lp(rng.standard_normal(m),0.6)*np.exp(-t*45))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t)
    return norm(y*np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05))
dB=lambda x:10**(x/20)
hit=lambda t: place(thud(1.4),t,dB(-17))
sw=lambda t,d=0.32: place(scan(d),t,dB(-29))
tk=lambda t,g=-28: place(tick(),t,dB(g))
wh=lambda t,d=0.35,g=-27: place(whoosh(d),t-d*0.7,dB(g))
imp=lambda t,g=-14: place(impact(),t,dB(g))
# rewind
wh(4.92,0.3); 
for k in range(6): tk(4.80+k*0.05,-36)
tk(5.10,-27)
# heart panel + ECG beeps on each R peak
hit(8.64)
def ecg_phase(t):
    r0,r1,a,b=1.15,2.5,9.62,10.42
    if t<a: return r0*t
    if t<b: return r0*a+r0*(t-a)+(r1-r0)*(t-a)**2/(2*(b-a))
    return r0*a+(r0+r1)/2*(b-a)+r1*(t-b)
tt=8.75; last=None
while tt<15.0:
    k=math.floor(ecg_phase(tt)-0.30)
    if last is not None and k!=last: place(beep(1000 if tt<10.2 else 1180),tt,dB(-33))
    last=k; tt+=0.002
tk(9.98); sw(10.96,0.5); imp(12.16,-20); sw(13.20,0.5); tk(14.54,-25)
# dial
wh(15.30); sw(17.62,1.0); tk(19.54); tk(23.80,-25)
# scale + chart
wh(25.74,0.3,-29)
for k in range(10): tk(26.72+k*0.06,-37)
tk(27.40,-25); sw(29.10,1.2); tk(30.36)
# mirror / bloodwork split
hit(31.00); sw(31.00,0.3); tk(33.56); sw(34.36,0.4); tk(35.96); tk(37.80); tk(38.25,-30); wh(39.55,0.3,-26); place(thud(1.0),39.60,dB(-20))
# receipt
wh(41.70,0.42,-27)
for r in (41.80,43.00,45.66,46.08):
    for k in range(5): tk(r+k*0.035,-34)
place(thud(1.0),47.12,dB(-18))
# lifespan + false choice
hit(48.78); tk(49.40); tk(50.98,-25); sw(52.22,0.6); imp(54.16)
# disclaimer switch
wh(56.52,0.3,-28); place(thud(0.9),58.70,dB(-21)); tk(61.20); wh(62.62,0.22,-27)
# checklist
wh(64.66,0.3,-28)
for t_ in (65.10,65.92,67.02,68.16): tk(t_,-30)
place(thud(1.0),69.50,dB(-20))
# silent damage
hit(70.80); sw(71.0,1.0); imp(74.32,-17); tk(75.38)
# roadmap
hit(77.80); sw(77.85,0.4)
for t_ in (79.14,81.76,83.00,85.46): tk(t_,-27)
sw(83.0,0.6)
# lab grid
wh(86.94,0.3,-28); sw(89.40,1.4); imp(91.36,-17)
# end card
place(thud(1.2),93.22,dB(-18)); tk(93.25,-30)
out=np.stack([L,R],1); print('sfx peak dBFS',20*np.log10(np.max(np.abs(out))))
w=wave.open(S+'/work/sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
