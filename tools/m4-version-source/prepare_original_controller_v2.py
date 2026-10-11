"""Freeze original5 single-worker controller; never invoke a worker or reader."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
PREP='149a328436631f8d7f7f579629deb2a8367bd3d1e76296cbaaaed14385c6fc30'
BUILD='85872a4a2a3932d1c2ab05c28aaad4e8b14a59d2137c9ff8b24e1dc45b75ed87'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 for rel,h in [('original-preparation-r5/report.json',PREP),('original-build-r5/build.json',BUILD)]:
  d=json.loads(pin(R/'reports/m4-version-source'/rel,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
 parent=pin(T/'run_original_v1.py','90e05b415bf8925b8d9aa17ec9b55deb694c09b91e6bd6a261408dcf1b05369f');s=parent.read_text()
 for a,b in [('7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529',PREP),('fd5caff7e35d7ab8e6a10e9d00f41c4ca7ddfcee7ee9261692f54e1fad68a292',BUILD),('original-preparation-r4/report.json','original-preparation-r5/report.json'),('original-build-r4/build.json','original-build-r5/build.json')]:
  assert s.count(a)==1;s=s.replace(a,b)
 s=s.replace('original4','original5');q=T/'run_original_v2.py';assert not q.exists();q.write_text(s);compile(s,str(q),'exec');pin(q);pin(__file__);pin(R/'tools/m4-pipeline/stages.py');out.mkdir(parents=True)
 d=dict(passed=True,controller=str(q),controller_sha256=sha(q),preparation_sha256=PREP,build_sha256=BUILD,scope='One bounded original5 broker/child with isolated byte-identical Windows provider; MW3 cwd/project reports root; transport metadata only; preparation',required_admission_keys=['passed','preparation_sha256','build_sha256','worker_sha256'],worker_invocations=1,broker_child_maximum_ms=180000,stage_timeout_seconds=200,payload_reader_opened=False,original_executed=False,native_executed=False,initializer_credit=0,exact_controller_delta=['original5 prep/build paths and exact SHA constants','descriptive original4 labels changed to original5'],files=pins);p=out/'report.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),controller_sha256=sha(q),passed=True,executed=False)))
if __name__=='__main__':main(sys.argv[1])
