# synthesised clinical SFX (original), timed to the graphic landings in render.py
import numpy as np, wave, json, sys
S=sys.argv[1]; WK=S+'/work/'
W_=json.load(open(WK+'words_final.json')); T=lambda i: W_[i]['s']
SR=48000; DUR=json.load(open(WK+'trim.json'))['dur']; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
rng=np.random.default_rng(7)
EVENTS=[]
def place(sig,t,gain=1.0,name=''):
    i=int(t*SR); s=sig[:max(0,n-i)]*gain; L[i:i+len(s)]+=s; R[i:i+len(s)]+=s; EVENTS.append((round(t,3),name))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2
    y=np.zeros(m); acc=0
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
def beat():   # low double heartbeat thump
    m=int(SR*0.7); t=np.arange(m)/SR; y=np.zeros(m)
    for off,g in [(0,1.0),(0.22,0.7)]:
        tt=np.clip(t-off,0,None); y+=g*np.sin(2*np.pi*(45+25*np.exp(-tt*30))*tt)*np.exp(-tt*16)*(t>=off)
    return y/np.max(np.abs(y))
dB=lambda x:10**(x/20)
hit=lambda t,g=-17: place(thud(1.4),t,dB(g),'hit')
sw=lambda t,d=0.32,g=-29: place(scan(d),t,dB(g),'scan')
tk=lambda t,g=-28: place(tick(),t,dB(g),'tick')
imp=lambda t: place(impact(),t,dB(-14),'impact')
def morph(t,d=0.45): place(whoosh(d),t,dB(-27),'whoosh')
# hook punch-in on "blood pressure"
place(thud(0.8),T(6),dB(-25),'punch')
# 0:06 split: standard panel, EKG, verdict
morph(T(22)+0.12); [tk(T(28)+k*0.16,-32) for k in range(4)]; sw(T(37),1.0,-31); tk(T(39)); tk(T(47),-30); imp(T(50)+0.10)
# 0:13 slots + stepper
morph(T(51)-0.12,0.35); hit(T(54)+0.20,-19); hit(T(55)+0.20,-19); [tk(T(i),-30) for i in (72,77,82)]
# 0:20 lipids
morph(T(83)); place(thud(1.0),T(92)+0.08,dB(-18),'hdl'); tk(T(99)); tk(T(102)); sw(T(105),1.3,-33)
# 0:31 ezetimibe
morph(T(116)-0.1); sw(T(119),0.35,-27); hit(T(119)+0.35,-20); place(thud(1.0),T(123)+0.05,dB(-19),'block'); tk(T(143)); tk(T(145)); tk(T(147)); tk(T(151),-26)
# 0:46 BP
morph(T(153)); sw(T(163),0.5,-31); tk(T(176))
# 0:56 telmisartan reveal + mechanism
hit(T(190)-0.1+0.22,-19); imp(T(198)); morph(T(199)); place(thud(1.2),T(200)+0.22,dB(-19),'plug'); tk(T(201)+0.7,-26); tk(T(206)); sw(T(212),0.8,-32); tk(T(216))
# 1:06 LV regression
hit(T(226)+0.17,-19); sw(T(232),1.2,-32); tk(T(236)); imp(T(239)+0.10)
# 1:13 beyond BP
morph(T(240)+0.2); sw(T(249),0.8,-33); [tk(T(257)+k*0.3,-31) for k in range(3)]; tk(T(264))
# 1:22 comparison table
morph(T(269)); sw(T(273),0.35,-30); [tk(T(i),-31) for i in (277,278,282,285,286)]
# 1:30 calm: heartbeat, clock, week
morph(T(287)-0.3,0.4); place(beat(),T(310),dB(-20),'beat'); hit(T(332)+0.12,-21); tk(T(334),-27); [tk(T(335)+k*0.07,-36) for k in range(7)]
# 1:45 CTA
morph(T(353)-0.25); [tk(T(i),-29) for i in (364,365,369)]; place(thud(1.2),T(376),dB(-17),'comment')
out=np.stack([L,R],1); print('sfx peak dBFS',20*np.log10(np.max(np.abs(out))),'events',len(EVENTS))
json.dump(EVENTS,open(WK+'sfx_events.json','w'))
w=wave.open(WK+'sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
