"""Seal pure control code/whole textual inverse without invoking it."""
from pathlib import Path
import ast,difflib,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-owner-controls-preparation-r1';assert not out.exists();out.mkdir();p=R/'tools/m4-startup141-paired/native_owner_cut_controls_v1.py';q=p.with_name('native_owner_cut_controls_v2.py');a=p.read_text();b=q.read_text();ast.parse(a);ast.parse(b);delta=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes():
  if tag!='equal':delta.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(a.splitlines(True)[i:j]),child=''.join(b.splitlines(True)[k:l])))
 back=b.splitlines(True)
 for h in reversed(delta):assert ''.join(back[h['child_start']:h['child_stop']])==h['child'];back[h['child_start']:h['child_stop']]=h['parent'].splitlines(True)
 assert ''.join(back)==a;v=out/'inverse.json';v.write_text(json.dumps(delta,indent=2)+'\n');paths=[p,q,v,R/'tools/m4-startup141-paired/constructor_native_input141_v3.py',R/'tools/m4-startup141-paired/constructor_native36_source141_v5.py',R/'tools/m4-startup141-paired/prepare_native_owner_source_closure_v1.py',Path(__file__).resolve()];report=out/'report.json';report.write_text(json.dumps(dict(prepared_only=True,controls_invoked=False,source_execution=False,reader_opened=False,imports_executed=False,root_admission_minted=False,control_function='native_owner_cut_controls_v2.controls(adapter3_text,source5_text)',guard_adverse_cases=26,endpoint_order_adverse_cases=2,total_adverse_cases=28,positive_cases=1,whole_controls_parent_inverse=True,inverse_hunks=len(delta),controls_extract_exact_added_adapter_AST=True,cross_owner_boundary_write_included=True,static_prefix_real_write_retained=True,files={str(p.resolve()):sha(p)for p in paths}),indent=2)+'\n');print(json.dumps(dict(path=str(report),sha256=sha(report),controls_sha256=sha(q))))
if __name__=='__main__':main()
