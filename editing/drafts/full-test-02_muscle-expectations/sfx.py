# Clinical SFX bed for full test 02 (times are in the edited-cut timeline). Writes sfx.wav (48 kHz stereo).
import numpy as np, wave, sys
SR=48000; DUR=3440/30; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(11)
def place(sig,t,pan=0.0,gain=1.0):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def norm(y): return y/np.max(np.abs(y))
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; fr=55+60*np.exp(-t*28)
    return norm(np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*(14/weight))+lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5)
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR
    return norm(np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; fr=48+90*np.exp(-t*30)
    return norm(np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t*7)+0.55*lp(rng.standard_normal(m),0.6)*np.exp(-t*45))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t)
    return norm(y*np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05))
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2; y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    return norm(y*np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2)
def riser(d):   # needle sweep: rising tone + noise
    m=int(SR*d); t=np.arange(m)/SR; fr=180+900*(t/d)**2
    return norm((np.sin(2*np.pi*np.cumsum(fr)/SR)*0.6+0.3*lp(rng.standard_normal(m),0.3))*np.minimum(1,t/0.05)*np.minimum(1,(d-t)/0.03))
def glitch():
    m=int(SR*0.18); t=np.arange(m)/SR; y=np.sign(np.sin(2*np.pi*(120+80*rng.standard_normal())*t))*0.5+rng.standard_normal(m)*0.5
    y*= (np.floor(t*90)%2)
    return norm(y*np.exp(-t*12))
dB=lambda x:10**(x/20)
hit=lambda t,g=-17: place(thud(1.4),t,gain=dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,gain=dB(g))
tk=lambda t,g=-28: place(tick(),t,gain=dB(g))
imp=lambda t,g=-14: place(impact(),t,gain=dB(g))
wh=lambda t,d=0.35,g=-26: place(whoosh(d),t-d*0.7,gain=dB(g))
# side rail
tk(2.30,-30); wh(5.75,0.3,-30)
for t in (7.54,9.18,11.06): tk(t,-30)
# bar chart
hit(12.0); sw(14.12,0.45); tk(14.58); sw(19.24,0.5); tk(19.74); sw(23.64,0.4); tk(24.04)
# split + stack + 5-year slam
wh(26.30,0.4);
for t in (30.90,31.50,32.58,33.56): place(thud(0.7),t,gain=dB(-24))
imp(35.90,-15)
# bell
hit(41.3); sw(41.4,1.0,-31); tk(41.96); tk(45.08); tk(48.14); sw(51.54,0.4,-31); tk(53.44); imp(56.38,-15)
# gantt / spectrum
wh(57.6,0.3,-30); sw(59.48,1.8,-32); tk(63.04,-26); tk(64.86,-30)
# scope
place(scan(0.6),66.40,gain=dB(-27)); imp(69.44,-17)
# risk
wh(70.35,0.3,-30); tk(71.28,-30); place(riser(0.4),73.92,gain=dB(-27)); tk(75.02,-28)
# expectation
hit(82.2); place(riser(0.35),84.70,gain=dB(-28)); tk(86.62); tk(86.84,-26)
# pip + speedometer
wh(87.05,0.45,-25); tk(88.20); tk(90.20); place(riser(0.9),93.40,gain=dB(-26)); imp(94.66,-15)
# battery
wh(95.5,0.3,-30); place(riser(0.6),100.16,gain=dB(-29)); tk(100.64,-27)
# lifespan
hit(101.8); place(thud(1.6),103.22,gain=dB(-16)); tk(105.18,-27); place(glitch(),106.92,gain=dB(-20))
# CTA
hit(108.8,-19); place(thud(1.2),111.20,gain=dB(-17))
out=np.stack([L,R],1); print('sfx peak dBFS',20*np.log10(np.max(np.abs(out))))
w=wave.open(sys.argv[1] if len(sys.argv)>1 else 'sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
