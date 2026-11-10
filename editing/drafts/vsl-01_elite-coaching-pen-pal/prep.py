import json,wave,numpy as np,re,subprocess
S='/tmp/claude-0/-home-user-coach-agz-/5d7337a9-30e0-51bc-b7ac-f55dfc784f28/scratchpad/vsl/'
W=json.load(open(S+'work/words_dtw.json'))
OFF=-0.18; DUR=257.23
for w in W: w['s']=round(max(0,w['s']+OFF),3)
for i,w in enumerate(W):
    nxt=W[i+1]['s'] if i+1<len(W) else DUR
    w['e']=round(min(nxt,w['s']+max(0.12,min(0.65,0.09*len(w['w'])+0.12))),3)
    w['e']=max(w['e'],w['s']+0.06)
wv=wave.open(S+'work/audio16.wav'); sr=wv.getframerate(); x=np.frombuffer(wv.readframes(wv.getnframes()),np.int16).astype(np.float32)/32768
hop=160; e=np.array([np.sqrt(np.mean(x[i:i+hop]**2)+1e-9) for i in range(0,len(x)-hop,hop)]); db=20*np.log10(e)
def emin(t,r=0.08):
    a=int((t-r)*100); b=int((t+r)*100); return (a+int(np.argmin(db[a:b])))/100
n=lambda s: re.sub(r"[^a-z0-9']","",s.lower())
# stumble: "But it's just," before "it's a different level"

cut=(204.6,206.12)   # 'But it's just,' + pause; verified on the energy profile

# silences
out=subprocess.run(['ffmpeg','-v','info','-i',S+'work/audio16.wav','-af','silencedetect=n=-35dB:d=0.33','-f','null','-'],capture_output=True,text=True).stderr
sil=[(float(a),float(b)) for a,b in re.findall(r'silence_start: ([\d.]+).*?\n.*?silence_end: ([\d.]+)',out)]
REM=[cut]
for a,b in sil:
    if b-a>0.33 and a>1 and not (a<206.2 and b>204.5): REM.append((round(a+0.08,3),round(b-0.07,3)))
REM=sorted(REM); 
FR=1/30; REM=[(round(a/FR)*FR,round(b/FR)*FR) for a,b in REM]
KEEP=[];t=0.0
for a,b in REM: KEEP.append([t,a]); t=b
KEEP.append([t,round(DUR//FR*FR,4)])
print('removed',round(sum(b-a for a,b in REM),2),'s in',len(REM),'cuts; out dur',round(sum(b-a for a,b in KEEP),2))
# drop words inside removed spans
Wf=[w for w in W if not any(a-0.01<=w['s']<b-0.02 for a,b in REM)]
k=[i for i,w in enumerate(Wf) if 206.0<w['s']<206.6 and n(w['w'])=='a'][0]
Wf.insert(k,{'w':"it's",'s':206.15,'e':206.3}); Wf[k+1]['s']=max(Wf[k+1]['s'],206.3)
json.dump(Wf,open(S+'words_final.json','w'),indent=0)
def cue(ph,after=0):
    p=[n(q) for q in ph.split()]
    for k in range(len(Wf)):
        if Wf[k]['s']>=after and [n(q['w']) for q in Wf[k:k+len(p)]]==p: return Wf[k]['s']
    raise KeyError(ph)
hook_end=min(6.0,max(3.0,cue('coaching')+0.55+0.5))
outdur=sum(b-a for a,b in KEEP)
def o2s(to):
    acc=0
    for a,b in KEEP:
        if to<acc+(b-a): return a+(to-acc)
        acc+=b-a
mid=o2s(outdur/2); cuts=[a for a,b in KEEP[1:]]
band_end=min(cuts,key=lambda c:abs(c-mid)) if min(abs(c-mid) for c in cuts)<3 else mid
# punch schedule
keys=[(cue('paying'),1.08),(cue('and then you send'),1.0),(cue("that's literally"),1.12),(cue('you know what'),1.0),(cue("it's like"),1.08),(cue('and most coaches'),1.0),
      (cue('brother you have a business'),1.08),(cue('so what does that mean'),1.0),(cue('honestly'),1.08),(cue('the truth is'),1.0),(cue('but what happens'),1.1),
      (cue("that's why we have to break"),1.0),(cue('at the end of the day'),1.08),(cue("it doesn't matter"),1.0),(cue('because at the end'),1.1),(cue('and this my friends'),1.0),
      (cue('completely different level'),1.12),(cue('like i send out'),1.0),(cue('some guys just want'),1.08),(cue('other guys want'),1.0),(cue('with that being said'),1.08),
      (cue('and i suppose'),1.0),(cue('make sure you reach out'),1.1)]
# at every cut, toggle the zoom to hide the jump
ev=sorted(keys)
P=[]; 
for k,(t0,z) in enumerate(ev):
    t1=ev[k+1][0] if k+1<len(ev) else 999; P.append([t0,t1,z])
for c in cuts:
    for p in P:
        if p[0]<c<p[1]:
            z2=1.0 if p[2]>1.0 else 1.06; P.append([c,min(p[1],c+3.0),z2]); break
P0=[[0,ev[0][0],1.0]]+P
edit=dict(src_dur=DUR,keep=KEEP,remove=REM,hook=dict(lines=['Paying for ELITE COACHING','getting a pen pal'],emphasis=['ELITE COACHING'],end=round(hook_end,3),y_px=300),
          band_end=round(band_end,3),punch=sorted(P0),shakes=[])
json.dump(edit,open(S+'edit.json','w'),indent=1)
print('hook_end',hook_end,'band_end',band_end,'mid',mid)
