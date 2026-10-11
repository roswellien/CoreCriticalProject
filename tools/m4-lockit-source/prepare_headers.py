"""Retain independent source byte provenance needed by the paired page gate."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);pins={};targets={}
 for oldname,newname in(('compare_connected_v4.py','compare_connected_v5.py'),('compare_provider124_v3.py','compare_provider124_v4.py')):
  old=HERE/oldname;pins[str(old)]=sha(old);s=old.read_text();assert s.count('import continuity as A')==1;s=s.replace('import continuity as A','import continuity as A\nimport header_derivations as H');assert s.count('lockit_rows=[]')==1;s=s.replace('lockit_rows=[]','lockit_rows=[];lockit_headers=[]');needle='expected_callbacks.append(roots[entry]);responses.completed_registry';assert s.count(needle)==1;s=s.replace(needle,'lockit_headers+=H.derive(machine,root_access_start,entry,before_pages,PAGES,cpu,level,seq,phase);'+needle);needle="('Lockit-source-derivations.json',lockit_rows)";assert s.count(needle)==1;s=s.replace(needle,needle+",('Lockit-header-derivations.json',lockit_headers)");needle='  passed=True\n except';assert s.count(needle)==1;s=s.replace(needle,"  need(len(lockit_headers)==108,'All nine exact new header byte source derivations across12cases');pin(ROOT/'tools/m4-lockit-source/header_derivations.py')\n"+needle);ast.parse(s);target=HERE/newname;assert not target.exists();target.write_text(s);pins[str(target)]=sha(target);targets[newname]=str(target)
 for name,h in(('adapter-preparation-r2','462f25521fa7f6ead36aeacf7290a75450da209055380eaa786a4b8690c3d2d3'),('provider-preparation-r2','6d6c0aa1fc8f6eaee462595afbf22af6f99838f6b1fd0ed96fdf77b70a29e967')):
  p=ROOT/'reports/m4-lockit-source'/name/'report.json';assert sha(p)==h;pins[str(p)]=h;d=json.loads(p.read_bytes())
  for p,h in d['files'].items():assert sha(p)==h;pins[p]=h
 for p in(HERE/'header_derivations.py',Path(__file__).resolve()):pins[str(p)]=sha(p)
 d=dict(passed=True,scope='Exact source branch-local nine-byte header derivations retained; comparison reads no candidate AFTER byte',generated=targets,header_fields=9,native_compared=False,initializer_credit=False,files=pins);(out/'report.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),generated=targets)))
if __name__=='__main__':main(sys.argv[1])
