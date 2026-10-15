"""Exact IR rewrites for the recompiled MFC-stage objects (used by inline_objects.py --cleanup).

1. Identity helpers. remill's __remill_flag_computation_* and __remill_compare_* helpers are defined in each module as
   `noinline optnone noduplicate` functions whose body is `ret i1 %0` (variadic, so LLVM can never inline them). A call
   is replaced by `or i1 <first argument>, false` (the same value) only when this module defines that helper with
   exactly that identity body.
2. Undefined representatives. Calls to mw34_attach_*_undefined_8 (mfc_routers.inc -> mf_undefined -> Stage::undefined,
   which always returns 0 after an owner check and a statistics counter) become the constant 0. Lifted MFC-stage code
   only runs inside Stage::run, so the owner check cannot fail there; the counter is not used for any decision.
3. 80-bit register copies. remill moves x87 stack slots with `llvm.memcpy(dst, src, 10)`; chains of these block load
   forwarding. Each becomes `load i80` + `store i80` of the same 10 bytes (bit-exact for every pattern, NaNs and
   unnormals included; slots never partially overlap).
Values seen by guest code are unchanged; transform() returns the rewritten text and per-kind counts.
"""
import re
IDENT=re.compile(r'^define internal zeroext i1 @(__remill_(?:flag_computation|compare)_\w+)\(i1 noundef zeroext %0(?:, \.\.\.)?\)[^{]*\{\n[\w.]+:\n  ret i1 %0\n\}',re.M)
CALL=re.compile(r'^(  %[\w.]+) = (?:tail |notail )?call (?:noundef )?zeroext i1 (?:\(i1, \.\.\.\) )?@(__remill_(?:flag_computation|compare)_\w+)\(i1 (?:noundef )?(?:zeroext )?(%[\w.]+|true|false)(?:,[^\n]*)?\)(?: #\d+)?$',re.M)
UND=re.compile(r'^(  %[\w.]+) = (?:tail )?call (?:noundef )?zeroext i8 @mw34_attach_\w+_undefined_8\(\)(?: #\d+)?$',re.M)
COPY=re.compile(r'^(\s*)(?:tail )?call void @llvm\.memcpy\.p0\.p0\.i(?:32|64)\(ptr [^%\n]*(%[\w.]+), ptr [^%\n]*(%[\w.]+), i(?:32|64) 10, i1 false\)(?: #\d+)?$',re.M)
def transform(text):
    ident=set(IDENT.findall(text));st=dict(identity_calls=0,undefined_calls=0,fp80_copies=0,kept_calls=0)
    def r_ident(m):
        if m.group(2) not in ident:st['kept_calls']+=1;return m.group(0)
        st['identity_calls']+=1;return f'{m.group(1)} = or i1 {m.group(3)}, false'
    def r_und(m):st['undefined_calls']+=1;return f'{m.group(1)} = or i8 0, 0'
    def r_copy(m):
        st['fp80_copies']+=1;t=f'%mw34.c80.{st["fp80_copies"]}'
        return f'{m.group(1)}{t} = load i80, ptr {m.group(3)}, align 1\n{m.group(1)}store i80 {t}, ptr {m.group(2)}, align 1'
    text=CALL.sub(r_ident,text);text=UND.sub(r_und,text);text=COPY.sub(r_copy,text)
    return text,st

# 4. Bridge effects (applied after merge_x87). The memory and x87-exception bridges never read or write guest State
#    (they touch guest memory and the host FPU only), and an exception thrown out of one is always a typed deny that
#    ends the run (no guest code resumes; callback faults also end in deny). Declaring them
#    `nounwind memory(inaccessiblemem: readwrite)` keeps every call, in order, while letting LLVM forward and drop
#    overwritten State stores across them. Lifted bodies get `uwtable` so a deny still unwinds cleanly through them.
#    Only effect beyond speed: a deny message may quote a State value from before the failing access.
BRIDGE_DECL=re.compile(r'^(declare dso_local [^@\n]*@__remill_(?:read_memory_\w+|write_memory_\w+|fpu_exception_clear|fpu_exception_test)\([^)\n]*\))(?: #\d+)?$',re.M)
BODY_DEF=re.compile(r'^(define [^\n]*@mw34_attach_\w+_body\([^\n]*\))((?: #\d+)?) \{$',re.M)
def annotate(text):
    st=dict(nounwind_bridges=0,uwtable_bodies=0)
    def r_decl(m):st['nounwind_bridges']+=1;return m.group(1)+' #990'
    def r_body(m):st['uwtable_bodies']+=1;return m.group(1)+' uwtable'+m.group(2)+' {'
    text=BRIDGE_DECL.sub(r_decl,text);text=BODY_DEF.sub(r_body,text)
    if st['nounwind_bridges']:text+='\nattributes #990 = { nounwind "no-builtins" memory(inaccessiblemem: readwrite) }\n'
    return text,st

# 5. Strict x87 (opt-in, --strict-x87; applied after annotate). remill orders each FP operation against the host
#    exception-flag reads with `asm sideeffect "" ~{memory}` fences, which pin all of State in memory. Exactly the same
#    ordering is obtained from LLVM's strict FP model: every FP operation becomes a constrained intrinsic
#    (round.dynamic, fpexcept.strict) in a `strictfp` body, ordered against the bridges (inaccessible memory = FP
#    environment), and the fences go. remill's denormal classification compares (against 0, infinity and the smallest
#    normal, all evaluated before the operation's exception clear) become integer tests on the bit pattern; equivalence
#    with the hardware compares was checked on all 2^32 float patterns and every 80-bit class (0 mismatches).
#    If any FP operation of a body cannot be converted, the module is returned unchanged.
F80_0='0xK00000000000000000000';F80_INF='0xK7FFF8000000000000000';F80_MIN='0xK00018000000000000000'
F32_0='0.000000e+00';F32_INF='0x7FF0000000000000';F32_MIN='0x3810000000000000'
FT={'x86_fp80':'f80','double':'f64','float':'f32'}
CLS=re.compile(r'^  (%[\w.]+) = fcmp (?:[a-z]+ )*?(ueq|oeq|olt) (x86_fp80|float) (%[\w.]+), ([^\n]+)$',re.M)
ARITH=re.compile(r'^(  %[\w.]+) = (fadd|fsub|fmul|fdiv|frem) (?:[a-z]+ )*?(x86_fp80|double|float) ([^,\n]+), ([^\n]+)$',re.M)
CONV=re.compile(r'^(  %[\w.]+) = (fpext|fptrunc|sitofp|uitofp|fptosi|fptoui) ([\w]+) ([^\s]+) to ([\w]+)$',re.M)
FCMP=re.compile(r'^(  %[\w.]+) = fcmp (?:[a-z]+ )*?(oeq|ogt|oge|olt|ole|one|ord|ueq|ugt|uge|ult|ule|une|uno) (x86_fp80|double|float) ([^,\n]+), ([^\n]+)$',re.M)
FENCE=re.compile(r'^\s*(?:tail )?call void asm sideeffect "", "~\{memory\},~\{dirflag\},~\{fpsr\},~\{flags\}"\(\)(?: #\d+)?\n',re.M)
LEFT=re.compile(r'= (?:fadd|fsub|fmul|fdiv|frem|fcmp|fpext|fptrunc|sitofp|uitofp|fptosi|fptoui) |@llvm\.(?:sqrt|rint|nearbyint|round|trunc|floor|ceil|pow|exp|log|sin|cos|fma|fmuladd|minnum|maxnum|lrint|llrint|lround|llround)\.')
CALLSITE=re.compile(r'^(  (?:%[\w.]+ = )?(?:tail |notail |musttail )?call [^\n]*\))((?: #\d+)?)$',re.M)
def _classify(text,st):
    k=[0]
    def t():k[0]+=1;return f'%mw34.k{k[0]}'
    def rep(m):
        lhs,pred,ty,v,c=m.groups();c=c.strip()
        key={('ueq',F80_0):'ueq0',('oeq',F80_INF):'inf',('olt',F80_MIN):'lt',('ueq',F32_0):'ueq0',('oeq',F32_INF):'inf',('olt',F32_MIN):'lt'}.get((pred,c))
        if not key:return m.group(0)
        st['classify_'+key]+=1
        if ty=='x86_fp80':
            b,e0,e,mm,j=t(),t(),t(),t(),t();o=[f'{b} = bitcast x86_fp80 {v} to i80',f'{e0} = lshr i80 {b}, 64',f'{e} = and i80 {e0}, 32767',f'{mm} = trunc i80 {b} to i64',f'{j} = lshr i64 {mm}, 63']
            if key=='ueq0':
                a,c1,d,x,y,xn,z,ze,zu,dt=(t() for _ in range(10))
                o+=[f'{a} = icmp eq i80 {e}, 0',f'{c1} = icmp eq i64 {mm}, 0',f'{d} = and i1 {a}, {c1}',f'{x} = icmp eq i80 {e}, 32767',f'{y} = icmp ne i64 {mm}, -9223372036854775808',f'{xn} = and i1 {x}, {y}',
                    f'{z} = icmp eq i64 {j}, 0',f'{ze} = icmp ne i80 {e}, 0',f'{zu} = and i1 {z}, {ze}',f'{dt} = or i1 {d}, {xn}',f'{lhs} = or i1 {dt}, {zu}']
            elif key=='inf':
                a,c1=t(),t();o+=[f'{a} = icmp eq i80 {e}, 32767',f'{c1} = icmp eq i64 {mm}, -9223372036854775808',f'{lhs} = and i1 {a}, {c1}']
            else:
                a,c1=t(),t();o+=[f'{a} = icmp eq i80 {e}, 0',f'{c1} = icmp eq i64 {j}, 0',f'{lhs} = and i1 {a}, {c1}']
        else:
            b,e0,e,mm=t(),t(),t(),t();o=[f'{b} = bitcast float {v} to i32',f'{e0} = lshr i32 {b}, 23',f'{e} = and i32 {e0}, 255',f'{mm} = and i32 {b}, 8388607']
            if key=='ueq0':
                a,c1,d,x,y,xn=(t() for _ in range(6));o+=[f'{a} = icmp eq i32 {e}, 0',f'{c1} = icmp eq i32 {mm}, 0',f'{d} = and i1 {a}, {c1}',f'{x} = icmp eq i32 {e}, 255',f'{y} = icmp ne i32 {mm}, 0',f'{xn} = and i1 {x}, {y}',f'{lhs} = or i1 {d}, {xn}']
            elif key=='inf':
                a,c1=t(),t();o+=[f'{a} = icmp eq i32 {e}, 255',f'{c1} = icmp eq i32 {mm}, 0',f'{lhs} = and i1 {a}, {c1}']
            else:o+=[f'{lhs} = icmp eq i32 {e}, 0']
        return '\n'.join('  '+x for x in o)
    return CLS.sub(rep,text)
def strict_x87(text,noexc=False):
    st=dict(classify_ueq0=0,classify_inf=0,classify_lt=0,constrained=0,fences=0,strict_applied=0,inline_clear=0,inline_test=0)
    if not FENCE.search(text):return text,st
    orig=text;text=_classify(text,st);decls=set()
    def arith(m):
        lhs,op,ty,a,b=m.groups();name=f'llvm.experimental.constrained.{op}.{FT[ty]}';decls.add(f'declare {ty} @{name}({ty}, {ty}, metadata, metadata)');st['constrained']+=1
        return f'{lhs} = call {ty} @{name}({ty} {a}, {ty} {b}, metadata !"round.dynamic", metadata !"fpexcept.strict") #997'
    def conv(m):
        lhs,op,ty,v,to=m.groups();st['constrained']+=1
        fa=lambda x:FT.get(x,x);name=f'llvm.experimental.constrained.{op}.{fa(to)}.{fa(ty)}'
        if op in('fpext','fptosi','fptoui'):decls.add(f'declare {to} @{name}({ty}, metadata)');return f'{lhs} = call {to} @{name}({ty} {v}, metadata !"fpexcept.strict") #997'
        decls.add(f'declare {to} @{name}({ty}, metadata, metadata)');return f'{lhs} = call {to} @{name}({ty} {v}, metadata !"round.dynamic", metadata !"fpexcept.strict") #997'
    def fcmp(m):
        lhs,p,ty,a,b=m.groups();name=f'llvm.experimental.constrained.fcmp.{FT[ty]}';decls.add(f'declare i1 @{name}({ty}, {ty}, metadata, metadata)');st['constrained']+=1
        return f'{lhs} = call i1 @{name}({ty} {a}, {ty} {b}, metadata !"{p}", metadata !"fpexcept.strict") #997'
    text=ARITH.sub(arith,text);text=CONV.sub(conv,text);text=FCMP.sub(fcmp,text)
    body=[l for l in text.split('\n') if not l.startswith('declare') and not l.startswith('define internal')]
    if any(LEFT.search(l) and 'constrained' not in l for l in body):return orig,dict(st,strict_applied=0,constrained=0,fences=0,classify_ueq0=0,classify_inf=0,classify_lt=0)
    text,st['fences']=FENCE.subn('',text)
    text=re.sub(r'^(define [^\n]*@mw34_attach_\w+_body\([^\n]*\)) uwtable',r'\1 uwtable strictfp',text,flags=re.M)
    groups=dict(re.findall(r'^attributes #(\d+) = \{ ([^}\n]*) \}$',text,re.M));added={}
    def cs(m):
        g=m.group(2).strip()
        if g=='#997':return m.group(0)
        if not g:return m.group(1)+' #998'
        n=g[1:]
        if n not in added:added[n]=str(2000+int(n))
        return m.group(1)+' #'+added[n]
    text=CALLSITE.sub(cs,text)
    extra=[f'attributes #{v} = {{ {groups[k]} strictfp }}' for k,v in added.items() if k in groups]
    text+='\n'+'\n'.join(sorted(decls)+extra+['attributes #997 = { strictfp }','attributes #998 = { strictfp }'])+'\n'
    st['inline_clear']=st['inline_test']=0;text=inline_x87_brackets(text,st)
    if noexc:text=x87_noexc(text,st)
    st['strict_applied']=1;return text,st

# 6. Inline x87 exception brackets (part of --strict-x87, only in converted bodies). __remill_fpu_exception_clear(127)
#    is `fnclex` and __remill_fpu_exception_test(127) is `fnstsw & 127` (composition.cpp). In a strictfp body they are
#    emitted as inline assembly whose only declared effect is the FP environment (inaccessible memory, like the
#    constrained operations they bracket), instead of out-of-line calls that cost a call and spill live x87 values.
#    Other masks keep the out-of-line bridge.
XCLR=re.compile(r'^  (?:tail )?call void @__remill_fpu_exception_clear\(i32 (?:noundef )?127\)(?: #\d+)?$',re.M)
XTST=re.compile(r'^  (%[\w.]+) = (?:tail )?call (?:noundef )?i32 @__remill_fpu_exception_test\(i32 (?:noundef )?127\)(?: #\d+)?$',re.M)
def inline_x87_brackets(text,st):
    k=[0]
    text,st['inline_clear']=XCLR.subn('  call void asm sideeffect "fnclex", "~{dirflag},~{fpsr},~{flags}"() #999',text)
    def tst(m):
        k[0]+=1;a,b=f'%mw34.sw{k[0]}',f'%mw34.sz{k[0]}'
        return (f'  {a} = call i16 asm sideeffect "fnstsw $0", "={{ax}},~{{dirflag}},~{{fpsr}},~{{flags}}"() #999\n'
                f'  {b} = zext i16 {a} to i32\n  {m.group(1)} = and i32 {b}, 127')
    text,st['inline_test']=XTST.subn(tst,text)
    if st['inline_clear'] or st['inline_test']:text+='\nattributes #999 = { nounwind strictfp memory(inaccessiblemem: readwrite) }\n'
    return text

# 7. No x87 exception tracking in the game's own code (--x87-noexc, with --strict-x87). Mech3.exe never reads the x87
#    exception flags: all 3,733 FNSTSW sites test only AH (C0/C2/C3: 0x41, 0x01, 0x40), and it has no FNSTENV, FNSAVE
#    or FNCLEX. So in game-image bodies (0x401000-0x5bb000) the exception brackets become nothing (test reads 0), the
#    stores to the exception bytes are removed, and constrained operations use fpexcept.ignore (still ordered against
#    rounding-mode changes). CRT and MFC bodies keep full tracking (the game calls CRT math that can call _matherr).
EXC_OFFS=tuple(range(2745,2758,2))
def x87_noexc(text,st):
    names=set(re.findall(r'^  (%[\w.]+) = getelementptr inbounds (?:nuw )?i8, ptr %state, i(?:32|64) ('+'|'.join(map(str,EXC_OFFS))+r')$',text,re.M) and
              [m.group(1) for m in re.finditer(r'^  (%[\w.]+) = getelementptr inbounds (?:nuw )?i8, ptr %state, i(?:32|64) (?:'+'|'.join(map(str,EXC_OFFS))+r')$',text,re.M)])
    st['exc_stores']=0
    def rs(m):
        if m.group(1) in names:st['exc_stores']+=1;return ''
        return m.group(0)
    text=re.sub(r'^  store i8 [^,\n]+, ptr (%[\w.]+)(?:, align \d+)?\n',rs,text,flags=re.M)
    text,st['noexc_clear']=re.subn(r'^  call void asm sideeffect "fnclex", "~\{dirflag\},~\{fpsr\},~\{flags\}"\(\) #999\n','',text,flags=re.M)
    text,st['noexc_test']=re.subn(r'^  (%mw34\.sw\d+) = call i16 asm sideeffect "fnstsw \$0", "=\{ax\},~\{dirflag\},~\{fpsr\},~\{flags\}"\(\) #999$',r'  \1 = or i16 0, 0',text,flags=re.M)
    text=text.replace('metadata !"fpexcept.strict"','metadata !"fpexcept.ignore"')
    return text

# 8. Flat guest memory (--flat-mem; host memory/guest_memory.hpp fork). The memory token recompiled code passes around
#    is the flat base of the guest address space, so a guest load/store is base + zero-extended address. Each
#    __remill_read/write_memory_{8,16,32,64,f32,f64} call becomes an unaligned load/store through the token (a write's
#    returned token is the token itself). Unmapped or protected pages fault in hardware; the Stage turns such a fault
#    into its typed deny. Guest code then sees what the original saw on Windows: page-level protection only.
FLAT_TY={'8':'i8','16':'i16','32':'i32','64':'i64','f32':'float','f64':'double'}
FLAT_RD=re.compile(r'^  (%[\w.]+) = (?:tail |notail )?call (?:noundef )?(?:zeroext )?(?:i8|i16|i32|i64|float|double) @__remill_read_memory_(8|16|32|64|f32|f64)\(ptr (?:noundef )?(%[\w.]+), i32 (?:noundef )?(%[\w.]+|-?\d+)\)(?: #\d+)?$',re.M)
FLAT_WR=re.compile(r'^  (%[\w.]+) = (?:tail |notail )?call (?:noundef )?ptr @__remill_write_memory_(8|16|32|64|f32|f64)\(ptr (?:noundef )?(%[\w.]+), i32 (?:noundef )?(%[\w.]+|-?\d+), (?:i8|i16|i32|i64|float|double) (?:noundef )?(?:zeroext )?(%[\w.]+|-?[\w.+]+)\)(?: #\d+)?$',re.M)
def flat_mem(text,st):
    k=[0]
    def addr(m,a):
        k[0]+=1;z,g=f'%mw34.fz{k[0]}',f'%mw34.fg{k[0]}'
        return z,g,(f'  {z} = zext i32 {a} to i64\n  {g} = getelementptr i8, ptr {m}, i64 {z}\n')
    def rd(mt):
        lhs,w,m,a=mt.groups();z,g,pre=addr(m,a);return pre+f'  {lhs} = load {FLAT_TY[w]}, ptr {g}, align 1'
    def wr(mt):
        lhs,w,m,a,v=mt.groups();z,g,pre=addr(m,a);return pre+f'  store {FLAT_TY[w]} {v}, ptr {g}, align 1\n  {lhs} = getelementptr i8, ptr {m}, i64 0'
    text,st['flat_reads']=FLAT_RD.subn(rd,text);text,st['flat_writes']=FLAT_WR.subn(wr,text)
    left=len(re.findall(r'call [^\n]*@__remill_(?:read|write)_memory_(?:8|16|32|64|f32|f64)\(',text));st['flat_left']=left
    return text
