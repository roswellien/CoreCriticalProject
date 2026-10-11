"""Exact controls-to-final125 native/literal link equivalence; no capture reader."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh final equivalence review');out.mkdir(parents=True);pins={};rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Exact compiled/source identity '+str(p));need(str(p)not in pins or pins[str(p)]==a,'Stable current identity');pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 cbp=R/'reports/m4-tree-review/controls-build-r3/build.json';fbp=R/'reports/m4-joint-startup125/build-r1/build.json'
 cb=read(cbp,'ce9c498c654f9711c11873f457d7aafa38eae37a4b9e2c000a659bfec9a792c5');fb=read(fbp,'cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165')
 cp=read(cb['preparation'],cb['preparation_sha256']);fp=read(fb['preparation'],fb['preparation_sha256']);controls=read(R/'reports/m4-tree-review/controls-validation-r3/report.json','a369de58c7ecdd9b6494a57c74b8e135f85ac56d3588c06fda9e1093ed8eb6e2')
 need(cb['passed']and fb['passed']and controls['passed'],'Current actual controls and final build gates')
 native=read(fp['native_preparation'],fp['native_preparation_sha256']);need(cp['native_preparation_sha256']==fp['native_preparation_sha256']==controls['native_preparation_sha256']=='9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2','Same exact native5 control/final lineage')
 source=Path(native['native_library']);native_dir=Path(native['native_include']);need(Path(cp['native_library'])==source==Path(fp['native_library']),'Same physical compiled library source path')
 for p,h in native['files'].items():
  if Path(p).parent==native_dir:pin(p,h)
 cdir=Path(cp['connected_include']);fdir=Path(fb['preparation']).parent
 # These full consumed registration headers are exactly equal, despite source
 # include-root aliases. Selected-table extents differ intentionally, as the
 # actual controls execute a single registered initializer.
 for n in('registration_contract.hpp',):
  a=pin(cdir/n).read_bytes();b=pin(fdir/n).read_bytes();need(a==b,'Byte-identical full97registration and26page header')
 need('array<unsigned,97>'in a.decode(),'Actual97 declarations')
 for n in('joint_protocol.hpp','native_main.cpp'):
  pin(cdir/n);pin(fdir/n)
 packed=lambda x:x.split('#pragma pack(push,1)',1)[1].split('#pragma pack(pop)',1)[0]
 need(packed((cdir/'joint_protocol.hpp').read_text())==packed((fdir/'joint_protocol.hpp').read_text()),'Control/final fixed packed Native ABI unchanged')
 entry=lambda p:next(l for l in p.read_text().splitlines()if 'static void registration_entry('in l)
 need(entry(cdir/'native_main.cpp')==entry(fdir/'native_main.cpp'),'Exact actual registered Runtime entry service source')
 ninja=pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
 for level in('O0','O2'):
  cworker=pin(cb['workers'][level]['path'],cb['workers'][level]['sha256']);fworker=pin(fb['workers'][level]['path'],fb['workers'][level]['sha256']);cgraph=pin(cworker.parent/'build.ninja').read_text();fgraph=pin(fworker.parent/'build.ninja').read_text()
  objects=cp['objects'][level];need(objects==fp['objects'][level]==cb['workers'][level]['literal_objects']==fb['workers'][level]['objects']and len(objects)==len(set(objects))==371,'Exact same371 literal input identities perlevel')
  def linked(graph,folder,exe):
   line=next(l for l in graph.splitlines()if l.startswith('build '+exe+': CXX_EXECUTABLE_LINKER'))
   tokens=line.split(' ',3)[3].split(' |')[0].split();return {str((folder/Path(t.replace('$:',':').replace('$ ',' '))).resolve()).casefold()for t in tokens if t.endswith(('.obj','.lib'))}
  clink=linked(cgraph,cworker.parent,cworker.name);flink=linked(fgraph,fworker.parent,fworker.name)
  for q in objects:
   v=pin(q,fb['sources'][str(Path(q).resolve())]);need(str(v).casefold()in clink and str(v).casefold()in flink,'Literal object actually linked into both workers')
   need(struct.unpack_from('<H',v.read_bytes())[0]==0x8664,'Every actual literal input AMD64')
  def object_node(graph,folder):
   source_token=str(source).replace(':','$:');line=next(l for l in graph.splitlines()if ': CXX_COMPILER_'in l and source_token in l);node=line[6:].split(': CXX_COMPILER_',1)[0];i=graph.index(line);block=graph[i:graph.index('\nbuild ',i+1)]
   flags=next(l.strip()for l in block.splitlines()if l.strip().startswith('FLAGS ='))
   defines=next(l.strip()for l in block.splitlines()if l.strip().startswith('DEFINES ='))
   return node,pin(folder/node),flags,defines
  cn,co,cf,cd=object_node(cgraph,cworker.parent);fn,fo,ff,fd=object_node(fgraph,fworker.parent);need(cf==ff and cd==fd,'Same actual compiler flags and ISA macros')
  need(str(co).casefold()in clink and str(fo).casefold()in flink,'Actual final and controls compiled library input linked')
  cr=co.read_bytes();fr=fo.read_bytes();need(len(cr)==len(fr)>=20,'Same whole actual COFF extent')
  ch=struct.unpack_from('<HHIIIHH',cr);fh=struct.unpack_from('<HHIIIHH',fr);need(ch[0]==fh[0]==0x8664 and ch[1]==fh[1]and ch[3:]==fh[3:]and ch[5]==0,'AMD64 standard20-byte COFF identity and section/symbol positions')
  different=[i for i,(x,y)in enumerate(zip(cr,fr))if x!=y];need(set(different)<=set(range(4,8))and cr[:4]==fr[:4]and cr[8:]==fr[8:],'Only explicit COFF TimeDateStamp bytes4:8 may differ; all code/data/symbol/relocation/header bytes exact')
  deps=[]
  for label,folder,node,binding_header in(('controls',cworker.parent,cn,cdir/level/'registry_build_bindings.hpp'),('final125',fworker.parent,fn,fdir/level/'registry_build_bindings.hpp')):
   result=subprocess.run([str(ninja),'-t','deps',node],cwd=folder,capture_output=True,timeout=20,creationflags=0x08000000);need(result.returncode==0,'Actual compiler dependency graph')
   report=out/f'{level}-{label}-consumed-dependencies.txt';report.write_bytes(result.stdout+result.stderr);pin(report)
   paths=[Path(l.strip())for l in result.stdout.decode().splitlines()[1:]if l.strip()];need(paths and len(paths)==len(set(paths)),'Complete distinct actual compiler dependencies')
   actual={str(pin(p)).casefold():sha(p)for p in paths};need(str(source).casefold()in actual and str(binding_header).casefold()in actual,'Actual compiler consumed native source and level-specific registration header')
   normalized={('<level-registration-header>'if k==str(binding_header).casefold()else k):v for k,v in actual.items()};deps.append(normalized)
  need(deps[0]==deps[1],'All actual compiler consumed dependencies equal physically, allowing only byte-identical level registration header path alias')
  for header in(cdir/level/'registry_build_bindings.hpp',fdir/level/'registry_build_bindings.hpp'):pin(header)
  need((cdir/level/'registry_build_bindings.hpp').read_bytes()==(fdir/level/'registry_build_bindings.hpp').read_bytes(),'Exact full consumed level registration macro header')
  rows.append(dict(level=level,controls_object=str(co),controls_object_sha256=sha(co),final_object=str(fo),final_object_sha256=sha(fo),whole_object_bytes=len(cr),only_permitted_difference=[4,8],actual_differing_offsets=different,controls_TimeDateStamp=ch[2],final_TimeDateStamp=fh[2],all_non_timestamp_bytes_equal=True,code_data_relocation_symbol_bytes_equal=True,linked_literal_inputs=371,actual_compiler_dependencies=len(deps[0]),compiler_flags=cf,ISA_defines=cd))
 pin(__file__)
 report=dict(passed=True,scope='Fresh controls-to-final125 exact linked native-library/literal/source dependency equivalence; one registered control root, full125 semantic schedule is separate',controls_validation_sha256=sha(R/'reports/m4-tree-review/controls-validation-r3/report.json'),controls_build_sha256=sha(cbp),bound_final_build_sha256=sha(fbp),native_preparation_sha256=fp['native_preparation_sha256'],levels=rows,linked_literal_COFFs_per_level=371,registration_roots=97,level_registration_headers_byte_identical=True,full_registration_headers_byte_identical=True,fixed_ABI_byte_identical=True,only_permitted_COFF_difference=[4,8],parent_build_field_invented=False,capture_payload_read=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),levels=rows)))
if __name__=='__main__':main(sys.argv[1])
