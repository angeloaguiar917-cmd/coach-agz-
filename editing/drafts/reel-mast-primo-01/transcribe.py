import json,sys,wave,numpy as np
from faster_whisper import WhisperModel
src,out,mode=sys.argv[1],sys.argv[2],sys.argv[3]
m=WhisperModel(sys.argv[4] if len(sys.argv)>4 else "small.en",device="cpu",compute_type="int8")
wv=wave.open(src);a=np.frombuffer(wv.readframes(wv.getnframes()),np.int16).astype(np.float32)/32768
VOC="Coach AGZ. Masteron, Primobolan, Primo, drostanolone, methenolone, aromatase, aromatization, estrogen receptor, E1, estrone, Testosterone, trenbolone, tren, Masteron, Primobolan, EQ, Equipoise, Anavar, Deca, nandrolone, HCG, estradiol, E2, aromatase inhibitor, SHBG, DHT, androgen receptor, hematocrit, mg, milligrams, cycle, TRT, bloodwork."
prompt=VOC if mode=='clean' else "Um, uh, so, like, I- I mean, you know, uh, the the... "+VOC
segs,_=m.transcribe(a,word_timestamps=True,beam_size=5,initial_prompt=prompt,condition_on_previous_text=False,vad_filter=False,suppress_tokens=[] if mode!='clean' else [-1])
out_w=[]
for s in segs:
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}")
    for w in s.words: out_w.append({"w":w.word.strip(),"s":round(w.start,3),"e":round(w.end,3)})
json.dump(out_w,open(out,'w'))
