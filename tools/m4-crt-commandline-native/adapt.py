"""Retarget exact CALL/MOV and declared capture jump; no result/number repair."""
from pathlib import Path
import ctypes as c,hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lifting'))
from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(folder):
 folder=Path(folder).resolve();assert folder.parent==ROOT/'reports/m4-crt-commandline-native';guest=folder/'guest.ll';text=guest.read_text()
 assert re.findall(r'^define ptr @([^ (]+)',text,re.M)==['sub_7800188c']
 assert not re.search(r'\b(?:undef|poison|atomic|volatile|float|double|x86_fp80|inttoptr|ptrtoint)\b',text)
 assert text.count('@__remill_missing_block(')==2 and text.count('call ptr @__remill_function_call(')==1
 # The only missing block is the explicitly authored external capture target,
 # not an unimplemented original branch. Its address must be checked at runtime.
 candidate=text.replace('@__remill_missing_block(', '@mw34_cmd_outer_capture(');(folder/'candidate.ll').write_text(candidate)
 api=LLVM(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll');ctx=api.ContextCreate();module,buffer,error=c.c_void_p(),c.c_void_p(),c.c_void_p();gd=hd=builder=None
 try:
  api.check(api.CreateMemoryBufferWithContentsOfFile(str(folder/'candidate.ll').encode(),c.byref(buffer),c.byref(error)),error);api.check(api.ParseIRInContext(ctx,buffer,c.byref(module),c.byref(error)),error);api.check(api.VerifyModule(module,2,c.byref(error)),error)
  gd=api.CreateTargetData(api.GetDataLayoutStr(module));hd=api.CreateTargetData(HOST_LAYOUT.encode());assert api.PointerSize(gd)==4 and api.PointerSize(hd)==8
  layouts={}
  for name in re.findall(r'^%([^ =]+) = type',text,re.M):
   ty=api.GetTypeByName2(ctx,name.encode());assert ty and not api.IsOpaqueStruct(ty)
   def layout(d):return dict(size=api.ABISizeOfType(d,ty),align=api.ABIAlignmentOfType(d,ty),offsets=[api.OffsetOfElement(d,ty,i) for i in range(api.CountStructElementTypes(ty))])
   a,b=layout(gd),layout(hd);assert a==b;layouts[name]=a
  assert layouts['struct.State']['size']==3504
  entry=api.GetNamedFunction(module,b'sub_7800188c');assert api.signature(entry)==('ptr',['ptr','i32','ptr'])
  offsets=checked_state_offsets(api,entry,gd);bridges={'__remill_read_memory_32':('i32',['ptr','i32']),'__remill_write_memory_32':('ptr',['ptr','i32','i32']),'__remill_function_call':('ptr',['ptr','i32','ptr']),'mw34_cmd_outer_capture':('ptr',['ptr','i32','ptr'])};counts={};nounwind=api.GetEnumAttributeKindForName(b'nounwind',8)
  for fn in api.iterate(api.GetFirstFunction(module),api.GetNextFunction):
   name=api.name(fn)
   if not api.CountBasicBlocks(fn):assert name in bridges and api.signature(fn)==bridges[name]
   api.SetFunctionCallConv(fn,0);api.RemoveEnumAttributeAtIndex(fn,FUNCTION_INDEX,nounwind)
   for attr in (b'target-cpu',b'target-features'):api.RemoveStringAttributeAtIndex(fn,FUNCTION_INDEX,attr,len(attr))
   for block in api.iterate(api.GetFirstBasicBlock(fn),api.GetNextBasicBlock):
    for ins in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
     assert not api.IsAIntToPtrInst(ins) and not api.IsAPtrToIntInst(ins)
     if api.IsACallInst(ins):
      f=api.GetCalledValue(ins);assert api.IsAFunction(f);target=api.name(f);counts[target]=counts.get(target,0)+1;api.SetInstructionCallConv(ins,0);api.RemoveCallSiteEnumAttribute(ins,FUNCTION_INDEX,nounwind)
  assert counts=={'__remill_read_memory_32':1,'__remill_write_memory_32':2,'__remill_function_call':1,'mw34_cmd_outer_capture':1}
  builder=api.CreateBuilderInContext(ctx);wrapper=api.AddFunction(module,b'mw34_cmd_writer',api.GlobalGetValueType(entry));block=api.AppendBasicBlockInContext(ctx,wrapper,b'entry');api.PositionBuilderAtEnd(builder,block);args=(c.c_void_p*3)(*(api.GetParam(wrapper,i) for i in range(3)));call=api.BuildCall2(builder,api.GlobalGetValueType(entry),entry,args,3,b'actual_writer');api.BuildRet(builder,call)
  api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode());api.check(api.VerifyModule(module,2,c.byref(error)),error);api.check(api.PrintModuleToFile(module,str(folder/'host.ll').encode(),c.byref(error)),error)
  report=dict(passed=True,scope='Exact CALL/MOV plus explicit authored capture jump, typed external capture only; no RET/full attach/native body execution',guest_sha256=sha(guest),candidate_sha256=sha(folder/'candidate.ll'),host_sha256=sha(folder/'host.ll'),source_sha256=sha(__file__),base_adapter_sha256=sha(ROOT/'tools/lifting/host_adapter.py'),LLVM_C_sha256=sha(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll'),layouts=layouts,State_offsets=offsets,calls=counts,bridges=bridges,authored_external_capture=0x10000100,original_call=0x7800188c,original_call_return=0x78001892,original_global=0x78037174)
  (folder/'layout.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,host_sha256=report['host_sha256'],layout_sha256=sha(folder/'layout.json'))))
 finally:
  if builder:api.DisposeBuilder(builder)
  for d in (gd,hd):
   if d:api.DisposeTargetData(d)
  if module.value:api.DisposeModule(module)
  api.ContextDispose(ctx)
if __name__=='__main__':main(sys.argv[1])
