"""Adapt four exact static definitions with real compiled calls and checked routing."""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
from dead_flags import prove
from extract_image import FUNCTIONS, IMAGE_SHA
from state_fields import state_fields,rendered
sys.path.insert(0,str(ROOT/'tools/lifting'))
from host_adapter import LLVM,HOST_LAYOUT,FLAG_HELPERS,FUNCTION_INDEX,checked_state_offsets
LLVM_SHA='34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'
BRIDGES={'__remill_read_memory_32':('i32',['ptr','i32']),
         '__remill_write_memory_32':('ptr',['ptr','i32','i32']),
         '__remill_write_memory_8':('ptr',['ptr','i32','i8']),
         '__remill_function_return':('ptr',['ptr','i32','ptr'])}
ANNOTATIONS=FLAG_HELPERS|{'__remill_compare_neq'}
FIELDS={2065:('CF',1),2067:('PF',1),2069:('AF',1),2071:('ZF',1),2073:('SF',1),2077:('OF',1),
        2216:('EAX',4),2248:('ECX',4),2264:('EDX',4),2232:('EBX',4),2312:('ESP',4),2472:('EIP',4)}
COUNTS={
 'sub_410910':{'__remill_flag_computation_carry':1,'__remill_flag_computation_zero':2,'__remill_flag_computation_sign':2,'__remill_flag_computation_overflow':2,'__remill_read_memory_32':1,'__remill_write_memory_8':1,'__remill_function_return':1,'llvm.ctpop.i8':2,'__remill_compare_neq':1},
 'sub_410940':{'__remill_write_memory_32':24,'__remill_write_memory_8':4,'llvm.ctpop.i8':3,'__remill_flag_computation_zero':3,'__remill_flag_computation_sign':3,'__remill_flag_computation_overflow':2,'__remill_read_memory_32':2,'__remill_undefined_8':1,'__remill_flag_computation_carry':1,'__remill_compare_neq':1,'sub_40daf0':1,'sub_40db30':1,'__remill_function_return':1},
 'sub_40daf0':{'__remill_read_memory_32':4,'__remill_write_memory_32':3,'__remill_function_return':1},
 'sub_40db30':{'__remill_read_memory_32':6,'__remill_write_memory_32':4,'__remill_undefined_8':2,'llvm.ctpop.i8':2,'__remill_flag_computation_carry':1,'__remill_flag_computation_zero':1,'__remill_flag_computation_sign':1,'__remill_flag_computation_overflow':1,'__remill_write_memory_8':1,'__remill_function_return':1}}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,why):
 if not ok:raise ValueError(why)
def admit_slice_record(path):
 image=json.loads(path.read_text())
 require(image['profile']=='m4-connected-initializers-410910-410940' and image['image_sha256']==IMAGE_SHA and image['code_bytes']==305 and image['code_sha256']=='68b13b88a1aab772ec1474ed256b10eec7627b5496e6be3e7e90b2a0431a50aa','Wrong connected extraction metadata')
 raw=Path(image['image_path']).read_bytes();bundle=Path(image['code_path']).read_bytes()
 require(sha(Path(image['image_path']))==IMAGE_SHA and sha(Path(image['code_path']))==image['code_sha256'],'Changed connected private inputs')
 require(len(image['functions'])==4 and [f['entry_va'] for f in image['functions']]==list(FUNCTIONS),'Wrong complete function inventory')
 cursor=0
 for f in image['functions']:
  size,offset,code,ir=FUNCTIONS[f['entry_va']]
  require((f['size_bytes'],f['file_offset'],f['code_sha256'],f['guest_ir_sha256'],f['bundle_offset'])==(size,offset,code,ir,cursor) and f['end_va']==f['entry_va']+size,'Unadmitted function metadata')
  require(sha(Path(f['code_path']))==code and bundle[cursor:cursor+size]==raw[offset:offset+size],'Changed complete body/image binding');cursor+=size
 g=image['global_page'];require(g['base']==0x604000 and g['size']==4096 and Path(g['initial_path']).read_bytes()==bytes(4096) and sha(Path(g['initial_path']))==g['initial_sha256'],'Wrong shared zero-fill page')
 s=image['stack_page'];require(s['base']==0x20001000 and s['size']==4096 and s['required_relative_span']==[-28,4] and s['return_sentinel']==0x10000100,'Wrong full call stack domain')
 for name,digest in image['source_tools'].items():require(sha(Path(name))==digest,'Changed extraction source/tool binding')
 return image
def adapt(dll,guest,host,record,slice_record):
 private=(ROOT/'reports/m4-initializer-chain').resolve()
 require(all(p.resolve().is_relative_to(private) for p in (guest,host,record,slice_record)),'Private chain IR must remain ignored')
 require(sha(dll)==LLVM_SHA,'Wrong pinned LLVM DLL')
 image=admit_slice_record(slice_record)
 require(sha(guest)=='d25aad7224d790f7d1c2d8e06554b010464d78b867b3e8ac2010ac5d2c03739e','Linked guest IR identity differs')
 for f in image['functions']:
  size,offset,code,ir=FUNCTIONS[f['entry_va']]
  require((f['size_bytes'],f['file_offset'],f['code_sha256'],f['guest_ir_sha256'])==(size,offset,code,ir),'Unadmitted function extraction')
  require(sha(Path(f['code_path']))==code and sha(guest.parent/f"guest-{f['entry_va']:x}.ll")==ir,'Unreviewed complete individual guest IR')
 source=guest.read_text();require(set(re.findall(r'^define .*?@([^ (]+)',source,re.M))==set(COUNTS),'Incomplete linked static bodies')
 require(not re.search(r'\b(?:undef|poison|atomic|volatile|inttoptr|ptrtoint|x86_fp80|float|double)\b',source),'Unsupported linked operation')
 primary=(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()
 require(re.search(r'uint8_t __remill_undefined_8\(void\)\s*\{\s*return 0;\s*}',primary),'Upstream undefined identity changed')
 for name in ANNOTATIONS:
  args=r'bool result, \.\.\.' if name in FLAG_HELPERS else r'bool result'
  require(re.search(r'bool '+name+r'\('+args+r'\)\s*\{\s*return result;\s*}',primary),'Upstream flag identity changed')
 api=LLVM(dll)
 for name,result,args in [('SetLinkage',None,[c.c_void_p,c.c_uint]),('IsAStoreInst',c.c_void_p,[c.c_void_p]),('PositionBuilderBefore',None,[c.c_void_p,c.c_void_p])]:
  f=getattr(api.dll,'LLVM'+name);f.restype,f.argtypes=result,args;setattr(api,name,f)
 context=api.ContextCreate();module,buffer,error=c.c_void_p(),c.c_void_p(),c.c_void_p();gd=hd=builder=None
 try:
  api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest.resolve()).encode(),c.byref(buffer),c.byref(error)),error)
  api.check(api.ParseIRInContext(context,buffer,c.byref(module),c.byref(error)),error);api.check(api.VerifyModule(module,2,c.byref(error)),error)
  guest_layout=api.GetDataLayoutStr(module).decode();gd=api.CreateTargetData(guest_layout.encode());hd=api.CreateTargetData(HOST_LAYOUT.encode())
  require((api.PointerSize(gd),api.PointerSize(hd))==(4,8),'Wrong pointer domain');layouts={}
  for name in re.findall(r'^%([^ =]+) = type',source,re.M):
   ty=api.GetTypeByName2(context,name.encode());require(ty and not api.IsOpaqueStruct(ty),'Opaque State type')
   def layout(data):return {'size':api.ABISizeOfType(data,ty),'alignment':api.ABIAlignmentOfType(data,ty),'offsets':[api.OffsetOfElement(data,ty,i) for i in range(api.CountStructElementTypes(ty))]}
   before,after=layout(gd),layout(hd);require(before==after,'Changed complete State layout: '+name);layouts[name]=before
  require(layouts['struct.State']['size']==3504,'Unexpected State size')
  all_writes=[];functions={}
  for name,counts in COUNTS.items():
   entry=api.GetNamedFunction(module,name.encode());require(api.signature(entry)==('ptr',['ptr','i32','ptr']) and not api.IsFunctionVarArg(api.GlobalGetValueType(entry)),'Wrong entry signature')
   offsets=checked_state_offsets(api,entry,gd);calls={};writes=[]
   for bi,block in enumerate(api.iterate(api.GetFirstBasicBlock(entry),api.GetNextBasicBlock)):
    for ins in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
     require(not api.IsAIntToPtrInst(ins) and not api.IsAPtrToIntInst(ins),'Guest/host pointer conversion')
     if api.IsAStoreInst(ins):
      line=rendered(api,ins).strip();pointer=re.search(r', ptr (%[A-Za-z0-9_.$]+), align ',line);require(pointer,'Unreviewed store destination');dest=pointer[1]
      if dest in offsets:
       offset=offsets[dest];width=api.ABISizeOfType(gd,api.TypeOf(api.GetOperand(ins,0)));require(offset in FIELDS and width==FIELDS[offset][1],'Unknown State write')
       writes.append({'offset':offset,'width':width,'field':FIELDS[offset][0],'destination_ssa':dest,'block_index':bi,'instruction':line})
      else:require(dest in {'%MONITOR','%STATE','%MEMORY','%NEXT_PC','%RETURN_PC','%BRANCH_TAKEN'},'Aliased/unknown store')
     if api.IsACallInst(ins):
      callee=api.GetCalledValue(ins);require(api.IsAFunction(callee),'Indirect host call');target=api.name(callee);calls[target]=calls.get(target,0)+1
   require(calls==counts,'Exact complete call set differs: '+name)
   body=re.search(r'^define ptr @'+name+r'\([^\n]+\) \{\n(.*?)^}',source,re.M|re.S)[1]
   proof=prove(body,offsets);functions[name]={'state_gep_offsets':offsets,'writes':writes,'call_counts':calls,'dead_flag_proof':proof};all_writes.extend(writes)
  builder=api.CreateBuilderInContext(context);nounwind=api.GetEnumAttributeKindForName(b'nounwind',8);lowered=[]
  for function in list(api.iterate(api.GetFirstFunction(module),api.GetNextFunction)):
   name=api.name(function)
   if name not in COUNTS:
    require(not api.CountBasicBlocks(function) and api.GetFirstUse(function),'Unexpected external declaration')
    signature=api.signature(function);variadic=bool(api.IsFunctionVarArg(api.GlobalGetValueType(function)))
    if name in ANNOTATIONS or name=='__remill_undefined_8':
     require(signature==(('i8',[]) if name=='__remill_undefined_8' else ('i1',['i1'])) and variadic==(name in FLAG_HELPERS),'Wrong scalar annotation signature')
     block=api.AppendBasicBlockInContext(context,function,b'identity');api.PositionBuilderAtEnd(builder,block)
     value=api.ConstInt(api.GetReturnType(api.GlobalGetValueType(function)),0,0) if name=='__remill_undefined_8' else api.GetParam(function,0)
     api.BuildRet(builder,value);api.SetLinkage(function,8);lowered.append(name)
    elif name in BRIDGES:require(signature==BRIDGES[name] and not variadic,'Wrong memory/return bridge signature')
    else:require(name=='llvm.ctpop.i8' and signature==('i8',['i8']) and not variadic,'Unreviewed external helper')
   api.SetFunctionCallConv(function,0);api.RemoveEnumAttributeAtIndex(function,FUNCTION_INDEX,nounwind)
   for attr in (b'target-cpu',b'target-features'):api.RemoveStringAttributeAtIndex(function,FUNCTION_INDEX,attr,len(attr))
   for block in api.iterate(api.GetFirstBasicBlock(function),api.GetNextBasicBlock):
    for ins in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
     if api.IsACallInst(ins):api.SetInstructionCallConv(ins,0);api.RemoveCallSiteEnumAttribute(ins,FUNCTION_INDEX,nounwind)
  prototype=api.GetNamedFunction(module,b'sub_410940');bridge=api.AddFunction(module,b'mw34_chain_enter_callee',api.GlobalGetValueType(prototype))
  for name in ('sub_40daf0','sub_40db30'):
   fn=api.GetNamedFunction(module,name.encode());api.PositionBuilderBefore(builder,api.GetFirstInstruction(api.GetFirstBasicBlock(fn)))
   args=(c.c_void_p*3)(*(api.GetParam(fn,i) for i in range(3)));call=api.BuildCall2(builder,api.GlobalGetValueType(bridge),bridge,args,3,b'checked_call_route');api.SetInstructionCallConv(call,0)
  for name in COUNTS:
   entry=api.GetNamedFunction(module,name.encode());api.SetLinkage(entry,8)
   if name in ('sub_410910','sub_410940'):
    wrapper=api.AddFunction(module,('mw34_chain_entry_'+name[4:]).encode(),api.GlobalGetValueType(entry));block=api.AppendBasicBlockInContext(context,wrapper,b'entry');api.PositionBuilderAtEnd(builder,block)
    args=(c.c_void_p*3)(*(api.GetParam(wrapper,i) for i in range(3)));call=api.BuildCall2(builder,api.GlobalGetValueType(entry),entry,args,3,b'memory');api.SetInstructionCallConv(call,0);api.BuildRet(builder,call)
  api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode());api.check(api.VerifyModule(module,2,c.byref(error)),error)
  api.check(api.PrintModuleToFile(module,str(host.resolve()).encode(),c.byref(error)),error)
  ranges=[{'offset':offset,'bytes':width,'width':width,'field':field,'store_count':sum(w['offset']==offset for w in all_writes)} for offset,(field,width) in sorted(FIELDS.items())]
  result={'schema_version':1,'profile':'m4-connected-initializers-410910-410940','guest_ir_sha256':sha(guest),'host_ir_sha256':sha(host),'slice_record_sha256':sha(slice_record),'image_sha256':IMAGE_SHA,'code_sha256':image['code_sha256'],
          'llvm_version':api.version,'dll_sha256':sha(dll),'state_bytes':3504,'guest_pointer_bits':32,'host_pointer_bits':64,'all_struct_layouts_equal':True,'struct_layouts':layouts,'state_fields':state_fields(layouts),'state_write_ranges':ranges,'functions':functions,
          'bridges':sorted(BRIDGES)+['mw34_chain_enter_callee'],'flag_annotation_identities':lowered,'compiled_direct_guest_calls':{'sub_410940':['sub_40daf0','sub_40db30']},'direct_call_route_hooks':2,
          'undefined_flag_policy':{'policy':'only complete-CFG-proven dead intermediate AF/OF replaced with upstreamzero','defined_exit_flags_mask':0xcd5,'excluded_exit_flags':[]},'semantic_repairs':[],'indirect_host_calls':0,'pointer_integer_conversions':0,
          'global_page':image['global_page'],'stack_page':image['stack_page'],'host_entries':['mw34_chain_entry_410910','mw34_chain_entry_410940']}
  record.write_text(json.dumps(result,indent=2)+'\n');return result
 finally:
  if builder:api.DisposeBuilder(builder)
  for data in (gd,hd):
   if data:api.DisposeTargetData(data)
  if module.value:api.DisposeModule(module)
  api.ContextDispose(context)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('llvm-dll','guest','host','record','slice-record'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();r=adapt(a.llvm_dll,a.guest,a.host,a.record,a.slice_record);print(json.dumps({'profile':r['profile'],'functions':list(r['functions']),'host_ir_sha256':r['host_ir_sha256']}))
