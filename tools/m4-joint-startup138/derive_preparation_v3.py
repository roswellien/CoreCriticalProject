"""Bind only the additive measured GDI component to the shared138 worker."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 pp=R/'reports/m4-joint-startup138/preparation-r2/report.json';out=pp.parent.parent/name;need(not out.exists(),'Fresh GDI joint revision');out.mkdir();pins={};copies=[];passed=False;d={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary inputs only');v=sha(p);need(h is None or h==v,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 try:
  pin(pp,'d20bd38e5c4f8021e204808e37c4ef752b21053210b493bdad495bd3c4f7c7aa');d=json.loads(pp.read_bytes());need(d['passed'],'Current unexecuted138 Context');wp=pin(R/'reports/m4-fps-native/connected-component-preparation-r4/report.json','c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21');wb=pin(R/'reports/m4-fps-native/connected-component-build-r4/build.json','d7e4d35fe95f7524d2c9a059e115de674d74752fc557d31400e70d319f1fa119');widget=json.loads(wp.read_bytes());build=json.loads(wb.read_bytes());need(widget['passed']and build['passed']and build['preparation_sha256']==sha(wp),'Actual GDI library compilation')
  for receipt in(d,widget,build):
   for p,h in receipt['files'].items():pin(p,h)
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':
    q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);raw=p.read_bytes();b=raw.replace(pp.parent.as_posix().encode(),out.as_posix().encode());q.write_bytes(b);copies.append(dict(source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p),path_rebase=raw!=b))
  for level in('O0','O2'):
   lib=pin(build['levels'][level]['library'],build['levels'][level]['library_sha256']);h=out/level/'widget_build_bindings.hpp';h.write_text('#pragma once\ninline constexpr const char*widget_component_gate="'+sha(wp)+'";\ninline constexpr const char*widget_library_sha="'+sha(lib)+'";\n')
  for row in copies:row.update(current_sha256=sha(row['target']),byte_identical=sha(row['target'])==row['source_sha256']);need(row['byte_identical']or row['path_rebase']or Path(row['target']).name=='widget_build_bindings.hpp','Only metadata/path binding changes')
  # The actual selected Context source and services body remain byte-identical.
  need((out/'native_main.cpp').read_bytes()==(pp.parent/'native_main.cpp').read_bytes(),'Whole current138 Context main unchanged');need((out/'widget_services.hpp').read_bytes()==(pp.parent/'widget_services.hpp').read_bytes(),'Whole caller registry service unchanged');need((out/'widget-phase-map.json').read_bytes()==(pp.parent/'widget-phase-map.json').read_bytes(),'Whole table associations unchanged');need((out/'source-page-union.json').read_bytes()==(pp.parent/'source-page-union.json').read_bytes(),'Whole69 source inventory unchanged')
  generated={}
  for p in out.rglob('*'):
   if p.is_file():pin(p);generated[str(p.resolve())]=sha(p)
  pin(__file__);pin(sys.executable);d.update(widget_component_include=str(wp.parent.resolve()),widget_component_preparation=str(wp.resolve()),widget_component_preparation_sha256=sha(wp),widget_component_build=str(wb.resolve()),widget_component_build_sha256=sha(wb),widget_libraries={k:v['library']for k,v in build['levels'].items()},generated_sources=generated);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d.update(passed=passed,parent_preparation=str(pp.resolve()),parent_preparation_sha256=sha(pp),prior_copy_relations=copies,files=pins,scope='Unexecuted current138 Context with source/manual GDI owning-image observations; whole shared Context/service/source schedule unchanged',worker_executed=False,execution_admitted=False,initializer_credit=0);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
