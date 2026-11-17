import json,subprocess,sys
runs=[(6.45, 6.82), (8.11, 8.36), (11.32, 11.67), (11.91, 12.69), (16.25, 16.64), (17.63, 19.1), (20.2, 20.94), (26.04, 26.51), (28.44, 28.85), (31.07, 31.59), (33.74, 34.75), (37.25, 38.18), (40.5, 40.78), (41.79, 42.16), (42.92, 43.19), (44.97, 45.25), (46.08, 46.42), (48.78, 49.07), (50.24, 51.58), (52.87, 53.27), (55.01, 55.75), (57.08, 57.36), (57.69, 58.64)]
keep_gap={(17.63,19.1):0.42,(57.69,58.64):0.40,(11.91,12.69):0.22}
cuts=[]
for a,b in runs:
    g=keep_gap.get((a,b),0.16)
    if b-a<=g+0.06: continue
    m=(b-a-g)/2; cuts.append((a+g/2+0.0, b-g/2))
cuts.append((38.86,39.21))  # stumble "not"
cuts.sort()
fr=lambda x: round(x*30)/30
segs=[];s=0.0
for a,b in cuts:
    segs.append((fr(s),fr(a))); s=b
segs.append((fr(s),61.1))
segs=[(a,b) for a,b in segs if b-a>0.03]
json.dump(segs,open('segments.json','w'))
print(len(segs), sum(b-a for a,b in segs))
fc=[]
for i,(a,b) in enumerate(segs):
    d=b-a
    fc.append(f"[0:v]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS,fps=30[v{i}];[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={d-0.008:.4f}:d=0.008[a{i}]")
fc.append(''.join(f'[v{i}][a{i}]' for i in range(len(segs)))+f"concat=n={len(segs)}:v=1:a=1[v][a]")
open('fc.txt','w').write(';'.join(fc))
subprocess.run(['ffmpeg','-v','error','-y','-i','../src/src.mov','-filter_complex_script','fc.txt','-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','14','-pix_fmt','yuv420p','-c:a','pcm_s16le','cut.mov'],check=True)
