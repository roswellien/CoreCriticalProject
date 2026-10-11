"""Freeze original6 single-worker controller; no launch or payload reader."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
PREP='37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6'
BUILD='cbe606c38282b970b3977305a030744f450923b928140d3f57b3502d7e36d4b7'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 for rel,h in [('original-controller-preparation-r2/report.json','b5262ea347b202137ac0b0192fa98a507da67876a3e70e800425e1ecab81b652'),('original-preparation-r6/report.json',PREP),('original-build-r6/build.json',BUILD)]:
  d=json.loads(pin(R/'reports/m4-version-source'/rel,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
 s=pin(T/'run_original_v2.py','b7e7decb61b145fc6177a24af7011cd50c98739f17202addd119957b63e7b18a').read_text()
 for a,b in [('149a328436631f8d7f7f579629deb2a8367bd3d1e76296cbaaaed14385c6fc30',PREP),('85872a4a2a3932d1c2ab05c28aaad4e8b14a59d2137c9ff8b24e1dc45b75ed87',BUILD),('original-preparation-r5/report.json','original-preparation-r6/report.json'),('original-build-r5/build.json','original-build-r6/build.json')]:
  assert s.count(a)==1;s=s.replace(a,b,1)
 s=s.replace('original5','original6');q=T/'run_original_v3.py';assert not q.exists();q.write_text(s);compile(s,str(q),'exec');pin(q);pin(__file__);out.mkdir(parents=True)
 d=dict(passed=True,controller=str(q),controller_sha256=sha(q),preparation_sha256=PREP,build_sha256=BUILD,scope='One bounded original6 broker/child, physical provider file IDs, isolated Windows provider; preparation only',required_admission_keys=['passed','preparation_sha256','build_sha256','worker_sha256'],worker_invocations=1,broker_child_maximum_ms=180000,stage_timeout_seconds=200,payload_reader_opened=False,original_executed=False,native_executed=False,initializer_credit=0,exact_controller_delta=['original6 prep/build paths and exact SHA constants','descriptive original5 labels changed to original6'],files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),controller_sha256=sha(T/'run_original_v3.py'),passed=True,executed=False)))
if __name__=='__main__':main(sys.argv[1])
