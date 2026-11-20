import sys,json,whisper
m=whisper.load_model(sys.argv[2])
r=m.transcribe(sys.argv[1],word_timestamps=True,language='en',condition_on_previous_text=False,fp16=False,
 initial_prompt=sys.argv[4] if len(sys.argv)>4 else "Um, uh, so, like. Steroid cycle, testosterone, Tren, Nebivolol, Telmisartan, ApoB, hematocrit, citrus bergamot, blood pressure, cholesterol, HDL, LDL, cardio.")
out=[]
for s in r['segments']:
  print(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}",flush=True)
  for w in s['words']: out.append({'w':w['word'].strip(),'s':round(w['start'],2),'e':round(w['end'],2),'p':round(w['probability'],2)})
json.dump(out,open(sys.argv[3],'w'))
