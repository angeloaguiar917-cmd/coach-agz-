import json
C=json.load(open('cut_tr.json'))['words']
out=[]; i=0
def add(w,s,e,end=False): out.append({'w':w,'s':s,'e':e,'end':end})
while i<len(C):
    w=C[i]; t=w['w']; k=t.lower().strip('.,?!')
    nxt=lambda j: C[i+j]['w'].lower().strip('.,?!') if i+j<len(C) else ''
    if k=="we'll" and nxt(1)=='tell': add('WITH',w['s'],C[i+1]['s']); add('TELMISARTAN',C[i+1]['s'],C[i+3]['e']); i+=4; continue
    if k=='npc' and nxt(1)=='1l1': add('NPC1L1',w['s'],C[i+1]['e'],True); i+=2; continue
    if k=='a' and nxt(1)=='pov': add('APOB',w['s'],C[i+1]['e'],True); i+=2; continue
    if k=='6' and nxt(1)=='p': add('6PM',w['s'],C[i+2]['e']); i+=3; continue
    M={'antibiotics':'ANABOLICS','apo':'APOB','azetomibe':'EZETIMIBE','azetomide':'EZETIMIBE','telmesartan':'TELMISARTAN','telmisartan':'TELMISARTAN','1l1':'NPC1L1'}
    add(M.get(k,t.upper().strip('.,?!')),w['s'],w['e'],t[-1] in '.,?!'); i+=1
# sentence ends missing punctuation in some segs: mark ends where next word starts a known sentence
for a,b in zip(out,out[1:]):
    if b['s']-a['e']>0.25: a['end']=True
for w in out:
    if w['w'] in ('LIVER','THING','FRIENDS','SIGNALING','GOOD','INTESTINES','LDL') : pass
json.dump(out,open('words_final.json','w'),indent=0)
print(len(out)); print(' '.join(f"{w['w']}[{w['s']:.2f}]{'|' if w['end'] else ''}" for w in out))
