"""Close eight recovered tail edges by linking their complete compiled helper."""
import argparse,ctypes as c,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
from bindings import FUNCTIONS,LINKED_IR_SHA
from state_fields import state_fields,rendered
sys.path.insert(0,str(ROOT/'tools/lifting'))
from host_adapter import LLVM,HOST_LAYOUT,FLAG_HELPERS,FUNCTION_INDEX,checked_state_offsets
DLL_SHA='34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'
CODE_SHA='8091fc698f5d5fc75afc1fc3f4926c9f98f2cbce614b5a667889320be799bd31'
BRIDGES={'__remill_read_memory_32':('mw34_integer_read32',('i32',['ptr','i32'])),
         '__remill_write_memory_32':('mw34_integer_write32',('ptr',['ptr','i32','i32'])),
         '__remill_write_memory_8':('mw34_integer_write8',('ptr',['ptr','i32','i8'])),
         '__remill_function_return':('mw34_integer_return',('ptr',['ptr','i32','ptr']))}
FIELDS={2065:('CF',1),2067:('PF',1),2069:('AF',1),2071:('ZF',1),2073:('SF',1),2077:('OF',1),
        2216:('EAX',4),2248:('ECX',4),2312:('ESP',4),2472:('EIP',4)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,text):
    if not ok:raise ValueError(text)
def adapt(dll,guest,host,record,recovery):
    private=(ROOT/'reports/m4-integer-startup').resolve()
    require(all(p.resolve().is_relative_to(private) for p in (guest,host,record,recovery)),'Private batch files required')
    require(sha(dll)==DLL_SHA and sha(guest)==LINKED_IR_SHA,'Pinned LLVM/complete linked IR differs')
    data=json.loads(recovery.read_text());require(data['profile']=='m4-integer-startup-fourteen-roots' and data['code_bytes']==389 and data['global_pages']==[0x605000,0x60b000],'Recovered batch domain differs');require(data['code_sha256']==CODE_SHA and sha(data['code_path'])==CODE_SHA,'Recovered bundle differs')
    require(data['image_sha256']=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf' and sha(data['image_path'])==data['image_sha256'],'Admitted image differs')
    require([f['entry'] for f in data['functions']]==list(FUNCTIONS),'Complete body inventory differs')
    raw=Path(data['image_path']).read_bytes()
    for f in data['functions']:
        known=FUNCTIONS[f['entry']]
        require(f['entry_va']==f['entry'] and f['end_va']==f['entry']+known['size'] and f['guest_ir_sha256']==known['guest_ir_sha256'],'Exact entry/end/IR metadata differs')
        require((f['size_bytes'],f['file_offset'],f['bundle_offset'],f['code_sha256'])==(known['size'],known['offset'],known['bundle'],known['code_sha256']),'Body binding differs')
        require(sha(f['code_path'])==known['code_sha256'] and raw[known['offset']:known['offset']+known['size']]==Path(f['code_path']).read_bytes(),'Body/image binding differs')
        require(sha(guest.parent/f"guest-{f['entry']:x}.ll")==known['guest_ir_sha256'],'Individual complete lift differs')
    source=guest.read_text();require(set(re.findall(r'^define .*?@([^ (]+)',source,re.M))=={'sub_'+format(e,'x') for e in FUNCTIONS},'Unclosed guest definition set')
    require(not re.search(r'\b(?:undef|poison|atomic|volatile|inttoptr|ptrtoint|x86_fp80|float|double)\b',source),'Unsupported operation')
    primary=(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()
    require(re.search(r'uint8_t __remill_undefined_8\(void\)\s*\{\s*return 0;\s*}',primary),'Upstream undefined representative changed')
    for name in FLAG_HELPERS:
        require(re.search(r'bool '+name+r'\(bool result, \.\.\.\)\s*\{\s*return result;\s*}',primary),'Upstream flag identity differs')
    api=LLVM(dll)
    specs=[('SetLinkage',None,[c.c_void_p,c.c_uint]),('IsAStoreInst',c.c_void_p,[c.c_void_p]),
           ('PositionBuilderBefore',None,[c.c_void_p,c.c_void_p]),('GetNumOperands',c.c_int,[c.c_void_p]),
           ('SetOperand',None,[c.c_void_p,c.c_uint,c.c_void_p]),('SetValueName2',None,[c.c_void_p,c.c_char_p,c.c_size_t]),('DeleteFunction',None,[c.c_void_p])]
    for name,result,args in specs:
        fn=getattr(api.dll,'LLVM'+name);fn.restype,fn.argtypes=result,args;setattr(api,name,fn)
    context=api.ContextCreate();module,buffer,error=c.c_void_p(),c.c_void_p(),c.c_void_p();gd=hd=builder=None
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest.resolve()).encode(),c.byref(buffer),c.byref(error)),error)
        api.check(api.ParseIRInContext(context,buffer,c.byref(module),c.byref(error)),error);api.check(api.VerifyModule(module,2,c.byref(error)),error)
        gd=api.CreateTargetData(api.GetDataLayoutStr(module));hd=api.CreateTargetData(HOST_LAYOUT.encode());require((api.PointerSize(gd),api.PointerSize(hd))==(4,8),'Wrong pointer domains')
        layouts={}
        for name in re.findall(r'^%([^ =]+) = type',source,re.M):
            ty=api.GetTypeByName2(context,name.encode());require(ty and not api.IsOpaqueStruct(ty),'Opaque State')
            def layout(data):return {'size':api.ABISizeOfType(data,ty),'alignment':api.ABIAlignmentOfType(data,ty),'offsets':[api.OffsetOfElement(data,ty,i) for i in range(api.CountStructElementTypes(ty))]}
            before,after=layout(gd),layout(hd);require(before==after,'State layout changed: '+name);layouts[name]=before
        require(layouts['struct.State']['size']==3504,'Wrong State size');functions={};tail_calls=[];all_writes=[]
        for entry,known in FUNCTIONS.items():
            name='sub_'+format(entry,'x');fn=api.GetNamedFunction(module,name.encode());require(api.signature(fn)==('ptr',['ptr','i32','ptr']),'Wrong guest ABI')
            offsets=checked_state_offsets(api,fn,gd);calls={};writes=[]
            for block in api.iterate(api.GetFirstBasicBlock(fn),api.GetNextBasicBlock):
                for ins in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
                    require(not api.IsAIntToPtrInst(ins) and not api.IsAPtrToIntInst(ins),'Guest/host pointer conversion')
                    if api.IsAStoreInst(ins):
                        line=rendered(api,ins).strip();pointer=re.search(r', ptr (%[A-Za-z0-9_.$]+), align ',line);require(pointer,'Unknown store destination');dest=pointer[1]
                        if dest in offsets:
                            offset=offsets[dest];width=api.ABISizeOfType(gd,api.TypeOf(api.GetOperand(ins,0)))
                            require(offset in FIELDS and width<=FIELDS[offset][1],'Unreviewed State write')
                            writes.append({'offset':offset,'width':width,'field':FIELDS[offset][0],'instruction':line})
                        else:require(dest in {'%MONITOR','%STATE','%MEMORY','%NEXT_PC','%RETURN_PC','%BRANCH_TAKEN'},'Aliased store')
                    if api.IsACallInst(ins):
                        callee=api.GetCalledValue(ins);require(api.IsAFunction(callee),'Indirect host call');target=api.name(callee);calls[target]=calls.get(target,0)+1
                        if target=='__remill_missing_block':tail_calls.append(ins)
            require(calls==known['calls'],'Exact complete call set differs: '+name)
            body=re.search(r'^define ptr @'+name+r'\([^\n]+\) \{\n(.*?)^}',source,re.M|re.S)[1]
            for dest,offset in offsets.items():
                if offset==2069:require(not re.search(r'load i8, ptr '+re.escape(dest)+r'\b',body),'Undefined AF consumed')
            undefined=calls.get('__remill_undefined_8',0)
            require(undefined==(1 if entry in (0x43ae30,0x4b5b20,0x4cfef0) else 0),'Undefined domain differs')
            functions[name]={'state_gep_offsets':offsets,'writes':writes,'call_counts':calls,
                             'undefined_exit_flags':['AF'] if undefined else [],'AF_loads':0};all_writes.extend(writes)
        require(len(tail_calls)==8,'Missing exact eight recovered tail edges')
        helper=api.GetNamedFunction(module,b'sub_43ae30')
        for call in tail_calls:api.SetOperand(call,api.GetNumOperands(call)-1,helper)
        missing=api.GetNamedFunction(module,b'__remill_missing_block');require(not api.GetFirstUse(missing),'Unresolved block remains');api.DeleteFunction(missing)
        builder=api.CreateBuilderInContext(context);nounwind=api.GetEnumAttributeKindForName(b'nounwind',8);lowered=[]
        for fn in list(api.iterate(api.GetFirstFunction(module),api.GetNextFunction)):
            name=api.name(fn)
            if name not in functions:
                require(not api.CountBasicBlocks(fn) and api.GetFirstUse(fn),'Unexpected declaration')
                if name in FLAG_HELPERS or name=='__remill_undefined_8':
                    require(api.signature(fn)==(('i8',[]) if name=='__remill_undefined_8' else ('i1',['i1'])),'Wrong scalar signature')
                    block=api.AppendBasicBlockInContext(context,fn,b'identity');api.PositionBuilderAtEnd(builder,block)
                    value=api.ConstInt(api.GetReturnType(api.GlobalGetValueType(fn)),0,0) if name=='__remill_undefined_8' else api.GetParam(fn,0)
                    api.BuildRet(builder,value);api.SetLinkage(fn,8);lowered.append(name)
                elif name in BRIDGES:
                    new,sig=BRIDGES[name];require(api.signature(fn)==sig and not api.IsFunctionVarArg(api.GlobalGetValueType(fn)),'Wrong checked bridge signature');api.SetValueName2(fn,new.encode(),len(new))
                else:require(name=='llvm.ctpop.i8' and api.signature(fn)==('i8',['i8']),'Unexpected external')
            api.SetFunctionCallConv(fn,0);api.RemoveEnumAttributeAtIndex(fn,FUNCTION_INDEX,nounwind)
            for attr in (b'target-cpu',b'target-features'):api.RemoveStringAttributeAtIndex(fn,FUNCTION_INDEX,attr,len(attr))
            for block in api.iterate(api.GetFirstBasicBlock(fn),api.GetNextBasicBlock):
                for ins in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
                    if api.IsACallInst(ins):api.SetInstructionCallConv(ins,0);api.RemoveCallSiteEnumAttribute(ins,FUNCTION_INDEX,nounwind)
        hook=api.AddFunction(module,b'mw34_integer_tail_enter',api.GlobalGetValueType(helper));api.PositionBuilderBefore(builder,api.GetFirstInstruction(api.GetFirstBasicBlock(helper)))
        args=(c.c_void_p*3)(*(api.GetParam(helper,i) for i in range(3)));api.BuildCall2(builder,api.GlobalGetValueType(hook),hook,args,3,b'checked_tail_route')
        for entry in FUNCTIONS:
            fn=api.GetNamedFunction(module,('sub_'+format(entry,'x')).encode());api.SetLinkage(fn,8)
            if entry!=0x43ae30:
                wrapper=api.AddFunction(module,('mw34_integer_entry_'+format(entry,'x')).encode(),api.GlobalGetValueType(fn));block=api.AppendBasicBlockInContext(context,wrapper,b'entry');api.PositionBuilderAtEnd(builder,block)
                args=(c.c_void_p*3)(*(api.GetParam(wrapper,i) for i in range(3)));call=api.BuildCall2(builder,api.GlobalGetValueType(fn),fn,args,3,b'memory');api.BuildRet(builder,call)
        api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode());api.check(api.VerifyModule(module,2,c.byref(error)),error)
        api.check(api.PrintModuleToFile(module,str(host.resolve()).encode(),c.byref(error)),error)
        result={'schema_version':1,'profile':'m4-integer-startup-fourteen-roots','guest_ir_sha256':sha(guest),'host_ir_sha256':sha(host),'recovery_sha256':sha(recovery),
                'dll_sha256':sha(dll),'state_bytes':3504,'guest_pointer_bits':32,'host_pointer_bits':64,'all_struct_layouts_equal':True,'struct_layouts':layouts,'state_fields':state_fields(layouts),
                'functions':functions,'state_write_ranges':all_writes,'closed_actual_tail_targets':{format(e,'x'):'43ae30' for e in list(FUNCTIONS)[:8]},
                'tail_edge_basis':'Hash-admitted encoded JMPs in complete wrappers; concrete PC checked on compiled helper entry; original block boundary resolved to exact complete static definition',
                'flag_annotation_identities':lowered,'undefined_policy':'Upstream zero representative for final undefined XOR AF, never loaded before return; exclude only AF for affected routes',
                'semantic_repairs':[],'bridges':[v[0] for v in BRIDGES.values()]+['mw34_integer_tail_enter'],'indirect_host_calls':0,'pointer_integer_conversions':0}
        record.write_text(json.dumps(result,indent=2)+'\n');return result
    finally:
        if builder:api.DisposeBuilder(builder)
        for data in (gd,hd):
            if data:api.DisposeTargetData(data)
        if module.value:api.DisposeModule(module)
        api.ContextDispose(context)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('llvm-dll','guest','host','record','recovery'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=adapt(a.llvm_dll,a.guest,a.host,a.record,a.recovery);print(json.dumps({'passed':True,'functions':len(r['functions']),'closed_tail_edges':8}))
