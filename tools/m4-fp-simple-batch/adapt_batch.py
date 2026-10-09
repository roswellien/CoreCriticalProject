"""Strict static host candidate for the exact first required FP initializer.

Retargets checked LLVM types/ABI and preserves dynamic FP operations. It does
not repair FP values/status or grant native execution/equivalence admission.
"""
from pathlib import Path
import ctypes as c
import json
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lifting'))
from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,digest

SHA=None;ENTRY=None;COUNTS=None
BRIDGES={'__remill_read_memory_f32':('float',['ptr','i32']),
         '__remill_write_memory_f32':('ptr',['ptr','i32','float']),
         '__remill_read_memory_32':('i32',['ptr','i32']),
         '__remill_function_return':('ptr',['ptr','i32','ptr']),
         '__remill_fpu_exception_clear':('void',['i32']),
         '__remill_fpu_exception_test':('i32',['i32'])}


def require(ok,why):
    if not ok:raise ValueError(why)
class FPTypes(LLVM):
    def type_name(self,typ):
        kind=self.GetTypeKind(typ)
        if kind in (0,2,3,4,14):return {0:'void',2:'float',3:'double',4:'x86_fp80',14:'metadata'}[kind]
        if kind==8:return 'i'+str(self.GetIntTypeWidth(typ))
        if kind==12:return 'ptr'
        raise ValueError('Unsupported boundary type')
    def signature(self,function):
        return (self.type_name(self.GetReturnType(self.GlobalGetValueType(function))),
                [self.type_name(self.TypeOf(self.GetParam(function,i))) for i in range(self.CountParams(function))])

def main():
    global SHA,ENTRY,COUNTS
    guest,host,record=map(lambda p:Path(p).resolve(),sys.argv[1:4])
    config={'4b5af0': {'SHA': '171689e19976ae891fe32c4b3d3b6296bb3187177da87d29084f65af5ec04728', 'entry': 4938480, 'counts': {'__remill_write_memory_f32': 1, '__remill_read_memory_f32': 2, '__remill_fpu_exception_test': 2, '__remill_function_return': 1, '__remill_fpu_exception_clear': 2, '__remill_read_memory_32': 1}}, '4c79d0': {'SHA': '15224837aa4a57542eeab28203dda495abea931447ae7fc437b8c61d6627ee59', 'entry': 5011920, 'counts': {'__remill_write_memory_f32': 1, '__remill_fpu_exception_test': 1, '__remill_function_return': 1, '__remill_fpu_exception_clear': 1, '__remill_read_memory_32': 2}}}[guest.stem];SHA=config['SHA'];ENTRY=config['entry'];COUNTS={name:config['counts'].get(name,0) for name in BRIDGES}
    require(digest(guest)==SHA,'Exact FP guest IR required')
    require(guest.is_relative_to(ROOT/'reports/m4-fp-native/lift-r1') and all(p.is_relative_to(ROOT/'reports/m4-fp-simple-batch') for p in (host,record)), 'Exact guest/private outputs required')
    require(not host.exists() and not record.exists(),'Fresh candidate output required')
    source=guest.read_text();transformed=source
    rules=[(r'^(  %\d+) = fmul x86_fp80 (%\d+), (%\d+)$',
            r'\1 = call x86_fp80 @llvm.experimental.constrained.fmul.f80(x86_fp80 \2, x86_fp80 \3, metadata !"round.dynamic", metadata !"fpexcept.strict")',
            'declare x86_fp80 @llvm.experimental.constrained.fmul.f80(x86_fp80, x86_fp80, metadata, metadata)',1),
           (r'^(  %\d+) = fptrunc x86_fp80 (%\d+) to float$',
            r'\1 = call float @llvm.experimental.constrained.fptrunc.f32.f80(x86_fp80 \2, metadata !"round.dynamic", metadata !"fpexcept.strict")',
            'declare float @llvm.experimental.constrained.fptrunc.f32.f80(x86_fp80, metadata, metadata)',1),
           (r'^(  %\d+) = fpext float (%\d+) to x86_fp80$',
            r'\1 = call x86_fp80 @llvm.experimental.constrained.fpext.f80.f32(float \2, metadata !"fpexcept.strict")',
            'declare x86_fp80 @llvm.experimental.constrained.fpext.f80.f32(float, metadata)',2)]
    if ENTRY==0x4c79d0:
        rules=[rules[1],(r'^(  %\d+) = sitofp i32 (%\d+) to x86_fp80$', r'\1 = call x86_fp80 @llvm.experimental.constrained.sitofp.f80.i32(i32 \2, metadata !"round.dynamic", metadata !"fpexcept.strict")', 'declare x86_fp80 @llvm.experimental.constrained.sitofp.f80.i32(i32, metadata, metadata)',1)]
    for pattern,replacement,declaration,count in rules:
        transformed,actual=re.subn(pattern,replacement,transformed,flags=re.M)
        require(actual==count,'Exact strict FP operation count differs')
        transformed+='\n'+declaration+'\n'
    transformed=transformed.replace('ptr noalias %memory) {','ptr noalias %memory) strictfp {',1)
    strict=host.with_suffix('.strict-input.ll');require(not strict.exists(),'Fresh strict source required');strict.write_text(transformed)
    dll=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll'
    require(digest(dll)=='34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb','Reviewed LLVM DLL required')
    api=FPTypes(dll);context=api.ContextCreate();module=c.c_void_p();buffer=c.c_void_p();error=c.c_void_p()
    gd=hd=builder=None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(strict).encode(),c.byref(buffer),c.byref(error)),error)
        api.check(api.ParseIRInContext(context,buffer,c.byref(module),c.byref(error)),error)
        api.check(api.VerifyModule(module,2,c.byref(error)),error)
        gd=api.CreateTargetData(api.GetDataLayoutStr(module));hd=api.CreateTargetData(HOST_LAYOUT.encode())
        require(api.PointerSize(gd)==4 and api.PointerSize(hd)==8,'Pointer layout differs')
        layouts={}
        for name in re.findall(r'^%([^ =]+) = type',source,re.M):
            typ=api.GetTypeByName2(context,name.encode())
            def layout(data):return {'size':api.ABISizeOfType(data,typ),'alignment':api.ABIAlignmentOfType(data,typ),
                                    'offsets':[api.OffsetOfElement(data,typ,i) for i in range(api.CountStructElementTypes(typ))]}
            before,after=layout(gd),layout(hd);require(before==after,'State layout changed: '+name);layouts[name]=before
        require(layouts['struct.State']['size']==3504,'Complete State size differs')
        entry=api.GetNamedFunction(module,('sub_'+hex(ENTRY)[2:]).encode());require(api.signature(entry)==('ptr',['ptr','i32','ptr']),'Entry ABI differs')
        counts={k:0 for k in BRIDGES};nounwind=api.GetEnumAttributeKindForName(b'nounwind',8)
        for function in api.iterate(api.GetFirstFunction(module),api.GetNextFunction):
            name=api.name(function)
            if not api.CountBasicBlocks(function) and api.GetFirstUse(function) and not name.startswith('llvm.'):
                require(name in BRIDGES and api.signature(function)==BRIDGES[name] and
                        not api.IsFunctionVarArg(api.GlobalGetValueType(function)),'Unreviewed boundary: '+name)
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
        require(counts==COUNTS,'Bridge call count differs')
        api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode())
        builder=api.CreateBuilderInContext(context);wrapper=api.AddFunction(module,('mw34_fp_entry_'+hex(ENTRY)[2:]).encode(),api.GlobalGetValueType(entry))
        block=api.AppendBasicBlockInContext(context,wrapper,b'entry');api.PositionBuilderAtEnd(builder,block)
        args=(c.c_void_p*3)(*(api.GetParam(wrapper,i) for i in range(3)))
        result=api.BuildCall2(builder,api.GlobalGetValueType(entry),entry,args,3,b'memory');api.BuildRet(builder,result)
        api.check(api.VerifyModule(module,2,c.byref(error)),error)
        api.check(api.PrintModuleToFile(module,str(host).encode(),c.byref(error)),error)
        record.write_text(json.dumps({'passed':True,'scope':'Strict static host IR candidate only; no native execution/equivalence',
            'entry':ENTRY,'guest_SHA':SHA,'host_SHA':digest(host),'strict_SHA':digest(strict),'adapter_SHA':digest(__file__),
            'llvm_DLL_SHA':digest(dll),'all_layouts_equal':True,'layouts':layouts,'bridge_calls':counts,
            'dynamic_rounding':True,'strict_exceptions':True,'numerical_or_status_repairs':False,'native_admitted':False},indent=2)+'\n')
        print(json.dumps({'candidate':hex(ENTRY),'structs':len(layouts),'bridge_calls':counts,'native_admitted':False}))
    finally:
        if builder:api.DisposeBuilder(builder)
        for data in (gd,hd):
            if data:api.DisposeTargetData(data)
        if module.value:api.DisposeModule(module)
        api.ContextDispose(context)

if __name__=='__main__':main()
