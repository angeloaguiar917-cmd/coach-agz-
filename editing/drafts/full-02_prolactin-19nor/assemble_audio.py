import numpy as np, wave, json
TR=json.load(open('trim.json')); KEEP=TR['keep']
w=wave.open('audio48.wav'); SR=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)
xf=int(SR*0.008); out=[]
for k,(a,b) in enumerate(KEEP):
    seg=x[int(round(a*SR)):int(round(b*SR))].copy()
    if k>0: seg[:xf]*=np.linspace(0,1,xf)[:,None]
    if k<len(KEEP)-1: seg[-xf:]*=np.linspace(1,0,xf)[:,None]
    out.append(seg)
y=np.concatenate(out)
o=wave.open('speech_cut.wav','wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes()); o.close()
print(len(y)/SR)
