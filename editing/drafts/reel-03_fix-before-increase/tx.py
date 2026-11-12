import sys,json,whisper
m=whisper.load_model(sys.argv[3] if len(sys.argv)>3 else "medium.en")
r=m.transcribe(sys.argv[1],word_timestamps=True,language="en",condition_on_previous_text=False,
  initial_prompt="Um, so, uh, Coach Agz on TRT. Testosterone, estradiol, E2, hematocrit, SHBG, free testosterone, bloodwork, cycle, dose, AI, aromatase inhibitor, ng/dL.")
W=[]
for s in r["segments"]:
    for w in s["words"]: W.append(dict(w=w["word"].strip(),s=round(w["start"],3),e=round(w["end"],3),p=round(w["probability"],3)))
json.dump(W,open(sys.argv[2],'w'),indent=0)
print(" ".join(f"[{x['s']:.1f}]{x['w']}" for x in W))
