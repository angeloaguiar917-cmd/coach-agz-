import json,subprocess,re
S='/tmp/claude-0/-home-user-coach-agz-/893583c8-f693-5502-b060-ae624265d10c/scratchpad'
FPS=30
log=subprocess.run(['ffmpeg','-i',S+'/src/audio16k.wav','-af','silencedetect=n=-38dB:d=0.22','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',log)]; en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',log)]
words=json.load(open(S+'/src/words_fill.json'))
END=79.58+0.30
rm=[]
for a,b in zip(st,en):
    if a<0.05 or b>END: continue
    keep=0.12; c0=a+0.05; c1=b-0.07   # keep 50ms tail + 70ms pre-roll
    if c1-c0<0.06: continue
    # don't cut through a recognised word
    if False and any(w['s']<c1-0.02 and w['e']>c0+0.02 for w in words if w['e']-w['s']>0.05): print('skip overlap',a,b); continue
    rm.append([round(c0*FPS)/FPS,round(c1*FPS)/FPS])
rm=[r for r in rm if r[1]>r[0]]
keep=[];t=0
for a,b in rm: keep.append([t,a]); t=b
keep.append([t,round(END*FPS)/FPS])
print('removed',rm,'total',round(sum(b-a for a,b in rm),2))
json.dump({'remove':rm,'keep':keep,'dur':sum(b-a for a,b in keep)},open(S+'/k/trim.json','w'),indent=1)
