import json,sys
from faster_whisper import WhisperModel
m=WhisperModel("small.en",device="cpu",compute_type="int8")
import numpy as np,wave
wv=wave.open(sys.argv[1]);a=np.frombuffer(wv.readframes(wv.getnframes()),np.int16).astype(np.float32)/32768
segs,_=m.transcribe(a,word_timestamps=True,beam_size=5,vad_filter=False)
out=[]
for s in segs:
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}")
    for w in s.words: out.append({"w":w.word.strip(),"s":round(w.start,3),"e":round(w.end,3)})
json.dump(out,open(sys.argv[2],'w'),indent=0)
