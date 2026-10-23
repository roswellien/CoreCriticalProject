"""ROOT bounded source/control review with preserved terminal failure evidence."""
from pathlib import Path
import hashlib,importlib.util,json,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-semantic-review/root-assist-controller-r1'
assert not out.exists();out.mkdir(parents=True);started=time.monotonic();passed=False;pins={}
try:
 source=R/'tools/m4-138-semantic-review/root_review_assist_v3.py'
 assert sha(source)=='ff28cd61ccefb1ef3b05fb9857bde731007808d7062bc0f8603da9b8161d3e43'
 pins[str(source)]=sha(source)
 spec=importlib.util.spec_from_file_location('root_semantic_assist',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.run('root-ordinary-assist-r1')
 target=R/'reports/m4-138-semantic-review/root-ordinary-assist-r1/report.json'
 d=json.loads(target.read_bytes());assert d['passed'];pins[str(target)]=sha(target)
 for p,h in d['files'].items():assert sha(p)==h;pins[p]=h
 passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
pins[str(Path(__file__).resolve())]=sha(__file__)
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,assist_executed=True,elapsed_seconds=time.monotonic()-started,semantic_main_executed=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))),flush=True)
raise SystemExit(0 if passed else 1)
