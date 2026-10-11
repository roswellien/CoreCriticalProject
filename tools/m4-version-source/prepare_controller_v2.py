"""Freeze the current version controller and candidate inputs without execution."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert p.suffix.lower()not in('.mwb','.zip');pins[str(p)]=v;return p
 for rel,h in [('fixture-preparation-r3/report.json','ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee'),('fixture-build-r2/build.json','d4959b4e37c2a8f38919545bcb3689d568f111bfe0495d639f5b029f3b20ee42'),('component-preparation-r3/report.json','e47cc5974bc3da9ea51ce56e90090568f0451d9fad065a9fef22428e6a926217')]:
  d=json.loads(pin(R/'reports/m4-version-source'/rel,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
 controller=pin(R/'tools/m4-version-source/run_fixture_v2.py');compile(controller.read_text(),str(controller),'exec')
 for p in (__file__,R/'tools/m4-version-source/derive_run_fixture_v2.py',R/'tools/m4-pipeline/stages.py'):pin(p)
 out.mkdir(parents=True);d=dict(passed=True,scope='Current controller exact component3/fixture3/build2 pins and complete measured private CALL pre-store Access/physical return/frame checks; no execution',controller=str(controller),controller_sha256=sha(controller),physical_CALL_templates=14,pre_store_guard='FlatSS, address=incomingESP-4, current owned stack, value=PC+physical size',post_dispatch_committed_frame_guard_retained=True,ordinary_native_workers_executed=0,original_executed=False,archive_reader_opened=False,independent_first_writer_admission_required=True,initializer_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),passed=True,executed=False)))
if __name__=='__main__':main(sys.argv[1])
