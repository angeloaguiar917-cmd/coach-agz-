import zipfile,pickle,struct,base64,sys,collections,numpy as np
pt,assets,out=sys.argv[1:4]
z=zipfile.ZipFile(pt); names=z.namelist(); root=names[0].split('/')[0]
DT={'HalfStorage':np.float16,'FloatStorage':np.float32,'LongStorage':np.int64,'IntStorage':np.int32,'BFloat16Storage':None}
class ST:
    def __init__(s,dt): s.dt=dt
cache={}
def load_storage(key,dt):
    if key not in cache: cache[key]=np.frombuffer(z.read(f'{root}/data/{key}'),dtype=dt)
    return cache[key]
def rebuild(storage,offset,size,stride,*a):
    arr=storage
    if len(size)==0: return arr[offset:offset+1].reshape(())
    return np.lib.stride_tricks.as_strided(arr[offset:],shape=size,strides=[s*arr.itemsize for s in stride]).copy()
class U(pickle.Unpickler):
    def find_class(s,mod,name):
        if mod=='torch._utils' and name=='_rebuild_tensor_v2': return rebuild
        if mod=='torch' and name in DT: return ST(DT[name])
        if mod=='collections' and name=='OrderedDict': return collections.OrderedDict
        if mod=='torch' and name=='device': return lambda *a: None
        raise Exception(f'{mod}.{name}')
    def persistent_load(s,pid):
        _,st,key,loc,n=pid; return load_storage(key,st.dt)
ck=U(z.open(f'{root}/data.pkl')).load()
dims=ck['dims']; sd=ck['model_state_dict']; print(dims)
f=open(out,'wb'); f.write(struct.pack('i',0x67676d6c))
for k in ['n_vocab','n_audio_ctx','n_audio_state','n_audio_head','n_audio_layer','n_text_ctx','n_text_state','n_text_head','n_text_layer','n_mels']: f.write(struct.pack('i',dims[k]))
f.write(struct.pack('i',1))
fil=np.load(assets+'/mel_filters.npz')[f"mel_{dims['n_mels']}"].astype(np.float32)
f.write(struct.pack('i',fil.shape[0])); f.write(struct.pack('i',fil.shape[1])); fil.tofile(f)
tok=open(assets+'/gpt2.tiktoken','rb').read()
toks={base64.b64decode(t):int(r) for t,r in (l.split() for l in tok.splitlines() if l)}
f.write(struct.pack('i',len(toks)))
for k in toks: f.write(struct.pack('i',len(k))); f.write(k)
for name,data in sd.items():
    data=np.asarray(data).squeeze()
    if name in ('encoder.conv1.bias','encoder.conv2.bias'): data=data.reshape(data.shape[0],1)
    nd=data.ndim
    if nd<2 or name in ('encoder.conv1.bias','encoder.conv2.bias','encoder.positional_embedding','decoder.positional_embedding'): data=data.astype(np.float32); ft=0
    else: data=data.astype(np.float16); ft=1
    s=name.encode(); f.write(struct.pack('iii',nd,len(s),ft))
    for i in range(nd): f.write(struct.pack('i',data.shape[nd-1-i]))
    f.write(s); np.ascontiguousarray(data).tofile(f)
f.close(); print('ok')
