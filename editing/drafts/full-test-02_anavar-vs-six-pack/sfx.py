# Clinical SFX bed for the Anavar vs six pack cut (times are in edited-cut seconds)
import numpy as np, wave, sys
SR=48000; DUR=float(sys.argv[1]); OUT=sys.argv[2]; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lpf(x,a):
    y=np.zeros_like(x); acc=0.0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def norm(y): return y/np.max(np.abs(y))
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2
    y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    return norm(y*np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2)
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    return norm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/weight))+lpf(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5)
def tick(fr=2400):
    m=int(SR*0.05); t=np.arange(m)/SR
    return norm(np.sin(2*np.pi*fr*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*fr*1.7*t)*np.exp(-t*220))
def beep(fr=1000,d=0.09):
    m=int(SR*d); t=np.arange(m)/SR; return np.sin(2*np.pi*fr*t)*np.minimum(1,t/0.004)*np.minimum(1,(d-t)/0.01)
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30)
    return norm(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.55*lpf(rng.standard_normal(m),0.6)*np.exp(-t*45))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lpf(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t)
    return norm(y*np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05))
def paper(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); hp=nz-lpf(nz,0.15)
    return norm(hp*np.sin(np.pi*np.clip(t/d,0,1))**1.5)
def click():
    m=int(SR*0.03); t=np.arange(m)/SR; return norm(lpf(rng.standard_normal(m),0.7)*np.exp(-t*300))
dB=lambda x:10**(x/20)
W=whoosh(0.28); TH=thud(1.4); TK=tick(); IM=impact()
hit=lambda t,g=-17: place(TH,t,gain=dB(g))
tk=lambda t,g=-28,p=0: place(TK,t,p,dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
wh=lambda t,d=0.28,g=-27,p=0: place(whoosh(d),max(0,t-d*0.8),p,dB(g))   # whoosh arrives on the landing
imp=lambda t,g=-14: place(IM,t,gain=dB(g))
# hook
hit(0.03,-19)
wh(1.62,p=-0.5); hit(1.62,-21); wh(3.58,p=0.5); hit(3.58,-21)
tk(6.36,-26,-0.4); tk(6.44,-26,0.4)
# agenda
for t in (7.75,8.26,9.46,10.42): tk(t,-30)
# triad
sw(11.0); tk(14.16); tk(14.42)
for t in (16.86,17.70,19.34): tk(t,-25); place(thud(0.8),t,gain=dB(-26))
tk(20.48,-26); hit(21.66,-20)
# lipid card
hit(23.45,-19); wh(26.0,0.4,-28); tk(25.14,-30); sw(27.55,0.22); tk(28.94,-26); sw(30.55,0.22); place(thud(1.0),30.96,gain=dB(-21)); tk(32.28,-26)
tk(35.02,-27)
for t in (36.84,37.37,37.91): place(beep(1000),t,gain=dB(-31))
# monitor tiles
wh(38.74,p=-0.6); tk(39.2,-28); place(click(),40.12,gain=dB(-20)); wh(41.96,p=-0.6); hit(43.76,-21)
# six pack
for i in range(6): tk(47.22+i*0.07,-27,-0.5+i*0.2)
sw(49.26,0.6,-31); hit(51.72,-18); place(paper(0.25),51.60,gain=dB(-29)); sw(53.25,0.22); wh(53.9,0.35,-28)
# fatty liver
hit(55.30,-19); sw(55.96,1.4,-31)
for t in (58.08,59.60,60.86): tk(t,-26)
# hazard / radar
imp(62.98,-15); hit(64.92,-20); wh(65.98,p=-0.6); place(click(),66.02,gain=dB(-20)); sw(67.36,0.3); wh(69.4,0.4,-28)
# agenda return
tk(71.0,-30); tk(71.26,-27)
# PiP scene
wh(77.0,0.45,-25)
for i in range(6): tk(78.54+i*0.12,-31)
tk(80.30,-25); place(TK,82.22,0,dB(-25)); hit(84.40,-20); sw(87.9,0.7,-30); hit(89.54,-19); imp(92.40,-14); wh(93.35,0.4,-26)
# receipts / legal
place(paper(0.3),97.6,gain=dB(-26)); place(paper(0.25),98.64,gain=dB(-28)); place(paper(0.3),100.36,gain=dB(-26)); imp(101.34,-16)
# body tile
wh(102.70,p=-0.6); tk(104.36,-27)
for i in range(6): tk(107.46+i*0.22,-30)
sw(110.40,1.2,-29); hit(112.96,-20); hit(113.56,-20)
# roadmap
sw(116.2,0.9,-30); hit(117.78,-21)
for t in (118.73,119.43,120.19): tk(t,-25)
place(thud(1.6),120.91,gain=dB(-18))
# CTA
hit(122.45,-19)
for i in range(8): tk(125.45+i*0.16,-31)
tk(128.81,-25); place(thud(1.8),130.03,gain=dB(-16))
out=np.stack([L,R],1); print('sfx peak dBFS',20*np.log10(np.max(np.abs(out))))
w=wave.open(OUT,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
