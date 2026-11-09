# Word timing helpers: whisper.cpp starts are quantised at segment edges, so snap
# word starts/ends that fall inside a detected pause onto the pause boundary.
import json, numpy as np, wave
def envelope(wav):
    w=wave.open(wav); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    if w.getnchannels()==2: x=x.reshape(-1,2).mean(1)
    hop=w.getframerate()//100; n=len(x)//hop
    return 20*np.log10(np.sqrt((x[:n*hop].reshape(n,hop)**2).mean(1))+1e-9)
def pauses(db,thr=None,minlen=0.08):
    thr=np.percentile(db,10)+8 if thr is None else thr
    q=db<thr; out=[]; i=0; n=len(q)
    while i<n:
        if q[i]:
            j=i
            while j<n and q[j]: j+=1
            if (j-i)*0.01>=minlen: out.append((i*0.01,j*0.01))
            i=j
        else: i+=1
    return out
def refine(words,wav):
    P=pauses(envelope(wav))
    for w in words:
        for a,b in P:
            if a<=w['s']<b: w['s']=round(b,2)
            if a<w['e']<=b: w['e']=round(a+0.02,2)
        if w['e']<=w['s']: w['e']=round(w['s']+0.12,2)
    for i in range(len(words)-1):   # keep monotonic
        if words[i+1]['s']<words[i]['s']: words[i+1]['s']=words[i]['s']+0.05
    return words
FIXES={'mastron':'Masteron','cirm':'SERM','undeclinate':'undecylenate','ais':'AIs','hematocrit':'hematocrit','primobolan':'Primobolan','equipoise':'Equipoise'}
def fix(words):
    for w in words:
        core=w['w'].strip('.,?!').lower(); tail=w['w'][len(w['w'].rstrip('.,?!')):]
        if core in FIXES: w['w']=FIXES[core]+tail
    return words
