"""Read-only independent exact-entry IR/ABI/source and first-fault audit."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry';OUT=BASE/'independent-first-fault-static-r2'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS={};COMMANDS=[]
def need(ok,w):
 if not ok:raise ValueError(w)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();got=sha(p);need(h is None or got==h,'Frozen physical identity '+str(p));PINS[str(p)]=got;return p
def js(p,h=None):return json.loads(pin(p,h).read_text())
def flat(p):
 d=js(p);d=d.get('files',d)
 for p,h in d.items():pin(p,h)
 return len(d)
def run(argv,name):
 argv=list(map(str,argv));r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append(dict(command=argv,exit_code=r.returncode,log=str(p),sha256=sha(p)));need(r.returncode==0,'Independent read-only decode '+name);return r.stdout.decode(errors='replace')
def functions(s):
 return {m.group(1):m.group(2).splitlines()for m in re.finditer(r'^define [^\n]+@([A-Za-z0-9_]+)\([^\n]*\)[^\n]*\{\n(.*?)^\}',s,re.M|re.S)}
def normalized(lines):return [re.sub(r' #\d+','',x.replace('fastcc ',''))for x in lines if x.strip()]
def inverse(original,native):
 a,b=functions(original),functions(native);roots={k for k in a if k.startswith('sub_')};need(roots=={k for k in b if k.startswith('sub_')},'Exact complete root definition set')
 direct=0
 for name in roots:
  old=a[name];new=b[name];enters=[x for x in new if '@mw34_crte_enter('in x];need(len(enters)==1,'One actual typed root-entry check per complete function');new=[x for x in new if x not in enters]
  targets=[m.group(1)for line in old if(m:=re.search(r'call (?:fastcc )?ptr @(sub_[0-9a-f]+)\(',line))]
  i=0;restored=[]
  for line in new:
   if '@mw34_crte_direct('in line:need(i<len(targets),'Bounded exact original direct-call seam');line=line.replace('@mw34_crte_direct(', '@'+targets[i]+'(');i+=1
   restored.append(line)
  need(i==len(targets)and normalized(old)==normalized(restored),'Whole original instruction calculations unchanged after inverse seams: '+name);direct+=i
 need(direct==8,'Exactly eight source direct-call seams')
 types=lambda s:dict(re.findall(r'^%([^ =]+) = type (.*)$',s,re.M))
 need(types(original)==types(native)and len(types(original))==34,'Literal whole named State type definitions unchanged')
 for name,body in b.items():
  if name not in roots:need(name.startswith('__remill_')and [x for x in normalized(body)if not re.match(r'^\w+:',x)]==['  ret i1 %0'],'Annotation helper is exact scalar identity only')
 need('inttoptr'not in native and'ptrtoint'not in native and'longjmp'not in native and'setjmp'not in native,'No guest address pointer casts or foreign longjmp')
 return dict(roots=sorted(roots),direct_seams=direct,named_types=len(types(native)),instruction_calculation_changes=0)
def main():
 need(not OUT.exists(),'Fresh private independent entry audit');OUT.mkdir(parents=True)
 try:
  src=Path(__file__).resolve();(OUT/'review-source.py').write_bytes(src.read_bytes());pin(src);pin(OUT/'review-source.py')
  preparation=js(BASE/'preparation-r2/report.json','0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724');flat(BASE/'preparation-r2/pins.json')
  host=js(BASE/'native-preparation-r1/report.json');flat(BASE/'native-preparation-r1/pins.json')
  build=js(BASE/'first-fault-build-r4/build.json');need(build['passed']and not build['original_executed'],'Native-only final first-fault recipe')
  for key in('source_files','primary_pre_call_tools','artifacts'):
   for p,h in build[key].items():pin(p,h)
  observe=js(BASE/'first-fault-observation-r2/report.json','880f25fffaea5f527d8935aa6f420f5d7f914e1084f5d163eac6b0fd987acba5');pin(BASE/'first-fault-observation-r2/pins.json','09bd235d445aa61568cae03ba578037e6d174f7a96ea73cde59e183494f56c8e');flat(BASE/'first-fault-observation-r2/pins.json')
  need(observe['passed']and len(observe['rows'])==2 and len(observe['own_corruption_rejects'])==36 and observe['guest_source_PCs_observed_natively']==16,'Exact existing first-fault raw scope')
  for name in('first-fault-build-r1','first-fault-build-r2','first-fault-build-r3','first-fault-observation-r1','preparation-r1','independent-first-fault-static-r1'):
   for p in(BASE/name).rglob('*'):
    if p.is_file():pin(p)
  image=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');parser=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638');spec=importlib.util.spec_from_file_location('own_exact_metadata',parser);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);pe=mod.PEImage(image.read_bytes())
  need(pe.image_base+pe.entry_point_rva==0x5ac3a0,'Actual PE ordinary entry')
  spans=[]
  for source in preparation['source_spans']:
   start,size=source['address'],source['size'];offset,_=pe.rva_range(start-pe.image_base,size);b=pe.data[offset:offset+size];need(hashlib.sha256(b).hexdigest()==source['sha256'],'Every complete source byte span exact original');pin(source['path'],source['sha256']);spans.append((start,size))
  original=(BASE/'preparation-r2/guest.ll').read_text();native=(BASE/'native-preparation-r1/candidate.ll').read_text();need(sha(BASE/'native-preparation-r1/candidate.ll')==host['host_sha256'],'Exact native IR derivative');ir=inverse(original,native)
  decoder=pin(LLVM/'llvm-objdump.exe');readobj=pin(LLVM/'llvm-readobj.exe');decodes=[]
  for i,(address,size)in enumerate(spans):run([decoder,'-d','--x86-asm-syntax=intel','--start-address='+str(address),'--stop-address='+str(address+size),image],f'fresh-source-{address:x}.txt')
  for b in build['builds']:
   p=pin(b['object']);meta=run([readobj,'--symbols','--relocations','--unwind',p],b['level']+'-full-entry-coff.txt');run([decoder,'-d','--print-imm-hex',p],b['level']+'-full-entry-code.txt');need('StartAddress: sub_5ac3a0 'in meta and'__remill_read_memory_32'in meta and'__remill_write_memory_32'in meta and'__remill_function_call'in meta,'Actual entry unwind and checked typed memory/call dependencies');decodes.append(str(p))
   obj=next(Path(b['directory']).rglob('first_fault.cpp.obj'));pin(obj);meta=run([readobj,'--symbols','--relocations','--unwind',obj],b['level']+'-actual-adapter-coff.txt');run([decoder,'-d','--print-imm-hex',obj],b['level']+'-actual-adapter-code.txt');need('__CxxFrameHandler3'in meta and'sub_5ac3a0'in meta,'Actual enclosing C++ EH and complete translated entry call');decodes.append(str(obj))
  adapter=(ROOT/'tools/m4-crt-entry/first_fault.cpp').read_text();need('sub_5ac3a0(State*,unsigned,void*) noexcept(false)'in adapter and adapter.count('noexcept(false)')==10,'Exact throwing typed bridge/header declaration domain');need('r_.call_import({slot},{0x5ac3d5})'in adapter and'events_.size()==15'in adapter and'r.poisoned()'in adapter and'chain[0].handler.value==0x5ac586'in adapter,'First required service refuses completion and observes source-created FS chain')
  report=dict(passed=True,scope='Independent exact complete-entry static inverse-IR/source/typed ABI/object and scoped root first-fault observations; independent causal compiled fixtures remain next',IR=ir,source_spans=spans,source_unique_PCs=preparation['unique_instructions'],ordinary_entry_PCs=preparation['ordinary_entry_instructions'],reached_native_PCs=16,root_raw_rows=2,root_raw_corruptions=36,fresh_compiled_object_decodes=4,objects=decodes,actual_first_call=0x5ac3cf,required_IAT=0x5bb5a4,required_symbol='MSVCRT.dll!__set_app_type',installed_guest_SEH_handler=0x5ac586,guest_memory_only_FS=True,actual_SEH_dispatch=False,no_author_recovery_adapter_or_model_import=True,original_executed=False,reviewer_native_execution=False,full_CRT=False,full_startup=False,whole_M4_complete=False,limitations=['Prepared148-PC/11-root object is not148-PC native execution credit','Authored initialState/stack/FS policy, not actual original startup State','No numerical/live-stack coherence or actual host FP preservation claim','Only first unregistered required import; no service return or initialized CRT/menu behavior','Inverse exact IR seams prove retained original calculations, not semantic completion of those still-unimplemented services'],commands=COMMANDS)
  (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(OUT/'report.json')
  for p,h in PINS.items():need(sha(p)==h,'Stable independent read-only audit')
  (OUT/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n');print(json.dumps({'passed':True,'report_sha256':sha(OUT/'report.json'),'pins_sha256':sha(OUT/'pins.json'),'bindings':len(PINS)}))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
