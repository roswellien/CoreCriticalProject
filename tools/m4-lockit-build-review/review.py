"""Independent bounded packed-ABI and actual root124 final-link review.

No acceptance capture payload is read.  Historical capture pins stay outside
this compile/link review; source, compiled inputs and executable pins are physical.
"""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-lockit-build-review'
PREP=ROOT/'reports/m4-joint-startup124/preparation-r3'
PREPSHA='4954639d674ac7421d4567cd6bc496c2222614d7e986da0cb54dc05da225b3e1'
NPREP=ROOT/'reports/m4-lockit-native/preparation-r3'
NPSHA='4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d'
OLD=ROOT/'reports/m4-joint-startup120/preparation-r3'
OLDSHA='46e510f76d00722b2f46ef015d946a8ced3e0af0286e5ef8baf06e37797ff810'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def machine(p,pe=False):
 with Path(p).open('rb') as f:
  if pe:
   assert f.read(2)==b'MZ';f.seek(60);e=struct.unpack('<I',f.read(4))[0];f.seek(e);assert f.read(4)==b'PE\0\0'
  return struct.unpack('<H',f.read(2))[0]
def array(text,name):
 return [int(x,0)for x in re.search(r'\b'+name+r'\s*\{([^}]*)\}',text).group(1).split(',')]
def emit(out,report,pins):
 report['files']=pins;(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (out/'pins.json').write_text(json.dumps({'files':pins|{str(out/'report.json'):sha(out/'report.json')}},indent=2)+'\n')
 print(json.dumps({'passed':True,'report':str(out/'report.json'),'sha256':sha(out/'report.json')}))
def common(out):
 out=BASE/out;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(str(p),h,v);pins[str(p)]=v;return p
 for p,h in[(PREP/'report.json',PREPSHA),(NPREP/'report.json',NPSHA),(OLD/'report.json',OLDSHA)]:pin(p,h)
 p=json.loads((PREP/'report.json').read_bytes());n=json.loads((NPREP/'report.json').read_bytes());old=json.loads((OLD/'report.json').read_bytes())
 pin(__file__);return out,pins,pin,p,n,old
def abi(name):
 started=time.perf_counter();out,pins,pin,p,n,old=common(name)
 protocol=pin(PREP/'joint_protocol.hpp');oldproto=pin(OLD/'joint_protocol.hpp')
 text=protocol.read_text();oldtext=oldproto.read_text()
 packed=lambda t:t.split('#pragma pack(push,1)',1)[1].split('#pragma pack(pop)',1)[0]
 assert packed(text)==packed(oldtext),'Packed schema changed from accepted120'
 fixed=array(text,'pages');selected=array(text,'entries');extra_text=pin(PREP/'registration_contract.hpp').read_text();extra=array(extra_text,'registration_pages');registrations=array(extra_text,'registration_roots')
 assert selected==[x['entry']for x in p['selected_order']] and len(selected)==len(set(selected))==124
 assert registrations==p['registration_roots'] and len(registrations)==len(set(registrations))==96 and set(registrations)<=set(selected)
 assert extra==p['extra_pages'] and len(fixed)==len(set(fixed))==17 and len(extra)==len(set(extra))==26 and not set(fixed)&set(extra)
 assert set(selected)-{x['entry']for x in old['selected_order']}=={0x411010,0x4dc140,0x500660,0x5968f0}
 assert [x for x in selected if x not in n['new_roots']]==[x['entry']for x in old['selected_order']]
 assert len(set(fixed+extra))==43 and {0x7810a000,0x78145000,0x78146000}<=set(extra)
 compiler=pin(LLVM/'clang-cl.exe');source=pin(ROOT/'tools/m4-lockit-build-review/abi_witness.cpp');pin(ROOT/'tools/m4-lockit-build-review/build_abi.ps1')
 includes=[PREP,ROOT/'tools/m4-runtime',ROOT/'tools/m4-startup',ROOT/'runtime']
 levels=[]
 for level,flag in [('O0','/Od'),('O2','/O2')]:
  exe=out/f'abi-{level}.exe';obj=out/f'abi-{level}.obj'
  args=[str(compiler),'/nologo','/std:c++20','/MD','/EHs','/clang:-frounding-math','-Wno-invalid- offsetof'.replace('- offsetof','-offsetof'),flag,'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0']
  args += ['/I'+str(x)for x in includes]+['/imsvc'+str(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include'),'/Fo'+str(obj),'/Fe'+str(exe),str(source),'/link','/machine:x64']
  c=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=60);(out/f'{level}-compile.log').write_bytes(c.stdout+c.stderr);assert c.returncode==0,c.stderr[-3000:]
  assert machine(obj)==0x8664 and machine(exe,True)==0x8664
  result=subprocess.run([str(exe)],capture_output=True,timeout=10);assert result.returncode==0;values=json.loads(result.stdout);(out/f'{level}-witness.json').write_text(json.dumps(values,indent=2)+'\n')
  assert values['Native']==159716 and values['CPU_after']==[76,116] and values['FX_before']==[116,628]
  pin(obj);pin(exe);pin(out/f'{level}-compile.log');pin(out/f'{level}-witness.json');levels.append(dict(level=level,values=values,command=args))
 emit(out,dict(passed=True,scope='Independent AMD64 compiler offsetof witness and fixed/external source page geometry; no game or native corpus execution credit',packed_schema_identical_to_accepted120=True,fixed_pages=fixed,external_pages=extra,unique_whole_pages=43,selected_roots=124,registrations=96,levels=levels,elapsed_seconds=time.perf_counter()-started),pins)
def link(buildpath,digest,name):
 started=time.perf_counter();out,pins,pin,p,n,old=common(name)
 buildpath=pin(buildpath,digest);b=json.loads(buildpath.read_bytes());assert b['passed'] and b['preparation_sha256']==PREPSHA and Path(b['preparation']).resolve()==(PREP/'report.json').resolve()
 declared=json.loads(pin(buildpath.parent/'pins.json').read_bytes())['files'];sources=b['sources']
 # Check all candidate authored/generated physical files and actual compiled inputs,
 # without hashing historical capture bundles outside this bounded review.
 for directory in [PREP,NPREP]:
  for x in directory.rglob('*'):
   if x.is_file() and x.suffix in {'.cpp','.hpp','.h','.inc','.txt','.ll','.bc','.obj'}:
    key=str(x.resolve());assert key in sources,(key,'not bound in build sources');pin(x,sources[key])
 levels=[];nm=pin(LLVM/'llvm-nm.exe');new_symbols=[]
 for level in ['O0','O2']:
  w=b['workers'][level];exe=pin(w['path'],w['sha256']);assert machine(exe,True)==0x8664;folder=exe.parent;graph=pin(folder/'build.ninja',declared[str(folder/'build.ninja')]).read_text()
  assert '/machine:x64'in graph
  line=next(x for x in graph.splitlines()if x.startswith('build '+exe.name+': CXX_EXECUTABLE_LINKER'))
  tokens=line.split(' ',3)[3].split(' |')[0].split(' ');decode=lambda x:x.replace('$:',':').replace('$ ',' ')
  linked={str((folder/Path(decode(t))).resolve()).casefold()for t in tokens if t.endswith(('.obj','.lib'))}
  objects=w['objects'];assert objects==p['objects'][level] and len(objects)==363
  literal={str(pin(x,sources[str(Path(x).resolve())])).casefold()for x in objects};assert len(literal)==363 and literal<=linked
  for obj in objects:assert machine(obj)==0x8664
  added=[x for x in objects if x not in old['objects'][level]];assert len(added)==12 and all('/m4-lockit-source/'in x.replace('\\','/')for x in added)
  for obj in added:
   run=subprocess.run([str(nm),'--defined-only','--extern-only',obj],capture_output=True,timeout=10);assert run.returncode==0
   symbols=run.stdout.decode();assert symbols.count('_body')==1,(obj,symbols);new_symbols.append(dict(level=level,object=obj,defined_external_symbols=symbols.splitlines()))
  compiled={}
  for l in graph.splitlines():
   if not l.startswith('build ')or': CXX_COMPILER_'not in l:continue
   output,rest=l[6:].split(': CXX_COMPILER_',1);source=rest.split(' ',1)[1].split(' ||')[0].split(' |')[0]
   compiled[str((folder/Path(decode(source))).resolve()).casefold()]=str((folder/Path(decode(output))).resolve()).casefold()
  for source in [PREP/'native_main.cpp',Path(p['native_library']),Path(p['native_include'])/'crt_services.cpp']:
   key=str(source.resolve()).casefold();assert key in compiled and compiled[key]in linked
  for source,obj in compiled.items():
   # Case-insensitive dictionary lookup preserves exact reported Windows path pins.
   s=next(k for k in sources if k.casefold()==source);o=next(k for k in declared if k.casefold()==obj)
   pin(s,sources[s]);pin(o,declared[o]);assert machine(o)==0x8664
  writer=pin(ROOT/f'reports/m4-capture-direct/build-r4/capture_direct-{level}.obj');preserve=pin(ROOT/'reports/m4-capture-direct/build-r4/preserve.obj')
  assert machine(writer)==machine(preserve)==0x8664
  assert linked-literal==set(compiled.values())|{str(writer).casefold(),str(preserve).casefold()}
  assert len(compiled)==27 and len(linked)==392
  archives=p['retained_unlinked_archives'][level];assert len(archives)==1
  for archive in archives:assert str(pin(archive)).casefold()not in linked and Path(archive).name not in graph
  cache=pin(folder/'CMakeCache.txt').read_text();assert f'MW34_LEVEL:UNINITIALIZED={level}'in cache and 'registry_build_bindings.hpp'in graph
  levels.append(dict(level=level,literal_COFFs=363,added_literal_COFFs=12,compiled_objects=27,canonical_capture_objects=2,actual_linked_inputs=392,retained_unlinked_archives=1,worker_sha256=w['sha256'],actual_input_machine='AMD64'))
 emit(out,dict(passed=True,scope='Actual O0/O2 root124 final-link compiled source provenance and physical AMD64 COFF/PE review; historical acceptance capture pins and all execution gates are excluded',preparation_sha256=PREPSHA,native_preparation_sha256=NPSHA,build_sha256=digest,levels=levels,new_literal_symbols=new_symbols,literal_COFF_links=726,compiled_objects=54,actual_linked_inputs=784,elapsed_seconds=time.perf_counter()-started),pins)
if __name__=='__main__':
 if sys.argv[1]=='abi':abi(sys.argv[2])
 elif sys.argv[1]=='link':link(*sys.argv[2:])
 else:raise ValueError(sys.argv[1])
