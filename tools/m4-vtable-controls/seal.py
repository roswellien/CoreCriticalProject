"""Immutable exact compiled fixture and checker source snapshots after successful checks."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-vtable-controls'/name;assert not out.exists();out.mkdir();pins={};copies=[];dependencies={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 for path,h in [('build-r1/build.json','ffb1d2ba01313fafe3628c9ef071d67117488fe0975f2a8ded0d5d2ef5acda36'),('execution-r1/report.json','7f94c71955cdb44e1547570005acd5fb471089efe2cee83214bddf24de6e48fb'),('check-r1/report.json','0ab89ceb89d871ba9e56bbbc55227b6adc8f1f27d13d24b7772203ddc9db31de'),('static-r1/report.json',None)]:
  p=pin(R/'reports/m4-vtable-controls'/path,h);r=json.loads(p.read_bytes());assert r['passed'];dependencies[str(p)]=sha(p)
 src=[H/n for n in ('hooks.hpp','fixture.inc','build.py','build.ps1','capture.py','check.py','static.py','scaffold.py','seal.py')]+[R/'reports/m4-vtable-controls/build-r1'/n for n in ('fixture.cpp','hooks.hpp','capture.s','current_pages.hpp','CMakeLists.txt')]+[R/'tools/m4-container-controls/check_v2.py',R/'tools/m4-strings-review/fixture_hooks_v2.hpp',R/'tools/m4-strings-review/fixture_hooks.hpp']
 for p in src:
  p=pin(p);q=out/'sources'/p.parent.name/p.name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());pin(q,sha(p));copies.append(dict(source=str(p),copy=str(q),sha256=sha(p)))
 check=json.loads((R/'reports/m4-vtable-controls/check-r1/report.json').read_bytes());assert check['counts']['actual_attempts']==108 and check['counts']['causal_refusals']==52 and check['counts']['retry_refusals']==54
 r=dict(passed=True,copied_sources=len(copies),copies=copies,dependencies=dependencies,counts=check['counts'],files=pins,scope='Frozen successful27scenario local vtable fixture and exact-byte checker; compiled source copies and complete actual capture/check gates pinned. Independent causal audit remains separate.',initializer_credit=False)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),copied_sources=len(copies))))
if __name__=='__main__':main(sys.argv[1])
