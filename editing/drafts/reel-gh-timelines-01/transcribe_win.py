# Windowed transcription v2: 14 s windows / 3 s overlap, then a gap guard: any >0.9 s hole between words that
# contains speech energy is re-transcribed on its own (with context) and the words merged in. Prints gaps left.
import json,sys,wave,numpy as np
from faster_whisper import WhisperModel
src,out=sys.argv[1],sys.argv[2]; model=sys.argv[3] if len(sys.argv)>3 else 'medium.en'; VOC=sys.argv[4] if len(sys.argv)>4 else ''
m=WhisperModel(model,device="cpu",compute_type="int8")
wv=wave.open(src); sr=wv.getframerate(); a=np.frombuffer(wv.readframes(wv.getnframes()),np.int16).astype(np.float32)/32768
dur=len(a)/sr
def tx(s,e):
    r,_=m.transcribe(a[int(s*sr):int(e*sr)],word_timestamps=True,beam_size=5,temperature=0,condition_on_previous_text=False,
                     vad_filter=False,no_speech_threshold=None,initial_prompt="Um, uh. "+VOC)
    return [{"w":w.word.strip(),"s":round(w.start+s,3),"e":round(w.end+s,3)} for seg in r for w in seg.words]
WIN,OV=14.0,3.0; words=[]; s=0.0
while s<dur:
    e=min(dur,s+WIN); c0=s if s==0 else s+OV/2; c1=e if e>=dur else e-OV/2
    words+=[w for w in tx(s,e) if c0<=w['s']<c1]
    if e>=dur: break
    s=e-OV
def energy(t0,t1):
    seg=a[int(t0*sr):int(t1*sr)]; h=int(0.05*sr)
    if len(seg)<h: return 0
    r=[np.sqrt(np.mean(seg[i:i+h]**2)) for i in range(0,len(seg)-h,h)]; return sum(1 for v in r if 20*np.log10(v+1e-9)>-40)*0.05
for it in range(3):
    words.sort(key=lambda w:w['s']); fixed=False
    gaps=[(words[i]['e'],words[i+1]['s']) for i in range(len(words)-1) if words[i+1]['s']-words[i]['e']>0.9]
    if words and words[0]['s']>0.9: gaps.insert(0,(0.0,words[0]['s']))
    for g0,g1 in gaps:
        if energy(g0,g1)<0.4: continue
        new=[w for w in tx(max(0,g0-1.5),min(dur,g1+1.5)) if g0-0.05<=w['s']<g1-0.02]
        if new: words+=new; fixed=True
    if not fixed: break
words.sort(key=lambda w:w['s'])
left=[(round(words[i]['e'],2),round(words[i+1]['s'],2)) for i in range(len(words)-1) if words[i+1]['s']-words[i]['e']>0.9 and energy(words[i]['e'],words[i+1]['s'])>=0.4]
json.dump(words,open(out,'w')); print(len(words),'words; speech gaps left:',left); print(' '.join(w['w'] for w in words))
