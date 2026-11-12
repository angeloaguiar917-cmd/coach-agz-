import sys, json, whisper
m=whisper.load_model(sys.argv[3] if len(sys.argv)>3 else 'small.en')
r=m.transcribe(sys.argv[1], word_timestamps=True, language='en', condition_on_previous_text=False,
  initial_prompt=sys.argv[4] if len(sys.argv)>4 else "Coach AGZ. Tren, trenbolone, microdose, year round, testosterone, TRT, hematocrit, estradiol, prolactin, bloodwork, blood pressure, lipids, HDL, LDL, cardio, milligrams, mg.")
out=[]
for s in r['segments']:
    for w in s['words']: out.append({'w':w['word'].strip(),'s':round(w['start'],2),'e':round(w['end'],2),'p':round(w['probability'],2)})
json.dump(out,open(sys.argv[2],'w'),indent=0)
for s in r['segments']: print(f"{s['start']:6.2f}-{s['end']:6.2f} {s['text']}")
