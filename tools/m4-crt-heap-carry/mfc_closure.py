"""Static recursive-descent closure of the MFC42 DLL attach (research input for lift_closure.py).

Roots: _DllMainCRTStartup, the RawDllMain hook word [5F4CD0A4], _CRT_INIT, DllMain and every
non-null entry of MFC42's static initializer table [5F4CD1E8,5F4CD2E8), plus extra roots given
on the command line (targets reached only dynamically). Each function is disassembled from its
entry (llvm-objdump) following direct calls, conditional and direct jumps; jumps leaving the
decoded window become their own entries, and immediate operands that address the image's own code
(callback pointers pushed or stored) become roots. Any MFC42 operand naming an IAT cell bound to
MSVCRT (CALL/JMP through it or a register load of it) follows into the staged MSVCRT export body (the loader binding the stage reproduces); system
DLL imports and other indirect calls/jumps are recorded, not followed: the stage dispatch resolves
them at run time and unknown targets stop typed. No execution; writes a fresh JSON span list.
With the argument 'all', the roots also include every MFC42 export in .text and every aligned
.rdata/.data word that addresses .text (vtables, callbacks, EH funclets): an over-approximation
lifted once instead of one re-lift per dynamically discovered target.
JMP *TABLE(,reg,4) switch tables are decoded from the literal image (case targets near the
function become continuation entries).
With 'game', the roots are instead every entry of the game's main initializer table
([5E0000, 5E0244)); game IAT cells bound to MFC42 (by ordinal) or MSVCRT follow into those bodies,
and exclude=CLOSURE.json drops functions an earlier closure already lists (one body per address).
delta=CLOSURE.json traverses fully but writes only functions that closure does not already list.
With 'msvcp50', the roots are MSVCP50's entry, exports and data words addressing its .text.
repair=LIST recomputes the listed entries (hex, whitespace separated) and what they newly reach.
Usage: python -B mfc_closure.py OUT.json [all|game|msvcp50] [exclude=CLOSURE.json] [delta=CLOSURE.json] [EXTRA_ROOT_HEX...]
"""
import json,re,struct,subprocess,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
OD=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
IMAGES={'mfc42':(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8',0x5f400000,0x5f401000,0x5f497000),
        'msvcrt':(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',0x78000000,0x78001000,0x7802e000),
        'msvcp50':(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a',0x780c0000,0x780c1000,0x78115000),
        'mech3msg':(R/'MW3/Mech3Msg.dll','8899fabb7e57383a9a483cb048636bcc027334b48941aa49835cdcc1c4715b8c',0x10000000,0x10001000,0x10002000),
        # The staged Indeo IV50 codec rebased by rebase_image.py to 0x11000000 (VfW loads it after Mech3Msg holds
        # 0x10000000, so the loader relocates it there); .text 0x11001000..0x1107a945.
        'ir50':(R/'local/mw3-staged/derived/Ir50_32.base11000000.dll','9d066dbdb0b9903c2afb07284d609c7d3ed3278245040490e9805d4cd717958f',0x11000000,0x11001000,0x1107a945),
        'game':(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',0x400000,0x401000,0x5bb000)}
def image(a):
    for k,(_,_,_,lo,hi) in IMAGES.items():
        if lo<=a<hi:return k
class PE:
    def __init__(self,path,digest,base):
        self.b=b=Path(path).read_bytes();assert hashlib.sha256(b).hexdigest()==digest,'Exact staged image '+str(path);self.base=base
        pe=struct.unpack_from('<I',b,0x3c)[0];n=struct.unpack_from('<H',b,pe+6)[0];self.opt=pe+24;so=struct.unpack_from('<H',b,pe+20)[0]
        self.S=[struct.unpack_from('<IIII',b,self.opt+so+i*40+8) for i in range(n)]
    def off(self,rva):
        for vs,v,rs,rp in self.S:
            if v<=rva<v+max(vs,rs) and rva-v<rs:return rp+rva-v
        raise ValueError(hex(rva))
    def u32(self,rva):return struct.unpack_from('<I',self.b,self.off(rva))[0]
    def word(self,va):return self.u32(va-self.base)
    def cstr(self,rva):o=self.off(rva);return self.b[o:self.b.index(b'\0',o)].decode()
    def dir(self,i):return struct.unpack_from('<II',self.b,self.opt+96+8*i)
    def imports(self):
        res={};d=self.dir(1)[0]
        while self.u32(d+12):
            dll=self.cstr(self.u32(d+12));lookup,iat=self.u32(d),self.u32(d+16);i=0
            while self.u32(lookup+4*i):
                v=self.u32(lookup+4*i);res[self.base+iat+4*i]=(dll,'#%d'%(v&0xffff) if v&0x80000000 else self.cstr(v+2));i+=1
            d+=20
        return res
    def export(self,name):
        d,size=self.dir(0);ordbase,nfun,nnames,funs,names,ords=(self.u32(d+o) for o in (16,20,24,28,32,36))
        if name.startswith('#'):idx=int(name[1:])-ordbase
        else:idx=next(struct.unpack_from('<H',self.b,self.off(ords+2*i))[0] for i in range(nnames) if self.cstr(self.u32(names+4*i))==name)
        rva=self.u32(funs+4*idx);assert rva and not d<=rva<d+size,'Unforwarded export '+name;return self.base+rva
def insns(a):
    path,_,_,_,hi=IMAGES[image(a)]
    out=subprocess.run([str(OD),'-d','--no-show-raw-insn','--start-address=%d'%a,'--stop-address=%d'%min(a+WINDOW,hi),str(path)],capture_output=True,text=True,check=True).stdout
    res={}
    for line in out.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+(\S+)\s*(.*)',line)
        if m:res[int(m.group(1),16)]=(m.group(2),m.group(3))
    return res
WINDOW=0x3000  # decode window per function (was 0x600: functions reaching it were truncated)
def insn_len(k,a):
    path=IMAGES[k][0];out=subprocess.run([str(OD),'-d','--start-address=%d'%a,'--stop-address=%d'%(a+16),str(path)],capture_output=True,text=True,check=True).stdout
    for line in out.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)',line)
        if m and int(m.group(1),16)==a:return len(m.group(2).split())
    return 1
PES={}
def jump_table(k,table,entry):
    pe=PES.setdefault(k,PE(*IMAGES[k][:3]));lo,hi=IMAGES[k][3],IMAGES[k][4];out=[]
    for i in range(512):
        try:w=pe.word(table+4*i)
        except Exception:break
        if not lo<=w<hi:  # any case target in the image's code (shared tables may sit far from the function)
            if i==0:continue  # an unreachable slot 0 (MSVCRT memcpy/memmove index 1..3 tables overlap code)
            break
        out.append(w)
    for i in (1,2,3):  # negative indices (memcpy's "count-4" tables address the preceding table's slots)
        try:w=pe.word(table-4*i)
        except Exception:break
        if not lo<=w<hi:break
        out.append(w)
    return out
def function(entry,bound):
    k=image(entry);lo,hi_text=IMAGES[k][3],IMAGES[k][4]
    ins=insns(entry);keys=sorted(ins);seen=set();todo=[entry];calls=set();icalls=[];tails=set();hi=entry;imms=set()
    nxt={a:keys[i+1] for i,a in enumerate(keys[:-1])}
    while todo:
        a=todo.pop()
        while a in ins and a not in seen:
            seen.add(a);op,arg=ins[a];hi=max(hi,nxt[a] if a in nxt else a+insn_len(k,a))
            t=re.match(r'0x([0-9a-f]+)',arg)
            for v in re.findall(r'[$]0x([0-9a-f]+)',arg):
                if lo<=int(v,16)<hi_text:imms.add(int(v,16))
            # Any operand naming an MSVCRT-bound IAT cell (CALL/JMP through it, or a register load of it).
            for v in re.findall(r'0x([0-9a-f]+)',arg):
                if int(v,16) in bound:calls.add(bound[int(v,16)])
            if op.startswith('call'):
                if t:calls.add(int(t.group(1),16))
                else:icalls.append((hex(a),arg))
            elif op.startswith('jmp'):
                if t:
                    d=int(t.group(1),16)
                    if d in ins and abs(d-entry)<0x600:todo.append(d)
                    else:tails.add(d)
                else:
                    icalls.append((hex(a),'jmp '+arg))
                    # switch jump table: JMP *TABLE(,reg,4); each case target becomes a continuation entry
                    m=re.fullmatch(r'[*]0x([0-9a-f]+)[(],%e[a-z]{2},4[)]',arg)
                    if m:
                        for t in jump_table(k,int(m.group(1),16),entry):tails.add(t)
                break
            elif op.startswith('j'):
                if t:
                    d=int(t.group(1),16)
                    if d in ins:todo.append(d)
                    else:tails.add(d)
            elif op.startswith('ret'):break
            a=nxt.get(a)
    return dict(entry=entry,end=hi,image=k,calls=sorted(calls),icalls=icalls,tails=sorted(tails),imms=sorted(imms))
def main(out,*extra):
    out=Path(out);assert not out.exists(),'Fresh closure output'
    mfc=PE(*IMAGES['mfc42'][:3]);crt=PE(*IMAGES['msvcrt'][:3])
    bound={cell:crt.export(name) for cell,(dll,name) in mfc.imports().items() if dll.upper()=='MSVCRT.DLL'}
    flags={x for x in extra if x in ('all','game','msvcp50','mech3msg','ir50')};excl={x[8:] for x in extra if x.startswith('exclude=')};delta={x[6:] for x in extra if x.startswith('delta=')};repair={x[7:] for x in extra if x.startswith('repair=')};hexes=[int(x,16) for x in extra if x not in flags and not x.startswith(('exclude=','delta=','repair='))]
    ctors=[w for w in (mfc.word(a) for a in range(0x5f4cd1e8,0x5f4cd2e8,4)) if w]
    bounds={'mfc42':bound,'msvcrt':{},'game':{}}
    cp=PE(*IMAGES['msvcp50'][:3]);bounds['msvcp50']={cell:crt.export(name) for cell,(dll,name) in cp.imports().items() if dll.upper()=='MSVCRT.DLL'}
    if 'game' in flags:
        game=PE(*IMAGES['game'][:3]);bounds['game']={cell:(mfc.export(name) if dll.upper()=='MFC42.DLL' else crt.export(name)) for cell,(dll,name) in game.imports().items() if dll.upper() in ('MFC42.DLL','MSVCRT.DLL')}
        roots=[w for w in (game.word(a) for a in range(0x5e0000,0x5e0244,4)) if w]+hexes
        if 'all' in flags:  # every aligned game .rdata/.data word addressing game .text (vtables, callback tables)
            for vs,v,rs,rp in game.S:
                if v in (0x1bb000,0x1e0000):roots+=sorted({w for w in struct.unpack_from('<%dI'%(rs//4),game.b,rp) if 0x401000<=w<0x5bb000})
    elif 'mech3msg' in flags:  # entry, exports and non-code words addressing its .text
        mm=PE(*IMAGES['mech3msg'][:3]);bounds['mech3msg']={cell:crt.export(name) for cell,(dll,name) in mm.imports().items() if dll.upper()=='MSVCRT.DLL'}
        d,_=mm.dir(0);roots=[mm.base+struct.unpack_from('<I',mm.b,mm.opt+16)[0]]+(sorted({mm.base+mm.u32(mm.u32(d+28)+4*i) for i in range(mm.u32(d+20)) if mm.u32(mm.u32(d+28)+4*i)}) if d else [])+hexes
        for vs,v,rs,rp in mm.S:
            if v!=0x1000 and rs>=4:roots+=sorted({w for w in struct.unpack_from('<%dI'%(rs//4),mm.b,rp) if 0x10001000<=w<0x10002000})
    elif 'ir50' in flags:  # rebased codec: entry, exports and every non-code word addressing its .text (its own CRT)
        cx=PE(*IMAGES['ir50'][:3]);bounds['ir50']={};lo,hi=IMAGES['ir50'][3],IMAGES['ir50'][4]
        d,_=cx.dir(0);roots=[cx.base+struct.unpack_from('<I',cx.b,cx.opt+16)[0]]+sorted({cx.base+cx.u32(cx.u32(d+28)+4*i) for i in range(cx.u32(d+20)) if cx.u32(cx.u32(d+28)+4*i)})+hexes
        for vs,v,rs,rp in cx.S:
            if v!=0x1000 and rs>=4:roots+=sorted({w for w in struct.unpack_from('<%dI'%(rs//4),cx.b,rp) if lo<=w<hi})
    elif 'msvcp50' in flags:  # entry, every export and every .rdata/.data word addressing its .text
        d,_=cp.dir(0);roots=[cp.base+struct.unpack_from('<I',cp.b,cp.opt+16)[0]]+sorted({cp.base+cp.u32(cp.u32(d+28)+4*i) for i in range(cp.u32(d+20)) if cp.u32(cp.u32(d+28)+4*i)})+hexes
        for vs,v,rs,rp in cp.S:
            if v in (0x55000,0x84000):roots+=sorted({w for w in struct.unpack_from('<%dI'%(rs//4),cp.b,rp) if 0x780c1000<=w<0x78115000})
    else:roots=[0x5f4052a2,mfc.word(0x5f4cd0a4),0x5f40555b,0x5f4056d0]+ctors+hexes
    if 'all' in flags and 'game' not in flags:
        d,_=mfc.dir(0);roots+=sorted({mfc.base+mfc.u32(mfc.u32(d+28)+4*i) for i in range(mfc.u32(d+20)) if mfc.u32(mfc.u32(d+28)+4*i)})
        for vs,v,rs,rp in mfc.S:
            if v in (0x98000,0xcb000):roots+=sorted({w for w in struct.unpack_from('<%dI'%(rs//4),mfc.b,rp) if 0x5f401000<=w<0x5f497000})
    skip=set()
    for path in excl:skip|={f['entry'] for f in json.loads(Path(path).read_text())['functions']}
    if repair:  # recompute exactly these entries (and anything new they reach); nothing else
        fixed={int(x,16) for path in repair for x in Path(path).read_text().split()};skip-=fixed;roots=sorted(fixed)
    done={};todo=list(roots)
    while todo:
        a=todo.pop()
        if a in done or a in skip or image(a) is None:continue
        f=function(a,bounds.get(image(a),{}));done[a]=f;todo+=[c for c in f['calls']+f['tails']+f['imms'] if c not in done]
    have=set()
    for path in delta:have|={f['entry'] for f in json.loads(Path(path).read_text())['functions']}
    rows=[dict(entry=a,end=f['end'],image=f['image'],calls=f['calls'],tails=f['tails'],imms=f['imms'],icalls=f['icalls']) for a,f in sorted(done.items()) if a not in have]
    images={k:v[1] for k,v in IMAGES.items()}
    out.write_text(json.dumps(dict(image='mfc42',image_sha256=IMAGES['mfc42'][1],images=images,roots=roots,excluded=sorted(excl),functions=rows),indent=1)+'\n')
    print(out,len(rows),'functions',{k:sum(r['image']==k for r in rows) for k in IMAGES})
if __name__=='__main__':main(*sys.argv[1:])
