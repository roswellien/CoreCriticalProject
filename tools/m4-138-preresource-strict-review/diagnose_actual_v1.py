"""Finite actual output inventory/schema check only; literal source review separate."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(execution,name):
 out=R/'reports/m4-138-preresource-strict-review'/name;assert not out.exists();out.mkdir();files={};passed=False;counts={}
 epath=Path(execution).resolve();e=json.loads(epath.read_bytes());assert e['passed']and e['worker_closed']and e['worker_executed']and e['facts']['exit_code']==0
 admitted=e['files'];files[str(epath)]=sha(epath)
 def pin(p):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';h=sha(p);assert admitted.get(str(p))==h;assert files.setdefault(str(p),h)==h;return p
 prep=R/'reports/m4-138-preresource-strict-review/preparation-r2/report.json';v=json.loads(prep.read_bytes());assert v['passed'];files[str(prep)]=sha(prep)
 helper=prep.parent/'ordinary_case_v2.py';assert sha(helper)==v['files'][str(helper)];files[str(helper)]=sha(helper)
 s=importlib.util.spec_from_file_location('actual_inventory_only',helper);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 try:
  a=m.DirectoryCase(e['facts']['arguments'][-3],pin);counts=m.strict_case(a,e['mode']);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Actual single-case complete named retry/frame/13-root/no-widget-work/cleanup schema check. Literal causal derivation and physical native API lifetime proof NOT executed here',execution=str(epath),execution_sha256=files[str(epath)],level=e['level'],mode=e['mode'],counts=counts,literal_source_review_executed=False,physical_API_lifetime_review_executed=False,full_strict_gate_closed=False,worker_executed=False,capture_reader_opened=False,accepted_function_credit=0,initializer_credit=0,files=files)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2])
