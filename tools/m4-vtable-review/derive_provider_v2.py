"""Additive syntax-checked provider observer repair; prior preparation remains immutable."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-vtable-review'/name;assert not out.exists();out.mkdir();pins={};generated={}
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 parent=pin(R/'reports/m4-vtable-review/provider-preparation-r2/report.json');v=json.loads(parent.read_bytes());assert v['passed']
 for p,h in v['generated'].items():assert sha(p)==h;pin(p)
 a=pin(H/'final_observer120.py').read_text();assert a.count('old_ownerand')==1;a=a.replace('old_ownerand','old_owner and');ast.parse(a)
 b=pin(H/'observe120.py').read_text().replace('final_observer120','final_observer120_v2').replace('finally:a.close()','finally:a.close();del a');ast.parse(b)
 for name_,s in [('final_observer120_v2.py',a),('observe120_v2.py',b)]:
  p=H/name_;assert not p.exists();p.write_text(s);generated[str(p.resolve())]=sha(p)
 for q in ('exact_equal.py','vtable_model.py','event_model.py','string_observer116.py'):ast.parse(pin(H/q).read_text())
 pin(__file__);r=dict(passed=True,parent=str(parent),parent_sha256=sha(parent),scope='Additive syntax/parse repair of observation-only source; persistent semantic inputs unchanged, unused old draft preserved. Adds safe closed-reader release between native levels.',files=pins,generated=generated,syntax_checked=True,exact_equal_unchanged=True,prior_accepted_sources_modified=False,initializer_credit=False,native_executed=False)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
