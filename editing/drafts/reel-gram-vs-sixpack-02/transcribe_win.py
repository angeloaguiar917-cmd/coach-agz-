# Windowed transcription: 24 s windows with 4 s overlap, words kept from each window's core; avoids long-pass truncation.
import json,sys,wave,numpy as np
from faster_whisper import WhisperModel
src,out=sys.argv[1],sys.argv[2]; model=sys.argv[3] if len(sys.argv)>3 else 'medium.en'
VOC=sys.argv[4] if len(sys.argv)>4 else ''
m=WhisperModel(model,device="cpu",compute_type="int8")
wv=wave.open(src); sr=wv.getframerate(); a=np.frombuffer(wv.readframes(wv.getnframes()),np.int16).astype(np.float32)/32768
dur=len(a)/sr; WIN,OV=24.0,4.0; words=[]; s=0.0
while s<dur:
    e=min(dur,s+WIN); core0=s if s==0 else s+OV/2; core1=e if e>=dur else e-OV/2
    r,_=m.transcribe(a[int(s*sr):int(e*sr)],word_timestamps=True,beam_size=5,temperature=0,condition_on_previous_text=False,initial_prompt="Um, uh. "+VOC)
    for seg in r:
        for w in seg.words:
            t=w.start+s
            if core0<=t<core1: words.append({"w":w.word.strip(),"s":round(t,3),"e":round(w.end+s,3)})
    if e>=dur: break
    s=e-OV
json.dump(words,open(out,'w')); print(len(words),'words'); print(' '.join(w['w'] for w in words))
