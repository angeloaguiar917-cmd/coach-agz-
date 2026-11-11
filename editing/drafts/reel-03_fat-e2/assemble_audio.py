import wave,numpy as np,json,sys
S=sys.argv[1]; K=json.load(open(S+'/work/trim.json'))['keep']
w=wave.open(S+'/work/src48.wav'); SR=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(float)
xf=int(0.008*SR); out=np.zeros((0,2))
for a0,b0 in K:
    seg=a[int(round(a0*SR)):int(round(b0*SR))].copy()
    if len(out):
        r=np.linspace(0,1,xf)[:,None]; seg[:xf]=seg[:xf]*r+out[-xf:]*(1-r)*0  # fade in
        out[-xf:]*= (1-r)
        out[-xf:]+=seg[:xf]; seg=seg[xf:]
    out=np.vstack([out,seg])
w2=wave.open(S+'/work/voice.wav','wb'); w2.setnchannels(2); w2.setsampwidth(2); w2.setframerate(SR); w2.writeframes(np.clip(out,-32768,32767).astype(np.int16).tobytes()); w2.close()
print('dur',len(out)/SR)
