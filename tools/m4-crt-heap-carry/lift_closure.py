"""Lift every function of a pinned mfc_closure.py span list with lift_attach.py's exact lifter,
semantics, lowering and namespace (mw34_attach_m_<entry>). Source-only (no execution).

A function whose bytes contain a CALL to its own entry cannot be lifted as one object (the lifter
does not terminate when a direct call target equals the entry inside the lifted bytes). Such a
function is cut before its first self-call: the entry object covers [entry, first self-call) and
continuation objects, one per internal branch target after the entry and at the cut, each cover
[target, end). No continuation contains the function entry, so every self-call leaves its object
as an ordinary direct call; the stage dispatch joins the objects by address.
With PART=K/N only every N-th object starting at K is lifted, into lifts-rN-pK (partitions run as
separate processes and gen_mfc_dispatch.py merges them).
With retry=DIR[,DIR...] only the components those lift reports recorded as failed are lifted.
The x87/FP lowering extension (fp_lowering.py) is enabled.
Usage: python -B lift_closure.py CLOSURE.json CLOSURE_SHA256 lifts-rN [K/N] [retry=DIR,...] [skip=DIR,...]
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import lift_attach as L
OD=L.ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
def decode(image,start,end):
    out=subprocess.run([str(OD),'-d','--no-show-raw-insn','--start-address=%d'%start,'--stop-address=%d'%end,str(L.IMAGES[image][0])],capture_output=True,text=True,check=True).stdout
    return [(int(m.group(1),16),m.group(2),m.group(3)) for m in re.finditer(r'^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$',out,re.M)]
RAW_END={}
def raw_end(image,a):
    # End of the raw executable section holding a (spans are clipped to it; the lifter reads only raw bytes).
    if image not in RAW_END:
        import struct;b=Path(L.IMAGES[image][0]).read_bytes();pe=struct.unpack_from('<I',b,0x3c)[0];n=struct.unpack_from('<H',b,pe+6)[0];opt=pe+24;so=struct.unpack_from('<H',b,pe+20)[0];base=struct.unpack_from('<I',b,opt+28)[0]
        RAW_END[image]=[(base+va,base+va+rs) for vs,va,rs,rp in (struct.unpack_from('<IIII',b,opt+so+i*40+8) for i in range(n))]
    for lo,hi in RAW_END[image]:
        if lo<=a<hi:return hi
    return a+1
def spans(f):
    entry,end,image=f['entry'],f['end'],f.get('image','mfc42');end=min(end,raw_end(image,entry))
    if entry not in f['calls']:return [('m_%x'%entry,entry,end,entry,image)]
    ins=decode(image,entry,end);target=lambda arg:int(arg[2:].split()[0],16) if arg.startswith('0x') else None
    cut=min(a for a,op,arg in ins if op.startswith('call') and target(arg)==entry)
    conts={cut}|{target(arg) for a,op,arg in ins if op.startswith('j') and target(arg) is not None and entry<target(arg)<end}
    L.need(all(entry<t<end for t in conts),'Continuations inside the function after its entry')
    return [('m_%x'%entry,entry,cut,entry,image)]+[('m_%x'%t,t,end,t,image) for t in sorted(conts)]
def main(closure,digest,name,*opts):
    part=next((o for o in opts if '/' in o and not o.startswith(('retry=','skip='))),None);retry=[d for o in opts if o.startswith('retry=') for d in o[6:].split(',')];skip=[d for o in opts if o.startswith('skip=') for d in o[5:].split(',')]
    data=Path(closure).read_bytes();L.need(hashlib.sha256(data).hexdigest()==digest,'Exact pinned closure')
    C=json.loads(data);L.need(C['image']=='mfc42'and C['image_sha256']==L.IMAGES['mfc42'][1],'Closure of the pinned MFC42 image')
    L.need(all(C.get('images',{}).get(k,v[1])==v[1] for k,v in L.IMAGES.items()),'Closure images are the pinned images')
    entries={f['entry'] for f in C['functions']};S=[]
    for f in C['functions']:
        for s in spans(f):
            if s[3]!=f['entry'] and s[3] in entries:continue  # already a closure entry with its own object
            S.append(s)
    L.need(len({s[0] for s in S})==len(S),'One object per entry')
    if retry:
        failed=set()
        for d in retry:failed|=set(json.loads((Path(d)/'report.json').read_text()).get('failed',{}))
        S=[x for x in S if x[0] in failed];L.need(len(S)==len(failed),'Every failed component is a closure object')
    have=set()
    for d in skip:have|=set(json.loads((Path(d)/'report.json').read_text())['components'])
    S=[x for x in S if x[0] not in have]  # objects an earlier lift already holds
    if part:k,n=map(int,part.split('/'));L.need(0<=k<n,'Partition K/N');S=S[k::n];name='%s-p%d'%(name,k)
    L.SPANS=tuple(S)
    # Every direct-call symbol is renamed into the private mw34_mfc_ namespace, so the closure's
    # routers (gen_mfc_dispatch.py) never collide with symbols other composition objects define.
    out=L.ROOT/'reports/m4-crt-attach'/name
    class Renames(dict):
        def get(self,component,default=None):
            text=(out/(component+'-guest.ll')).read_text()
            return {x:'mw34_mfc_'+x for x in sorted(set(re.findall(r'^declare ptr @(sub_[0-9a-f]+)',text,re.M)))}
    L.RENAMES=Renames()
    # Hardware exception exits (DIV #DE) become an owner bridge that stops typed; SEH dispatch is not modelled.
    # LOCK-prefixed read-modify-write instructions bracket their accesses with atomic markers; the guest
    # runs on one host thread inside one Stage, so the markers are owner-checked ordering points.
    L.BRIDGES=L.BRIDGES|{'__remill_error','__remill_atomic_begin','__remill_atomic_end','__remill_async_hyper_call'}
    import fp_lowering as F;L.BRIDGES=L.BRIDGES|F.BRIDGES;L.LOWER_PATCHES=F.PATCHES;L.LLVM_CLASS=F.llvm_class;import x87_bridges as X;L.GUEST_IR_HOOK=lambda t:X.rewrite(t)[0]
    L.TOLERANT=True  # failures are recorded in the report and stop typed if reached
    L.main(name)
    (out/'closure.json').write_bytes(data)
if __name__=='__main__':main(*sys.argv[1:])
