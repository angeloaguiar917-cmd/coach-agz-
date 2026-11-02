import sys, json, subprocess
S=sys.argv[1]
src_code=open(S+'/full1/full_render.py').read().split("if __name__=='__main__':")[0]
_argv=sys.argv; sys.argv=['x',S]; exec(src_code); sys.argv=_argv
TR=json.load(open(T+'trim.json')); KEEP=TR['keep']
WORDS[:]=json.load(open(T+'words_captions_oldtl.json')); GROUPS=build_groups()
CUTS=sorted(set([b0 for b0,_ in BOUNDS[1:]]+[b for a,b in TR['remove']]))   # every jump point (old timeline)
def new_to_old(tn):
    acc=0
    for a,b in KEEP:
        if tn < acc+(b-a)-1e-9: return a+(tn-acc)
        acc+=b-a
    return KEEP[-1][1]-1/FPS
# punch-in alternates at EVERY jump cut (take changes + trims)
_orig_frame=frame
def seg_of(t):  # overrides full_render.seg_of used for zoom parity
    return sum(1 for c in CUTS if c<=t+1e-6)
globals()['seg_of']=seg_of
if __name__=='__main__':
    n0,n1,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
    olds=[round(new_to_old(n/FPS)*FPS) for n in range(n0,n1)]
    first,last=olds[0],olds[-1]
    dec=subprocess.Popen(['ffmpeg','-v','error','-i',T+'assembled.mov','-vf',f'select=between(n\\,{first}\\,{last})','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=720:1280:flags=lanczos','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    cur=first-1; buf=None
    for n,o in zip(range(n0,n1),olds):
        while cur<o:
            buf=dec.stdout.read(W*H*3); cur+=1
            if len(buf)<W*H*3: raise SystemExit(f'short read at old frame {cur}')
        enc.stdin.write(frame(Image.frombuffer('RGB',(W,H),buf),o/FPS).tobytes())
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',n0,n1)
