import json,subprocess,re
FPS=30
out=subprocess.run(['ffmpeg','-i','a16.wav','-af','silencedetect=n=-35dB:d=0.22','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([0-9.]+)',out)]; en=[float(x) for x in re.findall(r'silence_end: ([0-9.]+)',out)]
DUR=146.40
rem=[]
for a,b in zip(st,en):
    if b-a>0.22 and a>0.5: rem.append((round((a+0.06)*FPS)/FPS, round((b-0.06)*FPS)/FPS))
# tail: end after "appreciate you guys"
keep=[];t=0.0
for a,b in rem:
    if a>t: keep.append([t,a]); t=b
keep.append([t,DUR])
keep=[[round(a*FPS)/FPS,round(b*FPS)/FPS] for a,b in keep if b-a>0.05]
json.dump({'remove':rem,'keep':keep,'newdur':sum(b-a for a,b in keep)},open('trim.json','w'),indent=0)
print(len(rem),'cuts', sum(b-a for a,b in rem),'s removed; new dur',sum(b-a for a,b in keep))
fc='';n=len(keep)
for i,(a,b) in enumerate(keep):
    fc+=f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[v{i}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b-a-0.008:.4f}:d=0.008[a{i}];"
fc+=''.join(f'[v{i}][a{i}]' for i in range(n))+f'concat=n={n}:v=1:a=1[v][a]'
subprocess.run(['ffmpeg','-v','error','-y','-i','../src/src.mov','-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-crf','12','-preset','fast','-g','1','-pix_fmt','yuv420p','-c:a','pcm_s16le','assembled.mov'],check=True)
