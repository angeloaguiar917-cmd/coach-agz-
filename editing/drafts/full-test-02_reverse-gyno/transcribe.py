import sys,json,whisper
m=whisper.load_model(sys.argv[3])
r=m.transcribe(sys.argv[1],word_timestamps=True,language='en',initial_prompt=sys.argv[4] if len(sys.argv)>4 else "Gyno, gynecomastia, estrogen, E2, aromatase inhibitor, SERM, Nolvadex, raloxifene, prolactin, nipple, cycle, testosterone, bloodwork.",condition_on_previous_text=False)
W=[]
for s in r['segments']:
    print(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['text']}",flush=True)
    for w in s['words']: W.append({'w':w['word'].strip(),'s':round(w['start'],3),'e':round(w['end'],3),'p':round(w['probability'],2)})
json.dump(W,open(sys.argv[2],'w'))
