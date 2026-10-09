"""Complete six-instruction game CFG; frozen provider transfer lowering unchanged."""
import ctypes as c,hashlib,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lifting'));sys.path.insert(0,str(ROOT/'tools/x87-repair'));sys.path.insert(0,str(ROOT/'tools/m4-crt-control'))
from host_adapter import HOST_LAYOUT,FLAG_HELPERS,FUNCTION_INDEX,checked_state_offsets
from adapt_control import ControlLLVM
from adapt import pc_model
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def adapt(out):
 need(out.is_relative_to(ROOT/'reports/m4-crt-control-integration') and not (out/'game-host.ll').exists(),'Fresh private game adapter output')
 source=ROOT/'reports/m4-crt-control-integration/preparation-r1/guest.ll';text=source.read_text();need(set(re.findall(r'^define ptr @([^ (]+)',text,re.M))=={'sub_5ac5a0','sub_5ac5d6'} and not re.search(r'\b(?:undef|poison|volatile|atomic|float|double|x86_fp80|inttoptr|ptrtoint)\b',text) and '__remill_missing_block' not in text,'Complete bounded game value domain')
 api=ControlLLVM(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll');ctx=api.ContextCreate();module,buffer,error=c.c_void_p(),c.c_void_p(),c.c_void_p();builder=None;gd=hd=None
 try:
  api.check(api.CreateMemoryBufferWithContentsOfFile(str(source).encode(),c.byref(buffer),c.byref(error)),error);api.check(api.ParseIRInContext(ctx,buffer,c.byref(module),c.byref(error)),error);gd=api.CreateTargetData(api.GetDataLayoutStr(module));hd=api.CreateTargetData(HOST_LAYOUT.encode());layouts={};functions={};pcs=set()
  for name in re.findall(r'^%([^ =]+) = type',text,re.M):
   t=api.GetTypeByName2(ctx,name.encode());need(t and not api.IsOpaqueStruct(t),'Complete game State type')
   def layout(d):return {'size':api.ABISizeOfType(d,t),'align':api.ABIAlignmentOfType(d,t),'offsets':[api.OffsetOfElement(d,t,i)for i in range(api.CountStructElementTypes(t))]}
   a,b=layout(gd),layout(hd);need(a==b,'Exact complete game State layout');layouts[name]=a
  need(layouts['struct.State']['size']==3504,'Complete architectural State3504')
  for entry in (0x5ac5a0,0x5ac5d6):
   name=f'sub_{entry:x}';fn=api.GetNamedFunction(module,name.encode());body=re.search(r'^define ptr @'+name+r'[^\n]+\{\n(.*?)^}',text,re.M|re.S)[1];functions[name]={'CFG':pc_model(body,entry),'State_offsets':checked_state_offsets(api,fn,gd)};pcs.update(functions[name]['CFG']['instruction_PCs'])
  need(pcs=={0x5ac5a0,0x5ac5a5,0x5ac5aa,0x5ac5af,0x5ac5b2,0x5ac5d6},'Complete original six instruction PCs')
  builder=api.CreateBuilderInContext(ctx);bridges={'__remill_read_memory_32':('i32',['ptr','i32']),'__remill_write_memory_32':('ptr',['ptr','i32','i32']),'__remill_function_return':('ptr',['ptr','i32','ptr']),'__remill_jump':('ptr',['ptr','i32','ptr'])}
  nounwind=api.GetEnumAttributeKindForName(b'nounwind',8);willreturn=api.GetEnumAttributeKindForName(b'willreturn',10);api.dll.LLVMSetLinkage.argtypes=[c.c_void_p,c.c_int];api.dll.LLVMSetLinkage.restype=None
  for fn in list(api.iterate(api.GetFirstFunction(module),api.GetNextFunction)):
   name=api.name(fn)
   if name in FLAG_HELPERS:
    need(not api.CountBasicBlocks(fn) and api.signature(fn)==('i1',['i1']),'Exact scalar identity helper');block=api.AppendBasicBlockInContext(ctx,fn,b'identity');api.PositionBuilderAtEnd(builder,block);api.BuildRet(builder,api.GetParam(fn,0));api.dll.LLVMSetLinkage(fn,8)
   elif not api.CountBasicBlocks(fn):need(name in bridges and api.signature(fn)==bridges[name] or name=='llvm.ctpop.i8' and api.signature(fn)==('i8',['i8']),'Only checked external bridge ABI '+name)
   api.SetFunctionCallConv(fn,0)
   if name!='llvm.ctpop.i8':api.RemoveEnumAttributeAtIndex(fn,FUNCTION_INDEX,nounwind);api.RemoveEnumAttributeAtIndex(fn,FUNCTION_INDEX,willreturn)
   for attr in (b'target-cpu',b'target-features'):api.RemoveStringAttributeAtIndex(fn,FUNCTION_INDEX,attr,len(attr))
   for block in api.iterate(api.GetFirstBasicBlock(fn),api.GetNextBasicBlock):
    for ins in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
     if api.IsACallInst(ins):
      callee=api.GetCalledValue(ins);need(api.IsAFunction(callee),'No indirect host pointer call');api.SetInstructionCallConv(ins,0)
      if api.name(callee)!='llvm.ctpop.i8':api.RemoveCallSiteEnumAttribute(ins,FUNCTION_INDEX,nounwind);api.RemoveCallSiteEnumAttribute(ins,FUNCTION_INDEX,willreturn)
  proto=api.GetNamedFunction(module,b'sub_5ac5a0');hook=api.AddFunction(module,b'mw34_ci_enter',api.GlobalGetValueType(proto));position=api.dll.LLVMPositionBuilderBefore;position.argtypes=[c.c_void_p,c.c_void_p];position.restype=None
  for entry in (0x5ac5a0,0x5ac5d6):
   fn=api.GetNamedFunction(module,f'sub_{entry:x}'.encode());position(builder,api.GetFirstInstruction(api.GetFirstBasicBlock(fn)));args=(c.c_void_p*3)(*(api.GetParam(fn,i)for i in range(3)));api.BuildCall2(builder,api.GlobalGetValueType(hook),hook,args,3,b'checked_game_entry')
  api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode());api.check(api.VerifyModule(module,2,c.byref(error)),error);host=out/'game-host.ll';api.check(api.PrintModuleToFile(module,str(host).encode(),c.byref(error)),error)
 finally:
  if builder:api.DisposeBuilder(builder)
  for d in (gd,hd):
   if d:api.DisposeTargetData(d)
  if module.value:api.DisposeModule(module)
  api.ContextDispose(ctx)
 provider=ROOT/'reports/m4-crt-control/research-r1/host.ll';need(sha(provider)=='49e25a2cd2f9279970fac099141a08742ab678eb9b041be6b1368effc55ea5a9','Frozen complete provider lowering identity');link=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-link.exe';cmd=[str(link),str(host),str(provider),'-S','-o',str(out/'host.ll')];cp=subprocess.run(cmd,capture_output=True);(out/'link.stdout').write_bytes(cp.stdout);(out/'link.stderr').write_bytes(cp.stderr);need(cp.returncode==0,'Exact linked host module');combined=(out/'host.ll').read_text();need(all('@'+f'sub_{x:x}(' in combined for x in (0x5ac5a0,0x5ac5d6,0x780042e1,0x780042f7,0x7800432c,0x7800439f)),'All six actual definitions linked')
 (out/'game-layout.json').write_text(json.dumps({'passed':True,'source_path':str(source),'source_sha256':sha(source),'game_host_sha256':sha(host),'linked_host_sha256':sha(out/'host.ll'),'accepted_provider_host_path':str(provider),'accepted_provider_host_sha256':sha(provider),'functions':functions,'layouts':layouts,'complete_game_instruction_PCs':sorted(pcs),'complete_State_bytes':3504,'all_layouts_equal':True,'provider_mechanical_repairs_unchanged':True,'link_command':cmd,'link_exit_code':cp.returncode,'defined_wrapper_exit_flag_mask':0xcd5,'native_execution_accepted':False,'whole_M4_complete':False,'sources':{str(pathlib.Path(__file__)):sha(__file__),str(ROOT/'tools/lifting/host_adapter.py'):sha(ROOT/'tools/lifting/host_adapter.py'),str(ROOT/'tools/x87-repair/adapt_control.py'):sha(ROOT/'tools/x87-repair/adapt_control.py'),str(ROOT/'tools/m4-crt-control/adapt.py'):sha(ROOT/'tools/m4-crt-control/adapt.py')}},indent=2)+'\n')
if __name__=='__main__':adapt(pathlib.Path(sys.argv[1]).resolve())
