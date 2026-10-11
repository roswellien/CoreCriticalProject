"""External explicit clang COFF assembly composition of observed prep4."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};generated={};passed=False;parent={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;(str(p)not in pins or pins[str(p)]==v)or(_ for _ in()).throw(ValueError('Stable input'));pins[str(p)]=v;return p
 try:
  pp=pin(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r4/report.json','15647e6847286ec48f1f5a48b8214d8fcaca4cda8c8e907b742588babda29ebd');parent=json.loads(pp.read_bytes());assert parent['passed']
  for p,h in parent['files'].items():pin(p,h)
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(pin(p).read_bytes().replace(pp.parent.as_posix().encode(),out.as_posix().encode()))
  cm=(out/'CMakeLists.txt').read_text();assert cm.count('LANGUAGES CXX ASM)')==1;cm=cm.replace('LANGUAGES CXX ASM)','LANGUAGES CXX)');assert cm.count('"${MW34_PREP}/connected_hardware_boundary.s"')==1;cm=cm.replace('"${MW34_PREP}/connected_hardware_boundary.s"','"${MW34_HARDWARE_OBJECT}"');cm=cm.replace('if(NOT MW34_ROOT OR','if(NOT MW34_HARDWARE_OBJECT OR NOT MW34_ROOT OR');(out/'CMakeLists.txt').write_text(cm)
  for q in out.rglob('*'):
   if q.is_file():generated[str(q.resolve())]=sha(q);pin(q,generated[str(q.resolve())])
  pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(parent);report.update(passed=passed,parent_observed_preparation=str(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r4/report.json'),parent_observed_preparation_sha256='15647e6847286ec48f1f5a48b8214d8fcaca4cda8c8e907b742588babda29ebd',generated_sources=generated,files=pins,ASM_object_compiled_by_explicit_clang_command=True,worker_executed=False,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
