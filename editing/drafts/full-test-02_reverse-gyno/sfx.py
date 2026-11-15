import numpy as np, wave, json, sys
WD=sys.argv[1]; SR=48000; DUR=json.load(open(WD+'trim.json'))['newdur']+0.5; n=int(SR*DUR); L=np.zeros(n); R=np.zeros(n)
WT={int(k):v for k,v in json.load(open(WD+'wt.json')).items()}
def T(i):
    while i not in WT: i+=1
    return WT[i][0]
rng=np.random.default_rng(7)
def place(sig,t,gain=1.0):
    i=int(max(0,t)*SR); s=sig[:max(0,n-i)]*gain; L[i:i+len(s)]+=s; R[i:i+len(s)]+=s
def lpf(x,a):
    y=np.zeros_like(x); acc=0
    for k in range(len(x)): acc+=a*(x[k]-acc); y[k]=acc
    return y
def thud(w=1.0):
    m=int(SR*0.35); t=np.arange(m)/SR; f=55+60*np.exp(-t*28)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*(14/w))+lpf(rng.standard_normal(m),0.25)*np.exp(-t*160)*0.5; return y/np.max(np.abs(y))
def tick():
    m=int(SR*0.05); t=np.arange(m)/SR; y=np.sin(2*np.pi*2400*t)*np.exp(-t*140)+0.4*np.sin(2*np.pi*4100*t)*np.exp(-t*220); return y/np.max(np.abs(y))
def impact():
    m=int(SR*0.6); t=np.arange(m)/SR; f=48+90*np.exp(-t*30)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.55*lpf(rng.standard_normal(m),0.6)*np.exp(-t*45); return y/np.max(np.abs(y))
def scan(d):
    m=int(SR*d); t=np.arange(m)/SR; nz=rng.standard_normal(m); cut=0.05+0.35*(t/d); y=np.zeros(m); acc=0
    for k in range(m): acc+=cut[k]*(nz[k]-acc); y[k]=acc
    y=y-lpf(y,0.08)+0.15*np.sin(2*np.pi*(900+1400*t/d)*t); env=np.minimum(1,t/0.03)*np.minimum(1,(d-t)/0.05); return y*env/np.max(np.abs(y*env))
dB=lambda x:10**(x/20)
hit=lambda t: place(thud(1.4),t,dB(-18)); sw=lambda t,d=0.35: place(scan(d),t-d*0.8,dB(-30))
tk=lambda t,g=-30: place(tick(),t,dB(g)); imp=lambda t: place(impact(),t,dB(-15))
# scene entries: scan sweep into a thud on the landing
for i,off in [(45,-0.25),(91,-0.25),(149,-0.25),(281,-0.25),(359,-0.25),(411,-0.25),(521,-0.25)]: sw(T(i)+off+0.35); hit(T(i)+off+0.35)
for i in (9,129,222,490): tk(T(i),-26)
for i in (13,18,22,25,46,55,62,95,96,97,116,118,131,164,168,173,186,192,206,210,240,245,262,264,266,283,289,297,312,317,335,351,368,453,457,460,549,555,561,568): tk(T(i))
imp(T(71)); imp(T(127)); place(thud(1.0),T(211),dB(-17)); place(thud(1.0),T(406),dB(-17)); place(thud(1.2),T(251),dB(-18))
place(thud(1.2),T(324)+0.4,dB(-19)); tk(T(426)+0.6,-24); imp(T(518)); place(thud(1.2),T(541),dB(-17)); place(thud(1.4),T(579),dB(-17))
out=np.stack([L,R],1); print('sfx peak dBFS',20*np.log10(np.max(np.abs(out))))
w=wave.open(WD+'sfx.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out,-1,1)*32767).astype(np.int16).tobytes()); w.close()
