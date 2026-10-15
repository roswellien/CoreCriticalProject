"""Merge per-instruction x87 exception brackets across straight-line runs in lifted host IR.

remill brackets every x87 operation as
    __remill_fpu_exception_clear(127); <op>; %T = __remill_fpu_exception_test(127)
followed by seven sticky updates of the guest status-word exception bytes (State offsets 2745..2757, step 2):
    load byte; or (bit k of %T); store byte.
Host x87 exception flags are sticky like the guest bytes, so for a run of consecutive brackets in one basic
block (after simplifycfg) the union of every operation's flags can be read once: the first bracket keeps its
clear, the later brackets lose theirs, every bracket except the last reads constant 0 instead of the status word
(its sticky updates then store back the loaded values and are removed by the O2 pipeline), and the last bracket
reads the real status word and ORs the union in.

A run ends (the next bracket starts a new run with its own clear) at
  - a bracket whose test result has any use outside its own sticky-update region, or a mask other than 127;
  - any call other than the remill memory bridges, llvm intrinsics, remill's empty FP ordering barrier, remill's
    pure undefined-value helpers, and remill flag/compare helpers that this module defines as the identity
    (`__remill_flag_computation_*`, `__remill_compare_*`: `ret i1 %0`);
  - any load of an exception byte, or a store to one other than an assignment directly before a clear
    (remill assigns the denormal flag from the operands just before some brackets); a guest FCLEX or FNSTSW
    therefore always ends a run;
  - a basic-block boundary.
Within a run, flags of earlier operations stay set in the guest bytes (the hardware's sticky behaviour) where
remill's per-instruction denormal assignment would otherwise have reset them.
"""
import re,sys

FLAG_OFFS={str(o) for o in range(2745,2758,2)}
GEP=re.compile(r'^\s*(%[\w.]+) = getelementptr inbounds nuw i8, ptr %state, i32 (\d+)\s*$')
CLEAR=re.compile(r'^\s*call void @__remill_fpu_exception_clear\(i32 noundef (\d+|%[\w.]+)\)')
TEST=re.compile(r'^(\s*)(%[\w.]+) = call i32 @__remill_fpu_exception_test\(i32 noundef (\d+|%[\w.]+)\)')
LABEL=re.compile(r'^[\w.$\-]+:|^\d+:')
CALL=re.compile(r'\bcall\b')
OK_CALL=re.compile(r'call [^@]*@(__remill_read_memory_|__remill_write_memory_|llvm\.|mw34_\w+_undefined_\d+\(|__remill_undefined_)|call void asm sideeffect "", "~\{memory\},~\{dirflag\},~\{fpsr\},~\{flags\}"\(\)')
LOAD=re.compile(r'= load i8, ptr (%[\w.]+)')
STORE=re.compile(r'store i8 (%[\w.]+|-?\d+), ptr (%[\w.]+)')
REGION=re.compile(r'^\s*(%[\w.]+) = (getelementptr inbounds nuw i8, ptr %state, i32 (\d+)|load i8, ptr (%[\w.]+)(?:, align \d+)?|trunc i32 (%[\w.]+) to i8|(lshr|and|or) i8 .*)\s*$')

def uses(name,line):
    return re.search(re.escape(name)+r'\b',line) is not None

IDENT_DEF=re.compile(r'^define internal zeroext i1 @(__remill_(?:flag_computation|compare)_\w+)\(i1 noundef zeroext %0(?:, \.\.\.)?\)')
def transform(text):
    lines=text.split('\n')
    # remill flag/compare helpers defined in this module as the identity (body: a label line then `ret i1 %0`)
    identity=set()
    for q,l in enumerate(lines):
        m=IDENT_DEF.match(l)
        if m and q+3<len(lines):
            body=[x.strip() for x in lines[q+1:q+4]]
            if body[1]=='ret i1 %0' and body[2]=='}' and body[0].endswith(':'):identity.add(m.group(1))
    flagptr=set();flagoff={}
    for l in lines:
        m=GEP.match(l)
        if m and m.group(2) in FLAG_OFFS:flagptr.add(m.group(1));flagoff[m.group(1)]=m.group(2)
    # occurrence counts of every SSA name, for the "test used only in its region" check
    import collections
    TOK=re.compile(r'%[\w.]+\b')
    occ=collections.Counter(tok for l in lines for tok in TOK.findall(l))
    brackets=[]  # dicts: clear_idx, test_idx, test_name, region_end, mergeable
    n=len(lines);i=0
    while i<n:
        m=CLEAR.match(lines[i])
        if m:
            j=i+1
            while j<n and not TEST.match(lines[j]) and not CLEAR.match(lines[j]) and not LABEL.match(lines[j]):j+=1
            if j<n and TEST.match(lines[j]):
                t=TEST.match(lines[j]);name=t.group(2)
                k=j+1;names={name};stores=set();ok=True
                while k<n:
                    r=REGION.match(lines[k]);s=STORE.match(lines[k].strip())
                    if r:
                        if r.group(3) and r.group(3) not in FLAG_OFFS:break
                        if r.group(4) and r.group(4) not in flagptr:break
                        names.add(r.group(1));k+=1;continue
                    if s and s.group(2) in flagptr and (s.group(1) in names):
                        stores.add(s.group(2));k+=1;continue
                    break
                region=set(range(j+1,k))
                # the test result must not be used outside its region
                inside=sum(1 for q in range(j,k) for tok in TOK.findall(lines[q]) if tok==name)
                outside=occ[name]>inside
                mergeable=(m.group(1)=='127' and t.group(3)=='127' and len(stores)==7 and not outside)
                brackets.append(dict(clear=i,test=j,name=name,end=k,mergeable=mergeable,indent=t.group(1)))
                i=k;continue
        i+=1
    # basic blocks: a label line starts a block (the function entry block is unnamed); successors from terminators
    block_of=[None]*n;starts=[];cur_name=None;func=-1;func_of=[None]*n
    for q,l in enumerate(lines):
        if l.startswith('define '):func+=1;cur_name='%d:<entry>'%func;starts.append((cur_name,q+1))
        elif LABEL.match(l) and func>=0:cur_name='%d:%s'%(func,re.match(r'^([\w.$\-]+):',l).group(1));starts.append((cur_name,q))
        elif l.startswith('}'):cur_name=None
        block_of[q]=cur_name;func_of[q]=func
    span={};order=[nm for nm,_ in starts]
    for idx,(nm,st) in enumerate(starts):
        en=st
        while en<n and block_of[en]==nm:en+=1
        span[nm]=(st,en)
    succ={};pred=collections.defaultdict(set)
    for nm,(st,en) in span.items():
        term=''
        for q in range(en-1,st-1,-1):
            if lines[q].strip() and not lines[q].strip().startswith(';'):term=lines[q];break
        fn=nm.split(':',1)[0]
        targets=['%s:%s'%(fn,t) for t in re.findall(r'label %([\w.$\-]+)',term)] if re.match(r'\s*(br|switch|indirectbr)\b',term) else []
        succ[nm]=set(targets)
        for t in targets:pred[t].add(nm)
    def region_ok(A,B):
        # every path from A reaches B without leaving the region, no cycle back to A, single entry from A
        R=set();todo=list(succ.get(A,()))
        while todo:
            x=todo.pop()
            if x==B or x in R:continue
            if x==A:return None
            R.add(x);todo.extend(succ.get(x,()))
            if len(R)>64:return None
        if not succ.get(A):return None
        for x in R:
            if not succ.get(x):return None
            if not succ[x]<=R|{B}:return None
        for x in R|{B}:
            if not pred[x]<=R|{A}:return None
        if B not in set().union(*[succ[x] for x in R|{A}]):return None
        return R
    def call_ok(l):
        if OK_CALL.search(l):return True
        m=re.search(r'call [^@]*@(__remill_(?:flag_computation|compare)_\w+)\(',l)
        return bool(m and m.group(1) in identity)
    def line_ok(q,b):
        l=lines[q]
        if CALL.search(l) and not call_ok(l):return False
        lm=LOAD.search(l)
        if lm and lm.group(1) in flagptr:return False
        sm=STORE.search(l)
        if sm and sm.group(2) in flagptr:
            # only remill's denormal-flag assignment: one store to the DE byte (2753) directly before the next clear
            if block_of[q]!=block_of[b['clear']] or flagoff.get(sm.group(2))!='2753':return False
            for q2 in range(q+1,b['clear']):
                if lines[q2].strip():return False
        return True
    # decide runs: consecutive mergeable brackets with a clean gap
    def clean_gap(a,b):
        A=block_of[a['end']-1];B=block_of[b['clear']]
        if A!=B:
            R=region_ok(A,B)
            if R is None:return False
            check=list(range(a['end'],span[A][1]))+[q for x in R for q in range(*span[x])]+list(range(span[B][0],b['clear']))
            return all(LABEL.match(lines[q]) or line_ok(q,b) for q in check)
        for q in range(a['end'],b['clear']):
            l=lines[q]
            if LABEL.match(l):return False
            if not line_ok(q,b):return False
        return True
    def unused_old_gap(a,b):
        for q in range(a['end'],b['clear']):
            l=lines[q]
            if LABEL.match(l):return False
            if CALL.search(l) and not OK_CALL.search(l):return False
            lm=LOAD.search(l)
            if lm and lm.group(1) in flagptr:return False
            sm=STORE.search(l)
            if sm and sm.group(2) in flagptr:
                # an assignment directly before the next clear (only GEPs/stores to flag bytes in between)
                for q2 in range(q+1,b['clear']):
                    l2=lines[q2].strip()
                    if not (GEP.match(lines[q2]) or (STORE.search(l2) and STORE.search(l2).group(2) in flagptr) or l2==''):return False
        return True
    merged=0;runs=0;cur=[]
    def flush():
        nonlocal merged,runs
        if len(cur)>=2:
            runs+=1
            for b in cur[:-1]:
                lines[b['test']]=b['indent']+b['name']+' = add i32 0, 0  ; mw34 merged x87 run: union read by the last bracket'
            for b in cur[1:]:
                lines[b['clear']]='  ; mw34 merged x87 run: clear elided (sticky flags accumulate)'
                merged+=1
        cur.clear()
    for b in brackets:
        if not b['mergeable']:
            flush();continue
        if cur and clean_gap(cur[-1],b):cur.append(b)
        else:
            flush();cur.append(b)
    flush()
    return '\n'.join(lines),dict(brackets=len(brackets),mergeable=sum(b['mergeable'] for b in brackets),runs=runs,merged=merged)

if __name__=='__main__':
    t,stats=transform(open(sys.argv[1]).read())
    open(sys.argv[2],'w').write(t);print(stats)
