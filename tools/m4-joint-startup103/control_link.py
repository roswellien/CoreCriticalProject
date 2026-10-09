"""Independently bind the frozen CMake/Ninja link graph to actual control workers."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup103-root'/name;assert not out.exists();out.mkdir(parents=True);pins={};levels=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return p
 buildpath=pin(ROOT/'reports/m4-mfc-review/controls-build-r2/build.json','0664820d6ed94ec6d28024f1f0571b26d581f723e824b53777491d75c20e436c');build=json.loads(buildpath.read_bytes());assert build['passed']
 preparation=json.loads(pin(ROOT/'reports/m4-joint-startup103/preparation-r1/report.json','b8d18bc4765dee58c6a4e62082f2d74497833be1c8df0eee76532807c841bde6').read_bytes())
 cmake=pin(buildpath.parent/'CMakeLists.txt');source=cmake.read_text();fixture=pin(buildpath.parent/'fixture.cpp');capture=pin(buildpath.parent/'capture.obj');preserve=pin(ROOT/'reports/m4-capture-direct/build-r4/preserve.obj')
 assert str(fixture).replace('\\','/')in source and str(capture).replace('\\','/')in source
 assert '${MW34_OBJECTS}'in source and '${MW34_REGISTRY}'in source and '${MW34_WRITER}'in source
 assert all(c['exit_code']==0 for c in build['commands'])
 for level in('O0','O2'):
  worker=build['workers'][level];exe=pin(worker['path'],worker['sha256']);folder=exe.parent;graphpath=pin(folder/'build.ninja');graph=graphpath.read_text();assert '/machine:x64'in graph
  target=exe.name;line=next(s for s in graph.splitlines()if s.startswith('build '+target+': CXX_EXECUTABLE_LINKER'))
  # Ninja drive colons and spaces are escaped; the resulting object tokens are
  # compared as exact absolute paths rather than loose filename substrings.
  encoded=line.split(' ',3)[3].split(' |')[0];tokens=encoded.split(' ');linked={str((folder/Path(t.replace('$:',':').replace('$ ',' '))).resolve()).lower()for t in tokens if t.endswith(('.obj','.lib'))}
  objects=worker['objects'];assert objects==preparation['objects'][level]and len(objects)==296
  retained=[]
  for p in objects:
   p=pin(p,build['sources'][str(Path(p).resolve())])
   if p.suffix=='.lib':
    assert p==ROOT/f'build/m4-fdiv-native-build-r3-{level}/fdiv_registry.lib'and p.name not in graph
    retained.append(dict(path=str(p),sha256=sha(p),actually_linked=False));continue
   assert p.suffix=='.obj'and str(p).lower()in linked
  assert len(retained)==1
  for p in(capture,preserve):assert str(p).lower()in linked
  writer=pin(ROOT/f'reports/m4-capture-direct/build-r4/capture_direct-{level}.obj');assert str(writer).lower()in linked
  compiled={}
  for s in graph.splitlines():
   if not s.startswith('build ')or ': CXX_COMPILER_'not in s:continue
   output,rest=s[6:].split(': CXX_COMPILER_',1);inputpath=rest.split(' ',1)[1].split(' ||')[0].split(' |')[0].replace('$:',':').replace('$ ',' ')
   compiled[str((folder/Path(inputpath)).resolve()).lower()]=str((folder/Path(output.replace('$:',':').replace('$ ',' '))).resolve()).lower()
  for p in(fixture,ROOT/'reports/m4-mfc-native/preparation-r1/registry_library.cpp',ROOT/'reports/m4-mfc-native/preparation-r1/crt_services.cpp'):
   p=pin(p);assert str(p).lower()in compiled and compiled[str(p).lower()]in linked
  literal_paths={str(Path(p).resolve()).lower()for p in objects if Path(p).suffix=='.obj'};assert len(literal_paths)==295
  assert linked-literal_paths=={str(capture).lower(),str(preserve).lower(),str(writer).lower()}|set(compiled.values())
  for p in compiled.values():pin(p)
  cache=pin(folder/'CMakeCache.txt').read_text();assert re.search(r'^MW34_LEVEL:[^=]+='+level+'$',cache,re.M)
  assert 'registry_build_bindings.hpp'in graph and f'preparation-r1/{level}/registry_build_bindings.hpp'in graph.replace('\\','/')
  levels.append(dict(level=level,declared_source_inputs=296,linked_literal_COFFs=295,retained_unlinked_archives=retained,compiled_objects=len(compiled),linked_inputs=len(linked),fixture_registry_and_capture_linked=True,actual_successful_build=True,worker_sha256=worker['sha256']))
 pin(__file__);report=dict(passed=True,scope='Independent frozen generated CMake/Ninja link graph binds all295 individual literal COFFs, current fixture, derivative registry and actual capture assembly/writer to both executed AMD64 workers. The inherited FDIV proof archive is a retained physical dependency and does not appear in this link graph; actual reached-path scope is reviewed separately.',levels=levels,declared_source_inputs=592,actual_literal_COFF_links=590,retained_unlinked_archives=2,compiled_fixture_registry_checks=6,metadata_correction_only=True,workers_rebuilt=False,source_execution_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),levels=levels)))
if __name__=='__main__':main(sys.argv[1])
