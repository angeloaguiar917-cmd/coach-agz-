import numpy as np, wave
SR=48000; DUR=52.6; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def nrm(y): return y/np.max(np.abs(y))
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2
    y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    return nrm(y*np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2)
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    return nrm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/weight))+lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5)
def tick(fr=2400):
    m=int(SR*0.05); t=np.arange(m)/SR
    return nrm(np.sin(2*np.pi*fr*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*fr*1.7*t)*np.exp(-t*220))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30)
    return nrm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.55*lp(rng.standard_normal(m),0.6)*np.exp(-t*45))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t)
    return nrm(y*np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05))
def beep(d=0.08,fr=1000):
    m=int(SR*d); t=np.arange(m)/SR; return np.sin(2*np.pi*fr*t)*np.minimum(1,t/0.004)*np.minimum(1,(d-t)/0.004)
dB=lambda x:10**(x/20)
hit=lambda t,g=-17,w=1.4: place(thud(w),t,gain=dB(g))
tk=lambda t,g=-29,fr=2400: place(tick(fr),t,gain=dB(g))
imp=lambda t,g=-14: place(impact(),t,gain=dB(g))
wh=lambda t_end,d=0.35,g=-27: place(whoosh(d),t_end-d*0.75,gain=dB(g))
sw=lambda t,d,g=-31: place(scan(d),t,gain=dB(g))
# 0-11 turnaround widget
tk(5.62,-28); tk(6.10,-27); tk(8.05,-31,3000); tk(8.40,-24,3000); tk(10.66,-26)
# 11-17 scan
tk(11.30,-28); sw(11.8,3.0,-33); 
for c in range(15): tk(14.68+c*0.012,-38,3200)
hit(15.22,-19,1.0); hit(16.66,-21,1.6)
# split + results
wh(18.30,0.42); hit(19.48,-18); imp(20.02,-15); hit(21.40,-19); hit(22.16,-17,1.0)
wh(23.36,0.25,-29); hit(23.40,-19,0.9); tk(24.38,-25); wh(25.08,0.25,-29)
# bloodwork
for t in (25.52,25.88,26.30,26.72,27.06): tk(t,-32)
for t in (27.36,27.62,27.88,28.16,28.44): tk(t,-27,1800)
imp(29.06,-16)
# check-in log
for i in range(12): tk(30.88+i*0.113,-33,2600)
sw(32.6,0.85,-33); hit(33.98,-22,1.0)
for i,mk in enumerate([1,1,0,1,0,0,1,1,0,1,0,1]): tk(34.12+i*0.065,-30 if not mk else -36,1500 if not mk else 2600)
sw(34.5,1.05,-35); hit(35.74,-20,1.6); hit(36.0,-18,1.0)
# comms
hit(37.02,-18); wh(38.98,0.3,-30)
for i in range(7): tk(38.92+i*0.06,-32,2800)
for k in range(0,21,2): tk(42.2+k*0.045,-34,3000)
hit(39.30,-22,0.9); hit(43.40,-19,1.0)
# monitor
wh(44.0,0.38,-27); tk(43.90,-28)
for b in np.arange(44.05,45.5,0.5): place(beep(),b,gain=dB(-36))
place(beep(1.4)*np.linspace(1,0,int(SR*1.4))**0.6,45.54,gain=dB(-33)); hit(45.54,-17,1.8)
hit(47.76,-19,1.0); tk(48.54,-27)
for i,mk in enumerate([1,0,0,0,1,0,0,0,0,1,0,0]): tk(48.64+i*0.07,-31 if not mk else -36,1500 if not mk else 2600)
imp(49.58,-16)
# end card
wh(50.30,0.42); hit(50.40,-18,1.2); tk(51.05,-30); tk(51.2,-30,1500)
out=np.stack([L,R],1); print('sfx peak dBFS',20*np.log10(np.max(np.abs(out))))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
