import numpy as np, wave, json
SR=48000
rng=np.random.default_rng(7)
exec(open('synth.py').read())
TR=json.load(open('trim.json')); KEEP=TR['keep']
DUR=sum(b-a for a,b in KEEP); n=int(SR*DUR)+SR; L=np.zeros(n); R=np.zeros(n)
def o2n(t):
    acc=0
    for a,b in KEEP:
        if a<=t<b: return acc+t-a
        acc+=b-a
    return None
def place(sig,t,gain=1.0,pan=0.0):
    tn=o2n(t)
    if tn is None: print('dropped',t); return
    i=int(tn*SR); s=sig[:max(0,n-i)]*gain
    L[i:i+len(s)]+=s*(1-max(0,pan)); R[i:i+len(s)]+=s*(1+min(0,pan))
hit=lambda t,w=1.4,g=-17: place(thud(w),t,dB(g))
sw=lambda t,d=0.32,g=-29: place(scan(d),t,dB(g))
tk=lambda t,g=-28: place(tick(),t,dB(g))
imp=lambda t: place(impact(),t,dB(-14))
wh=lambda t,d=0.36,g=-27: place(whoosh(d),max(0,t-d*0.7),dB(g))
sw(0.90,0.28,-31); tk(2.26); tk(2.70,-31)
sw(4.40,0.28,-31); tk(4.89,-30); tk(5.65,-30); hit(7.70,1.0,-21); sw(8.32,0.8,-31); tk(8.70); hit(13.25,1.0,-20); tk(14.72,-24); hit(14.90,1.2,-18); tk(16.02)
sw(17.30); tk(18.44,-30); tk(19.30,-30)
hit(21.0,1.4,-19); sw(22.42,0.9,-31); tk(23.10); sw(25.46,0.5,-32); tk(27.20)
hit(29.66,1.6,-17); hit(30.12,1.6,-17); hit(30.84,1.8,-16); tk(31.70)
wh(32.55); hit(34.30,1.2,-18); sw(35.06,0.6,-31); sw(37.40,0.9,-28); tk(42.64); tk(43.10,-30); wh(43.80,0.3,-30)
hit(44.62,1.3,-20); tk(46.30); imp(51.94); tk(53.38)
wh(55.36); tk(58.98); tk(59.98); hit(61.92,1.0,-20); tk(63.42); tk(64.84)
wh(65.86,0.3,-30); place(paper(0.35),66.10,dB(-30)); tk(66.70); tk(67.72,-31); tk(68.52); sw(70.96,0.45,-28); tk(73.74)
sw(74.86,0.3,-31); tk(75.58)
hit(76.70,1.2,-19); tk(77.92); tk(78.86); tk(82.70)
wh(83.92,0.3,-28); imp(84.40); tk(85.96)
place(whoosh(0.3),87.98,dB(-27)); tk(88.68); tk(89.86); tk(90.88); hit(92.38,1.2,-19)
hit(94.92,1.3,-19); hit(100.56,1.8,-15)
y=np.stack([L,R],1)[:int(SR*DUR)]
o=wave.open('sfx.wav','wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes()); o.close(); print('ok',DUR)
