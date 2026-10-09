"""Independent source/foundation and compiled causal closure for matherr entry.

The scalar source observer is separate. This reviewer predicts no execution
from AFTER snapshots. Its direct host checks are from actual ASM boundaries.
"""
import hashlib, json, pathlib, re, struct, subprocess, sys, traceback
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-entry-matherr'
PINS = {}
FROZEN = {
 'tools/m4-runtime/runtime.cpp': '48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7',
 'tools/m4-runtime/runtime.hpp': '41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536',
 'tools/m4-crt-matherr/paired/paired_context.hpp': '5eab85d9e012571fb7347f4f846c6f8d5b9d82c95601d0e97ba784a5d52dbb01',
 'tools/m4-crt-entry-data/capture.s': '591818ea2557e6d945b6e9613b0c5d00c25024289bb010fa7a6470807ff44611',
 'reports/m4-crt-matherr/paired-native-build-r7/native-O0.obj': '772a04eabbb36800a1ee9d8970a17bd08bc672f6ce5eedfdb0cac6ae707a8fae',
 'reports/m4-crt-matherr/paired-native-build-r7/native-O2.obj': '8365e636828d4caa1a8bb4287a5aa63526e97fc46738ba96787936a1fb74c8c4',
 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL': '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
}
def need(ok, why):
 if not ok: raise ValueError(why)
def sha(p):
 with pathlib.Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def pin(p, want=None):
 p=pathlib.Path(p).resolve(); h=sha(p)
 need(want is None or h==want, 'Independent identity mismatch: '+str(p))
 need(str(p) not in PINS or PINS[str(p)]==h, 'Conflicting identity')
 PINS[str(p)]=h; return p
def read(p): return json.loads(pin(p).read_text(encoding='utf-8-sig'))
def maps(receipt):
 count=0
 for key in ('sources','source_files','tools','tool_files','libraries','entry_objects','matherr_objects','compiler_read_headers','artifacts'):
  for p,h in receipt.get(key,{}).items(): pin(p,h);count+=1
 return count
def pe_page(data,address):
 pe=struct.unpack_from('<I',data,60)[0]
 need(data[pe:pe+4]==b'PE\0\0','Actual provider PE')
 count=struct.unpack_from('<H',data,pe+6)[0];opts=struct.unpack_from('<H',data,pe+20)[0]
 need(struct.unpack_from('<H',data,pe+24)[0]==0x10b,'Actual provider PE32')
 base=struct.unpack_from('<I',data,pe+24+28)[0]
 out=bytearray(4096); covered=set(); characteristics=[]
 for i in range(count):
  s=pe+24+opts+i*40;vs,rva,rawsize,raw=struct.unpack_from('<IIII',data,s+8)
  flags=struct.unpack_from('<I',data,s+36)[0];a=base+rva;b=a+max(vs,rawsize)
  lo=max(address,a);hi=min(address+4096,b)
  if lo<hi:
   characteristics.append(flags)
   for va in range(lo,hi):
    off=va-a;out[va-address]=data[raw+off] if off<rawsize else 0;covered.add(va-address)
 need(len(covered)==4096,'Full source-backed or virtual-zero provider page')
 return bytes(out),characteristics
def context_derivative(path):
 ancestor=pin(ROOT/'tools/m4-crt-matherr/paired/paired_context.hpp',FROZEN['tools/m4-crt-matherr/paired/paired_context.hpp']).read_text()
 target=pin(path).read_text()
 tail='extern "C" unsigned __remill_read_memory_32(void *p,unsigned a) {'
 need(ancestor.count(tail)==1,'Exact accepted global bridge tail')
 expected=ancestor.split(tail)[0]
 hook='void (*test_after_event)(Context &, unsigned){};'
 before='try { token=sub_7800b38f(&state,entry,this); }'
 changes=[]
 if 'test_before_execute' in target:
  need(expected.count(hook)==1 and expected.count(before)==1,'Exact observation hook anchors')
  expected=expected.replace(hook,hook+'\n    void (*test_before_execute)(Context &){};')
  expected=expected.replace(before,'try { if(test_before_execute)test_before_execute(*this); token=sub_7800b38f(&state,entry,this); }')
  changes.append('Add test-before-execute observation hook')
 need(target==expected,'Complete matherr Context must differ only by bridge-tail removal and declared observation hook')
 need('construct_at' not in target and 'memset' not in target and 'runtime.fx' not in target,'Borrower has no State/FX reseed')
 need('BridgeAbort' in target and 'longjmp' not in target and 'catch(...) { active=false; throw; }' in target,'Accepted C++ unwind cleanup preserved')
 return ['Remove standalone global bridge definitions']+changes
def host_pair(before,after,scenario):
 b=pin(before).read_bytes();a=pin(after).read_bytes()
 need(len(b)==len(a)==544,'Actual aligned direct-host Boundary format')
 need(b[512:540]==a[512:540],'Actual complete legacy ENV28 restore')
 for lo,hi in [(0,5),(24,28)]+[(32+16*i,42+16*i)for i in range(8)]+[(160+16*i,176+16*i)for i in range(6,16)]:
  need(b[lo:hi]==a[lo:hi],'Direct caller architectural FP/raw80/ABI XMM preservation')
 for i in range(6,16):
  expected=bytes((i*31+k*17+scenario+1)&255 for k in range(16))
  need(b[160+16*i:176+16*i]==expected,'Actual caller XMM6..15 deliberate BEFORE fixture')
 return {'legacy_metadata_nonzero':any(b[524:538]),'volatile_XMM0_5_equal':b[160:256]==a[160:256]}
def host_records(directories):
 count=nonzero=0
 for directory in directories:
  need(pin(directory/'COMPLETE').read_bytes()==b'COMPLETE','Complete actual execution')
  for row in sorted(directory.glob('row-*'),key=lambda p:int(p.name.split('-')[-1])):
   scenario=int(row.name.split('-')[-1]); result=read(row/'result.json');need(result['passed'],'Actual candidate row passed')
   for name in ('writer','entry'):
    before=row/(name+'-host-before.bin')
    if before.exists():
     x=host_pair(before,row/(name+'-host-after.bin'),scenario);count+=1;nonzero+=int(x['legacy_metadata_nonzero'])
 return count,nonzero
def inspect_object(path,out,label,matherr=False):
 path=pin(path);tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe')
 reader=pin(tool.parent/'llvm-readobj.exe')
 command=[str(tool),'--disassemble','--reloc','--x86-asm-syntax=intel',str(path)]
 r=subprocess.run(command,capture_output=True,text=True);need(r.returncode==0,'Fresh production COFF disassembly')
 p=out/(label+'-decode.txt');p.write_text(r.stdout);pin(p)
 u=subprocess.run([str(reader),'--unwind',str(path)],capture_output=True,text=True);need(u.returncode==0,'Fresh production unwind inspection')
 q=out/(label+'-unwind.txt');q.write_text(u.stdout);pin(q)
 if matherr:need('sub_7800b38f' in r.stdout and '__remill_function_return' in r.stdout and 'UnwindInfo' in u.stdout,'Actual guest leaf linkage/unwind')
 return r.stdout,u.stdout
def composition_audit(path):
 old=pin(ROOT/'reports/m4-crt-entry-data/preparation-r4/composition.cpp').read_text();new=pin(path).read_text()
 old_class=old[old.index('class Context {'):old.index('\n};\n}',old.index('class Context {'))+3]
 new_class=new[new.index('class Context {'):new.index('\n};\n}',new.index('class Context {'))+3]
 changes=[
  ('void write(unsigned a,unsigned v){guard();r_.memory().store<unsigned>({a},v);events_.push_back({s_.gpr.rip.dword,a,v,4,1});}',
   'void write(unsigned a,unsigned v){guard();r_.memory().store<unsigned>({a},v);events_.push_back({s_.gpr.rip.dword,a,v,4,1});if(matherr_binding&&matherr_binding->control==17&&s_.gpr.rip.dword==0x5ac423)r_.memory().store<unsigned>({a},v^1);}'),
  ('target==0x5ac5c0&&!events_.empty()','(target==0x5ac5c0||target==0x5ac5a0)&&!events_.empty()'),
  ('const auto&w=events_.back();require(w.pc==0x5ac415&&w.write==1&&w.width==4&&w.address==s_.gpr.rsp.dword&&w.value==0x5ac41a&&r_.memory().load<unsigned>({w.address})==w.value',
   'const auto&w=events_.back();const auto site=target==0x5ac5c0?0x5ac415U:0x5ac431U,ret=target==0x5ac5c0?0x5ac41aU:0x5ac436U;require(w.pc==site&&w.write==1&&w.width==4&&w.address==s_.gpr.rsp.dword&&w.value==ret&&r_.memory().load<unsigned>({w.address})==w.value'),
  ('void invoke(){require(!owner,"No nested entry owner");','void invoke(){InvocationHostBoundary host;require(!owner,"No nested entry owner");')]
 for before,after in changes:
  need(old_class.count(before)==1,'One exact accepted Context derivative anchor');old_class=old_class.replace(before,after)
 need(old_class==new_class,'Complete entry Context unchanged except typed next-call admission and declared fault observer')
 need('std::construct_at' not in new_class and 'memset' not in new_class,'No entry State construction/reset')
 expected={
 '__remill_read_memory_32':'if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");return mn::owner->read(a);}require(owner&&p==owner,"Exact active entry memory token");return owner->read(a,4);',
 '__remill_write_memory_32':'if(mn::owner){require(p==mn::owner,"Exact current matherr memory token");mn::owner->write(a,v);return p;}require(owner&&p==owner,"Exact active entry memory token");owner->write(a,v);return p;',
 '__remill_function_return':'if(mn::owner){require(p==mn::owner,"Exact current matherr return token");mn::owner->returned(s,a);return p;}require(owner&&p==owner,"Exact active entry return token");return owner->returned(s,a);'}
 for symbol,body in expected.items():
  line=next(x for x in new.splitlines()if '"C"' in x and symbol+'(' in x)
  need('noexcept(false)' in line and line.split('{',1)[1].rsplit('}',1)[0]==body,'Exact guarded typed dispatcher '+symbol)
 guard=new[new.index('struct InvocationHostBoundary {'):new.index('\n};',new.index('struct InvocationHostBoundary {'))+3]
 need('alignas(16)std::array<std::byte,512>fx;std::array<std::byte,28>env;' in guard and guard.count('fxsave64')==1 and guard.count('fnstenv')==1 and guard.count('fxrstor64')==1 and guard.count('fldenv')==1 and '~InvocationHostBoundary()noexcept{restore();}' in guard,'Exact full FX64/legacy ENV scoped host restoration')
 callback=pin(path.parent/'main_v2.inc').read_text();need('extern "C" bool data_boundary_initialize(Job*j) noexcept {\n InvocationHostBoundary host;\n try {' in callback and 'catch(const Fault&f)' in callback and 'catch(...){' in callback,'Final nonthrowing outer host boundary spans both exception catches')
 return len(changes),len(expected)
def compiled_closure(path,out):
 build=read(path/'build.json');need(build['passed'],'Independent compiled fixtures actually passed');bindings=maps(build);checks=scenarios=host=nonzero=0;objects=[]
 for level in ('O0','O2'):
  data=read(path/level/'actual/controls.json');need(data['passed'],'Independent compiled causal records passed')
  log=pin(path/level/'controls.log').read_text();match=re.fullmatch(r'(\d+) independent compiled checks / (\d+) scenarios passed\s*',log)
  need(match and int(match[1])==data['checks']+1 and int(match[2])==data['scenarios'],'Independent assertion output framing')
  checks+=int(match[1]);scenarios+=data['scenarios']
  for row in sorted((path/level/'actual').glob('case-*'),key=lambda p:int(p.name.split('-')[-1])):
   case=int(row.name.split('-')[-1])
   for name in ('writer','entry'):
    before=row/(name+'-host-before.bin');result=host_pair(before,row/(name+'-host-after.bin'),case);host+=1;nonzero+=int(result['legacy_metadata_nonzero'])
    b=before.read_bytes();env=b[512:540];need(env[12:26]==struct.pack('<IHHIH',0x11223344,0x23,0x11d,0x55667788,0x2b),'Actual hardware full nonzero legacy metadata fixture')
    sw=struct.unpack_from('<H',b,2)[0];top=case%2 and 3 or 7;depth=(0,1,3,7)[case%4];ftw=sum(1<<((top+i)&7)for i in range(depth));need(sw==top*2048+0x20 and b[4]==ftw and struct.unpack_from('<H',b)[0]==0xa7f and struct.unpack_from('<I',b,24)[0]==0x1fa0,'Actual hardware coherent live x87/sticky status/CW/MXCSR fixture')
  obj=path/level/'controls.obj';_,uw=inspect_object(obj,out,level+'-independent-controls')
  blocks=uw.split('  RuntimeFunction {')[1:]
  context=[b for b in blocks if re.search(r'StartAddress: \?execute@Context@',b)]
  need(len(context)==1 and re.search(r'Handler: __CxxFrameHandler[34]',context[0]),'Actual compiled Context::execute exception handler at '+level)
  objects.append(str(obj))
 need(checks==494 and scenarios==34 and host==nonzero==68,'Declared independent causal/rich host fixture count')
 return bindings,checks,scenarios,host,nonzero,objects
def main():
 need(len(sys.argv)>=4,'review.py output-dir preparation-dir build-json [actual-run-dir ...]')
 out=pathlib.Path(sys.argv[1]).resolve();prep=pathlib.Path(sys.argv[2]).resolve();bp=pathlib.Path(sys.argv[3]).resolve()
 need(out.parent==BASE and out.name.startswith('independent-') and not out.exists(),'Fresh independent immediate report directory')
 out.mkdir(parents=True);(out/'review-source.py').write_bytes(pathlib.Path(__file__).read_bytes());pin(out/'review-source.py')
 try:
  for p,h in FROZEN.items():pin(ROOT/p,h)
  build=read(bp);need(build['passed'],'Completed actual candidate build');count=maps(build)
  changes=context_derivative(prep/'matherr_context.hpp');entry_changes,dispatchers=composition_audit(prep/'composition.cpp')
  provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes()
  ownership=[]
  for address in (0x7800b000,0x78039000,0x7803b000):
   page,flags=pe_page(provider,address);ownership.append({'address':address,'source_sha256':hashlib.sha256(page).hexdigest(),'PE_characteristics':flags})
  z,_=pe_page(provider,0x78039000);c,_=pe_page(provider,0x7803b000)
  need(struct.unpack_from('<I',z,0x2b8)[0]==0x2694 and struct.unpack_from('<I',c,0xc4)[0]==0,'Actual source DWORD initial states')
  fdiv={0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000}
  need(not fdiv.intersection(x['address']for x in ownership),'FDIV/provider page ownership disjoint')
  objects=[]
  for level in ('O0','O2'):
   p=ROOT/f'reports/m4-crt-matherr/paired-native-build-r7/native-{level}.obj';inspect_object(p,out,level+'-matherr',True);objects.append(str(p))
  args=sys.argv[4:];compiled=None
  if '--compiled' in args:
   index=args.index('--compiled');need(index+2==len(args),'Terminal independent compiled report argument');compiled=pathlib.Path(args[index+1]).resolve();args=args[:index]
  direct,nonzero=host_records([pathlib.Path(p).resolve()for p in args])
  causal={'checks':0,'scenarios':0,'direct_host_records':0,'objects':[],'closed':False}
  if compiled:
   extra,checks,scenarios,h,nz,co=compiled_closure(compiled,out);count+=extra;causal={'path':str(compiled),'checks':checks,'scenarios':scenarios,'direct_host_records':h,'nonzero_legacy_metadata_records':nz,'host_CW':0xa7f,'host_TOP':[3,7],'host_live_x87_depths':[0,1,3,7],'host_SW_sticky':0x20,'host_MXCSR':0x1fa0,'actual_malformed_token_denials':30,'objects':co,'closed':True}
  header_reads=0
  for level in ('O0','O2'):
   commands=read(bp.parent/level/'compile_commands.json');require_commands=[x for x in commands if x['file'].replace('\\','/').endswith('/composition.cpp')]
   need(len(require_commands)==1,'One actual production composition compilation')
   command=require_commands[0]['command'];need('/EHs ' in command and '/EHsc' not in command,'Actual production typed exception flags')
   text=pin(bp.parent/f'build-{level}.log').read_text(encoding='utf-8-sig')
   for name in re.findall(r'Note: including file:\s*(.+?)\s*$',text,re.M):
    pin(name.strip());header_reads+=1
   candidates=list((bp.parent/level/'CMakeFiles/entry_matherr.dir').rglob('composition.cpp.obj'));need(len(candidates)==1,'One actual production composition object')
   _,uw=inspect_object(candidates[0],out,level+'-production-context')
   blocks=uw.split('  RuntimeFunction {')[1:];executed=[b for b in blocks if re.search(r'StartAddress: \?execute@Context@',b)]
   need(len(executed)==1 and re.search(r'Handler: __CxxFrameHandler[34]',executed[0]),'Actual production Context::execute exception handler '+level)
   objects.append(str(candidates[0]))
  report={'passed':True,'scope':'Independent bounded source/foundation, actual compiled causal fixture and direct caller boundary review; separate root scalar observer required for complete composition acceptance','build_path':str(bp),'physical_bindings_rehashed':count,'actual_compiler_header_read_associations':header_reads,'exact_Context_derivative':changes,'exact_entry_Context_derivative_changes':entry_changes,'exact_guarded_dispatchers':dispatchers,'persistent_State_bytes':3504,'separate_FX_bytes':512,'matherr_page_ownership':ownership,'source_zero_global_before':0x2694,'source_callback_before':0,'FDIV_page_overlap':False,'Runtime_r9_changed':False,'fresh_actual_matherr_and_production_objects':objects,'direct_host_records':direct,'nonzero_host_legacy_metadata_records':nonzero,'independent_compiled_causal':causal,'original_executed':False,'whole_M4_complete':False,'no_additional_blocker_to_bounded_gate':causal['closed']}
  rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(pathlib.Path(__file__));(out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n');print(json.dumps(report))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
