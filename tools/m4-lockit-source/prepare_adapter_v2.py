"""Seal additive interface-compatible adapter bindings before any comparison."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);pins={};generated={}
 for report,digest,target_name in(('connected-preparation-r3','cdf8d9a2fd70816e9d9a9de02f253b75bf9e42e8a64c5308256a45ca55c18535','compare_connected_v4.py'),('provider-preparation-r1','cbbd0144eab914d27cb47db79457b834e47763e0d87a792b4d7b028a41f7def8','compare_provider124_v2.py')):
  p=ROOT/'reports/m4-lockit-source'/report/'report.json';assert sha(p)==digest;pins[str(p)]=digest;d=json.loads(p.read_bytes())
  for path,h in d['files'].items():assert sha(path)==h;pins[path]=h
  s=Path(d['comparer']).read_text();assert s.count('import responses as R')==1;s=s.replace('import responses as R','import responses_v2 as R');ast.parse(s);target=HERE/target_name;assert not target.exists();target.write_text(s);pins[str(target)]=sha(target);generated[target_name]=str(target)
 for p in(HERE/'responses_v2.py',Path(__file__).resolve()):pins[str(p)]=sha(p)
 d=dict(passed=True,scope='Complete inherited typed-contract module interface restored by additive alias exports; original response source computation unchanged',generated=generated,source_response_semantics_unchanged=True,native_compared=False,initializer_credit=False,files=pins);(out/'report.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),generated=generated)))
if __name__=='__main__':main(sys.argv[1])
