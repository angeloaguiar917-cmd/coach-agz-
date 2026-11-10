import sys,json,time,importlib
from pywhispercpp.model import Model
pw=importlib.import_module('_pywhispercpp')
m=Model(sys.argv[1],n_threads=4,print_progress=False,redirect_whispercpp_logs_to=None,context_params={'flash_attn':False,'dtw_token_timestamps':True,'dtw_aheads_preset':pw.WHISPER_AHEADS_MEDIUM_EN})
t=time.time()
m.transcribe(sys.argv[2],token_timestamps=True,initial_prompt=sys.argv[4] if len(sys.argv)>4 else "Coach AGZ. Coaching, bloodwork, TRT, Tren, cycle, protocol. Um, uh, like, you know.",language='en')
ctx=m._ctx; T=[]
for i in range(pw.whisper_full_n_segments(ctx)):
    for j in range(pw.whisper_full_n_tokens(ctx,i)):
        d=pw.whisper_full_get_token_data(ctx,i,j); txt=pw.whisper_full_get_token_text(ctx,i,j)
        if isinstance(txt,bytes): txt=txt.decode('utf-8','replace')
        if txt.startswith('[_') or txt.startswith('<|'): continue
        T.append({'t':txt,'dtw':d.t_dtw/100,'t0':d.t0/100,'t1':d.t1/100,'p':round(d.p,3)})
# merge tokens to words
W=[]
for k in T:
    if k['t'].startswith(' ') or not W: W.append({'w':k['t'].strip(),'s':k['dtw'],'toks':[k['dtw']],'p':k['p']})
    else: W[-1]['w']+=k['t']; W[-1]['toks'].append(k['dtw']); W[-1]['p']=min(W[-1]['p'],k['p'])
for i,w in enumerate(W):
    w['e']=W[i+1]['s'] if i+1<len(W) else w['toks'][-1]+0.3
    del w['toks']
W=[w for w in W if w['w']]
json.dump(W,open(sys.argv[3],'w'),indent=0); print('secs',time.time()-t,len(W)); print(' '.join(f"{w['w']}@{w['s']:.2f}" for w in W[:40]))
