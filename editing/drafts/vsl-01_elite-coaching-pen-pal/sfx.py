import sys,json,wave,numpy as np
S=sys.argv[1]; sys.argv=['render.py',S,'cues']
src=open(S+'/render.py').read().split("if __name__=='__main__':")[0]; G={'__name__':'sfxmod'}; exec(src,G)
E=json.load(open(S+'/edit.json')); REM=E['remove']; OUT=sum(b-a for a,b in E['keep'])
SR=48000; n=int(SR*(OUT+0.5)); L=np.zeros(n); R=np.zeros(n); rng=np.random.default_rng(7)
def m(t):
    for a,b in REM:
        if a<=t<b: return None
    return t-sum(min(b,t)-a for a,b in REM if a<t)
def place(sig,t,gain,pan=0.0,anchor=0.0):
    t=m(t)
    if t is None: print('dropped',t); return
    i=int((t-anchor)*SR); i=max(0,i); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
def lp(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def thud(w=1.0):
    k=int(SR*0.35); t=np.arange(k)/SR; f=55+60*np.exp(-t*28); body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/w))
    y=body+lp(rng.standard_normal(k),0.25)*np.exp(-t*160)*0.5; return y/np.max(np.abs(y))
def tick():
    k=int(SR*0.05); t=np.arange(k)/SR; y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220); return y/np.max(np.abs(y))
def impact():
    k=int(SR*0.6); t=np.arange(k)/SR; f=48+90*np.exp(-t*30); body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)
    y=body+0.55*lp(rng.standard_normal(k),0.6)*np.exp(-t*45); return y/np.max(np.abs(y))
def scan(d):
    k=int(SR*d); t=np.arange(k)/SR; nz=rng.standard_normal(k); cut=0.05+0.35*(t/d); y=np.zeros(k); acc=0
    for q in range(k): acc+=cut[q]*(nz[q]-acc); y[q]=acc
    y=y-lp(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05); return y*env/np.max(np.abs(y*env))
def whoosh(d):
    k=int(SR*d); t=np.arange(k)/SR; nz=rng.standard_normal(k); cut=0.02+0.25*np.sin(np.pi*np.clip(t/d,0,1))**2; y=np.zeros(k); acc=0
    for q in range(k): acc+=cut[q]*(nz[q]-acc); y[q]=acc
    env=np.sin(np.pi*np.clip(t/d,0,1)**0.7)**2; return y*env/np.max(np.abs(y*env))
dB=lambda x:10**(x/20)
TH=thud(1.4); TK=tick(); IM=impact(); SC2=scan(0.35); WH=whoosh(0.4)
for s in G['SC']:
    L_=s['lay']; t0=s['t0']
    if L_ in ('panel','full'): place(TH,t0,dB(-17))
    elif L_=='lower': place(SC2,t0,dB(-28))
    else: place(WH,t0+0.2,dB(-27),anchor=0.28)
g=G
for t in [g['c_five'],g['c_six']]: place(TK,t,dB(-26))
place(IM,g['c_looks'],dB(-15)); place(IM,g['c_penpal'],dB(-14)); place(IM,g['c_otherway'],dB(-14))
for nm,t in g['HUB'][1:]: place(TK,t,dB(-33))
for nm,t in g['XR']: place(TK,t,dB(-34))
for nm,t,*_ in g['CAL']: place(thud(0.6),t,dB(-27))
for nm,t in g['CH']: place(TK,t,dB(-30))
place(SC2,g['c_comm'],dB(-27)); place(SC2,g['c_everyday'],dB(-27))
place(scan(0.6),g['c_16'],dB(-28)); place(TK,g['c_17'],dB(-27)); place(TK,g['c_20'],dB(-27)); place(thud(1.0),g['c_2y'],dB(-21))
place(thud(1.0),g['c_noidea'],dB(-22))
for nm,t in g['INP']: place(TK,t,dB(-32))
place(thud(1.2),g['c_reach'],dB(-18))
for t in [g['c_70'],g['c_80'],g['c_90']]: place(TK,t,dB(-28))
out=np.stack([L,R],1); print('peak dBFS',20*np.log10(np.max(np.abs(out))))
w=wave.open(S+'/sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
