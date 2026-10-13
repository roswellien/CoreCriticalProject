"""Guest-IR rewrite for remill's x87 library calls (lift_closure.py lowering hook).

remill expresses FSQRT/FSIN/FCOS/FPTAN/FPATAN/FYL2X/F2XM1/FRNDINT as calls to sqrtl/sinl/cosl/tanl/
atanl/log2l/exp2l/llvm.nearbyint.f80 on x86_fp80. A Windows x64 host has no 80-bit long double
library, so each call becomes a raw-80-bit bridge that executes the literal host x87 instruction
(the contract of tools/m4-onexit-native fsqrt_raw80): the operand and result are 10-byte values in
entry-block buffers of the enclosing function. Fidelity limits (remill's decomposition, kept as is):
FYL2X arrives as log2l(x) then a separate multiply by y, and F2XM1 as exp2l(x) then -1.0, so those
two keep one extra rounding versus the single x87 instruction. FPREM arrives as fmodl(st0, st1) (the full
remainder); its bridge runs the host FPREM until C2 clears, which yields exactly that remainder.
FPATAN arrives as atanl(st1/st0), which loses the quadrant (x87 FPATAN is the two-argument arctangent: st0 < 0
adds +-pi). Its atanl operand is the fdiv of st1 by st0 (remill's checked division, kept for its exception
flags); the bridge takes those two operands and executes the host FPATAN on them. An atanl whose operand is not
such an fdiv fails the lift rather than produce a wrong angle.
remill models MMX/x87 register aliasing with __remill_undefined_64 (the MMX view after an x87 write) and
__remill_undefined_f80 (the x87 view after an MMX write). They take the same zero representative the stage gives
undefined flags. Hardware aliasing is deterministic (exponent 0xFFFF over the MMX value); code that executes EMMS
before switching units, as the Indeo codec does, never consumes either value.
"""
import re
BRIDGES={'mw34_x87_'+x+'_raw80' for x in ('fsqrt','fsin','fcos','ftan','fatan','flog2','fexp2','frndint','ftrunc','fprem','fpatan')}
CALLS={'sqrtl':'fsqrt','sinl':'fsin','cosl':'fcos','tanl':'ftan','atanl':'fatan','log2l':'flog2','exp2l':'fexp2','llvm.nearbyint.f80':'frndint','llvm.trunc.f80':'ftrunc'}
CALL=re.compile(r'^  (%[\w.]+) = (?:tail )?call x86_fp80 @(sqrtl|sinl|cosl|tanl|atanl|log2l|exp2l|llvm\.nearbyint\.f80|llvm\.trunc\.f80)\(x86_fp80 (?:noundef )?(%[\w.]+|0xK[0-9A-F]+)\)(?: #\d+)?$')
VAL=r'(%[\w.]+|0xK[0-9A-F]+)'
CALL2=re.compile(r'^  (%[\w.]+) = (?:tail )?call x86_fp80 @fmodl\(x86_fp80 (?:noundef )?'+VAL+r', x86_fp80 (?:noundef )?'+VAL+r'\)(?: #\d+)?$')
FDIV=re.compile(r'^  (%[\w.]+) = fdiv x86_fp80 '+VAL+r', '+VAL+r'$')
UNDEF=re.compile(r'^  (%[\w.]+) = (?:tail )?call (i64|x86_fp80) @__remill_undefined_(64|f80)\(\)(?: #\d+)?$')
UNDEF_SRET=re.compile(r'^  call void @__remill_undefined_f80\(ptr .*\s(%[\w.]+)\)(?: #\d+)?$')
def rewrite(text):
    lines=text.split('\n');out=[];k=0;used=set();func_start=None;pending=[];undef=False
    # fdiv definitions per function (SSA names are function-local)
    fdivs=[];cur=None
    for line in lines:
        if line.startswith('define '):cur={};fdivs.append(cur)
        elif cur is not None:
            m3=FDIV.match(line)
            if m3:cur[m3.group(1)]=(m3.group(2),m3.group(3))
    fn=-1
    def flush():
        nonlocal pending
        if pending and func_start is not None:
            # entry block starts on the first line after `define ... {` (after its label, if any)
            at=func_start+1
            if re.match(r'^[\w.]+:',out[at] if at<len(out) else ''):at+=1
            out[at:at]=pending
        pending=[]
    for line in lines:
        if line.startswith('define '):flush();func_start=len(out);out.append(line);fn+=1;continue
        if line=='}':flush();func_start=None;out.append(line);continue
        ms=UNDEF_SRET.match(line)
        if ms:
            undef=True;out.append(f'  store i80 0, ptr {ms.group(1)}, align 1');continue
        mu=UNDEF.match(line)
        if mu:
            undef=True;res,ty,_=mu.groups()
            out.append(f'  {res} = add i64 0, 0' if ty=='i64' else f'  {res} = bitcast i80 0 to x86_fp80');continue
        m2=CALL2.match(line)
        if m2:
            res,a,b=m2.groups();used.add('fprem')
            pending+=[f'  %x87.in.{k} = alloca x86_fp80, align 16',f'  %x87.in2.{k} = alloca x86_fp80, align 16',f'  %x87.out.{k} = alloca x86_fp80, align 16']
            out+=[f'  store x86_fp80 {a}, ptr %x87.in.{k}, align 16',f'  store x86_fp80 {b}, ptr %x87.in2.{k}, align 16',f'  call void @mw34_x87_fprem_raw80(ptr %x87.in.{k}, ptr %x87.in2.{k}, ptr %x87.out.{k})',f'  {res} = load x86_fp80, ptr %x87.out.{k}, align 16']
            k+=1;continue
        m=CALL.match(line)
        if m and m.group(2)=='atanl':
            res,_,val=m.groups()
            if fn<0 or val not in fdivs[fn]:raise ValueError('FPATAN atanl operand is not the fdiv of st1 by st0: '+val)
            y,x=fdivs[fn][val];used.add('fpatan')
            pending+=[f'  %x87.in.{k} = alloca x86_fp80, align 16',f'  %x87.in2.{k} = alloca x86_fp80, align 16',f'  %x87.out.{k} = alloca x86_fp80, align 16']
            out+=[f'  store x86_fp80 {y}, ptr %x87.in.{k}, align 16',f'  store x86_fp80 {x}, ptr %x87.in2.{k}, align 16',f'  call void @mw34_x87_fpatan_raw80(ptr %x87.in.{k}, ptr %x87.in2.{k}, ptr %x87.out.{k})',f'  {res} = load x86_fp80, ptr %x87.out.{k}, align 16']
            k+=1;continue
        if m:
            res,name,val=m.groups();op=CALLS[name];used.add(op)
            pending+=[f'  %x87.in.{k} = alloca x86_fp80, align 16',f'  %x87.out.{k} = alloca x86_fp80, align 16']
            out+=[f'  store x86_fp80 {val}, ptr %x87.in.{k}, align 16',f'  call void @mw34_x87_{op}_raw80(ptr %x87.in.{k}, ptr %x87.out.{k})',f'  {res} = load x86_fp80, ptr %x87.out.{k}, align 16']
            k+=1;continue
        out.append(line)
    flush()
    text='\n'.join(out)
    for name in CALLS:
        if any(CALLS[name]==op for op in used):text=re.sub(r'^declare [^\n]*@'+re.escape(name)+r'\([^\n]*\n','',text,flags=re.M)
    if undef:text=re.sub(r'^declare [^\n]*@__remill_undefined_(?:64|f80)\([^\n]*\n','',text,flags=re.M)
    if 'fprem' in used:text=re.sub(r'^declare [^\n]*@fmodl\([^\n]*\n','',text,flags=re.M)
    if 'fpatan' in used:text=re.sub(r'^declare [^\n]*@atanl\([^\n]*\n','',text,flags=re.M)
    if used:text+='\n'+'\n'.join(f'declare void @mw34_x87_{op}_raw80(ptr, ptr, ptr)' if op in ('fprem','fpatan') else f'declare void @mw34_x87_{op}_raw80(ptr, ptr)' for op in sorted(used))+'\n'
    return text,k
