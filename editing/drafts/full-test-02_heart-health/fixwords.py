import json,sys,re
S=sys.argv[1]; W=json.load(open(S+'/work/cut_words.json'))['words']
out=[]; i=0
FIX={'wrist':'risk','azetomibe':'ezetimibe','apov':'ApoB','telemosartan':'telmisartan','telmesartan':'telmisartan','fall':'falls','6pm':'6PM','ecg':'ECG','ekg':'EKG'}
while i<len(W):
    w=dict(W[i]); w['w']=w['w'].strip()
    if w['w']=='Is' and i+2<len(W) and W[i+2]['w'].strip().startswith('edamite'):
        w={'w':'Ezetimibe','s':W[i]['s'],'e':W[i+2]['e'],'p':1}; i+=3; out.append(w); continue
    core=re.sub(r'[^\w]','',w['w']).lower(); tail=re.sub(r'^[\w\']+','',w['w'])
    if core in FIX: w['w']=FIX[core]+tail
    out.append(w); i+=1
json.dump(out,open(S+'/work/words_final.json','w'),indent=0)
print(' '.join(f"{k}:{x['w']}@{x['s']:.2f}" for k,x in enumerate(out)))
