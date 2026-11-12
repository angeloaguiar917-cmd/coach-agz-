import json, re
R=json.load(open('words_med.json')); C=json.load(open('words_cut.json')); TR=json.load(open('trim.json'))
rem=TR['remove']
def m(t):
    for a,b in rem:
        if a<=t<b: return a-sum(bb-aa for aa,bb in rem if aa<a)
    return t-sum(min(b,t)-a for a,b in rem if a<t)
FIX={'tremolo':'trenbolone','trend':'tren','tremble':'tren','apob':'ApoB','micro':'micro'}
out=[]
for x in R:
    w=x['w']; k=re.sub(r'[^a-z]','',w.lower())
    if k in FIX: w=re.sub(r'[A-Za-z]+',FIX[k],w,1)
    out.append({'w':w,'s':round(m(x['s']),3),'e':round(m(x['e']),3)})
# merge "-catabolic", "-world", "-term" hyphen pieces
M=[]
for x in out:
    if x['w'].startswith('-') and M: M[-1]['w']+=x['w']; M[-1]['e']=x['e']
    else: M.append(x)
# "tren on" -> "tren alone" (re-check pass)
for i,x in enumerate(M):
    if x['w']=='on' and i>0 and M[i-1]['w']=='tren': x['w']='alone'
# merge "micro dosing"
F=[]
for x in M:
    if F and F[-1]['w'].lower()=='micro' and x['w'].lower().startswith('dosing'): F[-1]['w']='microdosing'+x['w'][6:]; F[-1]['e']=x['e']
    else: F.append(x)
json.dump(F,open('words_final.json','w'),indent=0)
print(len(F)); print(' '.join(x['w'] for x in F))
# drift check vs cut transcript: align identical lowercase words in order
import difflib
a=[re.sub(r'[^a-z0-9]','',x['w'].lower()) for x in F]; b=[re.sub(r'[^a-z0-9]','',x['w'].lower()) for x in C]
sm=difflib.SequenceMatcher(None,a,b,autojunk=False); d=[]
for blk in sm.get_matching_blocks():
    for j in range(blk.size): d.append((abs(F[blk.a+j]['s']-C[blk.b+j]['s']),F[blk.a+j]['w'],F[blk.a+j]['s']))
import numpy as np; dd=np.array([x[0] for x in d]); print('matched',len(d),'median',np.median(dd),'p95',np.percentile(dd,95),'max',dd.max()); print(sorted(d)[-6:])
