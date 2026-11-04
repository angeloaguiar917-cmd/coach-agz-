# Paper edit for "Micro tren hook 2": dead air >=0.22 s (-38 dB; quiet recording) trimmed to ~0.12 s. One take; no misspeaks found.
# Usage: python trim.py <work_dir>   (reads stab.mov, writes assembled.mov + trim.json)
import json, subprocess, sys
WD=sys.argv[1]; FPS=30
# silent runs measured with silencedetect (-32 dB, >=0.22 s) on the source audio
RUNS=[(6.31,6.61),(50.90,51.13),(53.92,54.15),(59.38,59.60),(104.38,104.80)]
remove=[]
for s,e in RUNS:
    a=int((s+0.06)*FPS+0.999); b=int((e-0.06)*FPS)          # keep ~60 ms of air each side, cut inward to whole frames
    if b>a: remove.append((a,b))
remove.sort()
SRC_N=int(round(118.328*FPS)); HOLD=1.3
keep=[]; cur=0
for a,b in remove: keep.append((cur,a)); cur=b
keep.append((cur,SRC_N))
keep=[(a,b) for a,b in keep if b>a]
fc=[]; F=0.008
for i,(a,b) in enumerate(keep):
    ta,tb=a/FPS,b/FPS; d=tb-ta
    fc.append(f"[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[0:a]atrim=start={ta:.5f}:end={tb:.5f},asetpts=PTS-STARTPTS,afade=t=in:d={F},afade=t=out:st={d-F:.5f}:d={F}[a{i}]")
fc.append(''.join(f"[v{i}][a{i}]" for i in range(len(keep)))+f"concat=n={len(keep)}:v=1:a=1[vc][ac]")
fc.append(f"[vc]tpad=stop_mode=clone:stop_duration={HOLD}[vo]"); fc.append(f"[ac]apad=pad_dur={HOLD}[ao]")
subprocess.run(['ffmpeg','-v','error','-y','-i',WD+'/stab.mov','-filter_complex',';'.join(fc),'-map','[vo]','-map','[ao]',
                '-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p','-r',str(FPS),'-c:a','pcm_s16le','-ar','48000',WD+'/assembled.mov'],check=True)
removed=sum(b-a for a,b in remove)/FPS
json.dump({'remove_frames':remove,'keep_frames':keep,'removed_s':round(removed,3),'hold_s':HOLD},open(WD+'/trim.json','w'),indent=1)
print('cuts',len(remove),'removed',round(removed,2),'s')
