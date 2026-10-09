"""Preserve complete provider CFG; mechanically replace three unsafe FP transfers."""
import argparse,ctypes as c,hashlib,json,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lifting'))
from host_adapter import LLVM,HOST_LAYOUT,FLAG_HELPERS,FUNCTION_INDEX,checked_state_offsets
sys.path.insert(0,str(ROOT/'tools/x87-repair'))
from adapt_control import ControlLLVM
from prepare import ENTRIES
SSA=r'%[A-Za-z0-9_.$]+'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def need(v,why):
 if not v:raise ValueError(why)
def blocks(body):
 out={'entry':[]};key='entry'
 for raw in body.splitlines():
  line=raw.split(';',1)[0].strip()
  if not line:continue
  if re.fullmatch(r'[A-Za-z0-9_.$]+:',line):key=line[:-1];need(key not in out,'Duplicate CFG block');out[key]=[]
  else:out[key].append(line)
 return out
def pc_model(body,entry):
 bs=blocks(body);pending=[('entry',entry)];seen={};pcs={};calls=[]
 while pending:
  key,pc=pending.pop()
  if key in seen:need(seen[key]==pc,'Conflicting static block PC');continue
  seen[key]=pc;local={'%NEXT_PC':pc,'%program_counter':entry};select=None;current=None
  for line in bs[key]:
   m=re.fullmatch(r'('+SSA+r') = load i32, ptr (%NEXT_PC|%RETURN_PC), align 4',line)
   if m:local[m[1]]=local.get(m[2]);continue
   m=re.fullmatch(r'('+SSA+r') = (add|sub) i32 ('+SSA+r'), (-?\d+)',line)
   if m and isinstance(local.get(m[3]),int):local[m[1]]=(local[m[3]]+(1 if m[2]=='add' else -1)*int(m[4]))&0xffffffff;continue
   m=re.fullmatch(r'('+SSA+r') = select i1 '+SSA+r', i32 ('+SSA+r'), i32 ('+SSA+r')',line)
   if m and m[2] in local and m[3] in local:local[m[1]]=(local[m[2]],local[m[3]]);continue
   m=re.fullmatch(r'store i32 ('+SSA+r'), ptr (%NEXT_PC|%RETURN_PC|%PC), align (?:4|8)',line)
   if m:
    value=local.get(m[1]);local[m[2]]=value
    if m[2]=='%PC' and isinstance(value,int):
     if current is None:current=value;pcs[key]=current
   if '@sub_' in line and 'call ptr' in line:calls.append({'instruction':current,'line':line})
  term=bs[key][-1];edges=re.findall(r'label %([A-Za-z0-9_.$]+)',term);n=local.get('%NEXT_PC')
  if term.startswith('ret ptr '):need(not edges,'Return has successor');continue
  need(term.startswith('br ') and len(edges) in (1,2),'Unsupported CFG terminator')
  if len(edges)==2:need(isinstance(n,tuple) and len(n)==2,'Branch PC not exact select');pending.extend(zip(edges,n))
  else:need(isinstance(n,int),'Unknown fallthrough PC');pending.append((edges[0],n))
 need(set(seen)==set(bs),'Unreachable or missing CFG block');return {'instruction_PCs':sorted(set(pcs.values())),'block_PCs':pcs,'direct_call_sites':calls,'all_blocks_reachable':True}
def undef_proof(body,offsets):
 # Every undefined byte must terminate directly in AF. No GPR/memory/branch
 # use is allowed. AF is architecturally undefined at logical-op exits.
 roots=re.findall(r'('+SSA+r') = call(?: zeroext)? i8 @__remill_undefined_8\(\)(?: #\d+)?',body);proof=[]
 for root in roots:
  uses=[x.strip() for x in body.splitlines() if root in re.findall(SSA,x) and not x.strip().startswith(root+' =')]
  need(len(uses)==1,'Undefined SSA escape');m=re.fullmatch(r'store i8 '+re.escape(root)+r', ptr ('+SSA+r'), align 1',uses[0]);need(m and offsets.get(m[1])==2069,'Only undefined AF allowed');proof.append({'root':root,'terminal':uses[0],'offset':2069})
 return {'undefined_calls':len(roots),'only_undefined_exit_flag':'AF','defined_exit_mask':0x8c5,'SSA_terminals':proof}
def adapt(folder):
 need(folder.is_relative_to(ROOT/'reports/m4-crt-control'),'Private exact provider IR required');guest=folder/'guest.ll';baseline=guest.read_text();need(set(re.findall(r'^define ptr @([^ (]+)',baseline,re.M))=={f'sub_{x:x}' for x in ENTRIES},'Exactly four complete static provider definitions');need(not re.search(r'\b(?:undef|poison|atomic|volatile|float|double|x86_fp80|inttoptr|ptrtoint)\b',baseline),'Unreviewed instruction/value domain');need('__remill_missing_block' not in baseline,'Incomplete provider CFG')
 api=ControlLLVM(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll');ctx=api.ContextCreate();module,buffer,error=c.c_void_p(),c.c_void_p(),c.c_void_p();gd=hd=builder=None
 try:
  api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest).encode(),c.byref(buffer),c.byref(error)),error);api.check(api.ParseIRInContext(ctx,buffer,c.byref(module),c.byref(error)),error);api.check(api.VerifyModule(module,2,c.byref(error)),error)
  gd=api.CreateTargetData(api.GetDataLayoutStr(module));hd=api.CreateTargetData(HOST_LAYOUT.encode());layouts={};proofs={};pc_union=set()
  for name in re.findall(r'^%([^ =]+) = type',baseline,re.M):
   t=api.GetTypeByName2(ctx,name.encode());need(t and not api.IsOpaqueStruct(t),'Complete State types')
   def layout(d):return {'size':api.ABISizeOfType(d,t),'align':api.ABIAlignmentOfType(d,t),'offsets':[api.OffsetOfElement(d,t,i) for i in range(api.CountStructElementTypes(t))]}
   x,y=layout(gd),layout(hd);need(x==y,'Complete State layout changed');layouts[name]=x
  need(layouts['struct.State']['size']==3504,'State3504 binding')
  for entry in ENTRIES:
   name=f'sub_{entry:x}';fn=api.GetNamedFunction(module,name.encode());need(api.signature(fn)==('ptr',['ptr','i32','ptr']),'Exact static entry ABI');body=re.search(r'^define ptr @'+name+r'[^\n]+\{\n(.*?)^}',baseline,re.M|re.S)[1];offsets=checked_state_offsets(api,fn,gd);proofs[name]={'CFG':pc_model(body,entry),'undefined':undef_proof(body,offsets),'State_offsets':offsets};pc_union.update(proofs[name]['CFG']['instruction_PCs'])
  original=set()
  for path in [ROOT/'reports/m4-crt-next/recovery-r2/0x780042e1-llvm.txt',ROOT/'reports/m4-crt-next/recovery-r2/0x7801129b-llvm.txt']:
   original.update(int(x,16) for x in re.findall(r'^([0-9a-f]+): [0-9a-f]{2} ',path.read_text(),re.M))
  need(pc_union==original and len(original)==148,'Complete original148 instruction CFG equality')
 finally:
  for d in (gd,hd):
   if d:api.DisposeTargetData(d)
  if module.value:api.DisposeModule(module)
  api.ContextDispose(ctx)
 # Exact SSA-bound instruction replacements; retain addresses and all integer
 # operations/CALLs/RETs. Preserve original baseline IR unmodified.
 edits=[(r'  %46 = call i32 @__remill_fpu_exception_test\(i32 noundef 127\) #4\n  call void @__remill_fpu_exception_clear\(i32 noundef %46\) #4\n  store ptr %45, ptr %MEMORY, align 4', '  %cf_wait = call ptr @mw34_cf_wait(ptr %state, i32 %43, ptr %45)\n  store ptr %cf_wait, ptr %MEMORY, align 4','FWAIT'),
 (r'  %55 = getelementptr inbounds nuw i8, ptr %state, i32 2768\n  %56 = load i16, ptr %55, align 16\n  %57 = call noundef ptr @__remill_write_memory_16\(ptr noundef %54, i32 noundef %53, i16 noundef zeroext %56\) #3','  %57 = call ptr @mw34_cf_store_cw(ptr %state, i32 %53, ptr %54)','FNSTCW'),
 (r'  %267 = getelementptr inbounds nuw i8, ptr %state, i32 2768\n  %268 = call noundef zeroext i16 @__remill_read_memory_16\(ptr noundef %266, i32 noundef %265\) #3\n  store i16 %268, ptr %267, align 16\n  %269 = lshr i16 %268, 10\n  %270 = and i16 %269, 3\n  %271 = zext nneg i16 %270 to i32\n  call void @__remill_fpu_set_rounding\(i32 noundef %271\) #4\n  store ptr %266, ptr %MEMORY, align 4','  %cf_load = call ptr @mw34_cf_load_cw(ptr %state, i32 %265, ptr %266)\n  store ptr %cf_load, ptr %MEMORY, align 4','FLDCW')]
 candidate=baseline;repairs=[]
 for pattern,replacement,name in edits:
  candidate,count=re.subn(pattern,replacement,candidate);need(count==1,'Exact one '+name+' instruction lowering');repairs.append({'instruction':name,'replacement_calls':count,'exact_old_pattern':pattern,'replacement':replacement})
 for name in ['__remill_fpu_exception_test','__remill_fpu_exception_clear','__remill_write_memory_16','__remill_read_memory_16','__remill_fpu_set_rounding']:
  candidate=re.sub(r'^declare[^\n]*@'+name+r'\([^\n]+\n','',candidate,flags=re.M);need('@'+name not in candidate,'Unsafe/unreviewed host helper remains')
 for name in ('wait','store_cw','load_cw'):candidate+='\ndeclare ptr @mw34_cf_'+name+'(ptr, i32, ptr)\n'
 private=folder/'candidate.ll';private.write_text(candidate);ctx=api.ContextCreate();module,buffer,error=c.c_void_p(),c.c_void_p(),c.c_void_p();builder=None
 try:
  api.check(api.CreateMemoryBufferWithContentsOfFile(str(private).encode(),c.byref(buffer),c.byref(error)),error);api.check(api.ParseIRInContext(ctx,buffer,c.byref(module),c.byref(error)),error);api.check(api.VerifyModule(module,2,c.byref(error)),error);builder=api.CreateBuilderInContext(ctx)
  annotations=FLAG_HELPERS|{'__remill_compare_eq','__remill_compare_neq'};bridges={'__remill_read_memory_32':('i32',['ptr','i32']),'__remill_write_memory_32':('ptr',['ptr','i32','i32']),'__remill_function_return':('ptr',['ptr','i32','ptr']),**{f'mw34_cf_{n}':('ptr',['ptr','i32','ptr']) for n in ('wait','store_cw','load_cw')}}
  nounwind=api.GetEnumAttributeKindForName(b'nounwind',8);counts={}
  for fn in list(api.iterate(api.GetFirstFunction(module),api.GetNextFunction)):
   name=api.name(fn)
   if name in annotations or name=='__remill_undefined_8':
    need(not api.CountBasicBlocks(fn),'Annotation definition preexists');need(api.signature(fn)==(('i8',[]) if name=='__remill_undefined_8' else ('i1',['i1'])),'Scalar annotation signature');block=api.AppendBasicBlockInContext(ctx,fn,b'identity');api.PositionBuilderAtEnd(builder,block);api.BuildRet(builder,api.ConstInt(api.GetReturnType(api.GlobalGetValueType(fn)),0,0) if name=='__remill_undefined_8' else api.GetParam(fn,0))
   elif not api.CountBasicBlocks(fn):need((name in bridges and api.signature(fn)==bridges[name]) or (name=='llvm.ctpop.i8' and api.signature(fn)==('i8',['i8'])),'Unreviewed external ABI '+name)
   api.SetFunctionCallConv(fn,0);api.RemoveEnumAttributeAtIndex(fn,FUNCTION_INDEX,nounwind)
   for attr in (b'target-cpu',b'target-features'):api.RemoveStringAttributeAtIndex(fn,FUNCTION_INDEX,attr,len(attr))
   for b in api.iterate(api.GetFirstBasicBlock(fn),api.GetNextBasicBlock):
    for ins in api.iterate(api.GetFirstInstruction(b),api.GetNextInstruction):
     need(not api.IsAIntToPtrInst(ins) and not api.IsAPtrToIntInst(ins),'Pointer conversion')
     if api.IsACallInst(ins):
      callee=api.GetCalledValue(ins);need(api.IsAFunction(callee),'Indirect host call');target=api.name(callee);counts[target]=counts.get(target,0)+1;api.SetInstructionCallConv(ins,0);api.RemoveCallSiteEnumAttribute(ins,FUNCTION_INDEX,nounwind)
  prototype=api.GetNamedFunction(module,b'sub_780042e1');enter=api.AddFunction(module,b'mw34_cf_enter',api.GlobalGetValueType(prototype));f=api.dll.LLVMPositionBuilderBefore;f.argtypes=[c.c_void_p,c.c_void_p];f.restype=None
  for entry in ENTRIES:
   fn=api.GetNamedFunction(module,f'sub_{entry:x}'.encode());f(builder,api.GetFirstInstruction(api.GetFirstBasicBlock(fn)));args=(c.c_void_p*3)(*(api.GetParam(fn,i) for i in range(3)));api.BuildCall2(builder,api.GlobalGetValueType(enter),enter,args,3,b'checked_entry')
  api.SetTarget(module,b'x86_64-pc-windows-msvc');api.SetDataLayout(module,HOST_LAYOUT.encode());api.check(api.VerifyModule(module,2,c.byref(error)),error);host=folder/'host.ll';api.check(api.PrintModuleToFile(module,str(host).encode(),c.byref(error)),error)
  (folder/'layout.json').write_text(json.dumps({'passed':True,'scope':'Actual complete four-body static provider CFG; bounded transfer repairs; runtime integration pending','guest_sha256':sha(guest),'candidate_sha256':sha(private),'host_sha256':sha(host),'source_sha256':sha(__file__),'complete_original_instructions':len(original),'all_complete_State_layouts_equal':True,'State_bytes':3504,'layouts':layouts,'functions':proofs,'call_counts':counts,'direct_guest_calls':3,'checked_entry_hooks':4,'mechanical_repairs':repairs,'defined_exit_flags_mask':0x8c5,'excluded_undefined_exit_flags':['AF'],'host_FP_exception_or_rounding_helpers_remaining':0,'whole_M4_complete':False},indent=2)+'\n')
 finally:
  if builder:api.DisposeBuilder(builder)
  if module.value:api.DisposeModule(module)
  api.ContextDispose(ctx)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=pathlib.Path);a=p.parse_args();adapt(a.folder.resolve())
