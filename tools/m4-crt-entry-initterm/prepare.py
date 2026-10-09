"""Recover, lift and lower the exact staged first _initterm provider."""
import ctypes as c,hashlib,json,pathlib,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-entry-initterm'
sys.path.insert(0,str(ROOT/'tools/m4-crt'));from recover_provider import PE,IMAGE_SHA,PROVIDER_SHA
sys.path.insert(0,str(ROOT/'tools/lifting'));from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert not out.exists() and out.parent==BASE;out.mkdir(parents=True);commands=[];files={}
 def pin(p):p=pathlib.Path(p).resolve();files[str(p)]=sha(p);return p
 game=PE(pin(ROOT/'MW3/Mech3.exe'),IMAGE_SHA);provider=PE(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),PROVIDER_SHA)
 assert provider.exports()['_initterm']['address']==0x780014f8
 slot=[i for i in game.imports()if i.get('name')=='_initterm' and i['library'].casefold()=='msvcrt.dll'];assert len(slot)==1 and slot[0]['iat']==0x5bb510
 code=provider.read(0x14f8,28);assert hashlib.sha256(code).hexdigest()=='960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678'
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';lift=pin(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe');sem=pin(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc');assert sha(sem)=='618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca'
 def run(program,args,name):
  pin(program);cp=subprocess.run([str(program),*args],capture_output=True);(out/(name+'.stdout')).write_bytes(cp.stdout);(out/(name+'.stderr')).write_bytes(cp.stderr);commands.append(dict(program=str(program),arguments=args,exit_code=cp.returncode));assert cp.returncode==0,name
 try:
  (out/'source.bin').write_bytes(code)
  run(llvm/'llvm-objdump.exe',['-d','--x86-asm-syntax=intel','--start-address=0x780014f8','--stop-address=0x78001514',str(provider.path)],'decode')
  flags=['--arch=x86','--os=windows','--address='+str(0x780014f8),'--entry_address='+str(0x780014f8),'--bytes='+code.hex(),'--semantics_dir='+str(sem.parent),'--ir_out='+str(out/'guest.ll')]
  run(lift,flags,'lift');text=(out/'guest.ll').read_text();assert re.findall(r'^define ptr @([^ (]+)',text,re.M)==['sub_780014f8'] and '__remill_missing_block'not in text
  dll=pin(llvm/'LLVM-C.dll');assert sha(dll)=='34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'
  api=LLVM(dll);ctx=api.ContextCreate();module,buffer,error=c.c_void_p(),c.c_void_p(),c.c_void_p();api.check(api.CreateMemoryBufferWithContentsOfFile(str(out/'guest.ll').encode(),c.byref(buffer),c.byref(error)),error);api.check(api.ParseIRInContext(ctx,buffer,c.byref(module),c.byref(error)),error)
  gd=api.CreateTargetData(api.GetDataLayoutStr(module));hd=api.CreateTargetData(HOST_LAYOUT.encode());layouts={}
  for n in re.findall(r'^%([^ =]+) = type',text,re.M):
   ty=api.GetTypeByName2(ctx,n.encode());f=lambda d:dict(size=api.ABISizeOfType(d,ty),alignment=api.ABIAlignmentOfType(d,ty),offsets=[api.OffsetOfElement(d,ty,i)for i in range(api.CountStructElementTypes(ty))]);a,b=f(gd),f(hd);assert a==b,n;layouts[n]=a
  assert len(layouts)==34 and layouts['struct.State']['size']==3504 and layouts['struct.State']['alignment']==8
  offsets=checked_state_offsets(api,api.GetNamedFunction(module,b'sub_780014f8'),gd)
  builder=api.CreateBuilderInContext(ctx);api.dll.LLVMSetLinkage.restype=None;api.dll.LLVMSetLinkage.argtypes=[c.c_void_p,c.c_uint];api.dll.LLVMSetValueName2.restype=None;api.dll.LLVMSetValueName2.argtypes=[c.c_void_p,c.c_char_p,c.c_size_t]
  helpers={};bridges=set();upstream=pin(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp');upstream_text=upstream.read_text()
  for fn in list(api.iterate(api.GetFirstFunction(module),api.GetNextFunction)):
   n=api.name(fn)
   if n.startswith('__remill_flag_computation_')or n.startswith('__remill_compare_'):
    assert not api.CountBasicBlocks(fn) and api.signature(fn)==('i1',['i1'])
    assert re.search(r'bool '+re.escape(n)+r'\(bool result(?:, \.\.\.)?\)\s*\{\s*return result;\s*}',upstream_text),n
    block=api.AppendBasicBlockInContext(ctx,fn,b'identity');api.PositionBuilderAtEnd(builder,block);api.BuildRet(builder,api.GetParam(fn,0));api.dll.LLVMSetLinkage(fn,8);helpers[n]='upstream bool identity, internal linkage'
   elif n=='__remill_undefined_8':
    api.dll.LLVMSetValueName2(fn,b'mw34_entry_initerm_undefined_8',len(b'mw34_entry_initerm_undefined_8'));bridges.add('mw34_entry_initerm_undefined_8')
   elif n.startswith('llvm.'):
    assert n=='llvm.ctpop.i8'
   elif n!='sub_780014f8':
    assert n in {'__remill_read_memory_32','__remill_write_memory_32','__remill_function_return','__remill_function_call'},n;bridges.add(n)
   api.SetFunctionCallConv(fn,0)
   for attr in (b'nounwind',b'willreturn'):api.RemoveEnumAttributeAtIndex(fn,FUNCTION_INDEX,api.GetEnumAttributeKindForName(attr,len(attr)))
   for attr in (b'target-cpu',b'target-features'):api.RemoveStringAttributeAtIndex(fn,FUNCTION_INDEX,attr,len(attr))
   for block in api.iterate(api.GetFirstBasicBlock(fn),api.GetNextBasicBlock):
    for inst in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
     assert not api.IsAIntToPtrInst(inst) and not api.IsAPtrToIntInst(inst)
     if api.IsACallInst(inst):
      assert api.IsAFunction(api.GetCalledValue(inst));api.SetInstructionCallConv(inst,0)
      for attr in(b'nounwind',b'willreturn'):api.RemoveCallSiteEnumAttribute(inst,FUNCTION_INDEX,api.GetEnumAttributeKindForName(attr,len(attr)))
  api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode());api.check(api.VerifyModule(module,2,c.byref(error)),error);api.check(api.PrintModuleToFile(module,str(out/'host.ll').encode(),c.byref(error)),error)
  api.DisposeBuilder(builder);api.DisposeTargetData(gd);api.DisposeTargetData(hd);api.DisposeModule(module);api.ContextDispose(ctx)
  for name in ('O0','O2'):run(llvm/'clang.exe',['--target=x86_64-pc-windows-msvc','-'+name,'-c',str(out/'host.ll'),'-o',str(out/f'provider-{name}.obj')],'compile-'+name)
  report=dict(passed=True,scope='Exact complete _initterm provider static lift/lowering/object preparation, no native or original execution credit',entry=0x780014f8,source_bytes=28,source_sha256=sha(out/'source.bin'),host_sha256=sha(out/'host.ll'),layouts=layouts,State_offsets=offsets,helpers=helpers,bridges=sorted(bridges),commands=commands,first_interval=[0x5e0248,0x5e024c],callback_success_admitted=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  for p in[ pathlib.Path(__file__),ROOT/'tools/m4-crt/recover_provider.py',ROOT/'tools/lifting/host_adapter.py',*out.iterdir()]:
   if p.is_file():pin(p)
  (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,helpers=helpers,bridges=sorted(bridges),report_sha256=sha(out/'report.json'))))
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
