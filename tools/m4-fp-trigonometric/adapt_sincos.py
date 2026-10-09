"""One exact FSIN/FCOS startup lift, strict FP and normal raw80 pointer ABI.

This baseline lowers sincosl to an actual compiled FSIN/FCOS primitive. It leaves the
lift's status bookkeeping unchanged so defects remain measurable. No original
bytes, expected results, full-state admission or service implementation here.
"""
from pathlib import Path
import ctypes as c
import json
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-fp-native'))
from adapt_first import FPTypes,HOST_LAYOUT,FUNCTION_INDEX,digest,require

ROOTS={'4c78f0':'776c67e472424e7bdc6175abe66d87165f41818f4b5b55d5dbe986fb8dea1a63'}
BRIDGES={'__remill_read_memory_f64':('double',['ptr','i32']),
 '__remill_write_memory_f32':('ptr',['ptr','i32','float']),
 '__remill_read_memory_32':('i32',['ptr','i32']),
 '__remill_function_return':('ptr',['ptr','i32','ptr']),
 '__remill_fpu_exception_clear':('void',['i32']),
 '__remill_fpu_exception_test':('i32',['i32']),
 'mw34_actual_fcos_raw80':('void',['ptr','ptr']),
 'mw34_actual_fsin_raw80':('void',['ptr','ptr']),
 '__remill_read_memory_f32':('float',['ptr','i32']),
 '__remill_write_memory_32':('ptr',['ptr','i32','i32'])}
COUNTS={name:1 for name in BRIDGES}
COUNTS.update(__remill_fpu_exception_clear=6,__remill_fpu_exception_test=6,__remill_read_memory_f64=1,__remill_write_memory_f32=3,__remill_read_memory_f32=2)

def candidate(guest,host):
    stem=guest.stem
    require(stem in ROOTS and digest(guest)==ROOTS[stem],'Exact complete sincos lift required')
    require(not host.exists(),'Fresh host candidate required')
    source=guest.read_text()
    transformed=source
    rules=[(r'^(  %\d+) = fptrunc x86_fp80 (%\d+) to float$',
      r'\1 = call float @llvm.experimental.constrained.fptrunc.f32.f80(x86_fp80 \2, metadata !"round.dynamic", metadata !"fpexcept.strict")',
      'declare float @llvm.experimental.constrained.fptrunc.f32.f80(x86_fp80, metadata, metadata)',3),
     (r'^(  %\d+) = fpext double (%\d+) to x86_fp80$',
      r'\1 = call x86_fp80 @llvm.experimental.constrained.fpext.f80.f64(double \2, metadata !"fpexcept.strict")',
      'declare x86_fp80 @llvm.experimental.constrained.fpext.f80.f64(double, metadata)',1),
     (r'^(  %\d+) = fpext float (%\d+) to x86_fp80$',
      r'\1 = call x86_fp80 @llvm.experimental.constrained.fpext.f80.f32(float \2, metadata !"fpexcept.strict")',
      'declare x86_fp80 @llvm.experimental.constrained.fpext.f80.f32(float, metadata)',2),
     (r'^(  %\d+) = fmul x86_fp80 (%\d+), (%\d+)$',
      r'\1 = call x86_fp80 @llvm.experimental.constrained.fmul.f80(x86_fp80 \2, x86_fp80 \3, metadata !"round.dynamic", metadata !"fpexcept.strict")',
      'declare x86_fp80 @llvm.experimental.constrained.fmul.f80(x86_fp80, x86_fp80, metadata, metadata)',1)]
    for pattern,replacement,declaration,count in rules:
        transformed,actual=re.subn(pattern,replacement,transformed,flags=re.M)
        require(actual==count,'Exact strict FP count differs')
        transformed+='\n'+declaration+'\n'
    # An x86_fp80 C return would use a different ABI from MSVC long double.
    # The actual instruction receives and produces exactly ten owned bytes.
    for operation in ('cos','sin'):
        pattern=r'^  (%\d+) = call x86_fp80 @'+operation+r'l\(x86_fp80 noundef (%\d+)\) #\d+$'
        def lower(match):
            result,value=match.groups();prefix='%mw.'+operation
            return (f'  {prefix}.input = alloca x86_fp80, align 16\n  {prefix}.output = alloca x86_fp80, align 16\n'
              f'  store x86_fp80 {value}, ptr {prefix}.input, align 16\n'
              f'  call void @mw34_actual_f{operation}_raw80(ptr {prefix}.input, ptr {prefix}.output)\n'
              f'  {result} = load x86_fp80, ptr {prefix}.output, align 16')
        transformed,count=re.subn(pattern,lower,transformed,flags=re.M);require(count==1,'Exactly one '+operation+' boundary required')
        transformed,count=re.subn(r'^declare dso_local x86_fp80 @'+operation+r'l\([^\n]+\n','',transformed,flags=re.M);require(count==1,'Exactly one old declaration required')
        transformed+='\ndeclare void @mw34_actual_f'+operation+'_raw80(ptr, ptr)\n'
    transformed=transformed.replace('ptr noalias %memory) {','ptr noalias %memory) strictfp {',1)
    strict=host.with_suffix('.strict-input.ll');require(not strict.exists(),'Fresh strict IR required');strict.write_text(transformed)
    dll=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll'
    require(digest(dll)=='34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb','Reviewed LLVM DLL required')
    api=FPTypes(dll);context=api.ContextCreate();module=c.c_void_p();buffer=c.c_void_p();error=c.c_void_p()
    gd=hd=builder=None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(strict).encode(),c.byref(buffer),c.byref(error)),error)
        api.check(api.ParseIRInContext(context,buffer,c.byref(module),c.byref(error)),error)
        api.check(api.VerifyModule(module,2,c.byref(error)),error)
        gd=api.CreateTargetData(api.GetDataLayoutStr(module));hd=api.CreateTargetData(HOST_LAYOUT.encode());layouts={}
        require(api.PointerSize(gd)==4 and api.PointerSize(hd)==8,'Pointer widths differ')
        for name in re.findall(r'^%([^ =]+) = type',source,re.M):
            typ=api.GetTypeByName2(context,name.encode())
            def layout(data):
                return {'size':api.ABISizeOfType(data,typ),'alignment':api.ABIAlignmentOfType(data,typ),
                  'offsets':[api.OffsetOfElement(data,typ,i) for i in range(api.CountStructElementTypes(typ))]}
            before,after=layout(gd),layout(hd);require(before==after,'Changed State layout '+name);layouts[name]=before
        require(layouts['struct.State']['size']==3504,'Full State extent differs')
        entry=api.GetNamedFunction(module,('sub_'+stem).encode());require(api.signature(entry)==('ptr',['ptr','i32','ptr']),'Entry ABI differs')
        counts={name:0 for name in BRIDGES};nounwind=api.GetEnumAttributeKindForName(b'nounwind',8)
        for function in api.iterate(api.GetFirstFunction(module),api.GetNextFunction):
            name=api.name(function)
            if not api.CountBasicBlocks(function) and api.GetFirstUse(function) and not name.startswith('llvm.'):
                require(name in BRIDGES and api.signature(function)==BRIDGES[name] and
                  not api.IsFunctionVarArg(api.GlobalGetValueType(function)),'Unreviewed external boundary '+name)
                api.SetFunctionCallConv(function,0)
            for attribute in (b'target-cpu',b'target-features',b'no-trapping-math'):
                api.RemoveStringAttributeAtIndex(function,FUNCTION_INDEX,attribute,len(attribute))
            api.RemoveEnumAttributeAtIndex(function,FUNCTION_INDEX,nounwind)
            for block in api.iterate(api.GetFirstBasicBlock(function),api.GetNextBasicBlock):
                for inst in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
                    require(not api.IsAIntToPtrInst(inst) and not api.IsAPtrToIntInst(inst),'Unreviewed pointer/integer cast')
                    if api.IsACallInst(inst):
                        called=api.GetCalledValue(inst)
                        if api.IsAFunction(called):
                            name=api.name(called)
                            if name in BRIDGES:counts[name]+=1;api.SetInstructionCallConv(inst,0)
                        api.RemoveCallSiteEnumAttribute(inst,FUNCTION_INDEX,nounwind)
        require(counts==COUNTS,'Exact bridge counts differ')
        api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode())
        builder=api.CreateBuilderInContext(context);wrapper=api.AddFunction(module,('mw34_fp_entry_'+stem).encode(),api.GlobalGetValueType(entry))
        block=api.AppendBasicBlockInContext(context,wrapper,b'entry');api.PositionBuilderAtEnd(builder,block)
        params=(c.c_void_p*3)(*(api.GetParam(wrapper,i) for i in range(3)))
        result=api.BuildCall2(builder,api.GlobalGetValueType(entry),entry,params,3,b'memory');api.BuildRet(builder,result)
        api.check(api.VerifyModule(module,2,c.byref(error)),error)
        api.check(api.PrintModuleToFile(module,str(host).encode(),c.byref(error)),error)
        return {'entry':int(stem,16),'guest_sha256':digest(guest),'strict_sha256':digest(strict),'host_sha256':digest(host),
          'all_layouts_equal':True,'layouts':layouts,'normal_raw80_pointer_boundary':True,'bridge_calls':counts,
          'status_repairs':False,'native_admitted':False,'llvm_DLL_sha256':digest(dll)}
    finally:
        if builder:api.DisposeBuilder(builder)
        for data in (gd,hd):
            if data:api.DisposeTargetData(data)
        if module.value:api.DisposeModule(module)
        api.ContextDispose(context)

def main():
    directory=Path(sys.argv[1]).resolve()
    require(directory.is_relative_to(ROOT/'reports/m4-fp-trigonometric') and not directory.exists(),'Fresh private candidate directory required')
    directory.mkdir(parents=True)
    records=[candidate(ROOT/'reports/m4-fp-native/lift-r1'/f'{stem}.ll',directory/f'{stem}.ll') for stem in ROOTS]
    bindings={str(path):digest(path) for path in directory.iterdir()}
    for path in [Path(__file__).resolve(),ROOT/'tools/m4-fp-native/adapt_first.py',ROOT/'tools/lifting/host_adapter.py']:
        bindings[str(path)]=digest(path)
    report={'passed':True,'scope':'Static four-sincos native candidates only; numerical primitive replaces external ABI; status unchanged',
      'records':records,'bindings':bindings}
    (directory/'adapter.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'candidates':len(records),'native_admitted':False}))

if __name__=='__main__':main()
