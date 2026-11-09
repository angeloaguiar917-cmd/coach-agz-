# Clinical SFX bed, synthesised; every event is placed on a graphic landing (raw timeline -> output timeline).
import sys, wave, numpy as np
sys.argv=[sys.argv[0],sys.argv[1],'x']
import render as R
SR=48000; DUR=R.TR['newdur']; n=int(SR*DUR)+SR; L=np.zeros(n); Rr=np.zeros(n)
rng=np.random.default_rng(7)
def o2n(t):
    for a,b in R.TR['remove']:
        if a<=t<b: return None
    return t-sum(min(b,t)-a for a,b in R.TR['remove'] if a<t)
def place(sig,t,pan=0.0,gain=1.0):
    t=o2n(t)
    if t is None or t<0: print('SFX dropped',t); return
    i=int(t*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); Rr[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def thud(weight=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/weight))+lp(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5
    return y/np.max(np.abs(y))
def tick(fr=2400):
    m=int(SR*0.05); t=np.arange(m)/SR
    y=np.sin(2*np.pi*fr*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*fr*1.7*t)*np.exp(-t*220); return y/np.max(np.abs(y))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.55*lp(rng.standard_normal(m),0.6)*np.exp(-t*45); return y/np.max(np.abs(y))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05); return y*env/np.max(np.abs(y*env))
def whoosh(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2; y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    env=np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2; return y*env/np.max(np.abs(y*env))
def sub(d=0.9):
    m=int(SR*d); t=np.arange(m)/SR; y=np.sin(2*np.pi*(38+20*np.exp(-t*8))*t)*np.exp(-t*4)*np.minimum(1,t/0.01); return y/np.max(np.abs(y))
dB=lambda x:10**(x/20)
T=R.T; SC=R.SCENES
hit=lambda t,g=-17: place(thud(1.4),t,gain=dB(g))
tk=lambda t,g=-29,fr=2400: place(tick(fr),t,gain=dB(g))
sw=lambda t,d=0.35,g=-29: place(scan(d),t,gain=dB(g))
imp=lambda t,g=-15: place(impact(),t,gain=dB(g))
wh=lambda t,d=0.4,g=-28: place(whoosh(d),t-d*0.7,gain=dB(g))
# hook: slots tick in, #3 flags
t3=T('three',0.6)
for i in range(3): tk(t3+0.08*i,-32)
place(thud(0.8),T('last',5.8),gain=dB(-22))
# band slots unlock as each compound is named
for w,nr in (('primobolan',12.0),('masteron',32.4),('equipoise',56.8)): tk(T(w,nr),-27,3400)
# 01 primo card
wh(SC[0][0],0.35); hit(SC[0][0]+0.1,-21); tk(T('aromatizer',13.4),-27,3200)
for tt in (T('dht',17.3),T("doesn't",17.9),T('lower',19.3)): tk(tt-0.05,-28)
# crash graph
hit(SC[1][0]); sw(SC[1][0]+0.2,0.5,-31); imp(T('ais',23.6),-17); tk(T('without',23.9),-27,1800)
for w,nr in (('joints',25.9),('libido',26.5),('mood',27.2)): tk(T(w,nr),-28,1600)
place(thud(1.0),T('garbage',28.4),gain=dB(-19))
# masteron title
place(sub(),T('masteron',32.0),gain=dB(-17)); tk(T('secondarily',29.4),-28); place(scan(0.18),T('builder',33.8),gain=dB(-30))
# pip handoff + mechanism
wh(SC[3][0]+0.3,0.5,-26); tk(T('anti-estrogenic',38.7),-27); hit(T('androgen',40.6)+0.6,-23); place(thud(0.7),T('oppose',42.1),gain=dB(-21))
tk(T('tissue',44.5),-29); tk(T('serm',45.8),-26,3000); sw(T('blocking',48.9)-0.1,0.3); tk(T('not',53.8),-27); wh(SC[3][1]+0.25,0.45,-27)
# EQ verdict
imp(T('equipoise',56.7),-16); place(thud(1.0),T('beginners',59.4),gain=dB(-20))
# scatter cutaway
hit(SC[5][0],-19); sw(SC[5][0],0.3,-28)
rngp=np.random.default_rng(11)
for i in range(0,36,4): tk(R.lerp(T('ability',64.4),T('place',69.0)-0.4,i/36),-34,2800)
imp(T('place',69.0),-18)
# ester scan monitor
sw(SC[6][0],0.6,-27); place(thud(0.9),SC[6][0]+2.4,gain=dB(-24)); sw(T('releasing',76.5),1.6,-32); imp(T('last',79.0),-19)
# fix stack + calendar
hit(SC[7][0],-21)
for w,nr in (('ancillaries',83.8),('supplements',84.8),('compounds',86.0)): place(thud(0.5),T(w,nr),gain=dB(-24))
for k in range(12): tk(R.lerp(T('next',87.0),T('8',87.3),k/7) if k<8 else R.lerp(T('8',87.3)+0.05,T('12',87.6)+0.15,(k-8)/3),-33,2000+k*80)
# hct gauge
sw(T('elevated',92.1)-0.05,0.65,-28); imp(T('hematocrit',92.6)+0.05,-18)
# lab doc
wh(SC[9][0]+0.4,0.45,-25); place(thud(0.6),SC[9][0]+0.4,gain=dB(-22))
for k,v,u,key,near in R.LAB: tk(T(key,near),-30,2600)
sw(T('cross-reference',102.6),0.35); imp(T('matters',104.3),-16)
# stepper + cta
for w,nr in (('measure',105.7),('understand',106.4),('informed',107.6)): place(thud(0.6),T(w,nr),gain=dB(-22))
hit(SC[11][0],-21); tk(T('compounds',111.8),-28); tk(T('read',113.3),-28); place(thud(1.2),T('comment',114.8),gain=dB(-16))
out=np.stack([L,Rr],1)[:int(SR*DUR)]; pk=np.max(np.abs(out)); print('sfx peak dBFS',round(20*np.log10(pk),1))
w=wave.open(sys.argv[1]+'/work/sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
