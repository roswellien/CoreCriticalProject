"""Freeze original4 single-worker controller without invoking any worker/reader."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 for rel,h in [('original-preparation-r4/report.json','7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529'),('original-build-r4/build.json','fd5caff7e35d7ab8e6a10e9d00f41c4ca7ddfcee7ee9261692f54e1fad68a292')]:
  d=json.loads(pin(R/'reports/m4-version-source'/rel,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
 p=pin(R/'tools/m4-version-source/run_original_v1.py');compile(p.read_text(),str(p),'exec');pin(__file__);pin(R/'tools/m4-pipeline/stages.py');out.mkdir(parents=True)
 d=dict(passed=True,controller=str(p),controller_sha256=sha(p),scope='One bounded original4 broker/child, MW3 cwd and explicit project reports root, transport metadata only; no execution',required_admission_keys=['passed','preparation_sha256','build_sha256','worker_sha256'],worker_invocations=1,broker_child_maximum_ms=180000,stage_timeout_seconds=200,payload_reader_opened=False,original_executed=False,native_executed=False,initializer_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),passed=True,executed=False)))
if __name__=='__main__':main(sys.argv[1])
