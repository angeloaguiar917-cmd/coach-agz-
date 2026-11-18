import numpy as np, wave
SR=48000; DUR=84.1334; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n); rng=np.random.default_rng(7)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/weight))+lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5
    return y/np.max(np.abs(y))
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220); return y/np.max(np.abs(y))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.55*lp(rng.standard_normal(m),0.6)*np.exp(-t*45); return y/np.max(np.abs(y))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05)
    return y*env/np.max(np.abs(y*env))
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2
    y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    env=np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2; return y*env/np.max(np.abs(y*env))
dB=lambda x:10**(x/20)
hit=lambda t,g=-17: place(thud(1.4),t,gain=dB(g))
sw=lambda t,d=0.32: place(scan(d),t,gain=dB(-29))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t,g=-15: place(impact(),t,gain=dB(g))
wh=lambda t_land,d=0.34,g=-27: place(whoosh(d),max(0,t_land-d*0.7),gain=dB(g))
# B myth cards
hit(5.10,-20); sw(5.3,0.8); imp(6.24,-17); hit(6.86,-20); sw(7.0,1.2); imp(8.42,-17)
# C bubble iris + chain
wh(9.40); for_t=[9.16,10.20,11.34,12.04]
for t in for_t: tk(t,-27)
place(thud(0.8),10.72,gain=dB(-20)); tk(13.50,-30); wh(16.80,0.3,-29)
# D chart
hit(16.80,-21); [tk(17.0+i*0.12,-33) for i in range(4)]; sw(19.48,0.6); imp(22.18,-16)
# E side split
wh(23.10); hit(25.02,-22); hit(25.62,-22); tk(27.54,-25); sw(28.8,0.7); place(thud(1.2),33.02,gain=dB(-17)); tk(33.86,-27); sw(35.34,0.5)
wh(36.80,0.3,-29)
# G RAAS
hit(37.25,-20); [tk(t,-29) for t in (38.94,39.40,40.14)]; tk(40.84,-26); sw(41.6,0.5); place(thud(1.0),45.0,gain=dB(-19)); tk(46.02,-25)
# H cascade
wh(46.84); [place(thud(0.7+0.2*i),t,gain=dB(-22+i)) for i,t in enumerate((46.78,47.80,49.34))]; imp(50.90,-14); tk(52.02,-27); wh(53.0,0.3,-29)
# I THE FIX
sw(52.82,0.35); imp(53.32,-13)
# J/K clock + verdict
hit(54.35,-21); [tk(t,-28) for t in (56.06,57.54,58.30,59.96,61.28)]; sw(61.7,0.4)
place(thud(1.0),62.28,gain=dB(-19)); tk(63.58,-25); tk(65.22,-24); tk(66.50,-24)
# L window + dose
wh(67.70); tk(67.62,-27); tk(69.08,-29); [tk(70.52+i*0.3,-31) for i in range(4)]; tk(71.46,-26)
# M CTA
hit(73.45,-21); place(thud(0.8),74.64,gain=dB(-21)); tk(75.38,-27); tk(77.12,-28); imp(80.40,-14); tk(81.54,-28)
out=np.stack([L,R],1); print('peak dBFS',20*np.log10(np.max(np.abs(out))))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
