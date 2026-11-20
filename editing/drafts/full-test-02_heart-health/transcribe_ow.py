import sys, json, whisper
wav,out,size=sys.argv[1],sys.argv[2],sys.argv[3]
m=whisper.load_model(size)
r=m.transcribe(wav,language="en",word_timestamps=True,condition_on_previous_text=False,
  initial_prompt=sys.argv[4] if len(sys.argv)>4 else "Coach AGZ on heart health: hematocrit, blood pressure, LDL, HDL, ApoB, left ventricular hypertrophy, echocardiogram, cardio, Tren, testosterone, TRT, cycle. Um, uh, so, like.")
W=[{"w":w["word"],"s":round(w["start"],3),"e":round(w["end"],3),"p":round(w.get("probability",1),3)} for s in r["segments"] for w in s["words"]]
json.dump({"segments":[{"start":s["start"],"end":s["end"],"text":s["text"]} for s in r["segments"]],"words":W},open(out,"w"),indent=0)
print("done",len(W))
