"""Bind only the additive borrowed onexit growth guard to current138."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 pp=R/'reports/m4-joint-startup138/preparation-r3/report.json';sp=R/'reports/m4-fps-native/service-preparation-r3/report.json';out=pp.parent.parent/name;need(not out.exists(),'Fresh growth-guard Context revision');out.mkdir();pins={};copies=[];passed=False;d={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary preparation only');v=sha(p);need(h is None or h==v,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 try:
  pin(pp,'ea6c0f3713796e85042039c8af7cf36f0b9faee7035cdf511be1af000023d7ca');pin(sp,'cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9');d=json.loads(pp.read_bytes());service=json.loads(sp.read_bytes());need(d['passed']and service['passed'],'Current138 and finite growth service prepared')
  for receipt in(d,service):
   for p,h in receipt['files'].items():pin(p,h)
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':
    q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);raw=p.read_bytes();b=raw.replace(pp.parent.as_posix().encode(),out.as_posix().encode());q.write_bytes(b);copies.append(dict(source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p),current_sha256=sha(q),path_rebase=raw!=b,byte_identical=raw==b))
  for name in('native_main.cpp','widget_services.hpp','widget-phase-map.json','source-page-union.json','onexit_session.hpp','connected_hardware_boundary.s'):
   need((out/name).read_bytes()==(pp.parent/name).read_bytes(),'Whole Context/source/ABI file unchanged '+name)
  need((out/'onexit_session.hpp').read_bytes()==(sp.parent/'session.hpp').read_bytes(),'Complete consumed Session header equals current service')
  generated={}
  for p in out.rglob('*'):
   if p.is_file():pin(p);generated[str(p.resolve())]=sha(p)
  pin(__file__);pin(sys.executable);d.update(native_library=service['native_library'],native_include=service['native_include'],borrowed_service_preparation=str(sp.resolve()),borrowed_service_preparation_sha256=sha(sp),generated_sources=generated);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d.update(passed=passed,scope='Unexecuted current138 measured-GDI shared Context, with only actual source-owned borrowed callback registry growth admission changed',parent_preparation=str(pp.resolve()),parent_preparation_sha256=sha(pp),prior_copy_relations=copies,files=pins,capture_archive_reader_opened=False,worker_executed=False,execution_admitted=False,initializer_credit=0);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
