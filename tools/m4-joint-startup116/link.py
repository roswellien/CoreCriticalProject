"""Bind every actual linked literal and compiled input to both final workers."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(buildpath,digest,name):
 out=ROOT/'reports/m4-joint-startup116-root'/name;assert not out.exists();out.mkdir(parents=True);pins={};levels=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return p
 buildpath=pin(buildpath,digest);b=json.loads(buildpath.read_bytes());assert b['passed']
 prep_path=pin(b['preparation'],b['preparation_sha256']);prep=prep_path.parent;p=json.loads(prep_path.read_bytes());assert p['passed']and p['linked_literal_COFFs_per_level']>=312
 literal_count=p['linked_literal_COFFs_per_level']
 for pp,h in json.loads(pin(buildpath.parent/'pins.json').read_bytes())['files'].items():pin(pp,h)
 for level in('O0','O2'):
  w=b['workers'][level];exe=pin(w['path'],w['sha256']);folder=exe.parent;graph=pin(folder/'build.ninja').read_text();assert '/machine:x64'in graph
  line=next(x for x in graph.splitlines()if x.startswith('build '+exe.name+': CXX_EXECUTABLE_LINKER'))
  tokens=line.split(' ',3)[3].split(' |')[0].split(' ')
  linked={str((folder/Path(t.replace('$:',':').replace('$ ',' '))).resolve()).casefold()for t in tokens if t.endswith(('.obj','.lib'))}
  objects=w['objects'];assert objects==p['objects'][level]and len(objects)==literal_count and all(Path(x).suffix=='.obj'for x in objects)
  literal={str(pin(x)).casefold()for x in objects};assert len(literal)==literal_count and literal<=linked
  compiled={}
  for line in graph.splitlines():
   if not line.startswith('build ')or ': CXX_COMPILER_'not in line:continue
   output,rest=line[6:].split(': CXX_COMPILER_',1);source=rest.split(' ',1)[1].split(' ||')[0].split(' |')[0].replace('$:',':').replace('$ ',' ')
   compiled[str((folder/Path(source)).resolve()).casefold()]=str((folder/Path(output.replace('$:',':').replace('$ ',' '))).resolve()).casefold()
  for source in(prep/'native_main.cpp',Path(p['native_library']),Path(p['native_include'])/'crt_services.cpp'):
   key=str(pin(source)).casefold();assert key in compiled and compiled[key]in linked
  for source,obj in compiled.items():pin(source);pin(obj)
  writer=pin(ROOT/f'reports/m4-capture-direct/build-r4/capture_direct-{level}.obj');preserve=pin(ROOT/'reports/m4-capture-direct/build-r4/preserve.obj')
  assert linked-literal==set(compiled.values())|{str(writer).casefold(),str(preserve).casefold()}
  assert len(compiled)==27 and len(linked)==literal_count+29
  archives=p['retained_unlinked_archives'][level];assert len(archives)==1
  for archive in archives:assert str(pin(archive)).casefold()not in linked and Path(archive).name not in graph
  cache=pin(folder/'CMakeCache.txt').read_text();assert f'MW34_LEVEL:UNINITIALIZED={level}'in cache and 'registry_build_bindings.hpp'in graph
  levels.append(dict(level=level,literal_COFFs=literal_count,compiled_objects=len(compiled),canonical_capture_objects=2,actual_linked_inputs=len(linked),retained_unlinked_archives=1,worker_sha256=w['sha256']))
 pin(__file__);r=dict(passed=True,scope='Actual final O0/O2 CMake/Ninja link input provenance; execution credit remains a separate gate',literal_COFF_links=2*literal_count,compiled_objects=54,actual_linked_inputs=2*(literal_count+29),retained_unlinked_archives=2,levels=levels,files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),levels=levels)))
if __name__=='__main__':main(*sys.argv[1:])
