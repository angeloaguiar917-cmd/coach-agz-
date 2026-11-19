import numpy as np, wave
SR=48000; DUR=24.4333; n=int(SR*DUR)+SR; L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m)
    cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2; y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    env=np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2; return y*env/np.max(np.abs(y*env))
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/weight)); click=lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5
    y=body+click; return y/np.max(np.abs(y))
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220); return y/np.max(np.abs(y))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30); body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)
    crack=lp(rng.standard_normal(m),0.6)*np.exp(-t*45); y=body+0.55*crack; return y/np.max(np.abs(y))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05)
    return y*env/np.max(np.abs(y*env))
def shutter():  # mechanical double click
    m=int(SR*0.12); y=np.zeros(m)
    for off,g in [(0,1.0),(int(SR*0.055),0.7)]:
        k=np.arange(m-off)/SR; y[off:]+=g*lp(rng.standard_normal(m-off),0.7)*np.exp(-k*260)
    return y/np.max(np.abs(y))
dB=lambda x:10**(x/20)
hit=lambda t,g=-17,w=1.4: place(thud(w),t,gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
wh=lambda t_land,d=0.3,g=-27: place(whoosh(d),t_land-d*0.7,gain=dB(g))
# credential
wh(2.20,0.25); hit(2.24,-20,1.0); tk(2.72,-27)
# inbox
for t in (3.36,3.58,3.88,4.02,4.28,4.56,4.80): tk(t,-35)
sw(3.58,0.7,-31); sw(4.92,0.6,-30)
# bloodwork dials
hit(5.68,-21,1.0)
for t in (6.06,6.48,6.76): sw(t,0.45,-33)
for t in (7.50,7.57,7.64): tk(t,-30)
# stack: vials land on the words, Tren heaviest
hit(8.06,-22,1.0); hit(8.76,-19,1.0); hit(9.22,-19,1.1); hit(9.98,-16,1.6)
# lethal (split in)
wh(10.80,0.4,-26); hit(11.42,-18); sw(11.62,0.8,-29); tk(11.70,-27); place(impact(),12.54,gain=dB(-14))
# camera
tk(13.40,-30); tk(13.90,-31); tk(13.98,-31); place(shutter(),15.22,gain=dB(-16)); wh(15.52,0.3,-28)
# compare
wh(16.00,0.4,-26); sw(16.22,0.5,-30); tk(16.40,-30); tk(17.14,-27)
wh(18.92,0.3,-27); wh(20.14,0.3,-27); tk(20.46,-27); sw(20.62,0.6,-31); hit(21.17,-19,1.2); sw(21.85,0.55,-30)
# exit + reaction
wh(22.86,0.36,-28); place(impact(),23.48,gain=dB(-15)); hit(23.96,-19,1.2)
out=np.stack([L,R],1)[:int(SR*DUR)]; pk=np.max(np.abs(out)); print('sfx peak dBFS',20*np.log10(pk))
w=wave.open('sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
